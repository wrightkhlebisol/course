#!/usr/bin/env python3
"""
Demo script for Circuit Breaker Log System
Shows the circuit breaker functionality in action
"""

import time
import requests
import json
from datetime import datetime

def print_status(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def test_api_endpoint(endpoint, description):
    """Test an API endpoint and return the response"""
    try:
        response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
        print_status(f"✅ {description}: {response.status_code}")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        print_status(f"❌ {description}: {e}")
        return None

def simulate_circuit_breaker_activity():
    """Simulate some circuit breaker activity"""
    print_status("🔄 Simulating circuit breaker activity...")
    
    # Simulate some API calls that might fail
    for i in range(5):
        try:
            # This endpoint might not exist, simulating failures
            response = requests.post(f"http://localhost:8000/api/test/{i}", 
                                  json={"test": "data"}, timeout=2)
            print_status(f"API call {i+1}: {response.status_code}")
        except requests.exceptions.RequestException:
            print_status(f"API call {i+1}: Failed (expected)")
        
        time.sleep(1)

def main():
    print("🚀 Circuit Breaker Log System Demo")
    print("=" * 50)
    
    # Wait for services to be ready
    print_status("⏳ Waiting for services to start...")
    time.sleep(3)
    
    # Test basic endpoints
    print_status("📊 Testing API endpoints...")
    
    # Test metrics endpoint
    metrics = test_api_endpoint("/api/metrics", "Metrics API")
    
    # Test dashboard
    test_api_endpoint("/", "Dashboard")
    
    # Test health check
    test_api_endpoint("/health", "Health Check")
    
    # Show initial state
    if metrics:
        print_status("📈 Initial Circuit Breaker State:")
        cb_stats = metrics.get('circuit_breakers', {})
        global_stats = cb_stats.get('global_stats', {})
        print(f"   Total Circuits: {global_stats.get('total_circuits', 0)}")
        print(f"   Closed Circuits: {global_stats.get('closed_circuits', 0)}")
        print(f"   Open Circuits: {global_stats.get('open_circuits', 0)}")
        print(f"   Half-Open Circuits: {global_stats.get('half_open_circuits', 0)}")
    
    # Simulate some activity
    print("\n" + "=" * 50)
    simulate_circuit_breaker_activity()
    
    # Show final state
    print("\n" + "=" * 50)
    print_status("📊 Final Circuit Breaker State:")
    final_metrics = test_api_endpoint("/api/metrics", "Final Metrics")
    
    if final_metrics:
        cb_stats = final_metrics.get('circuit_breakers', {})
        global_stats = cb_stats.get('global_stats', {})
        print(f"   Total Calls: {global_stats.get('total_calls', 0)}")
        print(f"   Total Failures: {global_stats.get('total_failures', 0)}")
    
    print("\n" + "=" * 50)
    print_status("🎉 Demo completed!")
    print_status("🌐 Dashboard available at: http://localhost:8000")
    print_status("📊 API metrics at: http://localhost:8000/api/metrics")
    print_status("🛑 Stop with: ./stop.sh")

if __name__ == "__main__":
    main() 