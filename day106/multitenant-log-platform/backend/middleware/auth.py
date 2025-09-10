from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional, Dict, Any
from services.tenant_service import TenantService
import os
import structlog

logger = structlog.get_logger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "demo-secret-key-change-in-production")
ALGORITHM = "HS256"

security = HTTPBearer()
tenant_service = TenantService()

class TenantContext:
    """Holds tenant context for the current request"""
    def __init__(self, tenant_id: str, tenant_domain: str, user_id: str, username: str, role: str):
        self.tenant_id = tenant_id
        self.tenant_domain = tenant_domain
        self.user_id = user_id
        self.username = username
        self.role = role

def create_access_token(data: Dict[str, Any]) -> str:
    """Create JWT access token with tenant context"""
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_tenant_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TenantContext:
    """Extract tenant context from JWT token"""
    payload = verify_token(credentials.credentials)
    
    tenant_id = payload.get("tenant_id")
    tenant_domain = payload.get("tenant_domain")
    user_id = payload.get("user_id")
    username = payload.get("username")
    role = payload.get("role", "user")
    
    if not all([tenant_id, tenant_domain, user_id, username]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Verify tenant is still active
    tenant = tenant_service.get_tenant_by_id(tenant_id)
    if not tenant or tenant.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is not active"
        )
    
    return TenantContext(
        tenant_id=tenant_id,
        tenant_domain=tenant_domain,
        user_id=user_id,
        username=username,
        role=role
    )

def require_admin_role(context: TenantContext = Depends(get_current_tenant_context)) -> TenantContext:
    """Require admin role for the endpoint"""
    if context.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return context
