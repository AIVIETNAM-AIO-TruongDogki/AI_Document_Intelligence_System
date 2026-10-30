from pathlib import Path
from app.documents.models import ParsedDocument, PageText
from app.documents.parser import parse_pdf
from app.documents.cleaner import clean_text
from app.documents.chunker import TokenChunker
from app.ocr.factory import get_ocr_provider

def process_pdf(
    path: Path,
    document_id: str,
    chunk_size_tokens: int = 512,
    overlap_tokens: int = 64,
) -> ParsedDocument:
    # Lấy OCR Provider theo cấu hình môi trường
    ocr_provider = get_ocr_provider()
    
    # parse_pdf sẽ tự động kích hoạt OCR khi gặp trang scan / thiếu chữ
    metadata, raw_pages = parse_pdf(path, document_id, ocr_provider=ocr_provider)

    cleaned_pages = tuple(
        PageText(page_number=p.page_number, text=clean_text(p.text))
        for p in raw_pages
    )

    chunker = TokenChunker(
        chunk_size_tokens=chunk_size_tokens,
        overlap_tokens=overlap_tokens,
    )
    chunks = chunker.chunk_pages(document_id, cleaned_pages)

    return ParsedDocument(
        metadata=metadata,
        pages=cleaned_pages,
        chunks=chunks,
    )