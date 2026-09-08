from pydantic_settings import BaseSettings

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()

def risk_level(prob: float) -> str:
    if prob < settings.RISK_THRESHOLD_LOW:
        return "LOW"
    if prob < settings.RISK_THRESHOLD_HIGH:
        return "MEDIUM"
    return "HIGH"
