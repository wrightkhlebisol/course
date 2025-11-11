import pytest
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors.connection_manager import DatabaseConnectionManager
from src.collectors.postgresql_collector import PostgreSQLAuditCollector
from src.collectors.mysql_collector import MySQLAuditCollector
from src.collectors.mongodb_collector import MongoDBAbstractCollector

class TestDatabaseCollectors:
    
    def test_connection_manager_initialization(self):
        """Test connection manager initialization"""
        manager = DatabaseConnectionManager()
        assert manager is not None
        assert 'databases' in manager.config
        assert 'postgresql' in manager.config['databases']
        assert 'mysql' in manager.config['databases']
        assert 'mongodb' in manager.config['databases']
    
    @pytest.mark.asyncio
    async def test_postgresql_collector_initialization(self):
        """Test PostgreSQL collector initialization"""
        manager = DatabaseConnectionManager()
        collector = PostgreSQLAuditCollector(manager)
        assert collector is not None
        assert collector.connection_manager == manager
    
    def test_mysql_collector_initialization(self):
        """Test MySQL collector initialization"""
        manager = DatabaseConnectionManager()
        collector = MySQLAuditCollector(manager)
        assert collector is not None
        assert collector.connection_manager == manager
    
    def test_mongodb_collector_initialization(self):
        """Test MongoDB collector initialization"""
        manager = DatabaseConnectionManager()
        collector = MongoDBAbstractCollector(manager)
        assert collector is not None
        assert collector.connection_manager == manager
        
    def test_mongodb_collector_mock_collection(self):
        """Test MongoDB collector mock data collection"""
        manager = DatabaseConnectionManager()
        collector = MongoDBAbstractCollector(manager)
        
        # Test mock data generation
        logs = collector.collect_audit_logs()
        assert len(logs) == 10
        assert all('database_type' in log for log in logs)
        assert all(log['database_type'] == 'mongodb' for log in logs)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
