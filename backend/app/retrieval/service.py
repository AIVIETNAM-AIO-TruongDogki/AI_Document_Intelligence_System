from collections.abc import Sequence

from app.documents.models import Chunk
from app.embeddings.service import EmbeddingService
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.models import SearchResult, VectorRecord
from app.retrieval.reranker import BaseReranker
from app.retrieval.vector_store import BaseVectorStore


class SearchService:
    """Service điều phối toàn diện cho việc Index tài liệu và Tìm kiếm ngữ nghĩa (Dense only)."""

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


class HybridSearchService:
    """Điều phối toàn diện: Index đồng thời Dense & BM25, Truy hồi Hybrid kèm Reranking."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: BaseVectorStore,
        bm25_retriever: BM25Retriever,
        reranker: BaseReranker,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.reranker = reranker

    def index_chunks(self, chunks: Sequence[Chunk]) -> int:
        """Lưu trữ chunks song song vào cả VectorStore (Dense) và BM25Retriever (Sparse).

        Args:
            chunks: Danh sách các đoạn văn bản (Chunks).

        Returns:
            Số lượng chunks đã index thành công.
        """
        if not chunks:
            return 0

        # 1. Vector hóa và index vào Vector Store
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

        # 2. Đánh chỉ mục vào BM25 Retriever
        self.bm25_retriever.index_chunks(chunks)

        return len(records)

    def search(
        self,
        query: str,
        top_k: int = 5,
        dense_top_k: int = 20,
        bm25_top_k: int = 20,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        """Thực hiện Pipeline 4 bước Hybrid Retrieval:
        1. Dense Search lấy top dense_top_k (Ngữ nghĩa)
        2. BM25 Search lấy top bm25_top_k (Từ khóa chính xác)
        3. Reciprocal Rank Fusion kết hợp thành top candidates
        4. Cross-Encoder Rerank để trả về top top_k cuối cùng

        Args:
            query: Câu hỏi tìm kiếm.
            top_k: Số lượng kết quả cuối cùng mong muốn.
            dense_top_k: Số ứng viên Dense Search thu thập.
            bm25_top_k: Số ứng viên BM25 Lexical Search thu thập.
            document_id: (Tùy chọn) Lọc theo tài liệu.

        Returns:
            Danh sách SearchResult đã được xếp hạng tối ưu.
        """
        cleaned_query = query.strip()
        if not cleaned_query:
            raise ValueError("Câu hỏi tìm kiếm không được để trống.")

        if top_k <= 0:
            return []

        # 1. Dense Semantic Search
        query_vector = self.embedding_service.embed_query(cleaned_query)
        dense_results = self.vector_store.search(
            query_vector=query_vector,
            top_k=dense_top_k,
            document_id=document_id,
        )

        # 2. BM25 Lexical Search
        bm25_results = self.bm25_retriever.search(
            query=cleaned_query,
            top_k=bm25_top_k,
            document_id=document_id,
        )

        # 3. Reciprocal Rank Fusion (RRF)
        fused_candidates = reciprocal_rank_fusion(
            ranked_lists=[dense_results, bm25_results],
            top_k=max(dense_top_k, bm25_top_k),
        )

        if not fused_candidates:
            return []

        # 4. Cross-Encoder Rerank
        return self.reranker.rerank(
            query=cleaned_query,
            candidates=fused_candidates,
            top_k=top_k,
        )

    def delete_by_document(self, document_id: str) -> None:
        """Xóa toàn bộ dữ liệu của một tài liệu ở cả Vector Store và BM25."""
        self.vector_store.delete_by_document(document_id)
        self.bm25_retriever.delete_by_document(document_id)
