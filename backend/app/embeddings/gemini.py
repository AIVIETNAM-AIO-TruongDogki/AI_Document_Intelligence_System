import logging
import time
import google.generativeai as genai
from google.api_core import exceptions
from app.core.config import settings
from app.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Sử dụng mô hình gemini-embedding-001 của Google (3072 chiều, có cơ chế Rate Limit & Retry)."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "models/gemini-embedding-001",
    ) -> None:
        key = api_key or settings.gemini_api_key
        if not key:
            raise ValueError("Cần cấu hình GEMINI_API_KEY để sử dụng Embedding.")
        genai.configure(api_key=key)
        self.model_name = model_name
        self._dimension = 3072

    @property
    def dimension(self) -> int:
        return self._dimension

    def _embed_batch_with_retry(self, batch: list[str]) -> list[list[float]]:
        """Gọi API embedding cho 1 batch kèm cơ chế tự động chờ nếu chạm hạn ngạch Free Tier (429)."""
        max_retries = 5
        backoff_delay = 5.0

        for attempt in range(max_retries):
            try:
                result = genai.embed_content(
                    model=self.model_name,
                    content=batch,
                    task_type="retrieval_document",
                )
                raw = result.get("embedding", [])
                batch_embeddings: list[list[float]] = []

                if raw and isinstance(raw[0], (int, float)):
                    batch_embeddings.append([float(x) for x in raw])
                else:
                    for item in raw:
                        if isinstance(item, list):
                            batch_embeddings.append([float(x) for x in item])
                return batch_embeddings

            except exceptions.ResourceExhausted as e:
                logger.warning(
                    "Google Embedding chạm giới hạn Free Tier (100 RPM). Đang tự động đợi %ds trước khi thử lại (lần %d)...",
                    backoff_delay,
                    attempt + 1,
                )
                time.sleep(backoff_delay)
                backoff_delay = min(backoff_delay * 2, 60.0)
            except Exception as e:
                logger.error("Lỗi embedding: %s (thử lại sau %ds)", e, backoff_delay)
                if attempt == max_retries - 1:
                    raise
                time.sleep(backoff_delay)

        return []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        # Free tier giới hạn 100 requests/phút, chia nhỏ 25 chunks/batch và giãn cách nhẹ
        batch_size = 25

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_vectors = self._embed_batch_with_retry(batch)
            all_embeddings.extend(batch_vectors)
            # Giãn cách 0.5s giữa các batch để tránh dồn dập
            if i + batch_size < len(texts):
                time.sleep(0.5)

        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        max_retries = 3
        delay = 2.0
        for attempt in range(max_retries):
            try:
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_query",
                )
                raw = result.get("embedding", [])
                if raw and isinstance(raw[0], list):
                    return [float(x) for x in raw[0]]
                return [float(x) for x in raw]
            except exceptions.ResourceExhausted:
                time.sleep(delay)
                delay *= 2
            except Exception:
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay)
        return []
