from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from services.tenant_service import TenantService
from middleware.auth import create_access_token, get_current_tenant_context, TenantContext
from models.tenant import ServiceTier, TenantStatus
from database.connection import get_db
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])

def get_tenant_service():
    """Dependency to get tenant service with database session"""
    return TenantService()

# Pydantic models
class TenantCreateRequest(BaseModel):
    name: str
    domain: str
    service_tier: ServiceTier = ServiceTier.BASIC
    admin_email: EmailStr
    admin_username: str
    admin_password: str

class TenantResponse(BaseModel):
    id: str
    name: str
    domain: str
    status: str
    service_tier: str
    created_at: str

class LoginRequest(BaseModel):
    tenant_domain: str
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    tenant_id: str
    username: str

@router.post("/", response_model=TenantResponse)
async def create_tenant(request: TenantCreateRequest, tenant_service: TenantService = Depends(get_tenant_service)):
    """Create a new tenant with admin user"""
    try:
        # Create tenant
        tenant = tenant_service.create_tenant(
            name=request.name,
            domain=request.domain,
            service_tier=request.service_tier
        )
        
        # Create admin user
        tenant_service.create_tenant_user(
            tenant_id=str(tenant.id),
            email=request.admin_email,
            username=request.admin_username,
            password=request.admin_password,
            role="admin"
        )
        
        return TenantResponse(
            id=str(tenant.id),
            name=tenant.name,
            domain=tenant.domain,
            status=tenant.status.value,
            service_tier=tenant.service_tier.value,
            created_at=tenant.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Error creating tenant", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, tenant_service: TenantService = Depends(get_tenant_service)):
    """Authenticate user and return tenant-scoped JWT token"""
    user = tenant_service.authenticate_user(
        tenant_domain=request.tenant_domain,
        username=request.username,
        password=request.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Get tenant info
    tenant = tenant_service.get_tenant_by_id(str(user.tenant_id))
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    # Create JWT token with tenant context
    token_data = {
        "tenant_id": str(tenant.id),
        "tenant_domain": tenant.domain,
        "user_id": str(user.id),
        "username": user.username,
        "role": user.role
    }
    
    access_token = create_access_token(token_data)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        tenant_id=str(tenant.id),
        username=user.username
    )

@router.get("/me/stats")
async def get_tenant_stats(context: TenantContext = Depends(get_current_tenant_context), tenant_service: TenantService = Depends(get_tenant_service)):
    """Get statistics for current tenant"""
    stats = tenant_service.get_tenant_stats(context.tenant_id)
    return stats

@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: str, 
    context: TenantContext = Depends(get_current_tenant_context),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Get tenant details - only accessible by same tenant or system admin"""
    if context.tenant_id != tenant_id and context.role != "system_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    tenant = tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status.value,
        service_tier=tenant.service_tier.value,
        created_at=tenant.created_at.isoformat()
    )
