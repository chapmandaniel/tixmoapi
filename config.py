"""
Configuration module for Ticket Vendor API.

Uses Pydantic Settings to load and validate environment variables.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = Field(default="Ticket Vendor API")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Database
    database_url: str = Field(
        ..., description="PostgreSQL database URL with asyncpg driver"
    )
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_ticket_hold_ttl: int = Field(default=300)  # 5 minutes

    # JWT Authentication
    secret_key: str = Field(..., description="Secret key for JWT encoding")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )
    cors_allow_credentials: bool = Field(default=True)

    # Stripe
    stripe_secret_key: str = Field(..., description="Stripe secret key")
    stripe_publishable_key: str = Field(..., description="Stripe publishable key")
    stripe_webhook_secret: str = Field(..., description="Stripe webhook secret")

    # SendGrid
    sendgrid_api_key: str = Field(..., description="SendGrid API key")
    sendgrid_from_email: str = Field(default="noreply@ticketvendor.com")
    sendgrid_from_name: str = Field(default="Ticket Vendor")

    # Email Templates
    email_template_purchase_confirmation: str = Field(default="")
    email_template_waitlist_notification: str = Field(default="")
    email_template_ticket_reminder: str = Field(default="")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_per_hour: int = Field(default=1000)

    # File Storage
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")
    aws_region: str = Field(default="us-east-1")
    s3_bucket_name: str = Field(default="ticket-vendor-assets")

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # Monitoring
    sentry_dsn: str = Field(default="")
    log_level: str = Field(default="INFO")

    # Frontend URL
    frontend_url: str = Field(default="http://localhost:3000")

    # Security
    bcrypt_rounds: int = Field(default=12)
    session_timeout_minutes: int = Field(default=60)

    # Features
    enable_waitlist: bool = Field(default=True)
    enable_qr_codes: bool = Field(default=True)
    enable_rate_limiting: bool = Field(default=True)

    # Ticket Hold Duration
    ticket_hold_duration_seconds: int = Field(default=300)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for Alembic migrations)."""
        return self.database_url.replace("postgresql+asyncpg", "postgresql")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Create a global settings instance
settings = get_settings()
