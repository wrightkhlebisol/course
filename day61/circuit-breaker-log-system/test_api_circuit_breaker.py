#!/usr/bin/env python3
"""
Test to specifically trigger the API circuit breaker to open
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

def trigger_api_circuit_breaker():
    """Trigger the API circuit breaker to open"""
    print_status("🔥 Setting up API to always fail...")
    
    # Step 1: Start failure simulation (this sets high failure rates)
    try:
        response = requests.post("http://localhost:8000/api/simulate/failures", 
                               json={"duration": 60}, timeout=5)
        print_status(f"✅ Started failure simulation: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Failed to start simulation: {e}")
        return False
    
    print_status("📝 Processing logs to trigger API circuit breaker...")
    
    # Step 2: Process logs multiple times to trigger API failures
    # The API circuit breaker needs only 2 consecutive failures to open
    for i in range(5):  # Process 5 logs to ensure we get enough failures
        try:
            response = requests.post("http://localhost:8000/api/process/logs", 
                                   json={"count": 1}, timeout=5)
            print_status(f"📝 Processed log {i+1}: {response.status_code}")
            
            # Check circuit breaker status after each log
            metrics = test_api_endpoint("/api/metrics", f"Metrics after log {i+1}")
            if metrics:
                individual_cbs = metrics.get('circuit_breakers', {}).get('circuit_breakers', {})
                api_stats = individual_cbs.get('api_enrichment', {})
                state = api_stats.get('state', 'UNKNOWN')
                failed_calls = api_stats.get('failed_calls', 0)
                print_status(f"   🔥 API circuit breaker: {state} ({failed_calls} failures)")
                
                # Check if it opened
                if state == 'OPEN':
                    print_status("🎉 SUCCESS! API circuit breaker opened!")
                    return True
            
        except requests.exceptions.RequestException as e:
            print_status(f"❌ Failed to process log {i+1}: {e}")
        
        time.sleep(1)  # Wait between logs
    
    return False

def main():
    print("🔥 API Circuit Breaker Opening Test")
    print("=" * 50)
    
    # Check initial state
    print_status("📊 Checking initial circuit breaker state...")
    initial_metrics = test_api_endpoint("/api/metrics", "Initial Metrics")
    show_circuit_breaker_status(initial_metrics, "Initial State")
    
    # Trigger API circuit breaker
    print("\n" + "=" * 50)
    success = trigger_api_circuit_breaker()
    
    # Check final state
    print("\n" + "=" * 50)
    print_status("📊 Checking final circuit breaker state...")
    final_metrics = test_api_endpoint("/api/metrics", "Final Metrics")
    show_circuit_breaker_status(final_metrics, "Final State")
    
    if success:
        print_status("🎉 SUCCESS! API circuit breaker opened!")
    else:
        print_status("⚠️  API circuit breaker did not open. This might be due to:")
        print_status("   - Not enough consecutive failures")
        print_status("   - Random failures not hitting the threshold")
        print_status("   - Circuit breaker configuration")
    
    print("\n" + "=" * 50)
    print_status("🎉 Test completed!")
    print_status("💡 Check the dashboard at: http://localhost:8000")

if __name__ == "__main__":
    main() 