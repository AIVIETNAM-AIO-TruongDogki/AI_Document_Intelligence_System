import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import _hybrid_search_service
from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.search import router as search_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.seeder import seed_base_data_and_warmup
from app.db.session import Base, SessionLocal, engine
from app.workers.setting import close_arq_pool, close_redis_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    try:
        import app.db.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized.")

        # Tự động nạp tài liệu từ raw_data và làm nóng chỉ mục Hybrid Search
        with SessionLocal() as db_session:
            stats = seed_base_data_and_warmup(db=db_session, search_service=_hybrid_search_service)
            logger.info(
                "Base data ready: %d docs active, %d chunks indexed in Hybrid Search.",
                stats["total_active_documents"],
                stats["total_indexed_chunks"],
            )
    except Exception as exc:
        logger.warning("Startup initialization or base data seeding warning: %s", exc)

    yield

    await close_arq_pool()
    await close_redis_pool()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

# Cấu hình CORS linh hoạt cho mọi cổng phát triển Frontend (3000, 3001, v.v.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["http://localhost:3001", "http://127.0.0.1:3001"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(documents_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
