from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class AlertStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FAILED = "failed"

class LogAlert(BaseModel):
    id: str
    title: str
    message: str
    severity: AlertSeverity
    service: str
    component: str
    timestamp: datetime
    metadata: Dict[str, Any]
    affected_users: Optional[int] = None
    runbook_url: Optional[str] = None
    dashboard_url: Optional[str] = None
    raw_logs: List[str] = []

class SlackMessage(BaseModel):
    channel: str
    text: str
    blocks: List[Dict[str, Any]] = []
    thread_ts: Optional[str] = None
    attachments: List[Dict[str, Any]] = []

class NotificationStatus(BaseModel):
    alert_id: str
    status: AlertStatus
    channel: str
    message_ts: Optional[str] = None
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    error_message: Optional[str] = None
