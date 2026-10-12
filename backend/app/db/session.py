from collections.abc import Generator
from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

if not settings.database_url:
    raise ValueError(
        "DATABASE_URL is not configured. Please set DATABASE_URL in .env.local or environment variables."
    )

# Xử lý tương thích kết nối SQLite vs PostgreSQL (hỗ trợ psycopg v3 nếu URL là postgresql://)
db_url = settings.database_url
if db_url.startswith("postgresql://"):
    try:
        import psycopg  # noqa: F401
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    except ImportError:
        pass

connect_args: dict[str, Any] = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # Tự động kiểm tra tính sống còn của connection
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Lớp cơ sở cho toàn bộ SQLAlchemy 2.0 Models."""
    pass

def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency cung cấp Database Session trong vòng đời request."""
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()