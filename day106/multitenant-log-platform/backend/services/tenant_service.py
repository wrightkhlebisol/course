from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.tenant import Tenant, TenantUser, TenantStatus, ServiceTier
from database.connection import get_db
from passlib.context import CryptContext
from typing import Optional, List, Dict, Any
import structlog
import uuid

logger = structlog.get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TenantService:
    """Service for managing tenants and tenant users"""
    
    def create_tenant(self, name: str, domain: str, 
                     service_tier: ServiceTier = ServiceTier.BASIC,
                     settings: Dict[str, Any] = None) -> Tenant:
        """Create a new tenant"""
        db = next(get_db())
        try:
            tenant = Tenant(
                name=name,
                domain=domain,
                service_tier=service_tier,
                settings=settings or {}
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            logger.info("Tenant created", tenant_id=str(tenant.id), name=name, domain=domain)
            return tenant
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Tenant with domain {domain} already exists")
        finally:
            db.close()
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain"""
        db = next(get_db())
        try:
            return db.query(Tenant).filter(Tenant.domain == domain).first()
        finally:
            db.close()
    
    def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        db = next(get_db())
        try:
            return db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
        finally:
            db.close()
    
    def update_tenant_status(self, tenant_id: str, status: TenantStatus) -> bool:
        """Update tenant status"""
        db = next(get_db())
        try:
            tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
            if tenant:
                tenant.status = status
                db.commit()
                logger.info("Tenant status updated", tenant_id=tenant_id, status=status.value)
                return True
            return False
        finally:
            db.close()
    
    def create_tenant_user(self, tenant_id: str, email: str, username: str, 
                          password: str, role: str = "user") -> TenantUser:
        """Create a user for a tenant"""
        db = next(get_db())
        try:
            password_hash = pwd_context.hash(password)
            user = TenantUser(
                tenant_id=uuid.UUID(tenant_id),
                email=email,
                username=username,
                password_hash=password_hash,
                role=role
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Tenant user created", tenant_id=tenant_id, username=username)
            return user
        finally:
            db.close()
    
    def authenticate_user(self, tenant_domain: str, username: str, password: str) -> Optional[TenantUser]:
        """Authenticate a tenant user"""
        db = next(get_db())
        try:
            tenant = self.get_tenant_by_domain(tenant_domain)
            if not tenant or tenant.status != TenantStatus.ACTIVE:
                return None
            
            user = db.query(TenantUser).filter(
                TenantUser.tenant_id == tenant.id,
                TenantUser.username == username,
                TenantUser.is_active == True
            ).first()
            
            if user and pwd_context.verify(password, user.password_hash):
                logger.info("User authenticated", tenant_id=str(tenant.id), username=username)
                return user
            return None
        finally:
            db.close()
    
    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant statistics"""
        from backend.models.tenant import LogEntry
        db = next(get_db())
        try:
            tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
            if not tenant:
                return {}
            
            log_count = db.query(LogEntry).filter(LogEntry.tenant_id == tenant.id).count()
            user_count = db.query(TenantUser).filter(TenantUser.tenant_id == tenant.id).count()
            
            return {
                "tenant_id": str(tenant.id),
                "name": tenant.name,
                "domain": tenant.domain,
                "status": tenant.status.value,
                "service_tier": tenant.service_tier.value,
                "total_logs": log_count,
                "total_users": user_count,
                "created_at": tenant.created_at.isoformat()
            }
        finally:
            db.close()
