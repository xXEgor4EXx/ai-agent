from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Конфигурация приложения.

    Все значения могут быть переопределены через .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    APP_NAME: str = "PVA Expert AI Agent"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    GIGACHAT_CREDENTIALS: str = Field(default="")
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"
    GIGACHAT_MODEL: str = "GigaChat-2-Max"
    VERIFY_SSL: bool = False
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 3
    KNOWLEDGE_FILE: str = str(
        BASE_DIR / "data" / "knowledge_base.txt"
    )
    BITRIX_WEBHOOK_URL: str = ""
    BITRIX_USER_ID: str = ""
    REQUEST_TIMEOUT: int = 60
    MAX_RETRIES: int = 3
    RATE_LIMIT: int = 30
    MIN_SIMILARITY: float = 0.20
    TOP_K: int = 3
    MAX_CONTEXT_LENGTH: int = 2500


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()