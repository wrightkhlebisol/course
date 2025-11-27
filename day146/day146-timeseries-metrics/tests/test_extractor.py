"""
Tests for metrics extractor
"""
import pytest
from datetime import datetime
import sys
sys.path.insert(0, 'src')

from extractors.metrics_extractor import MetricsExtractor, Metric

def test_extractor_creation():
    """Test extractor initialization"""
    extractor = MetricsExtractor()
    assert extractor is not None
    assert len(extractor.patterns) > 0

def test_http_metrics_extraction():
    """Test HTTP metric extraction"""
    extractor = MetricsExtractor()
    
    log_entry = {
        'timestamp': '2025-06-16T10:00:00Z',
        'service': 'api-gateway',
        'component': 'http-handler',
        'level': 'INFO',
        'endpoint': '/api/users',
        'response_time': 123.45,
        'status_code': 200
    }
    
    metrics = extractor.extract_from_log(log_entry)
    
    assert len(metrics) >= 2  # At least response time and status
    assert any(m.measurement == 'http_response' for m in metrics)
    assert any(m.measurement == 'http_status' for m in metrics)

def test_resource_metrics_extraction():
    """Test resource metric extraction"""
    extractor = MetricsExtractor()
    
    log_entry = {
        'timestamp': '2025-06-16T10:00:00Z',
        'service': 'database',
        'component': 'processor',
        'level': 'INFO',
        'cpu_usage': 45.5,
        'memory_usage': 512.0
    }
    
    metrics = extractor.extract_from_log(log_entry)
    
    assert len(metrics) >= 1
    resource_metrics = [m for m in metrics if m.measurement == 'resource_usage']
    assert len(resource_metrics) > 0

def test_metric_tags():
    """Test metric tags are correctly set"""
    extractor = MetricsExtractor()
    
    log_entry = {
        'timestamp': '2025-06-16T10:00:00Z',
        'service': 'test-service',
        'component': 'test-component',
        'level': 'INFO',
        'host': 'test-host',
        'response_time': 100.0
    }
    
    metrics = extractor.extract_from_log(log_entry)
    metric = metrics[0]
    
    assert metric.tags['service'] == 'test-service'
    assert metric.tags['component'] == 'test-component'
    assert metric.tags['host'] == 'test-host'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
