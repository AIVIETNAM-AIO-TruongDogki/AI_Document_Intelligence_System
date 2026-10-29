from app.core.config import settings
from app.ocr.base import BaseOCRProvider
from app.ocr.gemini_provider import CachedGeminiOCRProvider

def get_ocr_provider() -> BaseOCRProvider | None:
    provider_type = settings.ocr_provider.lower()

    if provider_type == "none":
        return None

    if provider_type == "gemini":
        return CachedGeminiOCRProvider()

    if provider_type == "paddle":
        from app.ocr.paddle_provider import PaddleOCRProvider
        return PaddleOCRProvider()

    if provider_type == "composite":
        from app.ocr.paddle_provider import PaddleOCRProvider
        from app.ocr.composite import FallbackOCRProvider
        return FallbackOCRProvider(
            primary=PaddleOCRProvider(),
            fallback=CachedGeminiOCRProvider(),
        )

    raise ValueError(f"Không hỗ trợ OCR_PROVIDER='{provider_type}'")