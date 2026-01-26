from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://crm_user:senha_forte_aqui@postgres:5432/innexarcrm"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas
    
    # CORS - parse from string
    CORS_ORIGINS: str = "http://localhost:3000,https://sales.innexar.app,https://www.sales.innexar.app"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    # External API
    EXTERNAL_API_TOKEN: str = "change-me-in-production-external-token"
    
    # Frontend URL (Production Default)
    FRONTEND_URL: str = "https://innexar.com"

    # Allow extra env vars to prevent startup crash
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

settings = Settings()

