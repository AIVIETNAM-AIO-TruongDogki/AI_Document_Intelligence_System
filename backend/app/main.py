from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Khởi chạy logging và các tài nguyên khi app bật
    setup_logging()
    yield
    # Dọn dẹp tài nguyên khi app tắt (nếu có)


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.include_router(health_router)