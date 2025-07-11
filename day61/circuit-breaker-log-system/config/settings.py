"""
Configuration settings for circuit breaker system
"""
import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class CircuitBreakerSettings:
    """Circuit breaker configuration settings"""
    
    # Default circuit breaker settings
    DEFAULT_FAILURE_THRESHOLD: int = 5
    DEFAULT_RECOVERY_TIMEOUT: int = 60
    DEFAULT_TIMEOUT_DURATION: float = 10.0
    DEFAULT_HALF_OPEN_MAX_CALLS: int = 3
    
    # Service-specific settings
    DATABASE_FAILURE_THRESHOLD: int = 3
    DATABASE_RECOVERY_TIMEOUT: int = 30
    DATABASE_TIMEOUT_DURATION: float = 5.0
    
    MESSAGE_QUEUE_FAILURE_THRESHOLD: int = 5
    MESSAGE_QUEUE_RECOVERY_TIMEOUT: int = 20
    MESSAGE_QUEUE_TIMEOUT_DURATION: float = 3.0
    
    EXTERNAL_API_FAILURE_THRESHOLD: int = 2
    EXTERNAL_API_RECOVERY_TIMEOUT: int = 60
    EXTERNAL_API_TIMEOUT_DURATION: float = 10.0
    
    # Monitoring settings
    METRICS_COLLECTION_INTERVAL: int = 5
    METRICS_HISTORY_SIZE: int = 1000
    WEBSOCKET_UPDATE_INTERVAL: int = 2
    
    # Dashboard settings
    DASHBOARD_HOST: str = "0.0.0.0"
    DASHBOARD_PORT: int = 8000
    
    @classmethod
    def from_env(cls) -> 'CircuitBreakerSettings':
        """Create settings from environment variables"""
        return cls(
            DEFAULT_FAILURE_THRESHOLD=int(os.getenv('CB_DEFAULT_FAILURE_THRESHOLD', 5)),
            DEFAULT_RECOVERY_TIMEOUT=int(os.getenv('CB_DEFAULT_RECOVERY_TIMEOUT', 60)),
            DEFAULT_TIMEOUT_DURATION=float(os.getenv('CB_DEFAULT_TIMEOUT_DURATION', 10.0)),
            DEFAULT_HALF_OPEN_MAX_CALLS=int(os.getenv('CB_DEFAULT_HALF_OPEN_MAX_CALLS', 3)),
            
            DATABASE_FAILURE_THRESHOLD=int(os.getenv('CB_DATABASE_FAILURE_THRESHOLD', 3)),
            DATABASE_RECOVERY_TIMEOUT=int(os.getenv('CB_DATABASE_RECOVERY_TIMEOUT', 30)),
            DATABASE_TIMEOUT_DURATION=float(os.getenv('CB_DATABASE_TIMEOUT_DURATION', 5.0)),
            
            MESSAGE_QUEUE_FAILURE_THRESHOLD=int(os.getenv('CB_QUEUE_FAILURE_THRESHOLD', 5)),
            MESSAGE_QUEUE_RECOVERY_TIMEOUT=int(os.getenv('CB_QUEUE_RECOVERY_TIMEOUT', 20)),
            MESSAGE_QUEUE_TIMEOUT_DURATION=float(os.getenv('CB_QUEUE_TIMEOUT_DURATION', 3.0)),
            
            EXTERNAL_API_FAILURE_THRESHOLD=int(os.getenv('CB_API_FAILURE_THRESHOLD', 2)),
            EXTERNAL_API_RECOVERY_TIMEOUT=int(os.getenv('CB_API_RECOVERY_TIMEOUT', 60)),
            EXTERNAL_API_TIMEOUT_DURATION=float(os.getenv('CB_API_TIMEOUT_DURATION', 10.0)),
            
            METRICS_COLLECTION_INTERVAL=int(os.getenv('CB_METRICS_INTERVAL', 5)),
            METRICS_HISTORY_SIZE=int(os.getenv('CB_METRICS_HISTORY_SIZE', 1000)),
            WEBSOCKET_UPDATE_INTERVAL=int(os.getenv('CB_WEBSOCKET_UPDATE_INTERVAL', 2)),
            
            DASHBOARD_HOST=os.getenv('CB_DASHBOARD_HOST', '0.0.0.0'),
            DASHBOARD_PORT=int(os.getenv('CB_DASHBOARD_PORT', 8000))
        )

# Global settings instance
settings = CircuitBreakerSettings.from_env()
