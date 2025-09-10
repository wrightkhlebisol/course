import pytest
import asyncio
from backend.main import app
from backend.database.connection import engine, get_db
from backend.models.tenant import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import os

# Use PostgreSQL for testing (same as production)
TEST_DATABASE_URL = "postgresql://postgres:password@localhost:5432/multitenant_logs_test"
test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def setup_test_db():
    # Create test database if it doesn't exist
    import subprocess
    try:
        subprocess.run([
            "sudo", "-u", "postgres", "psql", "-c", 
            "CREATE DATABASE multitenant_logs_test;"
        ], check=False, capture_output=True)
    except:
        pass  # Database might already exist
    
    # Create test database tables
    try:
        Base.metadata.create_all(bind=test_engine)
        print("Test database tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise
    
    yield
    
    # Cleanup
    try:
        Base.metadata.drop_all(bind=test_engine)
        print("Test database tables cleaned up")
    except Exception as e:
        print(f"Error cleaning up tables: {e}")

@pytest.fixture
def client(setup_test_db):
    # Override the dependency to use test database
    app.dependency_overrides[get_db] = override_get_db
    
    # Also patch the tenant service and logs API to use test database
    from unittest.mock import patch
    from backend.services.tenant_service import TenantService
    
    def mock_get_db():
        while True:
            yield TestingSessionLocal()
    
    def mock_get_tenant_session(tenant_id):
        return TestingSessionLocal()
    
    with patch('backend.services.tenant_service.get_db', side_effect=mock_get_db), \
         patch('backend.database.connection.get_tenant_session', side_effect=mock_get_tenant_session), \
         patch('backend.api.logs_api.get_tenant_session', side_effect=mock_get_tenant_session):
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

@pytest.fixture
def db_session(setup_test_db):
    """Provide a database session for unit tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_test_environment(setup_test_db):
    """Automatically set up test environment for all tests"""
    # This fixture runs before each test
    pass

@pytest.fixture
def sample_tenant_data():
    return {
        "name": "Test Company",
        "domain": "test.com",
        "service_tier": "basic",  # Use lowercase enum value
        "admin_email": "admin@test.com",
        "admin_username": "testadmin",
        "admin_password": "testpass123"
    }
