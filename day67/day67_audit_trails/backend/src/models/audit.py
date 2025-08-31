from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import hashlib
import json

Base = declarative_base()

class AuditRecord(Base):
    __tablename__ = "audit_records"
    
    id = Column(Integer, primary_key=True, index=True)
    record_hash = Column(String(64), unique=True, nullable=False)
    previous_hash = Column(String(64), nullable=True)
    
    # Access details
    user_id = Column(String(100), nullable=False)
    session_id = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    
    # Operation details
    operation_type = Column(String(50), nullable=False)  # READ, SEARCH, DOWNLOAD
    resource_type = Column(String(50), nullable=False)   # LOG, METRIC, ALERT
    resource_id = Column(String(200), nullable=False)
    filters_applied = Column(Text, nullable=True)
    
    # Result
    success = Column(Boolean, nullable=False)
    records_returned = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_time_ms = Column(Integer, nullable=True)
    
    def generate_hash(self, previous_hash: str = None) -> str:
        """Generate SHA-256 hash for this record"""
        data = {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'operation_type': self.operation_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'success': self.success,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'previous_hash': previous_hash
        }
        
        hash_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def verify_integrity(self, previous_hash: str = None) -> bool:
        """Verify record integrity"""
        expected_hash = self.generate_hash(previous_hash)
        return expected_hash == self.record_hash

# Create indexes for performance
Index('idx_audit_user_time', AuditRecord.user_id, AuditRecord.created_at)
Index('idx_audit_resource', AuditRecord.resource_type, AuditRecord.resource_id)
Index('idx_audit_success', AuditRecord.success, AuditRecord.created_at)
