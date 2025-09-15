from sqlalchemy import Column, String, DateTime, Text, Enum as SQLEnum, JSON
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum
from datetime import datetime

Base = declarative_base()

class TenantState(Enum):
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPROVISIONING = "deprovisioning"
    ARCHIVED = "archived"

class TenantModel(Base):
    __tablename__ = "tenants"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    plan = Column(String, default="basic")
    state = Column(SQLEnum(TenantState), default=TenantState.PROVISIONING)
    api_key = Column(String, unique=True)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
