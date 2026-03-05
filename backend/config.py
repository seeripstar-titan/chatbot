"""
Application configuration loaded from environment variables.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "chatbot"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_secret_key: str = "change-me-in-production"
    app_cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("app_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://chatbot:chatbot_pass@localhost:5432/chatbot_db"
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # ── Redis ────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Google Gemini ────────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_max_tokens: int = 4096
    gemini_temperature: float = 1.0

    # ── JWT ───────────────────────────────────────────────────────────────
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ── Rate Limiting ────────────────────────────────────────────────────
    rate_limit_per_minute: int = 30
    rate_limit_per_hour: int = 500

    # ── Logging ──────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"

    # ── Widget ───────────────────────────────────────────────────────────
    widget_base_url: str = "http://localhost:8000"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
