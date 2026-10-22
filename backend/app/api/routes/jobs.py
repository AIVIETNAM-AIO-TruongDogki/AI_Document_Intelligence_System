from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_job_repo
from app.api.schemas.jobs import JobResponse
from app.db.repositories.job_repo import JobRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_response(job: JobModel) -> JobResponse:
    return JobResponse(
        job_id=job.id,
        document_id=job.document_id,
        filename=getattr(job, "filename", None),
        file_size=getattr(job, "file_size", None),
        task_name=job.task_name,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: str,
    job_repo: Annotated[JobRepository, Depends(get_job_repo)],
) -> JobResponse:
    job = job_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _to_response(job)


@router.get("", response_model=list[JobResponse])
def list_jobs(
    job_repo: Annotated[JobRepository, Depends(get_job_repo)],
) -> list[JobResponse]:
    return [_to_response(job) for job in job_repo.list_jobs(limit=20)]
