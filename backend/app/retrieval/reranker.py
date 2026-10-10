import re
from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.retrieval.models import SearchResult


class BaseReranker(ABC):
    """Giao diện trừu tượng cho Reranker Model."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: Sequence[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Tính điểm liên quan giữa query và text của từng candidate, sắp xếp lại kết quả."""


class MockReranker(BaseReranker):
    """Mock reranker tính toán deterministic dựa trên Jaccard token overlap + vị trí từ để test."""

    def _tokenize(self, text: str) -> list[str]:
        """Tách từ đơn giản, chuyển về chữ thường và loại bỏ ký tự đặc biệt."""
        clean = re.sub(r'[^\w\s]|_', ' ', text.lower())
        return [t for t in clean.split() if len(t) >= 1]

    def rerank(
        self,
        query: str,
        candidates: Sequence[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        if not candidates or top_k <= 0:
            return []

        cleaned_query = query.strip()
        query_tokens = self._tokenize(cleaned_query)
        if not query_tokens:
            return list(candidates[:top_k])

        query_set = set(query_tokens)
        scored_candidates: list[tuple[SearchResult, float]] = []

        for candidate in candidates:
            doc_tokens = self._tokenize(candidate.text)
            doc_set = set(doc_tokens)

            # 1. Jaccard Token Overlap: giao / hợp
            intersection = query_set & doc_set
            union = query_set | doc_set
            jaccard_score = len(intersection) / len(union) if union else 0.0

            # 2. Vị trí từ: Ưu tiên đoạn có từ khóa xuất hiện sớm ở đầu câu
            position_bonus = 0.0
            if doc_tokens and intersection:
                first_pos = next(
                    (idx for idx, token in enumerate(doc_tokens) if token in intersection),
                    len(doc_tokens),
                )
                position_bonus = 0.1 * (1.0 - (first_pos / len(doc_tokens)))

            total_score = min(round(jaccard_score + position_bonus, 4), 1.0)
            scored_candidates.append((candidate, total_score))

        # Sắp xếp giảm dần theo điểm Rerank
        scored_candidates.sort(key=lambda item: item[1], reverse=True)
        top_results = scored_candidates[:top_k]

        return [
            SearchResult(
                chunk_id=cand.chunk_id,
                document_id=cand.document_id,
                text=cand.text,
                page_numbers=cand.page_numbers,
                score=score,
            )
            for cand, score in top_results
        ]
