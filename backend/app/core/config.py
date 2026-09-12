from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "greenlane_db"
    REDIS_URL: str = "redis://localhost:6379"

    JWT_SECRET: str
    REFRESH_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"

    @property
    def mongodb_url(self) -> str:
        return self.MONGODB_URL

    @property
    def database_name(self) -> str:
        return self.DATABASE_NAME

    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL


settings = Settings()

# Validate secrets at startup
_jwt_secret = settings.JWT_SECRET
_refresh_secret = settings.REFRESH_SECRET
if not _jwt_secret or _jwt_secret == "change-me-to-a-very-long-random-string-at-deploy":
    raise ValueError(
        "JWT_SECRET environment variable is missing or set to an unsafe default. "
        "Set a strong, random secret before starting the application."
    )
if not _refresh_secret or _refresh_secret == "change-me-to-a-very-long-refresh-secret-at-deploy":
    raise ValueError(
        "REFRESH_SECRET environment variable is missing or set to an unsafe default. "
        "Set a strong, random secret before starting the application."
    )
