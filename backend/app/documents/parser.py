from pathlib import Path

import pymupdf

from app.documents.exceptions import InvalidDocumentError, NoExtractableTextError
from app.documents.models import DocumentMetadata, PageText


def parse_pdf(path: Path, document_id: str) -> tuple[DocumentMetadata, tuple[PageText, ...]]:
    if not path.is_file():
        raise InvalidDocumentError(f"File PDF không tồn tại: {path}")

    try:
        with pymupdf.open(path) as doc:
            if doc.page_count == 0:
                raise InvalidDocumentError("File PDF không có trang nào.")

            pages: list[PageText] = []
            total_chars = 0

            for index, page in enumerate(doc):
                text = page.get_text("text")
                total_chars += len(text.strip())
                pages.append(PageText(page_number=index + 1, text=text))

    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise InvalidDocumentError(f"Không thể đọc file PDF {path.name}: {exc}") from exc

    # Nếu toàn bộ file không có nổi 1 ký tự text hợp lệ -> Cần OCR (chưa hỗ trợ ở Phase 1)
    if total_chars == 0:
        raise NoExtractableTextError(
            "PDF không chứa văn bản trích xuất được. Có thể là PDF scan, hiện chưa hỗ trợ OCR."
        )

    metadata = DocumentMetadata(
        document_id=document_id,
        filename=path.name,
        page_count=len(pages),
    )
    return metadata, tuple(pages)