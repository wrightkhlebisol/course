"""Application configuration settings"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/errortracking"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Application settings
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Error processing settings
    MAX_STACK_TRACE_LENGTH: int = 10000
    SIMILARITY_THRESHOLD: float = 0.8
    ERROR_BATCH_SIZE: int = 100
    FINGERPRINT_CACHE_TTL: int = 3600
    
    class Config:
        env_file = ".env"

settings = Settings()
