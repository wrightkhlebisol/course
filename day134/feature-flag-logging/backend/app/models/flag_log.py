from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class FlagLog(Base):
    __tablename__ = "flag_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flag_id = Column(String, nullable=False, index=True)
    flag_name = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)  # 'create', 'update', 'delete', 'evaluate'
    previous_state = Column(JSON)
    new_state = Column(JSON)
    user_id = Column(String)
    user_agent = Column(String)
    ip_address = Column(String)
    context = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "flag_id": self.flag_id,
            "flag_name": self.flag_name,
            "event_type": self.event_type,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "user_id": self.user_id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "context": self.context,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
