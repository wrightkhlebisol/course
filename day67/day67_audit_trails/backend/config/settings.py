import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://audit_user:audit_pass@localhost:5432/audit_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Audit Settings
    AUDIT_RETENTION_DAYS: int = 365
    MAX_AUDIT_RECORDS_PER_REQUEST: int = 1000
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Audit Trail System"
    
    class Config:
        env_file = ".env"

settings = Settings()
