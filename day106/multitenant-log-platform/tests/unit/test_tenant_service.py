import pytest
from unittest.mock import patch
from backend.services.tenant_service import TenantService
from backend.models.tenant import ServiceTier, TenantStatus
from tests.conftest import TestingSessionLocal

@pytest.fixture
def tenant_service(db_session):
    """Create tenant service with test database session"""
    with patch('backend.services.tenant_service.get_db') as mock_get_db:
        # Create a generator that yields the db_session each time it's called
        def mock_db_generator():
            while True:
                yield db_session
        
        mock_get_db.return_value = mock_db_generator()
        yield TenantService()

def test_create_tenant(tenant_service):
    """Test tenant creation"""
    # Clear any existing data first
    from backend.models.tenant import Tenant
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        db.query(Tenant).delete()
        db.commit()
    finally:
        db.close()
    
    tenant = tenant_service.create_tenant(
        name="Test Company",
        domain="test.com",
        service_tier=ServiceTier.BASIC
    )
    
    assert tenant is not None
    assert tenant.name == "Test Company"
    assert tenant.domain == "test.com"
    assert tenant.service_tier == ServiceTier.BASIC
    assert tenant.status == TenantStatus.ACTIVE

def test_create_tenant_user(tenant_service):
    """Test tenant user creation"""
    # Create tenant first
    tenant = tenant_service.create_tenant(
        name="Test Company 2",
        domain="test2.com"
    )
    
    # Create user
    user = tenant_service.create_tenant_user(
        tenant_id=str(tenant.id),
        email="test@test.com",
        username="testuser",
        password="password123",
        role="admin"
    )
    
    assert user is not None
    assert user.tenant_id == tenant.id
    assert user.username == "testuser"
    assert user.role == "admin"

def test_authenticate_user(tenant_service):
    """Test user authentication"""
    # Create tenant and user
    tenant = tenant_service.create_tenant(
        name="Test Company 3",
        domain="test3.com"
    )
    
    tenant_service.create_tenant_user(
        tenant_id=str(tenant.id),
        email="test@test.com",
        username="testuser",
        password="password123"
    )
    
    # Test authentication
    user = tenant_service.authenticate_user("test3.com", "testuser", "password123")
    assert user is not None
    assert user.username == "testuser"
    
    # Test invalid credentials
    invalid_user = tenant_service.authenticate_user("test3.com", "testuser", "wrongpass")
    assert invalid_user is None
