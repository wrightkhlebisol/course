from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    department = Column(String(100))
    manager = Column(String(255))
    employee_id = Column(String(50))
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UserGroup(Base):
    __tablename__ = "user_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    group_dn = Column(String(512))
    group_name = Column(String(255))
    role = Column(String(50))  # Admin, Analyst, Viewer
    created_at = Column(DateTime, default=func.now())

class AuthSession(Base):
    __tablename__ = "auth_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True)
    user_id = Column(Integer, index=True)
    source_ip = Column(String(45))
    user_agent = Column(Text)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

class AuthLog(Base):
    __tablename__ = "auth_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), index=True)
    action = Column(String(50))  # login, logout, sync, failed_login
    source_ip = Column(String(45))
    user_agent = Column(Text)
    success = Column(Boolean)
    message = Column(Text)
    timestamp = Column(DateTime, default=func.now())
