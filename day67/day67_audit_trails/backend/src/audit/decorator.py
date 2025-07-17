from functools import wraps
from typing import Callable, Any, Dict
from fastapi import Request, HTTPException
from ..audit.service import AuditService
from ..utils.database import get_db
import time
import logging

logger = logging.getLogger(__name__)

def audit_access(operation_type: str, resource_type: str):
    """Decorator to audit API access"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user info
            request = None
            user_id = "anonymous"
            session_id = "no-session"
            
            # Find request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Try to get from kwargs
                request = kwargs.get('request')
            
            if not request:
                # Create a mock request for testing
                class MockRequest:
                    def __init__(self):
                        self.client = type('MockClient', (), {'host': 'localhost'})()
                        self.headers = {}
                
                request = MockRequest()
            
            # Extract user info from request (implement based on your auth system)
            user_id = request.headers.get('X-User-ID', 'anonymous')
            session_id = request.headers.get('X-Session-ID', 'no-session')
            
            # Prepare request info
            request_info = {
                'ip_address': request.client.host,
                'user_agent': request.headers.get('User-Agent', 'unknown')
            }
            
            # Start timing
            start_time = time.time()
            
            # Initialize audit service
            db = next(get_db())
            audit_service = AuditService(db)
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Calculate processing time
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Extract resource info from result or kwargs
                resource_id = str(kwargs.get('resource_id', 'unknown'))
                records_returned = len(result) if isinstance(result, list) else 1
                
                # Create audit record
                await audit_service.create_audit_record(
                    user_id=user_id,
                    session_id=session_id,
                    request_info=request_info,
                    operation_type=operation_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    success=True,
                    records_returned=records_returned,
                    processing_time_ms=processing_time_ms
                )
                
                return result
                
            except Exception as e:
                # Calculate processing time
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Create failure audit record
                await audit_service.create_audit_record(
                    user_id=user_id,
                    session_id=session_id,
                    request_info=request_info,
                    operation_type=operation_type,
                    resource_type=resource_type,
                    resource_id=str(kwargs.get('resource_id', 'unknown')),
                    success=False,
                    error_message=str(e),
                    processing_time_ms=processing_time_ms
                )
                
                raise
            
            finally:
                db.close()
        
        return wrapper
    return decorator
