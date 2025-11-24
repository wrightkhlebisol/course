"""Tests for data partitioner."""
import pytest
from datetime import datetime
from src.export.partitioner import DataPartitioner

def test_partition_key_generation():
    """Test partition key generation."""
    config = {
        'scheme': 'date_service_level',
        'date_format': 'year=%Y/month=%m/day=%d',
        'include_service': True,
        'include_level': True
    }
    
    partitioner = DataPartitioner(config)
    
    log_entry = {
        'service': 'api-gateway',
        'level': 'INFO'
    }
    
    export_time = datetime(2025, 5, 16, 10, 30, 0)
    key = partitioner.generate_partition_key(log_entry, export_time)
    
    assert 'year=2025' in key
    assert 'month=05' in key
    assert 'day=16' in key
    assert 'service=api-gateway' in key
    assert 'level=INFO' in key

def test_filename_generation():
    """Test filename generation."""
    config = {}
    partitioner = DataPartitioner(config)
    
    export_time = datetime(2025, 5, 16, 10, 30, 0)
    filename = partitioner.generate_filename(export_time, 'parquet', 'gzip')
    
    assert filename.startswith('export_')
    assert filename.endswith('.parquet.gz')
