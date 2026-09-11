from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "DocMind RAG"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8001

    MODEL_MODE: Literal["fake", "real"] = "fake"

    LLM_API_KEY: str | None = None
    LLM_ENDPOINT: str | None = None
    LLM_MODEL: str | None = None
    EMBEDDING_API_KEY: str | None = None
    EMBEDDING_ENDPOINT: str | None = None
    EMBEDDING_MODEL: str | None = None
    MODEL_TIMEOUT_SECONDS: float = 30.0
    MODEL_MAX_RETRIES: int = 2

    DATA_DIR: Path = Path("./data")
    CHUNK_SIZE: int = Field(default=700, ge=100)
    CHUNK_OVERLAP: int = Field(default=100, ge=0)
    TOP_K: int = Field(default=3, ge=1, le=20)
    MAX_DISTANCE: float = Field(default=0.5, ge=0.0)
    CONTEXT_MAX_CHARS: int = Field(default=7000, ge=500)
    MAX_UPLOAD_MB: int = Field(default=10, ge=1, le=100)
    EMBED_BATCH_SIZE: int = Field(default=32, ge=1, le=256)
    CHROMA_COLLECTION: str = "docmind_chunks"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_chunk_config(self):
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self

    @property
    def sqlite_path(self) -> Path:
        return self.DATA_DIR / "docmind.db"

    @property
    def chroma_dir(self) -> Path:
        return self.DATA_DIR / "chroma"

    @property
    def temp_dir(self) -> Path:
        return self.DATA_DIR / "tmp"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    def ensure_directories(self) -> None:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def missing_real_model_config(self) -> list[str]:
        if self.MODEL_MODE != "real":
            return []
        required = {
            "LLM_API_KEY": self.LLM_API_KEY,
            "LLM_ENDPOINT": self.LLM_ENDPOINT,
            "LLM_MODEL": self.LLM_MODEL,
            "EMBEDDING_API_KEY": self.EMBEDDING_API_KEY,
            "EMBEDDING_ENDPOINT": self.EMBEDDING_ENDPOINT,
            "EMBEDDING_MODEL": self.EMBEDDING_MODEL,
        }
        return [name for name, value in required.items() if not value or value == "CHANGE_ME"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
