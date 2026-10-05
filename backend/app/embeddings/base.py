from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract Base Class định nghĩa giao diện chung cho mọi nhà cung cấp Embedding.
    
    Quy tắc:
    - dimension: Số chiều vector đầu ra (ví dụ: 64, 384, 768, 1536).
    - embed_documents: Nhận vào danh sách đoạn text -> trả về ma trận vector.
    - embed_query: Nhận vào 1 câu hỏi -> trả về 1 vector.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Số chiều của vector embedding."""
        ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Vector hóa danh sách các đoạn văn bản (chunks)."""
        ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Vector hóa một câu hỏi của người dùng."""
        ...
