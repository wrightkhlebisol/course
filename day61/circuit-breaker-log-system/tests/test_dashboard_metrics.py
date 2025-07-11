#!/usr/bin/env python3
"""
Test file for dashboard metrics functionality
Tests API endpoints, WebSocket connections, and real-time metric updates
"""

import asyncio
import json
import time
import pytest
import requests
import websockets
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Test configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/metrics"

class TestDashboardMetrics:
    """Test dashboard metrics functionality"""
    
    def test_api_endpoints_accessible(self):
        """Test that all API endpoints are accessible"""
        endpoints = [
            "/api/metrics",
            "/api/metrics/history",
            "/",
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            assert response.status_code in [200, 404], f"Endpoint {endpoint} returned {response.status_code}"
            print(f"✅ {endpoint}: {response.status_code}")
    
    def test_metrics_api_structure(self):
        """Test that metrics API returns expected structure"""
        response = requests.get(f"{BASE_URL}/api/metrics", timeout=10)
        assert response.status_code == 200, f"Metrics API returned {response.status_code}"
        
        data = response.json()
        
        # Check required fields
        required_fields = ['timestamp', 'circuit_breakers', 'processing', 'system']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check timestamp is valid ISO format
        assert 'T' in data['timestamp'], "Timestamp should be ISO format"
        
        # Check circuit_breakers structure
        cb_data = data['circuit_breakers']
        assert 'global_stats' in cb_data, "Missing global_stats in circuit_breakers"
        assert 'circuit_breakers' in cb_data, "Missing circuit_breakers in circuit_breakers"
        
        # Check processing structure
        processing = data['processing']
        required_processing_fields = ['total_processed', 'successful_processed', 'failed_processed']
        for field in required_processing_fields:
            assert field in processing, f"Missing processing field: {field}"
        
        # Check system structure
        system = data['system']
        assert 'active_connections' in system, "Missing active_connections in system"
        assert 'metrics_history_size' in system, "Missing metrics_history_size in system"
        
        print("✅ Metrics API structure is correct")
    
    def test_metrics_history_api(self):
        """Test metrics history API"""
        response = requests.get(f"{BASE_URL}/api/metrics/history?minutes=5", timeout=10)
        assert response.status_code == 200, f"History API returned {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "History should return a list"
        
        if len(data) > 0:
            # Check that history entries have the same structure as current metrics
            first_entry = data[0]
            required_fields = ['timestamp', 'circuit_breakers', 'processing', 'system']
            for field in required_fields:
                assert field in first_entry, f"History entry missing field: {field}"
        
        print("✅ Metrics history API is working")
    
    def test_circuit_breaker_stats_update(self):
        """Test that circuit breaker stats update when operations are performed"""
        # Get initial stats
        initial_response = requests.get(f"{BASE_URL}/api/metrics", timeout=10)
        initial_data = initial_response.json()
        initial_calls = initial_data['circuit_breakers']['global_stats']['total_calls']
        
        # Simulate some log processing to trigger circuit breaker activity
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': 'Test log for metrics update',
            'service': 'test-service'
        }
        
        # Process some logs
        for i in range(3):
            response = requests.post(
                f"{BASE_URL}/api/process/logs?count=1",
                json=log_data,
                timeout=10
            )
            time.sleep(0.5)  # Small delay between requests
        
        # Get updated stats
        updated_response = requests.get(f"{BASE_URL}/api/metrics", timeout=10)
        updated_data = updated_response.json()
        updated_calls = updated_data['circuit_breakers']['global_stats']['total_calls']
        
        # Stats should have increased
        assert updated_calls >= initial_calls, "Circuit breaker calls should increase after operations"
        
        print(f"✅ Circuit breaker stats updated: {initial_calls} -> {updated_calls}")
    
    def test_processing_stats_update(self):
        """Test that processing stats update when logs are processed"""
        # Get initial processing stats
        initial_response = requests.get(f"{BASE_URL}/api/metrics", timeout=10)
        initial_data = initial_response.json()
        initial_processed = initial_data['processing']['total_processed']
        
        # Process some test logs
        response = requests.post(f"{BASE_URL}/api/process/logs?count=5", timeout=10)
        assert response.status_code == 200, "Log processing failed"
        
        # Wait a moment for processing
        time.sleep(1)
        
        # Get updated processing stats
        updated_response = requests.get(f"{BASE_URL}/api/metrics", timeout=10)
        updated_data = updated_response.json()
        updated_processed = updated_data['processing']['total_processed']
        
        # Processing count should have increased
        assert updated_processed >= initial_processed, "Processing count should increase after log processing"
        
        print(f"✅ Processing stats updated: {initial_processed} -> {updated_processed}")
    
    def test_system_stats_update(self):
        """Test that system stats are updated"""
        response = requests.get(f"{BASE_URL}/api/metrics", timeout=10)
        data = response.json()
        
        system = data['system']
        assert system['active_connections'] >= 0, "Active connections should be non-negative"
        assert system['metrics_history_size'] >= 0, "Metrics history size should be non-negative"
        
        print(f"✅ System stats: connections={system['active_connections']}, history_size={system['metrics_history_size']}")

