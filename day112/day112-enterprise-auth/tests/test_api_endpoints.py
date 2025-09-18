import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from src.api.main import app
import json

client = TestClient(app)

class TestAPIEndpoints:
    def test_health_endpoint(self):
        """Test health check endpoint"""
        with patch('src.api.main.ldap_service.health_check') as mock_health:
            mock_health.return_value = True
            
            response = client.get("/api/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert 'services' in data

    def test_login_success(self):
        """Test successful login"""
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        with patch('src.api.main.ldap_service.authenticate_user') as mock_auth, \
             patch('src.api.main.sync_service.create_user_from_ldap') as mock_create, \
             patch('src.api.main.Session') as mock_session:
            
            # Mock successful authentication
            mock_auth.return_value = (True, {
                'username': 'testuser',
                'email': 'test@company.com',
                'full_name': 'Test User',
                'dn': 'cn=testuser,dc=company,dc=com'
            })
            
            # Mock database operations
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            mock_user = Mock()
            mock_user.id = 1
            mock_user.username = 'testuser'
            mock_user.email = 'test@company.com'
            mock_user.full_name = 'Test User'
            
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_create.return_value = mock_user
            
            # Mock groups
            mock_db.execute.return_value.scalars.return_value.all.return_value = []
            
            response = client.post("/api/auth/login", json=login_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert 'token' in data
            assert data['user']['username'] == 'testuser'

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        with patch('src.api.main.ldap_service.authenticate_user') as mock_auth, \
             patch('src.api.main.Session') as mock_session:
            
            # Mock failed authentication
            mock_auth.return_value = (False, None)
            
            # Mock database for logging
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            response = client.post("/api/auth/login", json=login_data)
            
            assert response.status_code == 401
            data = response.json()
            assert 'Invalid credentials' in data['detail']

    def test_profile_endpoint_unauthorized(self):
        """Test profile endpoint without authentication"""
        response = client.get("/api/auth/profile")
        
        assert response.status_code == 401

    def test_profile_endpoint_authorized(self):
        """Test profile endpoint with valid token"""
        with patch('src.api.main.get_current_user') as mock_get_user, \
             patch('src.api.main.Session') as mock_session:
            
            # Mock authenticated user
            mock_user = Mock()
            mock_user.username = 'testuser'
            mock_user.email = 'test@company.com'
            mock_user.full_name = 'Test User'
            mock_user.department = 'IT'
            mock_user.manager = 'Manager'
            mock_user.id = 1
            
            mock_get_user.return_value = mock_user
            
            # Mock groups
            mock_db = Mock()
            mock_session.return_value = mock_db
            mock_group = Mock()
            mock_group.group_name = 'administrators'
            mock_group.role = 'Admin'
            mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_group]
            
            # Create a mock dependency override
            app.dependency_overrides[mock_session] = lambda: mock_db
            
            response = client.get("/api/auth/profile", headers={"Authorization": "Bearer fake-token"})
            
            # Clear override
            app.dependency_overrides.clear()
            
            assert response.status_code == 200
            data = response.json()
            assert data['username'] == 'testuser'
            assert 'Admin' in data['roles']
