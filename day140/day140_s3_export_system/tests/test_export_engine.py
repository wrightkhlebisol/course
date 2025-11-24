"""Tests for export engine."""
import pytest
from unittest.mock import Mock, MagicMock
from src.export.engine import ExportEngine
from src.storage.client import StorageClient

def test_export_engine_initialization():
    """Test export engine initialization."""
    config = {
        'database': {'url': 'sqlite:///:memory:', 'metadata_url': 'sqlite:///:memory:'},
        'export': {'batch_size': 1000, 'format': 'parquet', 'compression': 'gzip'},
        'partitioning': {},
        'retry': {}
    }
    
    storage_client = Mock(spec=StorageClient)
    engine = ExportEngine(config, storage_client)
    
    assert engine.batch_size == 1000
    assert engine.export_format == 'parquet'
    assert engine.compression == 'gzip'
