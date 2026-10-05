import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_search_service
from app.documents.models import Chunk
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_search_api_empty_query_fails_validation(client: TestClient) -> None:
    # Query rỗng phải bị Pydantic validate văng 422
    response = client.post("/api/v1/search", json={"query": ""})
    assert response.status_code == 422


def test_search_api_returns_results(client: TestClient) -> None:
    # Nạp sẵn 1 chunk vào search service để test
    search_service = get_search_service()
    chunks = [
        Chunk(
            chunk_id="chk_api_01",
            document_id="doc_api_test",
            text="Hệ thống trí tuệ tài liệu DocMind sử dụng FastAPI và Vector Search.",
            page_numbers=(1,),
            token_count=15,
        ),
    ]
    search_service.index_chunks(chunks)

    response = client.post(
        "/api/v1/search",
        json={
            "query": "DocMind su dung cong nghe gi?",
            "top_k": 3,
            "document_id": "doc_api_test",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "DocMind su dung cong nghe gi?"
    assert data["total_results"] == 1
    assert data["results"][0]["chunk_id"] == "chk_api_01"
    assert data["results"][0]["document_id"] == "doc_api_test"
    assert "DocMind" in data["results"][0]["text"]
