from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./opportunity_tracker.db"
    JWT_SECRET: str = "hackathon-super-secret-key-change-in-production-12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    FRONTEND_URL: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8000,http://localhost:8000"

    @property
    def cors_origins(self) -> List[str]:
        return [url.strip() for url in self.FRONTEND_URL.split(",") if url.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
