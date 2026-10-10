from app.retrieval.models import SearchResult
from app.retrieval.reranker import MockReranker


def test_mock_reranker_jaccard_ranking() -> None:
    reranker = MockReranker()
    c1 = SearchResult(
        chunk_id="c1",
        document_id="doc1",
        text="Công ty thông báo lịch nghỉ Tết năm 2026",
        page_numbers=(1,),
        score=0.5,
    )
    c2 = SearchResult(
        chunk_id="c2",
        document_id="doc1",
        text="Quy định nghỉ phép năm 2026 cho toàn thể nhân viên",
        page_numbers=(2,),
        score=0.4,
    )
    c3 = SearchResult(
        chunk_id="c3",
        document_id="doc2",
        text="Hướng dẫn cài đặt hệ thống máy chủ",
        page_numbers=(1,),
        score=0.8,
    )

    query = "nghỉ phép năm 2026"
    results = reranker.rerank(query, [c1, c2, c3], top_k=2)

    assert len(results) == 2
    # c2 trùng cả "nghỉ", "phép", "năm", "2026" nên điểm Jaccard phải cao nhất
    assert results[0].chunk_id == "c2"
    assert results[0].score > results[1].score


def test_mock_reranker_position_bonus() -> None:
    reranker = MockReranker()
    # 2 chunk có cùng số lượng từ trùng, nhưng c1 có từ khóa ở ngay đầu câu
    c1 = SearchResult(
        chunk_id="c1",
        document_id="doc1",
        text="RAG hệ thống tìm kiếm thông tin tổng quát",
        page_numbers=(1,),
        score=0.1,
    )
    c2 = SearchResult(
        chunk_id="c2",
        document_id="doc1",
        text="Tổng quát thông tin tìm kiếm hệ thống RAG",
        page_numbers=(1,),
        score=0.1,
    )

    query = "RAG"
    results = reranker.rerank(query, [c1, c2], top_k=2)

    assert results[0].chunk_id == "c1"
    assert results[0].score > results[1].score


def test_mock_reranker_edge_cases() -> None:
    reranker = MockReranker()
    assert reranker.rerank("test", [], top_k=5) == []
    assert reranker.rerank("", [SearchResult("c1", "d1", "text", (1,), 1.0)], top_k=5) != []
