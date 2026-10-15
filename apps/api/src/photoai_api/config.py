"""Configuration from environment variables (no hard-coded secrets). §2 immutable rule #10."""
from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "photo-ai"
    environment: str = "development"
    database_url: str = "sqlite:///./photoai.db"
    redis_url: str = "redis://localhost:6379/0"
    queue_name: str = "photoai_jobs"

    # Storage
    storage_backend: str = "local"  # local | s3
    local_storage_path: str = "./storage"
    bucket_name: str = "photoai"

    # Security
    secret_key: str = "dev-secret-change-me"
    api_key_header: str = "X-API-Key"

    # Limits
    max_upload_mb: int = 25
    max_image_pixels: int = 40_000_000
    ttl_days: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
