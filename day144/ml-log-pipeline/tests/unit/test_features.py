"""Test feature extraction"""
import pytest
from src.feature_engineering.log_features import LogFeatureExtractor
from datetime import datetime

def test_feature_extraction():
    """Test basic feature extraction"""
    extractor = LogFeatureExtractor()
    
    log = {
        'timestamp': datetime.now().isoformat(),
        'level': 'ERROR',
        'service': 'web',
        'component': 'auth',
        'message': 'Database connection timeout',
        'metrics': {
            'response_time': 5000,
            'error_count': 10
        }
    }
    
    features = extractor.extract_all_features(log)
    
    assert features.shape[0] > 0
    assert features.dtype == 'float32'
    
def test_batch_extraction():
    """Test batch feature extraction"""
    extractor = LogFeatureExtractor()
    
    logs = [
        {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'service': 'api',
            'component': 'payment',
            'message': 'Payment processed',
            'metrics': {}
        }
        for _ in range(10)
    ]
    
    features = extractor.extract_batch(logs)
    
    assert features.shape[0] == 10
    assert features.shape[1] > 0
