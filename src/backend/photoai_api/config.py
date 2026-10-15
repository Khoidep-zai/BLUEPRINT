"""Application configuration (P0: in-memory store, no external database)."""
from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    app_name: str = "Photo AI API"
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
