import os
from dataclasses import dataclass
from typing import List

@dataclass
class FailoverConfig:
    # Heartbeat settings
    heartbeat_interval: int = 2  # seconds
    heartbeat_timeout: int = 6   # seconds (3 missed heartbeats)
    
    # Node settings
    primary_port: int = 8001
    standby_ports: List[int] = None
    
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Health check settings
    health_check_interval: int = 5  # seconds
    health_check_timeout: int = 2   # seconds
    
    # Election settings
    election_timeout: int = 10  # seconds
    
    def __post_init__(self):
        if self.standby_ports is None:
            self.standby_ports = [8002, 8003, 8004]

# Load configuration
config = FailoverConfig()

# Environment overrides
if os.getenv('REDIS_HOST'):
    config.redis_host = os.getenv('REDIS_HOST')

if os.getenv('REDIS_PORT'):
    config.redis_port = int(os.getenv('REDIS_PORT'))
