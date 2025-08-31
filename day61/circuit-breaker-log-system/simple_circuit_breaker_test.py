#!/usr/bin/env python3
"""
Simple test to check circuit breaker state and trigger some processing
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

def show_circuit_breaker_status(metrics, title):
    """Display circuit breaker status"""
    if not metrics:
        return
    
    cb_stats = metrics.get('circuit_breakers', {})
    global_stats = cb_stats.get('global_stats', {})
    
    print(f"\n{title}:")
    print(f"   Total Circuits: {global_stats.get('total_circuits', 0)}")
    print(f"   Closed Circuits: {global_stats.get('closed_circuits', 0)}")
    print(f"   Open Circuits: {global_stats.get('open_circuits', 0)}")
    print(f"   Half-Open Circuits: {global_stats.get('half_open_circuits', 0)}")
    
    # Show individual circuit breakers
    individual_cbs = cb_stats.get('circuit_breakers', {})
    print("\n   Individual Circuit Breakers:")
    for name, stats in individual_cbs.items():
        state = stats.get('state', 'UNKNOWN')
        success_rate = stats.get('success_rate', 0)
        failed_calls = stats.get('failed_calls', 0)
        total_calls = stats.get('total_calls', 0)
        print(f"     {name}: {state} - {success_rate}% success ({failed_calls}/{total_calls} failed)")

def main():
    print("🔍 Simple Circuit Breaker State Check")
    print("=" * 50)
    
    # Check initial state
    print_status("📊 Checking current circuit breaker state...")
    initial_metrics = test_api_endpoint("/api/metrics", "Current Metrics")
    show_circuit_breaker_status(initial_metrics, "Current State")
    
    # Try to trigger some processing
    print_status("📝 Attempting to process some logs...")
    try:
        response = requests.post("http://localhost:8000/api/process/logs", 
                               json={"count": 1}, timeout=5)
        print_status(f"✅ Process logs: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print_status(f"   Processed: {result.get('processed', 0)} logs")
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Process logs failed: {e}")
    
    # Check state after processing
    print_status("📊 Checking state after processing...")
    time.sleep(2)
    final_metrics = test_api_endpoint("/api/metrics", "Final Metrics")
    show_circuit_breaker_status(final_metrics, "State After Processing")
    
    print("\n" + "=" * 50)
    print_status("🎉 Test completed!")
    print_status("💡 Check the dashboard at: http://localhost:8000")

if __name__ == "__main__":
    main() 