import datetime

from pydantic import BaseModel, Field

from app.db.models import JobStatus


class JobResponse(BaseModel):
    job_id: str
    document_id: str | None = None
    filename: str | None = None
    file_size: int | None = None
    task_name: str
    status: JobStatus
    progress: int = Field(..., ge=0, le=100)
    error_message: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class AsyncUploadResponse(BaseModel):
    job_id: str
    document_id: str
    status: JobStatus = JobStatus.PENDING
    message: str = "Document accepted and queued for background processing."
