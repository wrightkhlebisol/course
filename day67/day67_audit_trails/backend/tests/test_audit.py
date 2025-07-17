import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..src.models.audit import Base, AuditRecord
from ..src.audit.service import AuditService
from datetime import datetime

# Test database
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_create_audit_record(db):
    audit_service = AuditService(db)
    
    request_info = {
        'ip_address': '127.0.0.1',
        'user_agent': 'test-agent'
    }
    
    record = await audit_service.create_audit_record(
        user_id='test_user',
        session_id='test_session',
        request_info=request_info,
        operation_type='READ',
        resource_type='LOG',
        resource_id='log_123',
        success=True,
        records_returned=1
    )
    
    assert record.id is not None
    assert record.user_id == 'test_user'
    assert record.operation_type == 'READ'
    assert record.success == True
    assert record.record_hash is not None

def test_verify_audit_chain(db):
    audit_service = AuditService(db)
    
    # Create multiple records
    request_info = {'ip_address': '127.0.0.1', 'user_agent': 'test-agent'}
    
    for i in range(3):
        record = AuditRecord(
            user_id=f'user_{i}',
            session_id=f'session_{i}',
            ip_address='127.0.0.1',
            user_agent='test-agent',
            operation_type='READ',
            resource_type='LOG',
            resource_id=f'log_{i}',
            success=True,
            created_at=datetime.utcnow()
        )
        
        # Get previous hash
        previous_record = db.query(AuditRecord).order_by(AuditRecord.id.desc()).first()
        previous_hash = previous_record.record_hash if previous_record else None
        
        record.previous_hash = previous_hash
        record.record_hash = record.generate_hash(previous_hash)
        
        db.add(record)
        db.commit()
    
    # Verify chain
    verification = audit_service.verify_audit_chain()
    assert verification['integrity_status'] == 'VALID'
    assert verification['total_records'] == 3
    assert verification['verified_records'] == 3
    assert verification['failed_records'] == 0

def test_get_access_statistics(db):
    audit_service = AuditService(db)
    
    # Create test records
    for i in range(5):
        record = AuditRecord(
            user_id=f'user_{i}',
            session_id=f'session_{i}',
            ip_address='127.0.0.1',
            user_agent='test-agent',
            operation_type='READ',
            resource_type='LOG',
            resource_id=f'log_{i}',
            success=True,
            created_at=datetime.utcnow()
        )
        record.record_hash = record.generate_hash()
        db.add(record)
    
    db.commit()
    
    stats = audit_service.get_access_statistics()
    assert stats['total_accesses'] == 5
    assert stats['successful_accesses'] == 5
    assert stats['failed_accesses'] == 0
    assert 'READ' in stats['operations_by_type']
    assert 'LOG' in stats['resources_by_type']
