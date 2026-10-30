import logging
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)

from app.api.deps import get_document_repo, get_hybrid_search_service, get_job_repo
from app.api.schemas.documents import (
    ChunkSchema,
    DocumentDetailResponse,
    DocumentListItemSchema,
    DocumentUploadResponse,
)
from app.api.schemas.jobs import AsyncUploadResponse
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.job_repo import JobRepository, process_document_background
from app.db.session import SessionLocal
from app.documents.exceptions import InvalidDocumentError, NoExtractableTextError
from app.documents.service import process_pdf
from app.retrieval.service import HybridSearchService
from app.workers.setting import get_arq_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=AsyncUploadResponse | DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Tải lên và xử lý tài liệu PDF (hỗ trợ nền)",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="File PDF cần phân tích")],
    response: Response,
    hybrid_search_service: Annotated[HybridSearchService, Depends(get_hybrid_search_service)],
    doc_repo: Annotated[DocumentRepository, Depends(get_document_repo)],
    job_repo: Annotated[JobRepository, Depends(get_job_repo)],
    async_mode: bool = True,
) -> AsyncUploadResponse | DocumentUploadResponse:
    """API tải lên tài liệu PDF.

    - async_mode=True (mặc định): Trả về HTTP 202 Accepted và job_id để kiểm tra tiến độ nền.
    - async_mode=False: Xử lý đồng bộ và trả về HTTP 201 Created.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ chấp nhận tệp định dạng .pdf.",
        )

    document_id = f"doc_{uuid4()}"
    upload_dir = Path("/tmp/uploads") if Path("/tmp/uploads").is_dir() else None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=upload_dir) as temp_file:
        tmp_path = Path(temp_file.name)

    try:
        content = await file.read()
        tmp_path.write_bytes(content)

        if not async_mode:
            parsed_doc = process_pdf(path=tmp_path, document_id=document_id)
            if file.filename:
                parsed_doc = replace(
                    parsed_doc,
                    metadata=replace(parsed_doc.metadata, filename=file.filename),
                )

            hybrid_search_service.index_chunks(parsed_doc.chunks)
            doc_repo.save_parsed_document(parsed_doc, file_size=len(content))
            response.status_code = status.HTTP_201_CREATED

            return DocumentUploadResponse(
                document_id=document_id,
                filename=parsed_doc.metadata.filename,
                page_count=parsed_doc.metadata.page_count,
                chunk_count=len(parsed_doc.chunks),
            )

        job = job_repo.create_job(document_id=document_id)
        response.status_code = status.HTTP_202_ACCEPTED

        enqueued_to_redis = False
        try:
            from app.workers.setting import ping_redis

            if await ping_redis():
                arq_pool = await get_arq_pool()
                await arq_pool.enqueue_job(
                    "process_document_job",
                    job_id=job.id,
                    file_path=str(tmp_path),
                    original_filename=file.filename,
                    document_id=document_id,
                    _job_id=job.id,
                )
                enqueued_to_redis = True
        except Exception as queue_exc:
            logger.debug("Redis enqueue skipped (%s)", queue_exc)

        if not enqueued_to_redis:
            # Nếu không có Redis/ARQ, xử lý ngay lập tức bằng FastAPI background_tasks
            background_tasks.add_task(
                process_document_background,
                job_id=job.id,
                file_path=tmp_path,
                original_filename=file.filename,
                document_id=document_id,
                db_factory=SessionLocal,
                search_service=hybrid_search_service,
            )

        return AsyncUploadResponse(
            job_id=job.id,
            document_id=document_id,
            status=job.status,
        )

    except (InvalidDocumentError, NoExtractableTextError) as exp:
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exp),
        )
    except Exception:
        if not async_mode and tmp_path.exists():
            tmp_path.unlink()
        raise


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Xem chi tiết tài liệu và các đoạn trích",
)
def get_document_detail(
    document_id: str,
    doc_repo: Annotated[DocumentRepository, Depends(get_document_repo)],
) -> DocumentDetailResponse:
    """Lấy danh sách các chunks và metadata của tài liệu đã phân tích."""
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
