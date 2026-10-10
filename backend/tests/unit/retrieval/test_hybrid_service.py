import pytest

from app.documents.models import Chunk
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.service import EmbeddingService
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.reranker import MockReranker
from app.retrieval.service import HybridSearchService
from app.retrieval.vector_store import InMemoryVectorStore


@pytest.fixture
def hybrid_service() -> HybridSearchService:
    provider = MockEmbeddingProvider(dimension=16)
    emb_service = EmbeddingService(provider)
    vector_store = InMemoryVectorStore()
    bm25_retriever = BM25Retriever()
    reranker = MockReranker()
    return HybridSearchService(
        embedding_service=emb_service,
        vector_store=vector_store,
        bm25_retriever=bm25_retriever,
        reranker=reranker,
    )


def test_hybrid_search_service_index_and_search(hybrid_service: HybridSearchService) -> None:
    chunks = (
        Chunk(
            chunk_id="chk_01",
            document_id="doc_policy",
            text="Quy định nghỉ phép và chế độ nhân viên năm 2026",
            page_numbers=(1,),
            token_count=10,
        ),
        Chunk(
            chunk_id="chk_02",
            document_id="doc_policy",
            text="Chính sách bảo hiểm y tế và nghỉ ốm đau",
            page_numbers=(2,),
            token_count=9,
        ),
        Chunk(
            chunk_id="chk_03",
            document_id="doc_tech",
            text="Hệ thống trí tuệ nhân tạo và mô hình ngôn ngữ lớn LLM",
            page_numbers=(1,),
            token_count=11,
        ),
    )

    indexed = hybrid_service.index_chunks(chunks)
    assert indexed == 3

    # Kiểm tra cả 2 kho đều đã nhận dữ liệu
    assert len(hybrid_service.vector_store._records) == 3  # type: ignore[attr-defined]
    assert len(hybrid_service.bm25_retriever._corpus) == 3

    # Tìm kiếm với từ khóa chính xác
    results = hybrid_service.search("nghỉ phép 2026", top_k=2)
    assert len(results) <= 2
    assert results[0].chunk_id == "chk_01"


def test_hybrid_search_empty_query(hybrid_service: HybridSearchService) -> None:
    with pytest.raises(ValueError, match="Câu hỏi tìm kiếm không được để trống"):
        hybrid_service.search("   ")


def test_hybrid_search_delete_by_document(hybrid_service: HybridSearchService) -> None:
    chunks = (
        Chunk(
            chunk_id="chk_01",
            document_id="doc_a",
            text="Tài liệu mẫu A",
            page_numbers=(1,),
            token_count=4,
        ),
    )
    hybrid_service.index_chunks(chunks)
    hybrid_service.delete_by_document("doc_a")

    assert len(hybrid_service.vector_store._records) == 0  # type: ignore[attr-defined]
    assert len(hybrid_service.bm25_retriever._corpus) == 0
