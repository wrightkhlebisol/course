import json
import pika
import structlog
from datetime import datetime
from typing import Dict, Any, Optional
from app.models.flag_log import FlagLog
from sqlalchemy.orm import Session

logger = structlog.get_logger()

class FlagLoggingService:
    def __init__(self):
        self.setup_rabbitmq()
    
    def setup_rabbitmq(self):
        """Setup RabbitMQ connection for distributed logging"""
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = connection.channel()
            self.channel.exchange_declare(
                exchange='feature_flags',
                exchange_type='topic',
                durable=True
            )
        except Exception as e:
            logger.warning("RabbitMQ not available, falling back to database only", error=str(e))
            self.channel = None
    
    async def log_flag_event(
        self, 
        db: Session,
        flag_id: str,
        flag_name: str,
        event_type: str,
        previous_state: Optional[Dict] = None,
        new_state: Optional[Dict] = None,
        user_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """Log feature flag event to database and message queue"""
        
        # Create database log entry
        log_entry = FlagLog(
            flag_id=flag_id,
            flag_name=flag_name,
            event_type=event_type,
            previous_state=previous_state,
            new_state=new_state,
            user_id=user_id,
            user_agent=user_agent,
            ip_address=ip_address,
            context=context or {}
        )
        
        db.add(log_entry)
        db.commit()
        
        # Send to message queue for distributed processing
        if self.channel:
            try:
                message = {
                    "event_id": log_entry.id,
                    "timestamp": log_entry.timestamp.isoformat(),
                    "flag_name": flag_name,
                    "event_type": event_type,
                    "previous_state": previous_state,
                    "new_state": new_state,
                    "user_id": user_id,
                    "context": context or {}
                }
                
                routing_key = f"flags.{event_type}.{flag_name}"
                
                self.channel.basic_publish(
                    exchange='feature_flags',
                    routing_key=routing_key,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Make message persistent
                        content_type='application/json'
                    )
                )
            except Exception as e:
                logger.error("Failed to send flag event to queue", error=str(e))
        
        return log_entry
    
    async def log_flag_evaluation(
        self,
        db: Session,
        flag_name: str,
        result: bool,
        user_context: Dict,
        evaluation_context: Dict
    ):
        """Log flag evaluation for analytics"""
        await self.log_flag_event(
            db=db,
            flag_id=evaluation_context.get("flag_id", "unknown"),
            flag_name=flag_name,
            event_type="evaluate",
            new_state={"result": result, "user_context": user_context},
            context=evaluation_context
        )

logging_service = FlagLoggingService()
