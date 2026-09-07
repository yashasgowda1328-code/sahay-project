from pydantic_settings import BaseSettings, SettingsConfigDict
import logging
from typing import List
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "SAHAY API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+asyncpg://sahay:sahay@db:5432/sahay"

    CORS_ORIGINS_RAW: str = ""

    @property
    def CORS_ORIGINS(self) -> List[str]:
        import os
        v = self.CORS_ORIGINS_RAW or os.getenv("CORS_ORIGINS", "http://localhost:5173")
        v = v.strip()
        if not v:
            return []
        if v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                pass
        return [origin.strip() for origin in v.split(",") if origin.strip()]


settings = Settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
