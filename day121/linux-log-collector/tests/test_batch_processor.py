"""Test Batch Processor"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.collector.batch_processor.batch_processor import BatchProcessor, LogBatch
from src.collector.file_monitor.file_monitor import LogEntry


class TestBatchProcessor:
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            'collector': {
                'batch_size': 5,
                'batch_timeout': 1.0
            },
            'output': {
                'endpoint': 'http://localhost:8080/api/logs',
                'timeout': 30,
                'retry_attempts': 2
            }
        }
    
    def test_log_batch_creation(self):
        """Test log batch creation and filling"""
        batch = LogBatch(max_size=3, max_age=5.0)
        
        assert batch.is_empty()
        assert not batch.is_ready()
        
        # Add logs to batch
        for i in range(2):
            log_entry = LogEntry(
                content=f"Test log {i}",
                source_path="/var/log/test.log",
                log_type="test"
            )
            is_full = batch.add_log(log_entry)
            assert not is_full  # Not full yet
        
        # Add one more to fill it
        log_entry = LogEntry(
            content="Test log 2",
            source_path="/var/log/test.log", 
            log_type="test"
        )
        is_full = batch.add_log(log_entry)
        assert is_full  # Now it's full
        assert len(batch.logs) == 3
    
    def test_batch_age_ready(self):
        """Test batch ready by age"""
        import time
        
        batch = LogBatch(max_size=10, max_age=0.1)  # 100ms timeout
        
        log_entry = LogEntry(
            content="Test log",
            source_path="/var/log/test.log",
            log_type="test"
        )
        batch.add_log(log_entry)
        
        assert not batch.is_ready()  # Too young
        
        time.sleep(0.15)  # Wait longer than max_age
        assert batch.is_ready()  # Now ready due to age
    
    @pytest.mark.asyncio
    async def test_processor_initialization(self, config):
        """Test processor initialization"""
        processor = BatchProcessor(config)
        
        assert processor.batch_size == 5
        assert processor.batch_timeout == 1.0
        assert processor.endpoint == 'http://localhost:8080/api/logs'
        assert processor.retry_attempts == 2
    
    @pytest.mark.asyncio
    async def test_successful_batch_sending(self, config):
        """Test successful batch sending"""
        processor = BatchProcessor(config)
        
        # Create a test batch
        batch = LogBatch(max_size=2, max_age=5.0)
        log_entry = LogEntry(
            content="Test log",
            source_path="/var/log/test.log",
            log_type="test"
        )
        batch.add_log(log_entry)
        
        # Mock successful HTTP response
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            await processor._send_batch(batch)
            
            # Check stats were updated
            assert processor.stats['batches_sent'] == 1
            assert processor.stats['logs_sent'] == 1
    
    def test_stats_tracking(self, config):
        """Test statistics tracking"""
        processor = BatchProcessor(config)
        stats = processor.get_stats()
        
        assert 'batches_sent' in stats
        assert 'logs_sent' in stats
        assert 'bytes_sent' in stats
        assert 'send_errors' in stats
        assert 'last_send_time' in stats
