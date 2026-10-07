import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_documents_store, get_search_service
from app.api.schemas.documents import (
    ChunkSchema,
    DocumentDetailResponse,
    DocumentUploadResponse,
)
from app.documents.exceptions import InvalidDocumentError, NoExtractableTextError
from app.documents.models import ParsedDocument
from app.documents.service import process_pdf
from app.retrieval.service import SearchService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tải lên và xử lý tài liệu PDF",
)
async def upload_document(
    file: Annotated[UploadFile, File(description="File PDF cần phân tích")],
    search_service: Annotated[SearchService, Depends(get_search_service)],
    documents_store: Annotated[dict[str, ParsedDocument], Depends(get_documents_store)],
) -> DocumentUploadResponse:
    """API tải lên tài liệu PDF.
    
    Yêu cầu:
    1. Kiểm tra nếu file không có tên hoặc không đuôi .pdf -> raise HTTPException(400, "Chỉ chấp nhận tệp định dạng .pdf.")
    2. Tạo document_id ngẫu nhiên: doc_<uuid>
    3. Lưu file tạm bằng tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    4. Trong khối try:
       - Gọi process_pdf(path=tmp_path, document_id=document_id)
       - Gọi search_service.index_chunks(parsed_doc.chunks)
       - Lưu vào documents_store[document_id] = parsed_doc
       - Trả về DocumentUploadResponse(...)
       - Bắt (InvalidDocumentError, NoExtractableTextError) -> raise HTTPException(422, detail=str(exc))
    5. Trong khối finally: Xóa file tạm tmp_path.unlink() nếu file còn tồn tại.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ chấp nhận tệp định dạng .pdf.",
        )
    
    document_id = f"doc_{uuid4()}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        tmp_path = Path(temp_file.name)
    
    try:
        content = await file.read()
        tmp_path.write_bytes(content)

        parsed_doc = process_pdf(path=tmp_path, document_id=document_id)
        if file.filename:
            parsed_doc = replace(
                parsed_doc,
                metadata=replace(parsed_doc.metadata, filename=file.filename),
            )

        search_service.index_chunks(parsed_doc.chunks)
        documents_store[document_id] = parsed_doc
        return DocumentUploadResponse(
            document_id=document_id,
            filename=parsed_doc.metadata.filename,
            page_count=parsed_doc.metadata.page_count,
            chunk_count=len(parsed_doc.chunks),
        )
    except (InvalidDocumentError, NoExtractableTextError) as exp:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exp),
        )
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Xem chi tiết tài liệu và các đoạn trích",
)
def get_document_detail(
    document_id: str,
    documents_store: Annotated[dict[str, ParsedDocument], Depends(get_documents_store)],
) -> DocumentDetailResponse:
    """Lấy danh sách các chunks và metadata của tài liệu đã phân tích.
    
    Yêu cầu:
    1. Lấy parsed_doc = documents_store.get(document_id)
    2. Nếu không tìm thấy: raise HTTPException(404, f"Không tìm thấy tài liệu với ID: {document_id}")
    3. Trả về DocumentDetailResponse(document_id, filename, page_count, chunks=[ChunkSchema(...)])
    """
    parsed_doc = documents_store.get(document_id)
    if parsed_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tài liệu với ID: {document_id}",
        )

    return DocumentDetailResponse(
        document_id=parsed_doc.metadata.document_id,
        filename=parsed_doc.metadata.filename,
        page_count=parsed_doc.metadata.page_count,
        chunks=[
            ChunkSchema(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                page_numbers=list(chunk.page_numbers),
                token_count=chunk.token_count,
            )
            for chunk in parsed_doc.chunks
        ],
    )
