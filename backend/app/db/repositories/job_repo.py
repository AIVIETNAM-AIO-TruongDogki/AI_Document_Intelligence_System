from dataclasses import replace
from pathlib import Path
import uuid
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import JobModel, JobStatus
from app.db.repositories.document_repo import DocumentRepository
from app.documents.service import process_pdf
from app.retrieval.service import SearchService


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(
        self,
        document_id: str | None = None,
        task_name: str = "document_ingestion",
    ) -> JobModel:
        job = JobModel(
            id=f"job_{uuid.uuid4()}",
            document_id=document_id,
            task_name=task_name,
            status=JobStatus.PENDING,
            progress=0,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: str) -> JobModel | None:
        return self.db.query(JobModel).filter(JobModel.id == job_id).first()

    def update_progress(
        self,
        job_id: str,
        progress: int,
        status: JobStatus = JobStatus.PROCESSING,
    ) -> None:
        job = self.get_job(job_id)
        if job:
            job.progress = progress
            job.status = status
            self.db.commit()

    def mark_completed(self, job_id: str) -> None:
        job = self.get_job(job_id)
        if job:
            job.progress = 100
            job.status = JobStatus.COMPLETED
            self.db.commit()

    def mark_failed(self, job_id: str, error_message: str) -> None:
        job = self.get_job(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error_message = error_message
            self.db.commit()


async def process_document_background(
    job_id: str,
    file_path: Path,
    original_filename: str,
    document_id: str,
    db_factory: sessionmaker,
    search_service: SearchService,
) -> None:
    session = db_factory()
    job_repo = JobRepository(session)
    doc_repo = DocumentRepository(session)

    try:
        job = job_repo.get_job(job_id)
        if not job:
            return

        job_repo.update_progress(job_id, progress=10, status=JobStatus.PROCESSING)

        file_size = file_path.stat().st_size if file_path.exists() else 0
        parsed_doc = process_pdf(path=file_path, document_id=document_id)
        if original_filename:
            parsed_doc = replace(
                parsed_doc,
                metadata=replace(parsed_doc.metadata, filename=original_filename),
            )
        job_repo.update_progress(job_id, progress=40)

        search_service.index_chunks(parsed_doc.chunks)
        job_repo.update_progress(job_id, progress=70)

        doc_repo.save_parsed_document(parsed_doc, file_size=file_size)
        job_repo.update_progress(job_id, progress=90)

        job_repo.mark_completed(job_id)

    except Exception as e:
        session.rollback()
        job_repo.mark_failed(job_id, error_message=str(e))
        raise
    finally:
        if file_path.exists():
            file_path.unlink()
        session.close()
