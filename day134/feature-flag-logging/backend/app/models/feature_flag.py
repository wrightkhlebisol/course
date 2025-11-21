from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    enabled = Column(Boolean, default=False)
    rollout_percentage = Column(String, default="0")
    target_groups = Column(JSON, default=list)
    flag_metadata = Column("metadata", JSON, default=dict)  # Column name in DB is "metadata", Python attr is "flag_metadata"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    updated_by = Column(String)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "rollout_percentage": self.rollout_percentage,
            "target_groups": self.target_groups,
            "metadata": self.flag_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        }
