from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..audit.decorator import audit_access
from ..utils.database import get_db
from pydantic import BaseModel
import random
import json

router = APIRouter()

class LogEntry(BaseModel):
    id: str
    timestamp: datetime
    level: str
    message: str
    source: str
    user_id: Optional[str] = None
    redacted: bool = False

class LogSearchRequest(BaseModel):
    query: Optional[str] = None
    level: Optional[str] = None
    source: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100

# Simulated log data for demonstration
SAMPLE_LOGS = [
    {
        "id": f"log_{i}",
        "timestamp": datetime.utcnow() - timedelta(hours=random.randint(0, 24)),
        "level": random.choice(["INFO", "WARNING", "ERROR", "DEBUG"]),
        "message": f"Sample log message {i}",
        "source": random.choice(["web-server", "database", "api-gateway"]),
        "user_id": f"user_{random.randint(1, 100)}" if random.random() > 0.5 else None,
        "redacted": random.random() > 0.8
    }
    for i in range(1000)
]

@router.post("/search")
@audit_access("SEARCH", "LOG")
async def search_logs(
    request: Request,
    search_request: LogSearchRequest,
    db: Session = Depends(get_db)
):
    """Search logs with audit tracking"""
    # Simulate log search
    filtered_logs = SAMPLE_LOGS.copy()
    
    if search_request.query:
        filtered_logs = [log for log in filtered_logs if search_request.query.lower() in log["message"].lower()]
    
    if search_request.level:
        filtered_logs = [log for log in filtered_logs if log["level"] == search_request.level]
    
    if search_request.source:
        filtered_logs = [log for log in filtered_logs if log["source"] == search_request.source]
    
    # Apply limit
    filtered_logs = filtered_logs[:search_request.limit]
    
    return {
        "logs": filtered_logs,
        "total_count": len(filtered_logs),
        "search_params": search_request.dict()
    }

@router.get("/log/{log_id}")
@audit_access("READ", "LOG")
async def get_log_by_id(
    request: Request,
    log_id: str,
    db: Session = Depends(get_db)
):
    """Get specific log by ID"""
    # Find log by ID
    log = next((log for log in SAMPLE_LOGS if log["id"] == log_id), None)
    
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return log

@router.get("/logs/user/{user_id}")
@audit_access("READ", "USER_LOG")
async def get_user_logs(
    request: Request,
    user_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get logs for specific user"""
    user_logs = [log for log in SAMPLE_LOGS if log.get("user_id") == user_id]
    
    return {
        "user_id": user_id,
        "logs": user_logs[:limit],
        "total_count": len(user_logs)
    }
