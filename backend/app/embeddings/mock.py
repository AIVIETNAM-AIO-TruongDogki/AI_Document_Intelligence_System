import hashlib
import math
import random

from app.embeddings.base import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock Embedding Provider dùng cho Unit Tests và Development cục bộ.

    Yêu cầu:
    1. Dimension: Lưu số chiều vector, ném ValueError nếu dimension <= 0.
    2. Tính tất định (Deterministic): Cùng 1 text -> luôn ra cùng 1 vector.
    3. Chuẩn hóa L2: Độ dài vector norm = 1.0 (chia mỗi phần tử cho sqrt(sum(x^2))).
    """

    def __init__(self, dimension: int = 64) -> None:
        if dimension <= 0:
            raise ValueError("Số chiều dimension phải lớn hơn 0.")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def _generate_vector(self, text: str) -> list[float]:
        seed = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
        rng = random.Random(seed)
        raw_vector = [rng.uniform(-1.0, 1.0) for _ in range(self._dimension)]
        norm = math.sqrt(sum(x * x for x in raw_vector))
        return [round(x / norm, 6) for x in raw_vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._generate_vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._generate_vector(text)
