"""Test complete pipeline"""
import pytest
import json
from pathlib import Path

def test_training_pipeline():
    """Test model training"""
    # Check training data exists
    data_path = Path("data/processed/training_logs.json")
    assert data_path.exists()
    
    with open(data_path) as f:
        logs = json.load(f)
    
    assert len(logs) > 0

def test_api_health():
    """Test API health endpoint"""
    import requests
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip("API not running")
