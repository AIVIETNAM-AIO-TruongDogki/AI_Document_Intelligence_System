import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_document_repo, get_search_service
from app.api.schemas.documents import (
    ChunkSchema,
    DocumentDetailResponse,
    DocumentListItemSchema,
    DocumentUploadResponse,
)
from app.db.repositories.document_repo import DocumentRepository
from app.documents.exceptions import InvalidDocumentError, NoExtractableTextError
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
    doc_repo: Annotated[DocumentRepository, Depends(get_document_repo)],
) -> DocumentUploadResponse:
    """API tải lên tài liệu PDF.
    
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
        doc_repo.save_parsed_document(parsed_doc, file_size=len(content))

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
    doc_repo: Annotated[DocumentRepository, Depends(get_document_repo)],
) -> DocumentDetailResponse:
    """Lấy danh sách các chunks và metadata của tài liệu đã phân tích.
    """
    doc = doc_repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

    return DocumentDetailResponse(
        document_id=doc.id,
        filename=doc.filename,
        page_count=doc.page_count,
        chunks=[
            ChunkSchema(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                text=chunk.text,
                page_numbers=list(chunk.page_numbers),
                token_count=chunk.token_count,
            )
            for chunk in doc.chunks
        ],
    )


@router.get(
    "",
    response_model=list[DocumentListItemSchema],
    summary="Lấy danh sách các tài liệu đã tải lên",
)
def list_documents(
    doc_repo: Annotated[DocumentRepository, Depends(get_document_repo)],
) -> list[DocumentListItemSchema]:
    """Lấy danh sách toàn bộ tài liệu đã lưu trong CSDL."""
    docs = doc_repo.list_documents()
    return [
        DocumentListItemSchema(
            document_id=doc.id,
            filename=doc.filename,
            file_size=doc.file_size,
            page_count=doc.page_count,
        )
        for doc in docs
    ]


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa tài liệu",
)
def delete_document(
    document_id: str,
    doc_repo: Annotated[DocumentRepository, Depends(get_document_repo)],
) -> None:
    """Xóa một tài liệu và tự động cascade xóa toàn bộ trang & chunks liên quan."""
    deleted = doc_repo.delete_by_id(document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tài liệu với ID: {document_id}",
        )

