import math

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.retrieval.models import SearchResult, VectorRecord


def cosine_similarity(v1: Sequence[float], v2: Sequence[float]) -> float:
    """Tính độ tương đồng Cosine giữa 2 vector v1 và v2.
    
    Công thức: cos(theta) = (v1 . v2) / (||v1|| * ||v2||)
    """
    # TODO: Bạn hãy tự code ở đây:
    # 1. Kiểm tra nếu len(v1) != len(v2): raise ValueError
    # 2. Tính dot_product = sum(a * b for a, b in zip(v1, v2))
    # 3. Tính norm_v1 = math.sqrt(sum(a * a for a in v1))
    # 4. Tính norm_v2 = math.sqrt(sum(b * b for b in v2))
    # 5. Nếu norm_v1 == 0 hoặc norm_v2 == 0: return 0.0
    # 6. Trả về dot_product / (norm_v1 * norm_v2)
    if (len(v1) != len(v2)):
        raise ValueError()
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if (norm_v1 == 0 or norm_v2 == 0):
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
        # Lưu trữ dict mapping id -> VectorRecord để tránh duplicate ID
        self._records: dict[str, VectorRecord] = {}

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        # TODO: Bạn hãy tự code ở đây:
        # Lưu từng record vào dictionary self._records theo key là record.id
        for record in records:
            self._records[record.id] = record

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        # TODO: Bạn hãy tự code ở đây:
        # 1. Nếu self._records rỗng: return []
        # 2. Tạo danh sách scored_results = []
        # 3. Duyệt qua từng record trong self._records.values():
        #    - Nếu document_id được chỉ định và record.payload.get("document_id") != document_id: bỏ qua
        #    - Tính score = cosine_similarity(query_vector, record.vector)
        #    - Thêm (score, record) vào scored_results
        # 4. Sắp xếp scored_results giảm dần theo score: scored_results.sort(key=..., reverse=True)
        # 5. Cắt lấy top_k phần tử đầu tiên
        # 6. Đóng gói và trả về danh sách SearchResult(chunk_id, document_id, text, page_numbers, score)
        if (self._records is None):
            return []
        scored_results = []
        for record in self._records.values():
            if (document_id is not None and record.payload.get("document_id") != document_id):
                continue
            score = cosine_similarity(query_vector, record.vector)
            scored_results.append((score, record))
        scored_results.sort(key=lambda x: x[0], reverse=True)
        top_k_results = scored_results[:top_k]
        results = []
        for score, record in top_k_results:
            results.append(SearchResult(
                chunk_id=record.id,
                document_id=record.payload["document_id"],
                text=record.payload["text"],
                page_numbers=tuple(record.payload["page_numbers"]),
                score=score,
            ))
        return results

    def delete_by_document(self, document_id: str) -> None:
        # TODO: Bạn hãy tự code ở đây:
        # Tìm các record_id có payload["document_id"] == document_id và xóa khỏi self._records
        records_to_delete = [record for record in self._records.values() if record.payload["document_id"] == document_id]
        for record in records_to_delete:
            del self._records[record.id]