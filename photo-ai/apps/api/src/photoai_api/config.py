"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    app_name: str = "Photo AI API"
    debug: bool = False
    database_url: str = "postgresql://photoai:photoai@localhost:5432/photoai"
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"


settings = Settings()
