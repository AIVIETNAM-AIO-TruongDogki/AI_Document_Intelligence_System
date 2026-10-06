import math
from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.retrieval.models import SearchResult, VectorRecord


def cosine_similarity(v1: Sequence[float], v2: Sequence[float]) -> float:
    """Tính độ tương đồng Cosine giữa 2 vector v1 và v2.

    Công thức: cos(theta) = (v1 . v2) / (||v1|| * ||v2||)
    """
    if len(v1) != len(v2):
        raise ValueError("Hai vector phải có cùng số chiều.")

    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))

    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0

    return dot_product / (norm_v1 * norm_v2)


class BaseVectorStore(ABC):
    """Giao diện trừu tượng cho Vector Store (In-Memory, Qdrant, ChromaDB)."""

    @abstractmethod
    def upsert(self, records: Sequence[VectorRecord]) -> None:
        """Thêm mới hoặc cập nhật danh sách các vector bản ghi kèm payload."""
        ...

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        """Tìm kiếm top_k vector gần nhất với query_vector (kèm bộ lọc nếu có)."""
        ...

    @abstractmethod
    def delete_by_document(self, document_id: str) -> None:
        """Xóa toàn bộ các vector thuộc về một tài liệu cụ thể."""
        ...


class InMemoryVectorStore(BaseVectorStore):
    """Kho lưu trữ vector thuần trong RAM, lý tưởng cho Unit Test."""

    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        for record in records:
            self._records[record.id] = record

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        if not self._records:
            return []

        scored_results: list[tuple[float, VectorRecord]] = []
        for record in self._records.values():
            if document_id is not None and record.payload.get("document_id") != document_id:
                continue
            score = cosine_similarity(query_vector, record.vector)
            scored_results.append((score, record))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        top_k_results = scored_results[:top_k]

        return [
            SearchResult(
                chunk_id=record.id,
                document_id=record.payload["document_id"],
                text=record.payload["text"],
                page_numbers=tuple(record.payload["page_numbers"]),
                score=score,
            )
            for score, record in top_k_results
        ]

    def delete_by_document(self, document_id: str) -> None:
        target_ids = [
            record_id
            for record_id, record in self._records.items()
            if record.payload.get("document_id") == document_id
        ]
        for record_id in target_ids:
            del self._records[record_id]