"""Application configuration loaded from .env / environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Database — defaults to SQLite for local dev; set to PostgreSQL+asyncpg in prod
    DB_URL: str = "sqlite+aiosqlite:///./kisan_saathi_dev.db"

    # JWT
    JWT_SECRET: str = "change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # External APIs
    WEATHER_API_KEY: str = ""
    MAPS_API_KEY: str = ""
    ML_MODEL_ENDPOINT: str = "http://localhost:8001/predict"
    AGRISTACK_UFSI_KEY: str = ""

    # CORS — comma-separated string from env, converted to list
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"


settings = Settings()
