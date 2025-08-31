from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ComplianceFramework(Base):
    __tablename__ = "compliance_frameworks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    description = Column(Text)
    requirements = Column(JSON)
    retention_period_days = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    reports = relationship("ComplianceReport", back_populates="framework")

class ComplianceReport(Base):
    __tablename__ = "compliance_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    framework_id = Column(Integer, ForeignKey("compliance_frameworks.id"))
    title = Column(String(200))
    description = Column(Text)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    file_path = Column(String(500))
    file_format = Column(String(10))  # pdf, csv, json, xml
    generated_at = Column(DateTime)
    generated_by = Column(String(100))
    signature_hash = Column(String(128))
    metadata = Column(JSON)
    
    framework = relationship("ComplianceFramework", back_populates="reports")

class AuditTrail(Base):
    __tablename__ = "audit_trails"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100))
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    user_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)
    compliance_relevant = Column(Boolean, default=False)
