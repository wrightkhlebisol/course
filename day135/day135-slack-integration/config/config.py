from pydantic import BaseSettings
from typing import Dict, List
import os

class Settings(BaseSettings):
    # Slack Configuration
    slack_bot_token: str = os.getenv("SLACK_BOT_TOKEN", "")
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    slack_app_token: str = os.getenv("SLACK_APP_TOKEN", "")
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Alert Configuration
    max_alerts_per_minute: int = int(os.getenv("MAX_ALERTS_PER_MINUTE", "60"))
    deduplication_window_minutes: int = int(os.getenv("DEDUPLICATION_WINDOW_MINUTES", "5"))
    default_channel: str = os.getenv("DEFAULT_CHANNEL", "#alerts")
    critical_channel: str = os.getenv("CRITICAL_CHANNEL", "#critical-alerts")
    
    # Channel Routing Configuration
    channel_routing: Dict[str, str] = {
        "payment": "#payments-team",
        "database": "#database-team", 
        "api": "#backend-team",
        "frontend": "#frontend-team",
        "security": "#security-team"
    }
    
    # Severity Levels
    severity_channels: Dict[str, List[str]] = {
        "critical": ["#critical-alerts", "#on-call"],
        "error": ["#alerts"],
        "warning": ["#monitoring"],
        "info": ["#notifications"]
    }

    class Config:
        env_file = ".env"

settings = Settings()
