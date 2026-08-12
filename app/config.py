"""
Legal AI System - Application Configuration
============================================
Centralized settings management using pydantic-settings.
All values are loaded from environment variables or .env file.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "Legal AI System"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_secret_key: str = "change-this-in-production"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/legal_ai_db"
    database_url_sync: str = "postgresql://postgres:password@localhost:5432/legal_ai_db"

    # --- JWT ---
    jwt_secret_key: str = "change-this-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # --- CORS ---
    cors_origins: str = "http://localhost:4200,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # --- File Upload ---
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10
    allowed_extensions: str = ".pdf,.docx,.jpg,.jpeg,.png"

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse comma-separated extensions into a list."""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4"

    # --- Razorpay ---
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # --- Email / SMTP ---
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Legal AI System"
    smtp_from_email: str = "noreply@legalai.com"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Logging ---
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    # --- PDF Reports ---
    report_watermark_text: str = "CONFIDENTIAL"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
