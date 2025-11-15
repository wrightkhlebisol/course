"""Error and ErrorGroup database models"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

class ErrorGroup(Base):
    __tablename__ = "error_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    fingerprint = Column(String(64), unique=True, index=True)
    title = Column(String(500), nullable=False)
    status = Column(String(20), default="new")  # new, acknowledged, resolved, ignored
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    count = Column(Integer, default=1)
    level = Column(String(10), default="error")  # debug, info, warning, error, critical
    platform = Column(String(50))
    tags = Column(JSON, default=dict)
    assigned_to = Column(String(100))
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    errors = relationship("Error", back_populates="group")

class Error(Base):
    __tablename__ = "errors"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("error_groups.id"), nullable=False)
    event_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True)
    message = Column(Text, nullable=False)
    stack_trace = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(10), default="error")
    platform = Column(String(50))
    release = Column(String(100))
    environment = Column(String(50), default="production")
    user_id = Column(String(100))
    request_id = Column(String(100))
    trace_id = Column(String(100))  # From distributed tracing
    span_id = Column(String(100))   # From distributed tracing
    context = Column(JSON, default=dict)
    tags = Column(JSON, default=dict)
    extra = Column(JSON, default=dict)
    
    # Relationships
    group = relationship("ErrorGroup", back_populates="errors")
