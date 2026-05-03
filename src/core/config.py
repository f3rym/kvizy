from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Telegram
    telegram_bot_token: str

    # Database
    database_url: str
    db_password: str

    # Redis
    redis_url: str

    # Security
    encryption_key: str

    # Application
    environment: str = "development"
    log_level: str = "INFO"

    # Optional
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
