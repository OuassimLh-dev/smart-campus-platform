from functools import lru_cache
from pathlib import Path

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: PostgresDsn

    @field_validator("database_url")
    @classmethod
    def validate_driver(cls, value: PostgresDsn) -> PostgresDsn:
        if value.scheme not in {"postgresql", "postgresql+psycopg"}:
            raise ValueError("DATABASE_URL must use postgresql or postgresql+psycopg")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
