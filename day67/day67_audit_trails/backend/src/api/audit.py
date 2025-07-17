from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..models.audit import AuditRecord
from ..audit.service import AuditService
from ..audit.decorator import audit_access
from ..utils.database import get_db
from pydantic import BaseModel

router = APIRouter()

class AuditRecordResponse(BaseModel):
    id: int
    record_hash: str
    user_id: str
    ip_address: str
    operation_type: str
    resource_type: str
    resource_id: str
    success: bool
    records_returned: Optional[int]
    created_at: datetime
    processing_time_ms: Optional[int]
    
    class Config:
        from_attributes = True

@router.get("/records", response_model=List[AuditRecordResponse])
@audit_access("READ", "AUDIT_RECORD")
async def get_audit_records(
    request: Request,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    operation_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get audit records with filtering"""
    audit_service = AuditService(db)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    records = audit_service.get_audit_records(
        user_id=user_id,
        resource_type=resource_type,
        operation_type=operation_type,
        start_date=start_date,
        limit=limit
    )
    
    return records

@router.get("/verify")
@audit_access("READ", "AUDIT_VERIFICATION")
async def verify_audit_chain(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(1000, ge=1, le=5000)
):
    """Verify audit chain integrity"""
    audit_service = AuditService(db)
    return audit_service.verify_audit_chain(limit)

@router.get("/statistics")
@audit_access("READ", "AUDIT_STATISTICS")
async def get_audit_statistics(
    request: Request,
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Get audit access statistics"""
    audit_service = AuditService(db)
    return audit_service.get_access_statistics(days)

@router.get("/compliance-report")
@audit_access("READ", "COMPLIANCE_REPORT")
async def generate_compliance_report(
    request: Request,
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Generate compliance report"""
    audit_service = AuditService(db)
    
    stats = audit_service.get_access_statistics(days)
    verification = audit_service.verify_audit_chain(1000)
    
    return {
        'report_period_days': days,
        'generated_at': datetime.utcnow(),
        'statistics': stats,
        'integrity_verification': verification,
        'compliance_status': 'COMPLIANT' if verification['integrity_status'] == 'VALID' else 'NON_COMPLIANT'
    }
