from pathlib import Path

from app.documents.chunker import TokenChunker
from app.documents.cleaner import clean_text
from app.documents.models import PageText, ParsedDocument
from app.documents.parser import parse_pdf


def process_pdf(
    path: Path,
    document_id: str,
    chunk_size_tokens: int = 512,
    overlap_tokens: int = 64,
) -> ParsedDocument:
    # 1. Trích xuất trang và thông tin tệp
    metadata, raw_pages = parse_pdf(path, document_id)

    # 2. Làm sạch văn bản từng trang
    cleaned_pages = tuple(
        PageText(page_number=p.page_number, text=clean_text(p.text))
        for p in raw_pages
    )

    # 3. Cắt nhỏ thành các chunk
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