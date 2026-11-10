"""Application settings with caching and validation."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application configuration with environment variable support."""

    # Application
    APP_NAME: str = "AlphaCouncil"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # API
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"]
    )

    # Database
    DATABASE_URL: Optional[str] = Field(default=None)
    DATABASE_URL_POOLED: Optional[str] = Field(default=None)

    @property
    def async_database_url(self) -> str:
        """Get async database URL safely parsed for asyncpg."""
        url = self.DATABASE_URL or self.DATABASE_URL_POOLED
        if not url:
            return "postgresql+asyncpg://postgres:postgres@localhost:5432/alphacouncil"

        # Strip query parameters that asyncpg might choke on in connection string
        if "?" in url:
            url = url.split("?", 1)[0]

        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif not url.startswith("postgresql+asyncpg://"):
            # Fallback or prepend
            if "://" in url:
                scheme, rest = url.split("://", 1)
                url = f"postgresql+asyncpg://{rest}"
            else:
                url = f"postgresql+asyncpg://{url}"

        return url

    # Neon Auth & Storage
    NEON_AUTH_URL: Optional[str] = Field(default=None)
    NEON_JWKS: Optional[str] = Field(default=None)
    AWS_ENDPOINT_URL_S3: Optional[str] = Field(default=None)
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    AWS_REGION: Optional[str] = Field(default="us-east-2")
    S3_BUCKET: Optional[str] = Field(default="alphacouncil")

    # Redis/Celery (Aiven Redis)
    REDIS_URL: Optional[str] = Field(default=None)
    CELERY_BROKER_URL: Optional[str] = Field(default=None)
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None)

    @property
    def get_celery_broker_url(self) -> str:
        """Get Celery broker URL, ensuring ssl_cert_reqs for rediss://."""
        url = self.CELERY_BROKER_URL or self.REDIS_URL
        if url and url.startswith("rediss://") and "ssl_cert_reqs" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}ssl_cert_reqs=CERT_NONE"
        return url

    @property
    def get_celery_result_backend(self) -> str:
        """Get Celery result backend URL, ensuring ssl_cert_reqs for rediss://."""
        url = self.CELERY_RESULT_BACKEND or self.REDIS_URL
        if url and url.startswith("rediss://") and "ssl_cert_reqs" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}ssl_cert_reqs=CERT_NONE"
        return url

    # LLM Providers
    GROQ_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    OPENROUTER_API_KEY: Optional[str] = Field(default=None)

    # NGX
    KOBO_API_KEY: str = Field(default=None)

    # Default models
    DEFAULT_LLM_PROVIDER: str = Field(default="openrouter")
    DEFAULT_GROQ_MODEL: str = Field(default="openai/gpt-oss-20b")
    DEFAULT_OPENROUTER_MODEL: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b:free")
    DEFAULT_CLAUDE_MODEL: str = Field(default="claude-sonnet-4-20250514")

    # Market Data
    KOBO_API_KEY: Optional[str] = Field(default=None)

    # Web Search
    TAVILY_API_KEY: Optional[str] = Field(default=None)

    # Embedding Services
    VOYAGE_API_KEY: Optional[str] = Field(default=None)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    LOG_FILE: Optional[str] = Field(default="logs/alphacouncil.log")
    LOG_ROTATION: str = Field(default="10 MB")
    LOG_RETENTION: str = Field(default="30 days")
    LOG_JSON: bool = Field(default=False, description="Enable JSON logging")

    # Paths
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    UPLOAD_DIR: Path = Field(default_factory=lambda: Path("./uploads"))

    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Change this in production!"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)

    # Market Data
    YAHOO_FINANCE_TIMEOUT: int = Field(default=30)

    # Debate Settings
    MAX_DEBATE_ROUNDS: int = Field(default=3)
    DEBATE_TIMEOUT_SECONDS: int = Field(default=300)

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper

    @field_validator("UPLOAD_DIR", mode="before")
    @classmethod
    def ensure_upload_dir(cls, v: str | Path) -> Path:
        """Ensure upload directory exists."""
        path = Path(v) if isinstance(v, str) else v
        path.mkdir(parents=True, exist_ok=True)
        return path

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:

    return Settings()


settings = get_settings()
