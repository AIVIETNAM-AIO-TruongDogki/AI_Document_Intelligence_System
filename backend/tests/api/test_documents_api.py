import io
from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_upload_invalid_file_extension(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"Day la file text", "text/plain")},
    )
    assert response.status_code == 400
    assert "Chỉ chấp nhận tệp định dạng .pdf" in response.json()["detail"]


def test_upload_and_get_document_success(client: TestClient, tmp_path: Path) -> None:
    # 1. Tạo file PDF mẫu có nội dung văn bản
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text((50, 50), "Trang 1: Quy trinh phan tich tai lieu tu dong.")
    page2 = doc.new_page()
    page2.insert_text((50, 50), "Trang 2: Trich xuat thong tin va vector hoa.")
    pdf_bytes = io.BytesIO()
    doc.save(pdf_bytes)
    doc.close()
    pdf_bytes.seek(0)

    # 2. Upload file PDF qua API
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("sample_report.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert data["filename"] == "sample_report.pdf"
    assert data["page_count"] == 2
    assert data["chunk_count"] >= 1

    doc_id = data["document_id"]

    # 3. Lấy chi tiết tài liệu vừa upload
    detail_res = client.get(f"/api/v1/documents/{doc_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["document_id"] == doc_id
    assert len(detail_data["chunks"]) == data["chunk_count"]


def test_get_non_existent_document(client: TestClient) -> None:
    response = client.get("/api/v1/documents/non_existent_doc_id")
    assert response.status_code == 404
    assert "Không tìm thấy" in response.json()["detail"]


def test_list_and_delete_document_lifecycle(client: TestClient) -> None:
    # 1. Tạo file PDF mẫu
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Tai lieu can kiem tra xoa.")
    pdf_bytes = io.BytesIO()
    doc.save(pdf_bytes)
    doc.close()
    pdf_bytes.seek(0)

    # 2. Upload
    up_res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("to_delete.pdf", pdf_bytes, "application/pdf")},
    )
    assert up_res.status_code == 201
    doc_id = up_res.json()["document_id"]

    # 3. List kiểm tra có tài liệu
    list_res = client.get("/api/v1/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert any(d["document_id"] == doc_id for d in docs)

    # 4. Xóa tài liệu
    del_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 204

    # 5. Kiểm tra tài liệu đã bị xóa (404)
    get_res = client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 404

