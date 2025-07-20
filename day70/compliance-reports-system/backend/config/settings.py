from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/compliance_db"
    
    # Security
    secret_key: str = "compliance-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Report Settings
    reports_storage_path: str = "./exports"
    max_report_size_mb: int = 100
    report_retention_days: int = 90
    
    # Compliance Frameworks
    supported_frameworks: list = ["SOX", "HIPAA", "PCI_DSS", "GDPR"]
    
    class Config:
        env_file = ".env"

settings = Settings()
