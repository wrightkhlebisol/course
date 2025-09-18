import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.sync.service import UserSyncService, sync_service

class TestUserSyncService:
    @pytest.fixture
    def sync_service_instance(self):
        return UserSyncService()

    def test_map_group_to_role_direct_mapping(self, sync_service_instance):
        """Test direct group to role mapping"""
        assert sync_service_instance.map_group_to_role('administrators') == 'Admin'
        assert sync_service_instance.map_group_to_role('log-analysts') == 'Analyst'
        assert sync_service_instance.map_group_to_role('log-viewers') == 'Viewer'

    def test_map_group_to_role_pattern_matching(self, sync_service_instance):
        """Test pattern-based group to role mapping"""
        assert sync_service_instance.map_group_to_role('IT-Admins') == 'Admin'
        assert sync_service_instance.map_group_to_role('developers') == 'Analyst'
        assert sync_service_instance.map_group_to_role('regular-users') == 'Viewer'

    @pytest.mark.asyncio
    async def test_create_user_from_ldap(self, sync_service_instance):
        """Test creating user from LDAP information"""
        user_info = {
            'username': 'testuser',
            'email': 'test@company.com',
            'full_name': 'Test User',
            'department': 'IT',
            'dn': 'cn=testuser,dc=company,dc=com'
        }
        
        with patch('src.sync.service.Session') as mock_session, \
             patch('src.sync.service.ldap_service.get_user_groups') as mock_get_groups:
            
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            mock_get_groups.return_value = [
                {'dn': 'cn=admin,dc=company,dc=com', 'name': 'administrators'}
            ]
            
            user = await sync_service_instance.create_user_from_ldap(user_info)
            
            # Verify database operations
            mock_db.add.assert_called()
            mock_db.commit.assert_called()

    @pytest.mark.asyncio 
    async def test_sync_all_users(self, sync_service_instance):
        """Test syncing all users"""
        with patch('src.sync.service.Session') as mock_session, \
             patch.object(sync_service_instance, 'sync_user') as mock_sync_user:
            
            # Mock database return
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            mock_user1 = Mock(username='user1')
            mock_user2 = Mock(username='user2') 
            mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_user1, mock_user2]
            
            # Mock sync results
            mock_sync_user.side_effect = [True, True]
            
            stats = await sync_service_instance.sync_all_users()
            
            assert stats['total'] == 2
            assert stats['success'] == 2
            assert stats['failed'] == 0
