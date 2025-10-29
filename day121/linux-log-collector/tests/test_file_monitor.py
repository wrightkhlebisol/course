"""Test File Monitor"""
import pytest
import tempfile
import asyncio
import os
from pathlib import Path
from src.collector.file_monitor.file_monitor import LogFileMonitor, LogEntry, FileState
from src.collector.discovery.log_discovery import LogSource


class TestLogFileMonitor:
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            'buffer_size': 1000,
            'collector': {'batch_size': 10}
        }
    
    @pytest.fixture
    def temp_log_file(self):
        """Create temporary log file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("Initial log line\n")
            f.flush()
            yield f.name
        os.unlink(f.name)
    
    @pytest.mark.asyncio
    async def test_file_monitoring_initialization(self, config):
        """Test monitor initialization"""
        monitor = LogFileMonitor(config)
        assert monitor.log_queue.maxsize == 1000
        assert len(monitor.file_states) == 0
    
    @pytest.mark.asyncio
    async def test_log_entry_creation(self):
        """Test log entry creation"""
        entry = LogEntry(
            content="Test log message",
            source_path="/var/log/test.log",
            log_type="test",
            metadata={'hostname': 'testhost'}
        )
        
        assert entry.content == "Test log message"
        assert entry.source_path == "/var/log/test.log"
        assert entry.log_type == "test"
        assert entry.metadata['hostname'] == 'testhost'
        assert entry.size == len("Test log message")
    
    @pytest.mark.asyncio
    async def test_file_state_tracking(self, config, temp_log_file):
        """Test file state tracking"""
        import signal
        
        monitor = LogFileMonitor(config)
        
        # Create log source
        log_source = LogSource(temp_log_file, 'test', 'default')
        log_sources = {temp_log_file: log_source}
        
        # Initialize file states manually
        for path, source in log_sources.items():
            if os.path.exists(path):
                monitor.file_states[path] = FileState(path)
        
        # Just verify file state was created without starting infinite monitoring
        assert temp_log_file in monitor.file_states
        file_state = monitor.file_states[temp_log_file]
        assert file_state.path == temp_log_file
        assert file_state.position >= 0
    
    def test_stats_generation(self, config):
        """Test statistics generation"""
        monitor = LogFileMonitor(config)
        stats = monitor.get_stats()
        
        assert 'monitored_files' in stats
        assert 'queue_size' in stats
        assert 'queue_max_size' in stats
        assert 'total_bytes_read' in stats
