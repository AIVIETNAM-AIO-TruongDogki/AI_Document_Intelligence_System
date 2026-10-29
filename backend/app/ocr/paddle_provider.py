import io
from typing import Any
from PIL import Image
import numpy as np

from app.ocr.base import BaseOCRProvider


class PaddleOCRProvider(BaseOCRProvider):
    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "Chưa cài đặt 'paddleocr' hoặc môi trường Python không tương thích (cần Python 3.10-3.12). "
                "Hãy chạy lệnh: pip install paddlepaddle paddleocr hoặc đổi OCR_PROVIDER='gemini' trong .env"
            ) from exc

        # Khởi tạo model khi đã import thành công
        self._ocr: Any = PaddleOCR(use_angle_cls=True, lang="vi", show_log=False)

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(image)

        result = self._ocr.ocr(img_np, cls=True)
        if not result or not result[0]:
            return ""

        extracted_lines = [line[1][0] for line in result[0] if line and line[1]]
        return "\n".join(extracted_lines)