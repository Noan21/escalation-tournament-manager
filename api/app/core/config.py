from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


def _build_default_database_url() -> str:
    env_url = os.getenv("ANGROM_DATABASE_URL")
    if env_url:
        return env_url

    user = os.getenv("ANGROM_DB_USER")
    password = os.getenv("ANGROM_DB_USER_PASSWORD")
    host = os.getenv("ANGROM_DB_HOST")
    port = os.getenv("ANGROM_DB_POOL_PORT")
    database = os.getenv("ANGROM_APP_POOL")

    if not all([user, password, host, port, database]):
        raise RuntimeError(
            "Database configuration missing. Define ANGROM_DATABASE_URL or "
            "ANGROM_DB_USER/ANGROM_DB_USER_PASSWORD/ANGROM_DB_HOST/"
            "ANGROM_DB_POOL_PORT/ANGROM_APP_POOL."
        )

    return (
        f"postgresql+psycopg_async://{user}:{password}@{host}:{port}/{database}"
        "?sslmode=require"
    )


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="ANGROM_", case_sensitive=False)

    database_url: str = Field(default_factory=_build_default_database_url)

    jwt_access_secret: str = Field(
        default="dev-access-secret",
        description="Secret key for signing access tokens.",
    )
    jwt_refresh_secret: str = Field(
        default="",
        description="Secret key for signing refresh tokens (defaults to access secret).",
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_minutes: int = Field(default=15)
    refresh_token_days: int = Field(default=7)

    email_verification_hours: int = Field(default=24)
    magic_link_minutes: int = Field(default=15)

    @model_validator(mode="after")
    def default_refresh_secret(self) -> Settings:
        if not self.jwt_refresh_secret:
            self.jwt_refresh_secret = self.jwt_access_secret
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
