"""Configuration management for the incident management system"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Keys (use environment variables in production)
    pagerduty_api_key: str = Field(default="test_pd_key", env="PAGERDUTY_API_KEY")
    opsgenie_api_key: str = Field(default="test_og_key", env="OPSGENIE_API_KEY")
    
    # Webhook validation
    pagerduty_webhook_secret: Optional[str] = Field(default=None, env="PAGERDUTY_WEBHOOK_SECRET")
    opsgenie_webhook_secret: Optional[str] = Field(default=None, env="OPSGENIE_WEBHOOK_SECRET")
    
    # Database
    database_url: str = Field(default="sqlite:///./incidents.db", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # System settings
    max_alerts_per_minute: int = Field(default=100)
    default_escalation_timeout_minutes: int = Field(default=15)
    
    # Feature flags
    enable_pagerduty: bool = Field(default=True)
    enable_opsgenie: bool = Field(default=True)
    enable_webhook_validation: bool = Field(default=True)
    
    class Config:
        env_file = ".env"

_settings = None

def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
