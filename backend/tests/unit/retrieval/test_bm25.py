import pytest

from app.documents.models import Chunk
from app.retrieval.bm25 import BM25Retriever


@pytest.fixture
def sample_chunks() -> list[Chunk]:
    return [
        Chunk(
            chunk_id="chunk_1",
            document_id="doc_policy",
            text="Quy định nghỉ phép năm 2026 của nhân viên chính thức.",
            page_numbers=(1,),
            token_count=10,
        ),
        Chunk(
            chunk_id="chunk_2",
            document_id="doc_policy",
            text="Quy định nghỉ ốm đau và bảo hiểm y tế năm 2026.",
            page_numbers=(2,),
            token_count=11,
        ),
        Chunk(
            chunk_id="chunk_3",
            document_id="doc_tech",
            text="Kiến trúc hệ thống Retrieval-Augmented Generation RAG và Vector Database.",
            page_numbers=(1,),
            token_count=10,
        ),
    ]


def test_bm25_tokenize() -> None:
    retriever = BM25Retriever()
    text = "Hợp đồng (Kinh tế) số: 123/2026/HĐ-KT @HCM...!"
    tokens = retriever.tokenize(text)
    assert "hợp" in tokens
    assert "đồng" in tokens
    assert "kinh" in tokens
    assert "tế" in tokens
    assert "123" in tokens
    assert "2026" in tokens
    assert "hđ" in tokens
    assert "kt" in tokens
    assert "hcm" in tokens
    # Đảm bảo không còn ký tự đặc biệt dính vào token
    assert all("@" not in t and ":" not in t and "/" not in t for t in tokens)


def test_bm25_indexing_and_statistics(sample_chunks: list[Chunk]) -> None:
    retriever = BM25Retriever()
    indexed_count = retriever.index_chunks(sample_chunks)

    assert indexed_count == 3
    assert len(retriever._corpus) == 3
    assert retriever._avgdl > 0

    # Từ "quy" và "định" xuất hiện trong 2 chunks (chunk_1, chunk_2)
    assert retriever._doc_frequencies["quy"] == 2
    assert retriever._doc_frequencies["định"] == 2
    # Từ "rag" chỉ xuất hiện trong 1 chunk (chunk_3)
    assert retriever._doc_frequencies["rag"] == 1

    # IDF của từ hiếm ("rag") phải lớn hơn IDF của từ phổ biến hơn ("quy")
    assert retriever._idf["rag"] > retriever._idf["quy"]


def test_bm25_search_ranking(sample_chunks: list[Chunk]) -> None:
    retriever = BM25Retriever()
    retriever.index_chunks(sample_chunks)

    # Tìm kiếm chính xác về nghỉ phép
    results = retriever.search("nghỉ phép 2026", top_k=2)
    assert len(results) >= 1
    # chunk_1 có cả "nghỉ", "phép", "2026" nên phải xếp đầu tiên
    assert results[0].chunk_id == "chunk_1"
    assert results[0].score > 0

    # Tìm kiếm về RAG
    rag_results = retriever.search("RAG Vector Database", top_k=1)
    assert len(rag_results) == 1
    assert rag_results[0].chunk_id == "chunk_3"


def test_bm25_search_with_document_filter(sample_chunks: list[Chunk]) -> None:
    retriever = BM25Retriever()
    retriever.index_chunks(sample_chunks)

    # Lọc chỉ trong doc_tech
    results = retriever.search("2026 nghỉ phép", top_k=5, document_id="doc_tech")
    # doc_tech không chứa từ khóa này
    assert len(results) == 0

    # Lọc trong doc_policy
    results_policy = retriever.search("2026", top_k=5, document_id="doc_policy")
    assert len(results_policy) == 2
    assert all(r.document_id == "doc_policy" for r in results_policy)


def test_bm25_delete_by_document(sample_chunks: list[Chunk]) -> None:
    retriever = BM25Retriever()
    retriever.index_chunks(sample_chunks)

    deleted = retriever.delete_by_document("doc_policy")
    assert deleted == 2
    assert len(retriever._corpus) == 1
    assert "chunk_1" not in retriever._corpus
    assert "chunk_2" not in retriever._corpus
    assert "chunk_3" in retriever._corpus

    # Thống kê phải được cập nhật lại
    assert "quy" not in retriever._doc_frequencies
    assert retriever._doc_frequencies["rag"] == 1
