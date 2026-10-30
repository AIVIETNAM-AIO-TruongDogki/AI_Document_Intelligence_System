import logging
from app.core.config import settings
from app.ocr.base import BaseOCRProvider

logger = logging.getLogger(__name__)


def get_ocr_provider() -> BaseOCRProvider | None:
    provider_type = (settings.ocr_provider or "none").lower()

    if provider_type == "none":
        return None

    if provider_type == "gemini":
        if not settings.gemini_api_key:
            logger.debug("Bỏ qua Gemini OCR vì chưa cấu hình GEMINI_API_KEY.")
            return None
        try:
            from app.ocr.gemini_provider import CachedGeminiOCRProvider
            return CachedGeminiOCRProvider()
        except Exception as exc:
            logger.warning("Không thể khởi tạo Gemini OCR Provider (%s), chuyển sang chế độ không OCR.", exc)
            return None

    if provider_type == "paddle":
        try:
            from app.ocr.paddle_provider import PaddleOCRProvider
            return PaddleOCRProvider()
        except Exception as exc:
            logger.warning("Không thể khởi tạo PaddleOCR (%s), chuyển sang chế độ không OCR.", exc)
            return None

    if provider_type == "composite":
        try:
            from app.ocr.paddle_provider import PaddleOCRProvider
            from app.ocr.gemini_provider import CachedGeminiOCRProvider
            from app.ocr.composite import FallbackOCRProvider
            return FallbackOCRProvider(
                primary=PaddleOCRProvider(),
                fallback=CachedGeminiOCRProvider(),
            )
        except Exception as exc:
            logger.warning("Không thể khởi tạo Composite OCR (%s), chuyển sang chế độ không OCR.", exc)
            return None

    return None
