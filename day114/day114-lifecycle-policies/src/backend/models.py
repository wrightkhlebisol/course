from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()

class LogEntry(Base):
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String, unique=True, index=True)
    log_type = Column(String, index=True)  # customer_activity, transaction_logs, etc.
    current_tier = Column(String, default="hot")
    file_path = Column(String)
    file_size_bytes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    log_metadata = Column(JSON)
    
class PolicyRule(Base):
    __tablename__ = "policy_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    log_type = Column(String, index=True)
    rule_type = Column(String)  # time_based, size_based, access_based
    conditions = Column(JSON)
    action = Column(String)  # move_to_warm, move_to_cold, archive, delete
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class PolicyExecution(Base):
    __tablename__ = "policy_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer)
    log_entry_id = Column(Integer)
    action_taken = Column(String)
    execution_time = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean)
    error_message = Column(Text, nullable=True)
    cost_impact = Column(Float, default=0.0)
