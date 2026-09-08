from pydantic_settings import BaseSettings
import os

def _fix_db_url(url: str) -> str:
    # Render provides postgres:// but SQLAlchemy requires postgresql://
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./bhoomi.db"
    JWT_SECRET: str = "change-me-super-secret-jwt-key-demo-only"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    DEMO_MODE: bool = True
    BHASHINI_API_URL: str = "https://api.bhashini.gov.in"
    BHASHINI_API_KEY: str = ""
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    MODEL_PATH: str = "./ml/artifacts/model.joblib"
    LOG_LEVEL: str = "INFO"
    REDIS_URL: str = "redis://localhost:6379/0"
    RISK_THRESHOLD_LOW: float = 0.40
    RISK_THRESHOLD_HIGH: float = 0.70
    ALERT_THRESHOLD_CRITICAL: float = 0.85
    ALERT_RISK_INCREASE: float = 0.15
    # Render injects PORT and external URLs
    PORT: int = 8000
    FRONTEND_URL: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

    def get_database_url(self) -> str:
        url = os.getenv("DATABASE_URL", self.DATABASE_URL)
        return _fix_db_url(url)

    def get_cors_origins(self) -> list:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        # Auto-include Render frontend URL and common Render domains
        extra = []
        if self.FRONTEND_URL:
            extra.append(self.FRONTEND_URL.strip())
        # Allow Render's preview URLs via wildcard is not supported by CORS; we explicitly add env CORS_ORIGINS
        # If running on Render, allow all frontend origins via env var
        for e in extra:
            if e and e not in origins:
                origins.append(e)
        # In production on Render, if CORS_ORIGINS env contains frontend URL, it will be used
        return origins if origins else ["*"]

settings = Settings()
# Fix DATABASE_URL at import time for SQLAlchemy
import os as _os
_os.environ["DATABASE_URL"] = settings.get_database_url()

def risk_level(prob: float) -> str:
    if prob < settings.RISK_THRESHOLD_LOW:
        return "LOW"
    if prob < settings.RISK_THRESHOLD_HIGH:
        return "MEDIUM"
    return "HIGH"
