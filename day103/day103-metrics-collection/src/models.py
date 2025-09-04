from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge" 
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class MetricPoint(BaseModel):
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = {}
    metric_type: MetricType = MetricType.GAUGE

class SystemMetrics(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_bytes_sent: int
    network_bytes_recv: int
    load_average: List[float]
    uptime: float
    timestamp: datetime

class ApplicationMetrics(BaseModel):
    logs_processed_total: int
    logs_processed_rate: float
    active_connections: int
    queue_depth: int
    error_rate: float
    response_time_p95: float
    timestamp: datetime

class Alert(BaseModel):
    id: str
    metric_name: str
    level: AlertLevel
    threshold: float
    current_value: float
    message: str
    timestamp: datetime
    resolved: bool = False

class MetricsSnapshot(BaseModel):
    system_metrics: SystemMetrics
    application_metrics: ApplicationMetrics
    alerts: List[Alert]
    timestamp: datetime
