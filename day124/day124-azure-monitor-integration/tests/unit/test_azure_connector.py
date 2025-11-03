import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src directory to Python path
src_dir = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_dir))

from azure_monitor.connector import AzureMonitorConnector, AzureLogEntry
from config.azure_config import DEMO_CONFIG

class TestAzureMonitorConnector:
    
    @pytest.fixture
    def connector(self):
        return AzureMonitorConnector(DEMO_CONFIG)
    
    def test_connector_initialization(self, connector):
        """Test connector initializes correctly"""
        assert connector.config == DEMO_CONFIG
        assert connector.rate_limiter is not None
        assert not connector.connection_healthy
    
    @pytest.mark.asyncio
    async def test_connection(self, connector):
        """Test Azure connection"""
        connected = await connector.connect()
        assert connected is True
        assert connector.connection_healthy is True
    
    @pytest.mark.asyncio
    async def test_discover_workspaces(self, connector):
        """Test workspace discovery"""
        await connector.connect()
        workspaces = await connector.discover_workspaces()
        
        assert len(workspaces) > 0
        assert all('id' in ws for ws in workspaces)
        assert all('name' in ws for ws in workspaces)
    
    @pytest.mark.asyncio
    async def test_query_logs(self, connector):
        """Test log querying"""
        await connector.connect()
        
        log_count = 0
        async for log_entry in connector.query_logs('demo-workspace-1'):
            assert isinstance(log_entry, AzureLogEntry)
            assert log_entry.workspace_id == 'demo-workspace-1'
            assert log_entry.source == 'azure_monitor'
            log_count += 1
            if log_count >= 5:  # Test first 5 logs
                break
        
        assert log_count == 5
    
    @pytest.mark.asyncio  
    async def test_health_status(self, connector):
        """Test health status reporting"""
        await connector.connect()
        health = await connector.get_health_status()
        
        assert 'healthy' in health
        assert 'workspaces_configured' in health
        assert health['workspaces_configured'] == len(DEMO_CONFIG.workspace_ids)
