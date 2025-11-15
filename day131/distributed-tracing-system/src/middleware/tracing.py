import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from src.tracing.context import TraceContextManager, TraceContext
from src.tracing.collector import get_trace_collector
from config.config import config

logger = structlog.get_logger()

class TracingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for distributed tracing"""
    
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing context"""
        start_time = time.time()
        
        # Extract trace context from headers
        trace_id = request.headers.get(config.trace_id_header)
        parent_span_id = request.headers.get(config.span_id_header)
        
        # Create trace context
        context = TraceContextManager.create_trace_context(
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            service_name=self.service_name,
            operation_name=f"{request.method} {request.url.path}"
        )
        
        # Set context for this request
        TraceContextManager.set_context(context)
        
        # Add trace headers to request state
        request.state.trace_context = context
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Record successful span
            trace_collector = await get_trace_collector()
            await trace_collector.record_span(
                context=context,
                operation=f"{request.method} {request.url.path}",
                duration_ms=duration_ms,
                status="success",
                metadata={
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "user_agent": request.headers.get("user-agent", ""),
                    "remote_addr": request.client.host if request.client else ""
                }
            )
            
            # Add trace headers to response
            response.headers[config.trace_id_header] = context.trace_id
            response.headers[config.span_id_header] = context.span_id
            
            return response
            
        except Exception as e:
            # Calculate duration for failed request
            duration_ms = (time.time() - start_time) * 1000
            
            # Record failed span
            trace_collector = await get_trace_collector()
            await trace_collector.record_span(
                context=context,
                operation=f"{request.method} {request.url.path}",
                duration_ms=duration_ms,
                status="error",
                metadata={
                    "method": request.method,
                    "path": str(request.url.path),
                    "error": str(e),
                    "user_agent": request.headers.get("user-agent", ""),
                    "remote_addr": request.client.host if request.client else ""
                }
            )
            
            logger.error("Request failed", 
                        trace_id=context.trace_id, 
                        span_id=context.span_id,
                        error=str(e))
            raise

class TracedLogger:
    """Logger that automatically includes trace context"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = structlog.get_logger()
    
    def _add_trace_context(self, **kwargs):
        """Add current trace context to log data"""
        context = TraceContextManager.get_current_context()
        if context:
            kwargs.update({
                "trace_id": context.trace_id,
                "span_id": context.span_id,
                "parent_span_id": context.parent_span_id,
                "service": self.service_name
            })
        return kwargs
    
    def info(self, message: str, **kwargs):
        """Log info message with trace context"""
        kwargs = self._add_trace_context(**kwargs)
        self.logger.info(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with trace context"""
        kwargs = self._add_trace_context(**kwargs)
        self.logger.error(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with trace context"""
        kwargs = self._add_trace_context(**kwargs)
        self.logger.warning(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with trace context"""
        kwargs = self._add_trace_context(**kwargs)
        self.logger.debug(message, **kwargs)
