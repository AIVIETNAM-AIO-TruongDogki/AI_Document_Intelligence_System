import logging
from app.ocr.base import BaseOCRProvider

logger = logging.getLogger(__name__)

class FallbackOCRProvider(BaseOCRProvider):
    """Chạy PaddleOCR nội bộ trước. Nếu kết quả rỗng hoặc gặp lỗi -> Gọi Gemini cứu trợ."""
    def __init__(self, primary: BaseOCRProvider, fallback: BaseOCRProvider) -> None:
        self.primary = primary
        self.fallback = fallback

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        try:
            text = self.primary.extract_text_from_image(image_bytes)
            # Nếu PaddleOCR nhận diện được nội dung tử tế -> Trả về
            if text and len(text.strip()) > 10:
                return text
            logger.info("Primary OCR (Paddle) cho kết quả quá ít chữ, chuyển hướng sang Fallback...")
        except Exception as exc:
            logger.error("Primary OCR bị lỗi: %s. Kích hoạt Fallback...", exc)

        # Chuyển hướng sang Provider dự phòng (Gemini)
        return self.fallback.extract_text_from_image(image_bytes)