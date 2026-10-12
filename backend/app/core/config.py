from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "DocMind"
    app_env: str = "development"
    log_level: str = "INFO"
    gemini_api_key: str | None = None
    database_url: str = "sqlite:///./docmind.db"
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


settings = Settings()