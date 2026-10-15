"""Application configuration (self-hosted CPU, in-memory store, no database)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Photo AI API"
    debug: bool = False
    # Max upload size in MB (mirrors the upload guard default).
    max_upload_mb: int = 20
    # CORS origins for the bundled frontend (served from the same origin by
    # default; the list matters only when the frontend runs on its own port).
    cors_origins: list[str] = ["*"]


settings = Settings()
