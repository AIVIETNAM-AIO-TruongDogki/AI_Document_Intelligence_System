import asyncio
from unittest.mock import MagicMock, patch
import pytest

from app.db.models import JobStatus
from app.documents.models import DocumentMetadata, ParsedDocument
from app.workers.main import WorkerSettings
from app.workers.tasks import process_document_job, startup


def test_worker_settings_attributes():
    """Kiểm tra các thông số kỹ thuật của ARQ WorkerSettings."""
    assert WorkerSettings.functions == [process_document_job]
    assert WorkerSettings.max_jobs == 10
    assert WorkerSettings.job_timeout == 600
    assert WorkerSettings.max_tries == 3
    assert WorkerSettings.health_check_interval == 10


def test_worker_startup_context_injection():
    """Kiểm tra cơ chế Dependency Injection thông qua ctx của ARQ."""
    ctx = {}
    asyncio.run(startup(ctx))
    assert "db_factory" in ctx
    assert "search_service" in ctx


def test_process_document_job_success(tmp_path):
    """Kiểm tra luồng xử lý job khi file hợp lệ."""
    dummy_pdf = tmp_path / "sample.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4 dummy content")

    mock_db = MagicMock()
    mock_job_repo = MagicMock()
    mock_doc_repo = MagicMock()

    mock_job = MagicMock()
    mock_job.id = "job_123"
    mock_job_repo.get_job.return_value = mock_job

    mock_search_service = MagicMock()

    ctx = {
        "db_factory": lambda: mock_db,
        "search_service": mock_search_service,
    }

    with (
        patch("app.workers.tasks.JobRepository", return_value=mock_job_repo),
        patch("app.workers.tasks.DocumentRepository", return_value=mock_doc_repo),
        patch("app.workers.tasks.process_pdf") as mock_process_pdf,
    ):
        mock_parsed = ParsedDocument(
            metadata=DocumentMetadata(document_id="doc_123", filename="orig.pdf", page_count=1),
            pages=(),
            chunks=(),
        )
        mock_process_pdf.return_value = mock_parsed

        result = asyncio.run(
            process_document_job(
                ctx=ctx,
                job_id="job_123",
                file_path=str(dummy_pdf),
                original_filename="sample.pdf",
                document_id="doc_123",
            )
        )

        assert result["status"] == "success"
        assert result["job_id"] == "job_123"
        # Kiểm tra các milestone progress đã được cập nhật
        mock_job_repo.update_progress.assert_any_call("job_123", progress=10, status=JobStatus.PROCESSING)
        mock_job_repo.update_progress.assert_any_call("job_123", progress=40)
        mock_job_repo.update_progress.assert_any_call("job_123", progress=70)
        mock_job_repo.update_progress.assert_any_call("job_123", progress=90)
        mock_job_repo.mark_completed.assert_called_once_with("job_123")


def test_process_document_job_failure(tmp_path):
    """Kiểm tra xử lý lỗi và rollback trạng thái khi job thất bại."""
    dummy_pdf = tmp_path / "corrupt.pdf"
    dummy_pdf.write_bytes(b"corrupt")

    mock_db = MagicMock()
    mock_job_repo = MagicMock()
    mock_job = MagicMock()
    mock_job_repo.get_job.return_value = mock_job

    ctx = {
        "db_factory": lambda: mock_db,
        "search_service": MagicMock(),
    }

    with (
        patch("app.workers.tasks.JobRepository", return_value=mock_job_repo),
        patch("app.workers.tasks.DocumentRepository"),
        patch("app.workers.tasks.process_pdf", side_effect=RuntimeError("Corrupt PDF file")),
    ):
        with pytest.raises(RuntimeError):
            asyncio.run(
                process_document_job(
                    ctx=ctx,
                    job_id="job_failed",
                    file_path=str(dummy_pdf),
                    original_filename="corrupt.pdf",
                    document_id="doc_fail",
                )
            )

        mock_db.rollback.assert_called_once()
        mock_job_repo.mark_failed.assert_called_once()
