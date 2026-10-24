from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract Base Class định nghĩa giao diện chung cho mọi nhà cung cấp Embedding.
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
