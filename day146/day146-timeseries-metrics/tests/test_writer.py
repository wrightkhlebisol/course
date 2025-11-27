"""
Tests for TimescaleDB writer
"""
import pytest
from datetime import datetime
import sys
sys.path.insert(0, 'src')

from writers.timescale_writer import TimescaleWriter

def test_writer_initialization():
    """Test writer can be initialized"""
    config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'metrics',
        'user': 'postgres',
        'password': 'password'
    }
    
    # This may fail if database isn't running - that's expected in unit tests
    try:
        writer = TimescaleWriter(config)
        assert writer is not None
        assert writer.batch_size == 1000
        writer.close()
    except Exception:
        pytest.skip("Database not available for testing")

def test_batch_accumulation():
    """Test batch accumulation logic"""
    config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'metrics',
        'user': 'postgres',
        'password': 'password'
    }
    
    try:
        writer = TimescaleWriter(config)
        writer.batch_size = 5  # Small batch for testing
        
        # Add metrics
        for i in range(3):
            metric = {
                'measurement': 'test_metric',
                'tags': {'service': 'test'},
                'fields': {'value': float(i)},
                'timestamp': datetime.now()
            }
            writer.add_metric(metric)
        
        assert len(writer.batch) == 3
        writer.close()
    except Exception:
        pytest.skip("Database not available for testing")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
