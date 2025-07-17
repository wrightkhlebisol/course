from fastapi import Request

def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    return request.client.host

def get_user_agent(request: Request) -> str:
    """Get user agent from request"""
    return request.headers.get('User-Agent', 'unknown')
