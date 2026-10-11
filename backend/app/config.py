from functools import lru_cache
from typing import Literal
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Path("data")
    ai_fallback: Literal['disabled', 'mock'] = 'disabled'
    max_upload_bytes: int = 10 * 1024 * 1024
    cors_origins: list[str] | str = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    @field_validator("cors_origins")
    @classmethod
    def assemble_cors_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return [origin.rstrip("/") for origin in value]

    @property
    def db_path(self) -> Path:
        return self.data_dir / "documents.db"

    @property
    def originals_dir(self) -> Path:
        return self.data_dir / "originals"


@lru_cache
def get_settings() -> Settings:
    return Settings()
