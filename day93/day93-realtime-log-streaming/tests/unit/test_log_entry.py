import pytest
import sys
import os
from datetime import datetime

# Add backend/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

from models.log_entry import LogEntry

def test_log_entry_creation():
    """Test creating a log entry"""
    log_entry = LogEntry(
        id="test-123",
        timestamp=datetime.now(),
        level="INFO",
        message="Test log message",
        source="test",
        stream_id="application"
    )
    
    assert log_entry.id == "test-123"
    assert log_entry.level == "INFO"
    assert log_entry.message == "Test log message"
    assert log_entry.source == "test"
    assert log_entry.stream_id == "application"

def test_log_entry_serialization():
    """Test log entry serialization to dict"""
    timestamp = datetime.now()
    log_entry = LogEntry(
        id="test-456",
        timestamp=timestamp,
        level="ERROR",
        message="Error message",
        source="test",
        stream_id="system"
    )
    
    data = log_entry.dict()
    assert data["id"] == "test-456"
    assert data["level"] == "ERROR"
    assert data["message"] == "Error message"
    assert data["source"] == "test"
    assert data["stream_id"] == "system"
