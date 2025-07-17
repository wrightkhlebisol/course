#!/usr/bin/env python3

import sys
import os
import asyncio
from datetime import datetime, timedelta
import random

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.audit import Base, AuditRecord
from src.audit.service import AuditService
from config.settings import settings

async def generate_demo_data():
    """Generate demo audit records"""
    print("📊 Generating demo audit data...")
    
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    audit_service = AuditService(db)
    
    # Demo users and operations
    users = ['admin', 'analyst', 'developer', 'security_team', 'manager']
    operations = ['READ', 'SEARCH', 'DOWNLOAD']
    resources = ['LOG', 'METRIC', 'ALERT', 'REPORT']
    
    # Generate 50 demo records
    for i in range(50):
        user_id = random.choice(users)
        operation = random.choice(operations)
        resource = random.choice(resources)
        
        # Random timestamp within last 30 days
        timestamp = datetime.utcnow() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        request_info = {
            'ip_address': f"192.168.1.{random.randint(1, 255)}",
            'user_agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            ])
        }
        
        success = random.random() > 0.1  # 90% success rate
        
        await audit_service.create_audit_record(
            user_id=user_id,
            session_id=f"session_{i}",
            request_info=request_info,
            operation_type=operation,
            resource_type=resource,
            resource_id=f"{resource.lower()}_{random.randint(1, 1000)}",
            success=success,
            records_returned=random.randint(1, 100) if success else None,
            error_message=None if success else "Access denied",
            processing_time_ms=random.randint(10, 500)
        )
    
    db.close()
    print("✅ Demo data generated successfully!")

if __name__ == "__main__":
    asyncio.run(generate_demo_data())
