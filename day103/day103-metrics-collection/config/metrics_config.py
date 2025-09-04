from dataclasses import dataclass
from typing import Dict, List
import os

@dataclass
class MetricsConfig:
    # Collection settings
    collection_interval: int = 5  # seconds
    batch_size: int = 100
    buffer_size: int = 1000
    
    # Storage settings
    redis_url: str = "redis://localhost:6379/0"
    influxdb_url: str = "http://localhost:8086"
    influxdb_token: str = "metrics-token"
    influxdb_org: str = "distributed-logs"
    influxdb_bucket: str = "system-metrics"
    
    # Retention policies
    high_resolution_retention: str = "1h"  # 1 second resolution
    medium_resolution_retention: str = "24h"  # 1 minute resolution  
    low_resolution_retention: str = "30d"  # 1 hour resolution
    
    # Alert thresholds
    cpu_warning_threshold: float = 75.0
    cpu_critical_threshold: float = 90.0
    memory_warning_threshold: float = 80.0
    memory_critical_threshold: float = 95.0
    disk_warning_threshold: float = 85.0
    disk_critical_threshold: float = 95.0
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    dashboard_port: int = 3000
    
    @classmethod
    def from_env(cls):
        return cls(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            influxdb_url=os.getenv("INFLUXDB_URL", "http://localhost:8086"),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000"))
        )
