from pydantic_settings import BaseSettings
from typing import List, Dict, Any
import os

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Archive Configuration
    archive_base_path: str = "data/archives"
    cache_path: str = "data/cache"
    index_path: str = "data/indexes"
    
    # Performance Settings
    max_concurrent_downloads: int = 5
    chunk_size: int = 8192
    cache_size_mb: int = 1024
    
    # Compression Settings
    supported_formats: List[str] = ["gzip", "lz4", "zstd", "raw"]
    default_compression: str = "lz4"
    
    # Query Settings
    max_query_days: int = 365
    default_page_size: int = 100
    max_page_size: int = 1000
    
    model_config = {"env_file": ".env"}

settings = Settings()
