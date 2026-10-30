from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_URL = "redis://localhost:6379/0"
WORKER_MAX_JOBS = 10
JOB_TIMEOUT_SECONDS = 600


class Settings(BaseSettings):
    app_name: str = "DocMind"
    app_env: str = "development"
    log_level: str = "INFO"
    gemini_api_key: str | None = None
    database_url: str = "sqlite:///./docmind.db"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Redis & Distributed Worker Settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant Vector DB Settings (Phase 9.1)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "docmind_chunks"
    use_qdrant: bool = True

    # Embedding & Gatekeeper Settings (Phase 9.1 & 9.2)
    embedding_provider: Literal["bge", "gemini", "mock"] = "bge"
    enable_gatekeeper: bool = True
    gatekeeper_accept_threshold: float = 0.70
    gatekeeper_reject_threshold: float = 0.35
    enable_faithfulness_verifier: bool = True

    # Langfuse Observability Settings (Phase 9.4)
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "http://localhost:3001"

    worker_max_jobs: int = 10
    job_timeout_seconds: int = 600
    model_config = SettingsConfigDict(
        env_file=(
            BACKEND_DIR / ".env.local",
            BACKEND_DIR / ".env",
            ".env.local",
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    ocr_provider: Literal["none", "gemini", "paddle", "composite"] = "gemini"
    ocr_min_chars_threshold: int = 30
    ocr_cache_dir: str = ".cache/ocr"
    gemini_ocr_rpm_limit: int = 15


settings = Settings()
