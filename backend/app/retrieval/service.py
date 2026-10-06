from collections.abc import Sequence

from app.documents.models import Chunk
from app.embeddings.service import EmbeddingService
from app.retrieval.models import SearchResult, VectorRecord
from app.retrieval.vector_store import BaseVectorStore


class SearchService:
    """Service điều phối toàn diện cho việc Index tài liệu và Tìm kiếm ngữ nghĩa."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: BaseVectorStore,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def index_chunks(self, chunks: Sequence[Chunk]) -> int:
        """Vector hóa và lưu danh sách Chunks vào Vector Store.

        Args:
            chunks: Danh sách chunks được cắt từ tài liệu PDF.

        Returns:
            Số lượng chunks đã được lưu thành công.
        """
        if not chunks:
            return 0

        chunks_tuple, vectors = self.embedding_service.embed_chunks(chunks)
        records = [
            VectorRecord(
                id=chunk.chunk_id,
                vector=vector,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "page_numbers": list(chunk.page_numbers),
                    "token_count": chunk.token_count,
                },
            )
            for chunk, vector in zip(chunks_tuple, vectors)
        ]
        self.vector_store.upsert(records)
        return len(records)

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        """Thực hiện tìm kiếm ngữ nghĩa từ câu hỏi của người dùng.

        Args:
            query: Câu hỏi hoặc từ khóa tìm kiếm.
            top_k: Số lượng đoạn trích liên quan nhất cần trả về.
            document_id: (Tùy chọn) Chỉ tìm kiếm trong tài liệu có ID này.

        Returns:
            Danh sách SearchResult sắp xếp theo độ tương đồng giảm dần.
        """
        cleaned_query = query.strip()
        if not cleaned_query:
            raise ValueError("Câu hỏi tìm kiếm không được để trống.")

        query_vector = self.embedding_service.embed_query(cleaned_query)
        return self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            document_id=document_id,
        )
