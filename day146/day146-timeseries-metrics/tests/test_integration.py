"""
Integration tests for the complete pipeline
"""
import pytest
import sys
sys.path.insert(0, 'src')

from extractors.metrics_extractor import MetricsExtractor
from generators.log_generator import LogGenerator

def test_end_to_end_extraction():
    """Test log generation through extraction"""
    generator = LogGenerator()
    extractor = MetricsExtractor()
    
    # Generate test log
    log = generator.generate_log()
    
    # Extract metrics
    metrics = extractor.extract_from_log(log)
    
    assert len(metrics) > 0
    assert all(hasattr(m, 'measurement') for m in metrics)
    assert all(hasattr(m, 'tags') for m in metrics)
    assert all(hasattr(m, 'fields') for m in metrics)

def test_batch_generation():
    """Test batch log generation"""
    generator = LogGenerator()
    
    batch = generator.generate_batch(count=10)
    
    assert len(batch) == 10
    assert all('timestamp' in log for log in batch)
    assert all('service' in log for log in batch)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
