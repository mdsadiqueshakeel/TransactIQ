from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "TransactIQ"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: PostgresDsn = Field(
        default="postgresql+psycopg://transactiq:transactiq@postgres:5432/transactiq"
    )
    redis_url: RedisDsn = Field(default="redis://redis:6379/0")
    celery_broker_url: RedisDsn = Field(default="redis://redis:6379/0")
    celery_result_backend: RedisDsn = Field(default="redis://redis:6379/1")

    upload_dir: Path = Path("/app/storage/uploads")
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
