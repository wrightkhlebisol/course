#!/usr/bin/env python3
"""
Test script to demonstrate circuit breakers actually opening
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
        response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
        print_status(f"✅ {description}: {response.status_code}")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        print_status(f"❌ {description}: {e}")
        return None

def post_api_endpoint(endpoint, data, description):
    """Test a POST API endpoint and return the response"""
    try:
        response = requests.post(f"http://localhost:8000{endpoint}", json=data, timeout=10)
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

def trigger_circuit_breakers():
    """Trigger circuit breakers by processing logs with high failure rates"""
    print_status("🔥 Setting up high failure rates...")
    
    # Step 1: Start failure simulation (this sets high failure rates in the services)
    result = post_api_endpoint("/api/simulate/failures", {"duration": 120}, "Started failure simulation")
    if not result:
        print_status("❌ Failed to start failure simulation")
        return False
    
    print_status("📝 Processing logs to trigger circuit breakers...")
    
    # Step 2: Process logs in batches to trigger circuit breakers
    for batch in range(1, 6):  # Process 5 batches
        print_status(f"📝 Processing batch {batch}...")
        
        # Process multiple logs in each batch
        for i in range(3):  # 3 logs per batch
            result = post_api_endpoint("/api/process/logs", {"count": 1}, f"Log {i+1} in batch {batch}")
            if result:
                print_status(f"   ✅ Batch {batch}, Log {i+1}: {result.get('processed', 0)} logs processed")
            else:
                print_status(f"   ❌ Batch {batch}, Log {i+1}: Failed")
            
            time.sleep(0.5)  # Small delay between logs
        
        # Check circuit breaker status after each batch
        print_status(f"📊 Checking circuit breaker status after batch {batch}...")
        metrics = test_api_endpoint("/api/metrics", f"Metrics after batch {batch}")
        show_circuit_breaker_status(metrics, f"Status after batch {batch}")
        
        time.sleep(1)  # Wait between batches
    
    return True

def main():
    print("🔥 Circuit Breaker Opening Test")
    print("=" * 50)
    
    # Wait for services to be ready
    print_status("⏳ Waiting for services to start...")
    time.sleep(3)
    
    # Test initial state
    print_status("📊 Checking initial circuit breaker state...")
    initial_metrics = test_api_endpoint("/api/metrics", "Initial Metrics")
    show_circuit_breaker_status(initial_metrics, "Initial State")
    
    # Trigger circuit breakers
    print("\n" + "=" * 50)
    success = trigger_circuit_breakers()
    
    if success:
        # Wait a bit more for circuit breakers to potentially open
        print_status("⏳ Waiting for circuit breakers to potentially open...")
        time.sleep(3)
        
        # Check final state
        print("\n" + "=" * 50)
        print_status("📊 Checking final circuit breaker state...")
        final_metrics = test_api_endpoint("/api/metrics", "Final Metrics")
        show_circuit_breaker_status(final_metrics, "Final State")
        
        # Check if any circuit breakers opened
        if final_metrics:
            cb_stats = final_metrics.get('circuit_breakers', {})
            global_stats = cb_stats.get('global_stats', {})
            open_circuits = global_stats.get('open_circuits', 0)
            
            if open_circuits > 0:
                print_status(f"🎉 SUCCESS! {open_circuits} circuit breaker(s) opened!")
            else:
                print_status("⚠️  No circuit breakers opened. This might be due to:")
                print_status("   - Failure thresholds not reached")
                print_status("   - Services not failing enough")
                print_status("   - Circuit breaker configuration")
    
    print("\n" + "=" * 50)
    print_status("🎉 Test completed!")
    print_status("💡 Check the dashboard at: http://localhost:8000")
    print_status("📊 API metrics at: http://localhost:8000/api/metrics")

if __name__ == "__main__":
    main() 