from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_rag_service
from app.documents.models import Chunk
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.service import EmbeddingService
from app.llm.base import MockLLMProvider
from app.main import app
from app.rag.context_builder import ContextBuilder
from app.rag.service import RAGService
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.reranker import MockReranker
from app.retrieval.service import HybridSearchService
from app.retrieval.vector_store import InMemoryVectorStore


@pytest.fixture
def test_rag_service() -> RAGService:
    """Tạo RAGService biệt lập với mock data để kiểm thử không gọi API bên ngoài."""
    vector_store = InMemoryVectorStore()
    embedding_service = EmbeddingService(MockEmbeddingProvider(dimension=64))
    bm25_retriever = BM25Retriever()
    reranker = MockReranker()

    hybrid_service = HybridSearchService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        bm25_retriever=bm25_retriever,
        reranker=reranker,
    )
    context_builder = ContextBuilder(max_context_tokens=2000)
    llm_provider = MockLLMProvider(
        fixed_answer="Nhân viên được hưởng 14 ngày nghỉ phép theo quy định [Nguồn 1]."
    )

    return RAGService(
        retrieval_service=hybrid_service,
        context_builder=context_builder,
        llm_provider=llm_provider,
    )


@pytest.fixture
def client(test_rag_service: RAGService) -> Generator[TestClient, None, None]:
    """Client test với dependency override cho RAGService."""
    app.dependency_overrides[get_rag_service] = lambda: test_rag_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_chat_api_empty_query_fails_validation(client: TestClient) -> None:
    """Kiểm tra câu hỏi rỗng bị Pydantic chặn bằng mã 422."""
    response = client.post("/api/v1/chat", json={"query": ""})
    assert response.status_code == 422


def test_chat_api_whitespace_query_fails(client: TestClient) -> None:
    """Kiểm tra câu hỏi toàn khoảng trắng bị bắt lỗi 400 Bad Request."""
    response = client.post("/api/v1/chat", json={"query": "     "})
    assert response.status_code == 400
    assert "Câu hỏi không được để trống" in response.json()["detail"]


def test_chat_api_success_with_sources(
    client: TestClient, test_rag_service: RAGService
) -> None:
    """Kiểm tra luồng hỏi đáp thành công kèm trích dẫn nguồn."""
    # 1. Nạp chunk mẫu vào Hybrid Search Service
    chunks = [
        Chunk(
            chunk_id="chunk_test_01",
            document_id="doc_hr_policy",
            text="Quy định nghỉ phép: Mỗi nhân viên được hưởng 14 ngày phép hàng năm.",
            page_numbers=(3,),
            token_count=18,
        ),
    ]
    test_rag_service.retrieval_service.index_chunks(chunks)

    # 2. Gửi request hỏi đáp
    response = client.post(
        "/api/v1/chat",
        json={
            "query": "Quy định nghỉ phép như thế nào?",
            "top_k": 3,
            "document_id": "doc_hr_policy",
        },
    )

    # 3. Xác thực phản hồi
    assert response.status_code == 200
    data = response.json()

    assert "14 ngày nghỉ phép" in data["answer"]
    assert len(data["sources"]) == 1

    source = data["sources"][0]
    assert source["source_index"] == 1
    assert source["chunk_id"] == "chunk_test_01"
    assert source["document_id"] == "doc_hr_policy"
    assert source["page_numbers"] == [3]
    assert "Quy định nghỉ phép" in source["snippet"]

    assert data["usage"]["prompt_tokens"] > 0
    assert data["usage"]["completion_tokens"] > 0
    assert data["usage"]["total_tokens"] > 0


def test_chat_api_no_matching_documents(client: TestClient) -> None:
    """Kiểm tra khi không có tài liệu nào liên quan thì sources trả về rỗng."""
    response = client.post(
        "/api/v1/chat",
        json={
            "query": "Chính sách lương thưởng là gì?",
            "top_k": 3,
            "document_id": "non_existent_doc",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sources"] == []


def test_chat_sessions_history_and_deletion(client: TestClient) -> None:
    """Kiểm tra lưu lịch sử chat, truy vấn phiên và xóa phiên trò chuyện."""
    # 1. Gửi tin nhắn đầu tiên (tự động tạo session)
    res1 = client.post("/api/v1/chat", json={"query": "Xin chào hệ thống!"})
    assert res1.status_code == 200
    session_id = res1.json()["session_id"]
    assert session_id.startswith("session_")

    # 2. Gửi tin nhắn tiếp theo trong cùng session
    res2 = client.post(
        "/api/v1/chat",
        json={"query": "Tôi muốn hỏi thêm câu thứ hai.", "session_id": session_id},
    )
    assert res2.status_code == 200
    assert res2.json()["session_id"] == session_id

    # 3. Lấy danh sách sessions
    sessions_res = client.get("/api/v1/chat/sessions")
    assert sessions_res.status_code == 200
    sessions_data = sessions_res.json()
    assert any(s["id"] == session_id for s in sessions_data)

    # 4. Lấy chi tiết session kèm lịch sử tin nhắn
    detail_res = client.get(f"/api/v1/chat/sessions/{session_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == session_id
    # Phải có 4 tin nhắn: user 1, assistant 1, user 2, assistant 2
    assert len(detail_data["messages"]) == 4
    assert detail_data["messages"][0]["role"] == "user"
    assert detail_data["messages"][0]["content"] == "Xin chào hệ thống!"
    assert detail_data["messages"][1]["role"] == "assistant"
    assert detail_data["messages"][2]["role"] == "user"
    assert detail_data["messages"][3]["role"] == "assistant"

    # 5. Xóa session
    del_res = client.delete(f"/api/v1/chat/sessions/{session_id}")
    assert del_res.status_code == 204

    # 6. Kiểm tra session đã bị xóa thật sự
    check_del = client.get(f"/api/v1/chat/sessions/{session_id}")
    assert check_del.status_code == 404

