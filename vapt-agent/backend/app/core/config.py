"""
Application Configuration - Loaded from environment variables / .env file.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "dev-secret-key-change-in-production"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ── Database ─────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://vaptuser:vaptpass@localhost:5432/vaptdb"
    DATABASE_URL_SYNC: str = "postgresql://vaptuser:vaptpass@localhost:5432/vaptdb"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ── Redis ─────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Celery ───────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── MinIO / S3 ────────────────────────────────────
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_EVIDENCE: str = "vapt-evidence"
    MINIO_BUCKET_REPORTS: str = "vapt-reports"
    MINIO_USE_SSL: bool = False

    # ── JWT ───────────────────────────────────────────
    JWT_SECRET_KEY: str = "dev-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── AI ───────────────────────────────────────────
    AI_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o"
    AWS_REGION: str = "us-east-1"
    AWS_BEDROCK_MODEL_ID: str = ""
    LOCAL_LLM_BASE_URL: str = "http://localhost:11434/v1"
    LOCAL_LLM_MODEL: str = "llama3"

    # ── CORS ─────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ── Proxy ────────────────────────────────────────
    MITM_PORT: int = 8080
    BACKEND_URL: str = "http://localhost:8000"

    # ── ZAP ──────────────────────────────────────────
    ZAP_API_KEY: str = "zap-api-key"
    ZAP_HOST: str = "localhost"
    ZAP_PORT: int = 8090

    # ── Nuclei ───────────────────────────────────────
    NUCLEI_TEMPLATES_PATH: str = "/app/nuclei-templates"
    NUCLEI_BINARY: str = "nuclei"


settings = Settings()
