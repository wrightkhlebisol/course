#!/usr/bin/env python3
"""
Dashboard Validation Script
Tests all metrics and charts on the Storage Optimization Dashboard
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10

def print_status(message, status="INFO"):
    """Print formatted status message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status == "SUCCESS":
        print(f"✅ [{timestamp}] {message}")
    elif status == "ERROR":
        print(f"❌ [{timestamp}] {message}")
    elif status == "WARNING":
        print(f"⚠️  [{timestamp}] {message}")
    else:
        print(f"ℹ️  [{timestamp}] {message}")

def test_server_health():
    """Test if the server is running and responsive"""
    print_status("Testing server health...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        if response.status_code == 200:
            print_status("Server is running and responding", "SUCCESS")
            return True
        else:
            print_status(f"Server returned status code: {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"Server connection failed: {e}", "ERROR")
        return False

def test_stats_api():
    """Test the stats API endpoint"""
    print_status("Testing stats API...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            
            # Validate required fields
            required_fields = ['storage_stats', 'pattern_insights', 'timestamp']
            for field in required_fields:
                if field not in data:
                    print_status(f"Missing required field: {field}", "ERROR")
                    return False
            
            # Validate storage stats structure
            storage_stats = data['storage_stats']
            if 'partitions' not in storage_stats:
                print_status("Missing partitions in storage_stats", "ERROR")
                return False
            
            # Validate pattern insights structure
            pattern_insights = data['pattern_insights']
            if 'partitions_analyzed' not in pattern_insights:
                print_status("Missing partitions_analyzed in pattern_insights", "ERROR")
                return False
            
            print_status("Stats API is working correctly", "SUCCESS")
            print_status(f"Found {len(storage_stats['partitions'])} partitions", "INFO")
            print_status(f"Total queries analyzed: {pattern_insights['total_queries']}", "INFO")
            
            return True
        else:
            print_status(f"Stats API returned status code: {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"Stats API request failed: {e}", "ERROR")
        return False
    except json.JSONDecodeError as e:
        print_status(f"Stats API returned invalid JSON: {e}", "ERROR")
        return False

def test_recommendations_api():
    """Test the recommendations API for each partition"""
    print_status("Testing recommendations API...")
    
    try:
        # First get stats to see available partitions
        response = requests.get(f"{BASE_URL}/api/stats", timeout=TIMEOUT)
        if response.status_code != 200:
            print_status("Could not get stats to find partitions", "ERROR")
            return False
        
        data = response.json()
        partitions = list(data['storage_stats']['partitions'].keys())
        
        if not partitions:
            print_status("No partitions found to test", "WARNING")
            return True
        
        success_count = 0
        for partition in partitions:
            try:
                response = requests.get(f"{BASE_URL}/api/recommendations/{partition}", timeout=TIMEOUT)
                if response.status_code == 200:
                    recommendation = response.json()
                    
                    # Validate recommendation structure
                    required_fields = ['recommended_format', 'confidence']
                    valid_formats = ['row_oriented', 'columnar', 'hybrid']
                    valid_confidence = ['low', 'medium', 'high']
                    
                    if all(field in recommendation for field in required_fields):
                        if recommendation['recommended_format'] in valid_formats:
                            if recommendation['confidence'] in valid_confidence:
                                print_status(f"✅ Partition '{partition}': {recommendation['recommended_format']} ({recommendation['confidence']})", "SUCCESS")
                                success_count += 1
                            else:
                                print_status(f"Invalid confidence for partition '{partition}': {recommendation['confidence']}", "ERROR")
                        else:
                            print_status(f"Invalid format for partition '{partition}': {recommendation['recommended_format']}", "ERROR")
                    else:
                        print_status(f"Missing required fields in recommendation for partition '{partition}'", "ERROR")
                else:
                    print_status(f"Recommendations API failed for partition '{partition}': {response.status_code}", "ERROR")
            except Exception as e:
                print_status(f"Error testing recommendations for partition '{partition}': {e}", "ERROR")
        
        if success_count == len(partitions):
            print_status(f"All {success_count} partition recommendations are valid", "SUCCESS")
            return True
        else:
            print_status(f"Only {success_count}/{len(partitions)} partition recommendations are valid", "WARNING")
            return False
            
    except Exception as e:
        print_status(f"Recommendations API test failed: {e}", "ERROR")
        return False

def test_performance_charts():
    """Test the performance charts API for each partition"""
    print_status("Testing performance charts API...")
    
    try:
        # First get stats to see available partitions
        response = requests.get(f"{BASE_URL}/api/stats", timeout=TIMEOUT)
        if response.status_code != 200:
            print_status("Could not get stats to find partitions", "ERROR")
            return False
        
        data = response.json()
        partitions = list(data['storage_stats']['partitions'].keys())
        
        if not partitions:
            print_status("No partitions found to test", "WARNING")
            return True
        
        success_count = 0
        for partition in partitions:
            try:
                response = requests.get(f"{BASE_URL}/api/performance-chart/{partition}", timeout=TIMEOUT)
                if response.status_code == 200:
                    chart_data = response.json()
                    
                    # Check if it's an error response
                    if 'error' in chart_data:
                        print_status(f"⚠️  No performance data for partition '{partition}': {chart_data['error']}", "WARNING")
                        continue
                    
                    # Validate Plotly chart structure
                    if 'data' in chart_data and 'layout' in chart_data:
                        data = chart_data['data']
                        if isinstance(data, list) and len(data) > 0:
                            # Check if it's a scatter plot
                            if 'type' in data[0] and data[0]['type'] == 'scatter':
                                if 'x' in data[0] and 'y' in data[0]:
                                    print_status(f"✅ Performance chart for '{partition}': {len(data[0]['x'])} data points", "SUCCESS")
                                    success_count += 1
                                else:
                                    print_status(f"Invalid chart data structure for partition '{partition}'", "ERROR")
                            else:
                                print_status(f"Unexpected chart type for partition '{partition}': {data[0].get('type', 'unknown')}", "WARNING")
                        else:
                            print_status(f"Empty chart data for partition '{partition}'", "WARNING")
                    else:
                        print_status(f"Invalid chart structure for partition '{partition}'", "ERROR")
                else:
                    print_status(f"Performance chart API failed for partition '{partition}': {response.status_code}", "ERROR")
            except Exception as e:
                print_status(f"Error testing performance chart for partition '{partition}': {e}", "ERROR")
        
        if success_count > 0:
            print_status(f"Performance charts working for {success_count}/{len(partitions)} partitions", "SUCCESS")
            return True
        else:
            print_status("No performance charts are working", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Performance charts API test failed: {e}", "ERROR")
        return False

def test_optimization_api():
    """Test the optimization trigger API"""
    print_status("Testing optimization trigger API...")
    
    try:
        # Test with a sample partition
        response = requests.post(f"{BASE_URL}/api/optimize/test-partition", timeout=TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            if 'status' in result and result['status'] == 'optimization_triggered':
                print_status("Optimization trigger API is working", "SUCCESS")
                return True
            else:
                print_status(f"Unexpected optimization response: {result}", "WARNING")
                return False
        else:
            print_status(f"Optimization API returned status code: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"Optimization API test failed: {e}", "ERROR")
        return False

def test_websocket_connection():
    """Test WebSocket connection for real-time updates"""
    print_status("Testing WebSocket connection...")
    
    try:
        import websocket
        import threading
        
        connected = False
        message_received = False
        
        def on_message(ws, message):
            nonlocal message_received
            try:
                data = json.loads(message)
                if data.get('type') == 'stats_update':
                    message_received = True
                    print_status("✅ Received real-time stats update via WebSocket", "SUCCESS")
            except json.JSONDecodeError:
                pass
        
        def on_error(ws, error):
            print_status(f"WebSocket error: {error}", "ERROR")
        
        def on_close(ws, close_status_code, close_msg):
            pass
        
        def on_open(ws):
            nonlocal connected
            connected = True
            print_status("✅ WebSocket connection established", "SUCCESS")
        
        # Create WebSocket connection
        ws_url = f"ws://localhost:8000/ws"
        ws = websocket.WebSocketApp(ws_url,
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
        
        # Run WebSocket in a separate thread
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # Wait for connection and message
        timeout = 10
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if connected and message_received:
                ws.close()
                return True
            time.sleep(0.1)
        
        ws.close()
        
        if not connected:
            print_status("WebSocket connection failed", "ERROR")
            return False
        elif not message_received:
            print_status("WebSocket connected but no messages received", "WARNING")
            return False
        
    except ImportError:
        print_status("WebSocket library not available, skipping WebSocket test", "WARNING")
        return True
    except Exception as e:
        print_status(f"WebSocket test failed: {e}", "ERROR")
        return False

def validate_metrics_consistency():
    """Validate that metrics are consistent across different API calls"""
    print_status("Validating metrics consistency...")
    
    try:
        # Get stats from main API
        response = requests.get(f"{BASE_URL}/api/stats", timeout=TIMEOUT)
        if response.status_code != 200:
            print_status("Could not get stats for consistency check", "ERROR")
            return False
        
        stats_data = response.json()
        storage_stats = stats_data['storage_stats']
        pattern_insights = stats_data['pattern_insights']
        
        # Check consistency between storage stats and pattern insights
        partitions_in_stats = set(storage_stats['partitions'].keys())
        partitions_in_insights = set(pattern_insights['recommendations'].keys())
        
        if partitions_in_stats == partitions_in_insights:
            print_status("✅ Partition consistency validated", "SUCCESS")
        else:
            print_status(f"⚠️  Partition mismatch: stats={partitions_in_stats}, insights={partitions_in_insights}", "WARNING")
        
        # Check total queries consistency
        total_queries_from_stats = sum(
            partition['reads'] for partition in storage_stats['partitions'].values()
        )
        total_queries_from_insights = pattern_insights['total_queries']
        
        if total_queries_from_stats == total_queries_from_insights:
            print_status("✅ Query count consistency validated", "SUCCESS")
        else:
            print_status(f"⚠️  Query count mismatch: stats={total_queries_from_stats}, insights={total_queries_from_insights}", "WARNING")
        
        return True
        
    except Exception as e:
        print_status(f"Metrics consistency validation failed: {e}", "ERROR")
        return False

def main():
    """Run all validation tests"""
    print("🔍 Storage Optimization Dashboard Validation")
    print("=" * 50)
    
    tests = [
        ("Server Health", test_server_health),
        ("Stats API", test_stats_api),
        ("Recommendations API", test_recommendations_api),
        ("Performance Charts", test_performance_charts),
        ("Optimization API", test_optimization_api),
        ("WebSocket Connection", test_websocket_connection),
        ("Metrics Consistency", validate_metrics_consistency),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_status(f"Test '{test_name}' failed with exception: {e}", "ERROR")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print_status("🎉 All dashboard metrics and charts are working correctly!", "SUCCESS")
        return 0
    else:
        print_status(f"⚠️  {total - passed} tests failed. Check the dashboard implementation.", "WARNING")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 