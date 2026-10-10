from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.models import SearchResult


def test_reciprocal_rank_fusion_basic() -> None:
    res_a1 = SearchResult(
        chunk_id="c1",
        document_id="doc1",
        text="Text 1",
        page_numbers=(1,),
        score=0.9,
    )
    res_a2 = SearchResult(
        chunk_id="c2",
        document_id="doc1",
        text="Text 2",
        page_numbers=(2,),
        score=0.8,
    )
    res_b1 = SearchResult(
        chunk_id="c2",
        document_id="doc1",
        text="Text 2",
        page_numbers=(2,),
        score=10.5,
    )
    res_b2 = SearchResult(
        chunk_id="c3",
        document_id="doc2",
        text="Text 3",
        page_numbers=(1,),
        score=5.0,
    )

    # c2 xuất hiện ở rank 2 trong list A và rank 1 trong list B -> điểm c2 phải cao nhất
    fused = reciprocal_rank_fusion([ [res_a1, res_a2], [res_b1, res_b2] ], top_k=3, rrf_k=60)

    assert len(fused) == 3
    assert fused[0].chunk_id == "c2"
    # c2 score = 1/(60+2) + 1/(60+1)
    expected_c2_score = (1.0 / 62.0) + (1.0 / 61.0)
    assert round(fused[0].score, 6) == round(expected_c2_score, 6)


def test_reciprocal_rank_fusion_empty_and_edge_cases() -> None:
    assert reciprocal_rank_fusion([], top_k=5) == []
    assert reciprocal_rank_fusion([[]], top_k=5) == []

    # Một list có phần tử, một list rỗng -> vẫn lấy được từ list có phần tử
    res = SearchResult(
        chunk_id="c1",
        document_id="doc1",
        text="Sample",
        page_numbers=(1,),
        score=1.0,
    )
    fused = reciprocal_rank_fusion([[res], []], top_k=5)
    assert len(fused) == 1
    assert fused[0].chunk_id == "c1"


def test_reciprocal_rank_fusion_top_k() -> None:
    items = [
        SearchResult(
            chunk_id=f"c{i}",
            document_id="doc1",
            text=f"Sample {i}",
            page_numbers=(i,),
            score=1.0,
        )
        for i in range(10)
    ]
    fused = reciprocal_rank_fusion([items], top_k=3)
    assert len(fused) == 3
