from app.documents.models import Chunk
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.service import EmbeddingService
from app.retrieval.models import VectorRecord
from app.retrieval.service import SearchService
from app.retrieval.vector_store import InMemoryVectorStore, cosine_similarity


def test_cosine_similarity() -> None:
    # 2 vector cùng hướng -> cosine = 1.0
    v1 = [1.0, 0.0]
    v2 = [2.0, 0.0]
    assert round(cosine_similarity(v1, v2), 4) == 1.0

    # 2 vector vuông góc -> cosine = 0.0
    v3 = [0.0, 1.0]
    assert round(cosine_similarity(v1, v3), 4) == 0.0


def test_in_memory_vector_store_upsert_and_search() -> None:
    store = InMemoryVectorStore()
    records = [
        VectorRecord(
            id="c1",
            vector=[1.0, 0.0, 0.0],
            payload={"document_id": "doc_a", "text": "Đoạn văn A", "page_numbers": [1]},
        ),
        VectorRecord(
            id="c2",
            vector=[0.0, 1.0, 0.0],
            payload={"document_id": "doc_b", "text": "Đoạn văn B", "page_numbers": [2]},
        ),
    ]
    store.upsert(records)

    # Search với vector gần với c1 hơn
    results = store.search(query_vector=[0.9, 0.1, 0.0], top_k=1)
    assert len(results) == 1
    assert results[0].chunk_id == "c1"
    assert results[0].document_id == "doc_a"
    assert results[0].score > 0.8

    # Search kèm bộ lọc document_id
    filtered = store.search(query_vector=[1.0, 0.0, 0.0], top_k=2, document_id="doc_b")
    assert len(filtered) == 1
    assert filtered[0].chunk_id == "c2"


def test_search_service_end_to_end() -> None:
    provider = MockEmbeddingProvider(dimension=16)
    emb_service = EmbeddingService(provider)
    vector_store = InMemoryVectorStore()
    search_service = SearchService(emb_service, vector_store)

    chunks = (
        Chunk(
            chunk_id="chk_01",
            document_id="doc_law",
            text="Luật thương mại sửa đổi 2026",
            page_numbers=(1, 2),
            token_count=10,
        ),
        Chunk(
            chunk_id="chk_02",
            document_id="doc_tech",
            text="Mô hình ngôn ngữ lớn LLM",
            page_numbers=(3,),
            token_count=8,
        ),
    )

    indexed_count = search_service.index_chunks(chunks)
    assert indexed_count == 2

    results = search_service.search("Tìm thông tin về luật thương mại", top_k=2)
    assert len(results) == 2
    assert all(r.score is not None for r in results)
