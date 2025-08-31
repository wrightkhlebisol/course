from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from ..models.audit import AuditRecord
from ..utils.security import get_client_ip, get_user_agent
import time
import json
import hashlib
import logging

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_audit_record(self, 
                                user_id: str,
                                session_id: str,
                                request_info: Dict[str, Any],
                                operation_type: str,
                                resource_type: str,
                                resource_id: str,
                                filters_applied: Optional[Dict] = None,
                                success: bool = True,
                                records_returned: Optional[int] = None,
                                error_message: Optional[str] = None,
                                processing_time_ms: Optional[int] = None) -> AuditRecord:
        """Create immutable audit record"""
        
        # Get previous hash for chain integrity
        previous_record = self.db.query(AuditRecord).order_by(desc(AuditRecord.id)).first()
        previous_hash = previous_record.record_hash if previous_record else None
        
        # Create audit record
        audit_record = AuditRecord(
            user_id=user_id,
            session_id=session_id,
            ip_address=request_info.get('ip_address', 'unknown'),
            user_agent=request_info.get('user_agent', 'unknown'),
            operation_type=operation_type,
            resource_type=resource_type,
            resource_id=resource_id,
            filters_applied=json.dumps(filters_applied) if filters_applied else None,
            success=success,
            records_returned=records_returned,
            error_message=error_message,
            processing_time_ms=processing_time_ms,
            previous_hash=previous_hash,
            created_at=datetime.utcnow()
        )
        
        # Generate hash for integrity
        audit_record.record_hash = audit_record.generate_hash(previous_hash)
        
        # Save to database
        self.db.add(audit_record)
        self.db.commit()
        self.db.refresh(audit_record)
        
        logger.info(f"Audit record created: {audit_record.record_hash}")
        return audit_record
    
    def get_audit_records(self, 
                         user_id: Optional[str] = None,
                         resource_type: Optional[str] = None,
                         operation_type: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: int = 100) -> List[AuditRecord]:
        """Retrieve audit records with filtering"""
        
        query = self.db.query(AuditRecord)
        
        if user_id:
            query = query.filter(AuditRecord.user_id == user_id)
        if resource_type:
            query = query.filter(AuditRecord.resource_type == resource_type)
        if operation_type:
            query = query.filter(AuditRecord.operation_type == operation_type)
        if start_date:
            query = query.filter(AuditRecord.created_at >= start_date)
        if end_date:
            query = query.filter(AuditRecord.created_at <= end_date)
        
        return query.order_by(desc(AuditRecord.created_at)).limit(limit).all()
    
    def verify_audit_chain(self, limit: int = 1000) -> Dict[str, Any]:
        """Verify integrity of audit chain"""
        records = self.db.query(AuditRecord).order_by(AuditRecord.id).limit(limit).all()
        
        verification_results = {
            'total_records': len(records),
            'verified_records': 0,
            'failed_records': 0,
            'integrity_status': 'VALID',
            'failures': []
        }
        
        previous_hash = None
        for record in records:
            if record.verify_integrity(previous_hash):
                verification_results['verified_records'] += 1
            else:
                verification_results['failed_records'] += 1
                verification_results['failures'].append({
                    'record_id': record.id,
                    'expected_hash': record.generate_hash(previous_hash),
                    'actual_hash': record.record_hash
                })
            
            previous_hash = record.record_hash
        
        if verification_results['failed_records'] > 0:
            verification_results['integrity_status'] = 'COMPROMISED'
        
        return verification_results
    
    def get_access_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get access statistics for compliance reporting"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = {
            'total_accesses': self.db.query(func.count(AuditRecord.id)).filter(
                AuditRecord.created_at >= start_date
            ).scalar(),
            'successful_accesses': self.db.query(func.count(AuditRecord.id)).filter(
                and_(AuditRecord.created_at >= start_date, AuditRecord.success == True)
            ).scalar(),
            'failed_accesses': self.db.query(func.count(AuditRecord.id)).filter(
                and_(AuditRecord.created_at >= start_date, AuditRecord.success == False)
            ).scalar(),
            'unique_users': self.db.query(func.count(func.distinct(AuditRecord.user_id))).filter(
                AuditRecord.created_at >= start_date
            ).scalar(),
            'operations_by_type': {},
            'resources_by_type': {}
        }
        
        # Get operation type breakdown
        op_stats = self.db.query(
            AuditRecord.operation_type,
            func.count(AuditRecord.id).label('count')
        ).filter(
            AuditRecord.created_at >= start_date
        ).group_by(AuditRecord.operation_type).all()
        
        stats['operations_by_type'] = {op.operation_type: op.count for op in op_stats}
        
        # Get resource type breakdown
        resource_stats = self.db.query(
            AuditRecord.resource_type,
            func.count(AuditRecord.id).label('count')
        ).filter(
            AuditRecord.created_at >= start_date
        ).group_by(AuditRecord.resource_type).all()
        
        stats['resources_by_type'] = {rs.resource_type: rs.count for rs in resource_stats}
        
        return stats
