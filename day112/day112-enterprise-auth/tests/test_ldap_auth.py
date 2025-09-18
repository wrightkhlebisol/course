import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.ldap.service import LDAPService

class TestLDAPService:
    @pytest.fixture
    def ldap_service(self):
        return LDAPService()

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, ldap_service):
        """Test successful LDAP authentication"""
        with patch('src.ldap.service.Connection') as mock_conn, \
             patch('src.ldap.service.Server') as mock_server:
            
            # Mock successful bind
            mock_user_conn = Mock()
            mock_user_conn.bind.return_value = True
            mock_user_conn.unbind.return_value = None
            
            mock_admin_conn = Mock()
            mock_admin_conn.entries = [Mock()]
            mock_admin_conn.entries[0].entry_dn = "cn=testuser,dc=company,dc=com"
            mock_admin_conn.entries[0].cn = "Test User"
            mock_admin_conn.entries[0].mail = "test@company.com"
            mock_admin_conn.entries[0].department = "IT"
            mock_admin_conn.entries[0].manager = "cn=manager,dc=company,dc=com"
            mock_admin_conn.unbind.return_value = None
            
            mock_conn.side_effect = [mock_admin_conn, mock_user_conn]
            
            result, user_info = await ldap_service.authenticate_user("testuser", "password123")
            
            assert result is True
            assert user_info is not None
            assert user_info['username'] == 'testuser'
            assert user_info['email'] == 'test@company.com'

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self, ldap_service):
        """Test LDAP authentication with invalid credentials"""
        with patch('src.ldap.service.Connection') as mock_conn, \
             patch('src.ldap.service.Server') as mock_server:
            
            mock_user_conn = Mock()
            mock_user_conn.bind.return_value = False
            
            mock_admin_conn = Mock()
            mock_admin_conn.entries = [Mock()]
            mock_admin_conn.entries[0].entry_dn = "cn=testuser,dc=company,dc=com"
            
            mock_conn.side_effect = [mock_admin_conn, mock_user_conn]
            
            result, user_info = await ldap_service.authenticate_user("testuser", "wrongpassword")
            
            assert result is False
            assert user_info is None

    @pytest.mark.asyncio 
    async def test_get_user_groups(self, ldap_service):
        """Test getting user group memberships"""
        with patch('src.ldap.service.Connection') as mock_conn, \
             patch('src.ldap.service.Server') as mock_server:
            
            mock_connection = Mock()
            mock_connection.entries = [
                Mock(entry_dn="cn=administrators,dc=company,dc=com", 
                     cn="administrators", description="Admin group"),
                Mock(entry_dn="cn=users,dc=company,dc=com", 
                     cn="users", description="User group")
            ]
            
            mock_conn.return_value = mock_connection
            
            groups = await ldap_service.get_user_groups("cn=testuser,dc=company,dc=com")
            
            assert len(groups) == 2
            assert groups[0]['name'] == 'administrators'
            assert groups[1]['name'] == 'users'

    @pytest.mark.asyncio
    async def test_health_check_success(self, ldap_service):
        """Test LDAP health check success"""
        with patch('src.ldap.service.Connection') as mock_conn, \
             patch('src.ldap.service.Server') as mock_server:
            
            mock_connection = Mock()
            mock_connection.bind.return_value = True
            mock_connection.bound = True
            mock_connection.unbind.return_value = None
            
            mock_conn.return_value = mock_connection
            
            result = await ldap_service.health_check()
            
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, ldap_service):
        """Test LDAP health check failure"""
        with patch('src.ldap.service.Connection') as mock_conn, \
             patch('src.ldap.service.Server') as mock_server:
            
            mock_conn.side_effect = Exception("Connection failed")
            
            result = await ldap_service.health_check()
            
            assert result is False
