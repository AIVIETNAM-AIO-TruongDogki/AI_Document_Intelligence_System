import logging
import uuid
from collections.abc import Sequence
from typing import Any

from app.retrieval.models import SearchResult, VectorRecord
from app.retrieval.vector_store import BaseVectorStore, InMemoryVectorStore

logger = logging.getLogger(__name__)


class QdrantVectorStore(BaseVectorStore):
    """Triển khai Vector Store chuẩn Production sử dụng Qdrant.

    Hỗ trợ kết nối Qdrant Server qua HTTP/gRPC hoặc chế độ Qdrant Local/In-Memory,
    tự động khởi tạo collection và có cơ chế fallback an toàn nếu chưa bật Qdrant service.
    """

    def __init__(
        self,
        url: str | None = None,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "docmind_chunks",
        vector_size: int = 1024,
        in_memory: bool = False,
    ) -> None:
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._fallback_store = InMemoryVectorStore()
        self._client: Any = None
        self._use_fallback = False

        try:
            from qdrant_client import QdrantClient

            if in_memory:
                self._client = QdrantClient(":memory:")
            elif url:
                self._client = QdrantClient(url=url, timeout=5.0)
            else:
                self._client = QdrantClient(host=host, port=port, timeout=5.0)

            self._ensure_collection()
        except Exception as exc:
            logger.warning(
                "Qdrant unavailable or qdrant-client not installed (%s). "
                "Using high-speed InMemoryVectorStore fallback.",
                exc,
            )
            self._use_fallback = True

    def _ensure_collection(self) -> None:
        """Đảm bảo collection tồn tại với cấu hình Cosine distance."""
        if self._client is None:
            return
        from qdrant_client.http import models as qmodels

        collections = self._client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.vector_size,
                    distance=qmodels.Distance.COSINE,
                ),
            )

    @staticmethod
    def _to_point_id(chunk_id: str) -> str:
        """Chuyển chunk_id bất kỳ sang UUID5 hợp lệ của Qdrant."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        """Thêm mới hoặc cập nhật danh sách các vector bản ghi kèm payload."""
        if not records:
            return

        # Luôn lưu song song vào fallback store để đảm bảo khả dụng 100%
        self._fallback_store.upsert(records)

        if self._use_fallback or self._client is None:
            return

        try:
            from qdrant_client.http import models as qmodels

            # Tự động điều chỉnh kích thước collection nếu vector_size thực tế khác mặc định
            actual_dim = len(records[0].vector)
            if actual_dim != self.vector_size:
                self.vector_size = actual_dim
                self._ensure_collection()

            points = [
                qmodels.PointStruct(
                    id=self._to_point_id(rec.id),
                    vector=rec.vector,
                    payload={
                        **rec.payload,
                        "chunk_id": rec.id,
                    },
                )
                for rec in records
            ]
            self._client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
        except Exception as exc:
            logger.warning("Qdrant upsert failed, switching to fallback store: %s", exc)
            self._use_fallback = True

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        """Tìm kiếm top_k vector gần nhất với query_vector (kèm bộ lọc document_id nếu có)."""
        if self._use_fallback or self._client is None:
            return self._fallback_store.search(
                query_vector=query_vector,
                top_k=top_k,
                document_id=document_id,
            )

        try:
            from qdrant_client.http import models as qmodels

            query_filter = None
            if document_id is not None:
                query_filter = qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=document_id),
                        )
                    ]
                )

            hits = self._client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
            )

            return [
                SearchResult(
                    chunk_id=str(hit.payload.get("chunk_id", hit.id)),
                    document_id=str(hit.payload["document_id"]),
                    text=str(hit.payload["text"]),
                    page_numbers=tuple(int(p) for p in hit.payload.get("page_numbers", [])),
                    score=float(hit.score),
                )
                for hit in hits
                if hit.payload is not None
            ]
        except Exception as exc:
            logger.warning("Qdrant search failed, falling back to in-memory: %s", exc)
            return self._fallback_store.search(
                query_vector=query_vector,
                top_k=top_k,
                document_id=document_id,
            )

    def delete_by_document(self, document_id: str) -> None:
        """Xóa toàn bộ các vector thuộc về một tài liệu cụ thể."""
        self._fallback_store.delete_by_document(document_id)

        if self._use_fallback or self._client is None:
            return

        try:
            from qdrant_client.http import models as qmodels

            self._client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="document_id",
                                match=qmodels.MatchValue(value=document_id),
                            )
                        ]
                    )
                ),
            )
        except Exception as exc:
            logger.warning("Qdrant delete_by_document failed: %s", exc)

    @property
    def _records(self) -> dict[str, VectorRecord]:
        """Tương thích ngược với các bài unit test kiểm tra trạng thái lưu trữ nội bộ."""
        return self._fallback_store._records
