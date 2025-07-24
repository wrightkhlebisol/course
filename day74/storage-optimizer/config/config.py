"""
Configuration settings for storage optimization system
"""
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class StorageConfig:
    # Storage paths
    base_data_path: str = "data"
    backup_path: str = "backups"
    
    # Format selection parameters
    analytical_threshold: float = 0.6
    full_record_threshold: float = 0.7
    
    # Compression settings
    enable_compression: bool = True
    compression_algorithm: str = "lz4"  # lz4, snappy, gzip
    
    # Performance settings
    batch_size: int = 1000
    max_memory_mb: int = 512
    
    # Query pattern analysis
    pattern_history_hours: int = 24
    min_queries_for_decision: int = 10
    
    # Migration settings
    auto_migration_enabled: bool = True
    migration_batch_size: int = 5000

@dataclass
class DashboardConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    auto_reload: bool = True
    log_level: str = "info"
    
    # WebSocket settings
    websocket_heartbeat: int = 5
    max_connections: int = 100

# Default configuration
DEFAULT_CONFIG = {
    'storage': StorageConfig(),
    'dashboard': DashboardConfig()
}

def load_config() -> Dict[str, Any]:
    """Load configuration from file or return defaults"""
    return DEFAULT_CONFIG
