import logging
import time
import google.generativeai as genai
from app.core.config import settings
from app.ocr.base import BaseOCRProvider
from app.ocr.cache import OCRCache

logger = logging.getLogger(__name__)


class CachedGeminiOCRProvider(BaseOCRProvider):
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or settings.gemini_api_key
        if not key:
            raise ValueError("Chưa cấu hình GEMINI_API_KEY cho OCR.")
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.cache = OCRCache(settings.ocr_cache_dir)
        self.last_call_time = 0.0
        self.min_interval = 60.0 / max(settings.gemini_ocr_rpm_limit, 1)

    def _rate_limit(self) -> None:
        """Kiểm soát tốc độ gọi tránh chạm HTTP 429 Quota Exceeded."""
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call_time = time.time()

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        # 1. Kiểm tra cache trước: Nếu ảnh này từng OCR rồi -> Trả kết quả ngay (0đ)
        try:
            cached_text = self.cache.get(image_bytes)
            if cached_text is not None:
                logger.info("OCR Cache Hit! Bỏ qua gọi API Gemini.")
                return cached_text
        except Exception as cache_exc:
            logger.debug("Lỗi đọc cache OCR: %s", cache_exc)

        # 2. Cơ chế Retry với Exponential Backoff
        prompt = (
            "Trích xuất toàn bộ văn bản trong ảnh này (giữ nguyên tiếng Việt/tiếng Anh). "
            "Nếu có bảng biểu, hãy định dạng thành Markdown table. Chỉ trả về nội dung text trích xuất."
        )

        max_retries = 2
        delay = 1.0
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = self.model.generate_content([
                    prompt,
                    {"mime_type": "image/png", "data": image_bytes}
                ])
                result_text = response.text.strip() if response and response.text else ""
                
                # Lưu vào cache cho các lần chạy sau
                if result_text:
                    try:
                        self.cache.set(image_bytes, result_text)
                    except Exception:
                        pass
                return result_text

            except Exception as exc:
                logger.warning("Gemini OCR lỗi lần %d: %s", attempt + 1, exc)
                if attempt == max_retries - 1:
                    logger.warning("Gemini OCR thất bại sau %d lần thử. Tiếp tục với trích xuất văn bản số chuẩn.", max_retries)
                    return ""
                time.sleep(delay)
                delay *= 2

        return ""
