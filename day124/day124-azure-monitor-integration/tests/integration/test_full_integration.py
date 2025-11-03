import pytest
import asyncio
import sys
import time
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_dir))

from azure_monitor.connector import AzureMonitorConnector
from azure_monitor.processor import AzureLogProcessor
from config.azure_config import DEMO_CONFIG

class TestFullIntegration:
    
    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Test complete log collection and processing flow"""
        connector = AzureMonitorConnector(DEMO_CONFIG)
        processor = AzureLogProcessor()
        
        # Connect to Azure
        connected = await connector.connect()
        assert connected
        
        # Discover workspaces
        workspaces = await connector.discover_workspaces()
        assert len(workspaces) > 0
        
        # Process logs from first workspace
        workspace_id = workspaces[0]['id']
        processed_count = 0
        
        async for log_entry in connector.query_logs(workspace_id):
            processed_entry = await processor.process_log_entry(log_entry)
            
            # Verify processed entry structure
            assert 'id' in processed_entry
            assert 'timestamp' in processed_entry
            assert 'workspace' in processed_entry
            assert 'source' in processed_entry
            assert processed_entry['source'] == 'azure_monitor'
            
            processed_count += 1
            if processed_count >= 10:  # Process 10 logs
                break
        
        # Verify statistics
        stats = processor.get_statistics()
        assert stats['total_processed'] >= 10
        
        # Verify insights
        insights = processor.get_insights_summary()
        assert 'total_logs_processed' in insights
        assert insights['total_logs_processed'] >= 10
        
        await connector.close()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        connector = AzureMonitorConnector(DEMO_CONFIG)
        
        # Test rapid requests
        start_time = time.time()
        
        for i in range(5):
            await connector.rate_limiter.acquire()
        
        elapsed = time.time() - start_time
        
        # Should complete quickly in demo mode
        assert elapsed < 2.0
        
        # Test rate limiter status
        status = connector.rate_limiter.get_status()
        assert 'tokens_available' in status
        assert 'rate_per_minute' in status