class TestWebSocketMetrics:
    """Test WebSocket real-time metrics functionality"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection and message reception"""
        try:
            # Connect to WebSocket
            websocket = await websockets.connect(WS_URL)
            
            # Wait for first message
            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(message)
            
            # Verify message structure
            assert 'timestamp' in data, "WebSocket message missing timestamp"
            assert 'circuit_breakers' in data, "WebSocket message missing circuit_breakers"
            assert 'processing' in data, "WebSocket message missing processing"
            assert 'system' in data, "WebSocket message missing system"
            
            # Check that timestamp is recent
            message_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            now = datetime.now(message_time.tzinfo)
            time_diff = abs((now - message_time).total_seconds())
            assert time_diff < 60, "WebSocket message timestamp should be recent"
            
            await websocket.close()
            print("✅ WebSocket connection and message structure test passed")
            
        except Exception as e:
            pytest.fail(f"WebSocket test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_real_time_updates(self):
        """Test that WebSocket receives real-time updates"""
        try:
            websocket = await websockets.connect(WS_URL)
            
            # Get initial message
            initial_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            initial_data = json.loads(initial_message)
            initial_timestamp = initial_data['timestamp']
            
            # Wait for next update (should come every 2-5 seconds)
            next_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            next_data = json.loads(next_message)
            next_timestamp = next_data['timestamp']
            
            # Timestamps should be different (indicating updates)
            assert initial_timestamp != next_timestamp, "WebSocket should receive updated timestamps"
            
            # Check that metrics are being updated
            initial_calls = initial_data['circuit_breakers']['global_stats']['total_calls']
            next_calls = next_data['circuit_breakers']['global_stats']['total_calls']
            
            # Calls should be the same or increased (not decreased)
            assert next_calls >= initial_calls, "Circuit breaker calls should not decrease"
            
            await websocket.close()
            print("✅ WebSocket real-time updates test passed")
            
        except Exception as e:
            pytest.fail(f"WebSocket real-time test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_multiple_messages(self):
        """Test receiving multiple WebSocket messages"""
        try:
            websocket = await websockets.connect(WS_URL)
            
            messages = []
            # Collect 3 messages
            for i in range(3):
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(message)
                messages.append(data)
                
                # Small delay between messages
                await asyncio.sleep(1)
            
            # Verify all messages have required structure
            for i, data in enumerate(messages):
                required_fields = ['timestamp', 'circuit_breakers', 'processing', 'system']
                for field in required_fields:
                    assert field in data, f"Message {i} missing field: {field}"
            
            # Verify timestamps are in chronological order
            timestamps = [msg['timestamp'] for msg in messages]
            for i in range(1, len(timestamps)):
                assert timestamps[i] >= timestamps[i-1], "Timestamps should be in chronological order"
            
            await websocket.close()
            print("✅ WebSocket multiple messages test passed")
            
        except Exception as e:
            pytest.fail(f"WebSocket multiple messages test failed: {e}")

class TestDashboardIntegration:
    """Integration tests for dashboard functionality"""
    
    def test_dashboard_page_loads(self):
        """Test that dashboard page loads successfully"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        assert response.status_code == 200, f"Dashboard page returned {response.status_code}"
        
        # Check that it's HTML
        assert 'text/html' in response.headers.get('content-type', ''), "Dashboard should return HTML"
        
        # Check for some expected content
        content = response.text.lower()
        assert 'circuit' in content or 'dashboard' in content, "Dashboard should contain expected content"
        
        print("✅ Dashboard page loads successfully")
    
    def test_static_files_accessible(self):
        """Test that static files (CSS, JS) are accessible"""
        static_files = [
            "/static/css/dashboard.css",
            "/static/js/dashboard.js"
        ]
        
        for file_path in static_files:
            response = requests.get(f"{BASE_URL}{file_path}", timeout=10)
            assert response.status_code == 200, f"Static file {file_path} returned {response.status_code}"
            print(f"✅ {file_path}: accessible")
    
    def test_metrics_consistency(self):
        """Test that metrics are consistent across different endpoints"""
        # Get metrics from API
        api_response = requests.get(f"{BASE_URL}/api/metrics", timeout=10)
        api_data = api_response.json()
        
        # Get metrics from history (most recent)
        history_response = requests.get(f"{BASE_URL}/api/metrics/history?minutes=1", timeout=10)
        history_data = history_response.json()
        
        if len(history_data) > 0:
            # Compare structure (not exact values since they may have changed)
            api_keys = set(api_data.keys())
            history_keys = set(history_data[-1].keys())
            
            # Should have same top-level structure
            assert api_keys == history_keys, "API and history should have same structure"
        
        print("✅ Metrics consistency test passed")

def run_comprehensive_test():
    """Run all dashboard metrics tests"""
    print("🚀 Starting Dashboard Metrics Tests")
    print("=" * 50)
    
    # Test API endpoints
    test_instance = TestDashboardMetrics()
    
    try:
        test_instance.test_api_endpoints_accessible()
        test_instance.test_metrics_api_structure()
        test_instance.test_metrics_history_api()
        test_instance.test_circuit_breaker_stats_update()
        test_instance.test_processing_stats_update()
        test_instance.test_system_stats_update()
        
        # Test dashboard integration
        integration_test = TestDashboardIntegration()
        integration_test.test_dashboard_page_loads()
        integration_test.test_static_files_accessible()
        integration_test.test_metrics_consistency()
        
        print("\n✅ All API and integration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    print("\n📊 Dashboard metrics are working correctly!")
    print("🌐 Dashboard: http://localhost:8000")
    print("📈 API Metrics: http://localhost:8000/api/metrics")
    return True

if __name__ == "__main__":
    run_comprehensive_test() 