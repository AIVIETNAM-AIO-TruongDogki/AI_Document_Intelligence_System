import pytest

from app.documents.chunker import TokenChunker
from app.documents.models import PageText


def test_chunker_validation_raises_error() -> None:
    with pytest.raises(ValueError, match="chunk_size_tokens"):
        TokenChunker(chunk_size_tokens=0)

    with pytest.raises(ValueError, match="overlap_tokens"):
        TokenChunker(chunk_size_tokens=100, overlap_tokens=100)


def test_chunks_retain_metadata_and_provenance() -> None:
    chunker = TokenChunker(chunk_size_tokens=10, overlap_tokens=2)
    pages = (
        PageText(page_number=1, text="Một hai ba bốn năm sáu bảy tám chín mười mười một mười hai"),
    )
    chunks = chunker.chunk_pages(document_id="doc_abc", pages=pages)

    assert len(chunks) >= 2
    assert chunks[0].chunk_id == "doc_abc_chunk_0001"
    assert chunks[1].chunk_id == "doc_abc_chunk_0002"
    assert all(c.document_id == "doc_abc" for c in chunks)
    assert all(c.page_numbers == (1,) for c in chunks)
    assert all(c.token_count <= 10 for c in chunks)