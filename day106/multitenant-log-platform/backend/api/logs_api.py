from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.tenant import LogEntry
from database.connection import get_tenant_session
from middleware.auth import get_current_tenant_context, TenantContext
import uuid
import structlog
import json

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

class LogEntryRequest(BaseModel):
    timestamp: Optional[datetime] = None
    level: str
    message: str
    source: Optional[str] = None
    service: Optional[str] = None
    log_metadata: Optional[Dict[str, Any]] = None
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def set_timestamp(cls, v):
        return v or datetime.utcnow()
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Level must be one of: {allowed_levels}')
        return v.upper()

class BulkLogRequest(BaseModel):
    logs: List[LogEntryRequest]

class LogSearchRequest(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    level: Optional[str] = None
    service: Optional[str] = None
    source: Optional[str] = None
    limit: int = 100
    offset: int = 0

class LogResponse(BaseModel):
    id: str
    timestamp: datetime
    level: str
    message: str
    source: Optional[str]
    service: Optional[str]
    log_metadata: Optional[Dict[str, Any]]
    created_at: datetime

async def store_log_entry(tenant_id: str, log_data: LogEntryRequest):
    """Store a single log entry with tenant isolation"""
    try:
        with get_tenant_session(tenant_id) as db:
            log_entry = LogEntry(
                tenant_id=uuid.UUID(tenant_id),
                timestamp=log_data.timestamp or datetime.utcnow(),
                level=log_data.level,
                message=log_data.message,
                source=log_data.source,
                service=log_data.service,
                log_metadata=log_data.log_metadata or {}
            )
            db.add(log_entry)
            db.flush()
            logger.info("Log entry stored", 
                       tenant_id=tenant_id, 
                       log_id=str(log_entry.id),
                       level=log_data.level)
    except Exception as e:
        logger.error("Failed to store log entry", 
                    tenant_id=tenant_id, 
                    error=str(e))
        raise

@router.post("/ingest")
async def ingest_log(
    log_request: LogEntryRequest,
    background_tasks: BackgroundTasks,
    context: TenantContext = Depends(get_current_tenant_context)
):
    """Ingest a single log entry"""
    background_tasks.add_task(store_log_entry, context.tenant_id, log_request)
    
    return {
        "status": "accepted",
        "tenant_id": context.tenant_id,
        "timestamp": log_request.timestamp.isoformat() if log_request.timestamp else datetime.utcnow().isoformat()
    }

@router.post("/ingest/bulk")
async def ingest_logs_bulk(
    bulk_request: BulkLogRequest,
    background_tasks: BackgroundTasks,
    context: TenantContext = Depends(get_current_tenant_context)
):
    """Ingest multiple log entries"""
    if len(bulk_request.logs) > 1000:  # Rate limiting
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 1000 logs per bulk request"
        )
    
    for log_data in bulk_request.logs:
        background_tasks.add_task(store_log_entry, context.tenant_id, log_data)
    
    return {
        "status": "accepted",
        "tenant_id": context.tenant_id,
        "count": len(bulk_request.logs)
    }

@router.post("/search")
async def search_logs(
    search_request: LogSearchRequest,
    context: TenantContext = Depends(get_current_tenant_context)
):
    """Search logs for current tenant"""
    try:
        with get_tenant_session(context.tenant_id) as db:
            query = db.query(LogEntry).filter(LogEntry.tenant_id == uuid.UUID(context.tenant_id))
            
            # Apply filters
            if search_request.start_time:
                query = query.filter(LogEntry.timestamp >= search_request.start_time)
            if search_request.end_time:
                query = query.filter(LogEntry.timestamp <= search_request.end_time)
            if search_request.level:
                query = query.filter(LogEntry.level == search_request.level.upper())
            if search_request.service:
                query = query.filter(LogEntry.service == search_request.service)
            if search_request.source:
                query = query.filter(LogEntry.source == search_request.source)
            
            # Apply pagination
            logs = query.order_by(LogEntry.timestamp.desc())\
                       .offset(search_request.offset)\
                       .limit(search_request.limit)\
                       .all()
            
            total_count = query.count()
            
            results = [
                LogResponse(
                    id=str(log.id),
                    timestamp=log.timestamp,
                    level=log.level,
                    message=log.message,
                    source=log.source,
                    service=log.service,
                    log_metadata=log.log_metadata,
                    created_at=log.created_at
                ) for log in logs
            ]
            
            return {
                "logs": results,
                "total_count": total_count,
                "offset": search_request.offset,
                "limit": search_request.limit
            }
    except Exception as e:
        logger.error("Log search failed", tenant_id=context.tenant_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )

@router.get("/analytics")
async def get_log_analytics(
    context: TenantContext = Depends(get_current_tenant_context)
):
    """Get log analytics for current tenant"""
    try:
        with get_tenant_session(context.tenant_id) as db:
            from sqlalchemy import func, text
            
            # Log count by level
            level_stats = db.query(
                LogEntry.level,
                func.count(LogEntry.id).label('count')
            ).filter(LogEntry.tenant_id == uuid.UUID(context.tenant_id))\
             .group_by(LogEntry.level)\
             .all()
            
            # Log count by service
            service_stats = db.query(
                LogEntry.service,
                func.count(LogEntry.id).label('count')
            ).filter(LogEntry.tenant_id == uuid.UUID(context.tenant_id))\
             .filter(LogEntry.service.isnot(None))\
             .group_by(LogEntry.service)\
             .limit(10)\
             .all()
            
            # Recent activity (last 24 hours)
            recent_activity = db.execute(text("""
                SELECT DATE_TRUNC('hour', timestamp) as hour,
                       COUNT(*) as count
                FROM log_entries 
                WHERE tenant_id = :tenant_id 
                  AND timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY hour
                ORDER BY hour
            """), {"tenant_id": context.tenant_id}).fetchall()
            
            return {
                "level_distribution": {
                    stat.level: stat.count for stat in level_stats
                },
                "service_distribution": {
                    stat.service or "unknown": stat.count for stat in service_stats
                },
                "hourly_activity": [
                    {
                        "hour": row.hour.isoformat(),
                        "count": row.count
                    } for row in recent_activity
                ]
            }
    except Exception as e:
        logger.error("Analytics generation failed", tenant_id=context.tenant_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analytics generation failed"
        )
