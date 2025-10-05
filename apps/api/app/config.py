from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", ".env.local"), env_file_encoding="utf-8", env_prefix="CONVERTER_")

    app_env: Literal["dev", "staging", "prod"] = Field(default="dev")
    log_level: str = Field(default="INFO")
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[3])
    data_root: Path = Field(default_factory=lambda: Path("vault"))
    database_url: str = Field(default="postgresql+psycopg2://converter:converter@localhost:5432/converter")
    redis_url: str = Field(default="redis://localhost:6379/0")
    ollama_endpoint: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3:8b")
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/1")
    enable_analytics: bool = Field(default=True)
    rollout_chunk_size: int = Field(default=1500)
    rollout_chunk_overlap: int = Field(default=200)


@lru_cache
def get_settings() -> Settings:
    return Settings()


