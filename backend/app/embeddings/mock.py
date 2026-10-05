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
        # TODO: Bạn hãy tự code ở đây:
        # 1. Kiểm tra nếu dimension <= 0 thì raise ValueError("Số chiều dimension phải lớn hơn 0.")
        # 2. Lưu vào self._dimension
        if dimension <= 0:
            raise ValueError("Số chiều dimension phải lớn hơn 0.")
        self._dimension = dimension 


    @property
    def dimension(self) -> int:
        # TODO: Bạn hãy tự code ở đây:
        # Trả về self._dimension
        return self._dimension  

    def _generate_vector(self, text: str) -> list[float]:
        # TODO: Bạn hãy tự code ở đây:
        # 1. Tạo seed tất định từ hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
        # 2. Dùng random.Random(seed) để sinh d số thực trong khoảng [-1.0, 1.0]
        # 3. Tính norm = math.sqrt(sum(x * x for x in raw_vector))
        # 4. Trả về vector đã chuẩn hóa [round(x / norm, 6) for x in raw_vector]
        seed = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
        rng = random.Random(seed)
        raw_vector = [rng.uniform(-1.0, 1.0) for _ in range(self._dimension)]
        norm = math.sqrt(sum(x*x for x in raw_vector))
        normalized_vector = [round(x / norm, 6) for x in raw_vector]
        return normalized_vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # TODO: Bạn hãy tự code ở đây:
        # Trả về danh sách vector bằng cách gọi self._generate_vector cho từng đoạn text
        return [self._generate_vector(text) for text in texts]
    def embed_query(self, text: str) -> list[float]:
        # TODO: Bạn hãy tự code ở đây:
        # Trả về 1 vector bằng cách gọi self._generate_vector cho chuỗi text
        return self._generate_vector(text)
