from collections.abc import Sequence

from app.retrieval.models import SearchResult


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[SearchResult]],
    top_k: int = 10,
    rrf_k: int = 60,
) -> list[SearchResult]:
    """Kết hợp nhiều danh sách kết quả tìm kiếm bằng thuật toán Reciprocal Rank Fusion (RRF)."""
    if not ranked_lists or top_k <= 0:
        return []

    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, SearchResult] = {}

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list, start=1):
            chunk_id = chunk.chunk_id
            if chunk_id not in chunk_map:
                chunk_map[chunk_id] = chunk
                rrf_scores[chunk_id] = 0.0

            rrf_scores[chunk_id] += 1.0 / (rrf_k + rank)

    if not rrf_scores:
        return []

    # Sắp xếp các chunk theo điểm RRF giảm dần
    sorted_items = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
    top_items = sorted_items[:top_k]

    return [
        SearchResult(
            chunk_id=chunk_map[cid].chunk_id,
            document_id=chunk_map[cid].document_id,
            text=chunk_map[cid].text,
            page_numbers=chunk_map[cid].page_numbers,
            score=score,
        )
        for cid, score in top_items
    ]