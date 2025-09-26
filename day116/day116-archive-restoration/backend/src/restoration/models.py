from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class CompressionType(str, Enum):
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"
    RAW = "raw"

class ArchiveMetadata(BaseModel):
    file_path: str
    start_time: datetime
    end_time: datetime
    compression: CompressionType
    original_size: int
    compressed_size: int
    record_count: int
    checksum: str
    tags: Dict[str, str] = Field(default_factory=dict)

class QueryRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    filters: Dict[str, Any] = Field(default_factory=dict)
    page_size: int = Field(default=100, le=1000)
    page_token: Optional[str] = None
    include_archived: bool = True
    stream_results: bool = False

class QueryResponse(BaseModel):
    records: List[Dict[str, Any]]
    total_count: int
    page_token: Optional[str] = None
    sources: List[str]
    processing_time_ms: int
    cache_hit: bool = False

class RestorationJob(BaseModel):
    job_id: str
    query: QueryRequest
    status: str
    progress: float
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    result_location: Optional[str] = None
    error_message: Optional[str] = None
