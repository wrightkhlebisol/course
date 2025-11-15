import uuid
import threading
import contextvars
from typing import Optional, Dict, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

# Context variables for async-safe trace context
trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('trace_id', default=None)
span_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('span_id', default=None)
parent_span_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('parent_span_id', default=None)

@dataclass
class TraceContext:
    """Represents trace context for a request"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    service_name: str = "unknown"
    operation_name: str = "unknown"
    start_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "service_name": self.service_name,
            "operation_name": self.operation_name
        }

class TraceContextManager:
    """Manages trace context across service boundaries"""
    
    @staticmethod
    def generate_trace_id() -> str:
        """Generate a new trace ID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_span_id() -> str:
        """Generate a new span ID"""
        return str(uuid.uuid4())[:8]
    
    @staticmethod
    def create_trace_context(
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        service_name: str = "unknown",
        operation_name: str = "unknown"
    ) -> TraceContext:
        """Create a new trace context"""
        if trace_id is None:
            trace_id = TraceContextManager.generate_trace_id()
        
        span_id = TraceContextManager.generate_span_id()
        
        context = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            service_name=service_name,
            operation_name=operation_name,
            start_time=time.time()
        )
        
        return context
    
    @staticmethod
    def set_context(context: TraceContext):
        """Set trace context for current execution"""
        trace_id_var.set(context.trace_id)
        span_id_var.set(context.span_id)
        parent_span_var.set(context.parent_span_id)
    
    @staticmethod
    def get_current_trace_id() -> Optional[str]:
        """Get current trace ID"""
        return trace_id_var.get()
    
    @staticmethod
    def get_current_span_id() -> Optional[str]:
        """Get current span ID"""
        return span_id_var.get()
    
    @staticmethod
    def get_current_context() -> Optional[TraceContext]:
        """Get current trace context"""
        trace_id = trace_id_var.get()
        span_id = span_id_var.get()
        parent_span_id = parent_span_var.get()
        
        if trace_id and span_id:
            return TraceContext(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id
            )
        return None

import time
