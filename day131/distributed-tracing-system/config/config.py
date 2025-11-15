import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class TracingConfig:
    """Configuration for distributed tracing system"""
    service_name: str = "distributed-tracing-system"
    trace_id_header: str = "X-Trace-Id"
    span_id_header: str = "X-Span-Id"
    parent_span_header: str = "X-Parent-Span-Id"
    sampling_rate: float = 0.1  # 10% sampling
    redis_url: str = "redis://localhost:6379"
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8000
    
@dataclass
class ServiceConfig:
    """Service-specific configuration"""
    api_gateway_port: int = 8001
    user_service_port: int = 8002
    database_service_port: int = 8003
    log_level: str = "INFO"
    enable_console_logs: bool = True
    
config = TracingConfig()
service_config = ServiceConfig()
