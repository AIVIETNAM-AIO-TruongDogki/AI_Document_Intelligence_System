from pathlib import Path
import pymupdf

from app.documents.exceptions import InvalidDocumentError, NoExtractableTextError
from app.documents.models import DocumentMetadata, PageText
from app.ocr.base import BaseOCRProvider

# Ngưỡng tối thiểu để coi một trang có text số hợp lệ
MIN_CHARS_PER_PAGE_THRESHOLD = 30


def parse_pdf(
    path: Path,
    document_id: str,
    ocr_provider: BaseOCRProvider | None = None,
) -> tuple[DocumentMetadata, tuple[PageText, ...]]:
    if not path.is_file():
        raise InvalidDocumentError(f"File PDF không tồn tại: {path}")

    try:
        with pymupdf.open(path) as doc:
            if doc.page_count == 0:
                raise InvalidDocumentError("File PDF không có trang nào.")

            pages: list[PageText] = []

            for index, page in enumerate(doc):
                # 1. Thử trích xuất văn bản số có sẵn
                extracted_text = page.get_text("text").strip()

                # 2. Kiểm tra xem trang có cần Fallback sang OCR hay không:
                # - Nếu text quá ngắn (trang scan/chụp)
                # - Hoặc trang không có text nhưng có chứa ảnh nhúng
                needs_ocr = len(extracted_text) < MIN_CHARS_PER_PAGE_THRESHOLD

                if needs_ocr and ocr_provider is not None:
                    # Chụp toàn bộ trang PDF thành ảnh với độ phân giải 200 DPI
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")

                    # Gọi OCR Engine nhận diện
                    ocr_text = ocr_provider.extract_text_from_image(img_bytes)
                    if ocr_text:
                        extracted_text = ocr_text

                pages.append(PageText(page_number=index + 1, text=extracted_text))

    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise InvalidDocumentError(f"Không thể đọc file PDF {path.name}: {exc}") from exc

    if not any(p.text.strip() for p in pages):
        raise NoExtractableTextError(f"Tệp PDF {path.name} không chứa văn bản có thể trích xuất.")

    metadata = DocumentMetadata(
        document_id=document_id,
        filename=path.name,
        page_count=len(pages),
    )
    return metadata, tuple(pages)
