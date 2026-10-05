from pathlib import Path

import pymupdf
import pytest

from app.documents.exceptions import InvalidDocumentError, NoExtractableTextError
from app.documents.parser import parse_pdf


def test_parser_raises_for_missing_file(tmp_path: Path) -> None:
    fake_path = tmp_path / "non_existent.pdf"
    with pytest.raises(InvalidDocumentError, match="không tồn tại"):
        parse_pdf(fake_path, "doc_1")


def test_parser_reads_valid_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text((50, 50), "Trang 1: Day la noi dung mau cua tai lieu.")
    page2 = doc.new_page()
    page2.insert_text((50, 50), "Trang 2: Day la noi dung trang hai.")
    doc.save(str(pdf_path))
    doc.close()

    metadata, pages = parse_pdf(pdf_path, "test_doc")

    assert metadata.document_id == "test_doc"
    assert metadata.page_count == 2
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "Trang 1: Day la noi dung mau" in pages[0].text
    assert pages[1].page_number == 2


def test_parser_raises_for_empty_text_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    doc = pymupdf.open()
    doc.new_page()  # Trang trắng tinh
    doc.save(str(pdf_path))
    doc.close()

    with pytest.raises(NoExtractableTextError, match="không chứa văn bản"):
        parse_pdf(pdf_path, "blank_doc")