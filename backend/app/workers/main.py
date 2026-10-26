import asyncio
import logging

from arq.worker import run_worker

from app.core.config import settings
from app.workers.setting import get_arq_redis_settings
from app.workers.tasks import process_document_job, shutdown, startup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("arq.worker")


class WorkerSettings:
    """Cấu hình kỹ thuật cho ARQ Worker (Consumer).
    
    - functions: Danh sách các coroutines/tasks mà worker này lắng nghe và xử lý.
    - redis_settings: Thông số kết nối Redis (Host, Port, DB, Pool Size).
    - max_jobs: Số lượng coroutine jobs tối đa worker xử lý đồng thời (Concurrency control).
    - job_timeout: Thời gian tối đa (giây) cho phép 1 job chạy trước khi bị SIGTERM/Cancelled.
    - max_tries: Số lần retry tối đa nếu gặp ngoại lệ chưa bắt được.
    - health_check_interval: Tần suất gửi heartbeat lên Redis để báo worker còn sống.
    """
    functions = [process_document_job]
    redis_settings = get_arq_redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = settings.worker_max_jobs
    job_timeout = settings.job_timeout_seconds
    max_tries = 3
    health_check_interval = 10


def main() -> None:
    """Khởi động Worker process: python -m app.workers.main"""
    logger.info("Starting ARQ Worker with max_jobs=%d, timeout=%ds...", 
                settings.worker_max_jobs, settings.job_timeout_seconds)
    asyncio.run(run_worker(WorkerSettings))


if __name__ == "__main__":
    main()
