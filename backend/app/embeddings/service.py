from collections.abc import Sequence

from app.documents.models import Chunk
from app.embeddings.base import EmbeddingProvider


class EmbeddingService:
    """Service điều phối việc chuyển đổi các Chunks và Query thành Vectors.
    
    Yêu cầu:
    1. dimension: Trả về provider.dimension
    2. embed_chunks: Nhận danh sách Chunk, trích xuất text, gọi provider và trả về (tuple[Chunk], tuple[vector])
    3. embed_query: Cắt khoảng trắng thừa query.strip(), nếu rỗng ném ValueError, sau đó gọi provider.embed_query
    """

    def __init__(self, provider: EmbeddingProvider) -> None:
        self.provider = provider

    @property
    def dimension(self) -> int:
        # TODO: Bạn hãy tự code ở đây:
        # Trả về self.provider.dimension
        return self.provider.dimension

    def embed_chunks(
        self,
        chunks: Sequence[Chunk],
    ) -> tuple[tuple[Chunk, ...], tuple[list[float], ...]]:
        # TODO: Bạn hãy tự code ở đây:
        # 1. Nếu chunks rỗng thì trả về ((), ())
        # 2. Lấy texts = [chunk.text for chunk in chunks]
        # 3. vectors = self.provider.embed_documents(texts)
        # 4. Trả về (tuple(chunks), tuple(vectors))
        if (len(chunks) == 0):
            return ((), ())
        texts = [chunk.text for chunk in chunks]
        vectors = self.provider.embed_documents(texts)
        return (tuple(chunks), tuple(vectors))

    def embed_query(self, query: str) -> list[float]:
        # TODO: Bạn hãy tự code ở đây:
        # 1. cleaned_query = query.strip()
        # 2. Nếu không có cleaned_query: raise ValueError("Câu hỏi tìm kiếm không được để trống.")
        # 3. Trả về self.provider.embed_query(cleaned_query)
        cleaned_query = query.strip()
        if not cleaned_query:
            raise ValueError("Câu hỏi tìm kiếm không được để trống.")
        return self.provider.embed_query(cleaned_query)
