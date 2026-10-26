import asyncio
import logging
from dataclasses import replace
from pathlib import Path
from typing import Any

from app.db.models import JobStatus
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.job_repo import JobRepository
from app.db.session import SessionLocal
from app.documents.service import process_pdf
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.service import EmbeddingService
from app.retrieval.service import SearchService
from app.retrieval.vector_store import InMemoryVectorStore

logger = logging.getLogger(__name__)


async def startup(ctx: dict[str, Any]) -> None:
    """Worker lifecycle hook - Khởi tạo tài nguyên dùng chung trong Context (ctx).
    
    Kỹ thuật Context Injection trong ARQ:
    - Tránh khởi tạo lại kết nối DB/Embedding Model ở mỗi job.
    - Chia sẻ chung Pool & Services trong suốt vòng đời của Worker process.
    """
    logger.info("Initializing worker context...")
    ctx["db_factory"] = SessionLocal
    
    # Khởi tạo embedding/retrieval service cho worker (nếu worker chạy độc lập)
    if "search_service" not in ctx:
        embedding_provider = MockEmbeddingProvider(dimension=64)
        embedding_service = EmbeddingService(embedding_provider)
        vector_store = InMemoryVectorStore()
        ctx["search_service"] = SearchService(embedding_service, vector_store)
        
    logger.info("Worker context initialized successfully.")


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker lifecycle hook - Dọn dẹp tài nguyên khi worker dừng."""
    logger.info("Cleaning up worker resources...")


def _sync_process_document(
    job_id: str,
    path: Path,
    original_filename: str,
    document_id: str,
    db_factory: Any,
    search_service: SearchService,
) -> None:
    """Hàm đồng bộ chạy CPU-bound (PyMuPDF, Chunking, Embedding, DB I/O).
    
    Được bọc trong `asyncio.to_thread` để tránh block Asyncio Event Loop của Worker.
    Nếu block event loop, Redis heartbeat (Keepalive) sẽ bị miss và ARQ coi worker đã chết.
    """
    session = db_factory()
    job_repo = JobRepository(session)
    doc_repo = DocumentRepository(session)

    try:
        job = job_repo.get_job(job_id)
        if not job:
            logger.warning("Job %s not found in DB. Skipping execution.", job_id)
            return

        # Bước 1: Bắt đầu xử lý (10%)
        job_repo.update_progress(job_id, progress=10, status=JobStatus.PROCESSING)

        file_size = path.stat().st_size if path.exists() else 0

        # Bước 2: Parse PDF & Trích xuất Metadata / Chunks (40%)
        parsed_doc = process_pdf(path=path, document_id=document_id)
        if original_filename:
            parsed_doc = replace(
                parsed_doc,
                metadata=replace(parsed_doc.metadata, filename=original_filename),
            )
        job_repo.update_progress(job_id, progress=40)

        # Bước 3: Đưa chunks vào Index Search / Vector Store (70%)
        search_service.index_chunks(parsed_doc.chunks)
        job_repo.update_progress(job_id, progress=70)

        # Bước 4: Lưu Document & Chunks vào DB (90%)
        doc_repo.save_parsed_document(parsed_doc, file_size=file_size)
        job_repo.update_progress(job_id, progress=90)

        # Bước 5: Hoàn tất (100%)
        job_repo.mark_completed(job_id)
        logger.info("Job %s (document %s) completed successfully.", job_id, document_id)

    except Exception as exc:
        session.rollback()
        logger.exception("Error processing document job %s: %s", job_id, exc)
        job_repo.mark_failed(job_id, error_message=str(exc))
        raise
    finally:
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        session.close()


async def process_document_job(
    ctx: dict[str, Any],
    job_id: str,
    file_path: str,
    original_filename: str,
    document_id: str,
) -> dict[str, Any]:
    """Consumer Job Handler nhận nhiệm vụ từ Redis Queue.
    
    Args:
        ctx: Worker context chứa tài nguyên singleton (DB, Search Service)
        job_id: Định danh công việc (UUID)
        file_path: Đường dẫn file PDF tạm trên disk
        original_filename: Tên file gốc người dùng upload
        document_id: Định danh tài liệu sau khi parse
    """
    logger.info("Executing job %s for file: %s", job_id, original_filename)
    path = Path(file_path)
    db_factory = ctx.get("db_factory", SessionLocal)
    search_service: SearchService = ctx["search_service"]

    # Đẩy tác vụ nặng vào worker thread pool của OS, giữ Event Loop luôn rảnh
    await asyncio.to_thread(
        _sync_process_document,
        job_id=job_id,
        path=path,
        original_filename=original_filename,
        document_id=document_id,
        db_factory=db_factory,
        search_service=search_service,
    )

    return {
        "status": "success",
        "job_id": job_id,
        "document_id": document_id,
    }