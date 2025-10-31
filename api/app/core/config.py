from pydantic import BaseSettings, PostgresDsn


class Settings(BaseSettings):
    database_url: PostgresDsn = "postgresql+asyncpg://postgres:postgres@db:5432/escalation"

    class Config:
        env_file = ".env"
        env_prefix = "ESCALATION_"


def get_settings() -> Settings:
    return Settings()
