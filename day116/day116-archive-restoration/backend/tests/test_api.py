import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from restoration.api import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Archive Restoration API" in response.json()["message"]

def test_query_endpoint():
    query_data = {
        "start_time": (datetime.now() - timedelta(days=1)).isoformat(),
        "end_time": datetime.now().isoformat(),
        "filters": {},
        "page_size": 10,
        "include_archived": True
    }
    
    response = client.post("/api/query", json=query_data)
    assert response.status_code == 200
    
    result = response.json()
    assert "records" in result
    assert "total_count" in result
    assert "processing_time_ms" in result

def test_query_validation():
    # Test invalid date range
    query_data = {
        "start_time": datetime.now().isoformat(),
        "end_time": (datetime.now() - timedelta(days=1)).isoformat(),
        "filters": {},
        "page_size": 10
    }
    
    response = client.post("/api/query", json=query_data)
    assert response.status_code == 400

def test_archives_endpoint():
    response = client.get("/api/archives")
    assert response.status_code == 200
    
    result = response.json()
    assert "archives" in result
    assert "total" in result

def test_stats_endpoint():
    response = client.get("/api/stats")
    assert response.status_code == 200
    
    result = response.json()
    assert "cache" in result
    assert "archives" in result
    assert "active_jobs" in result

def test_create_sample_archives():
    response = client.post("/api/demo/create-sample-archives")
    assert response.status_code == 200
    
    result = response.json()
    assert "message" in result
    assert "files" in result

def test_refresh_index():
    response = client.post("/api/refresh-index")
    assert response.status_code == 200

def test_clear_cache():
    response = client.delete("/api/cache")
    assert response.status_code == 200
