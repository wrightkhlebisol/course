#!/usr/bin/env python3
"""
Test script to demonstrate circuit breaker activation
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

def trigger_circuit_breakers():
    """Trigger circuit breakers by processing logs with failures"""
    print_status("🔥 Triggering circuit breakers with high failure rates...")
    
    # Step 1: Start failure simulation (sets high failure rates)
    try:
        response = requests.post("http://localhost:8000/api/simulate/failures", 
                               json={"duration": 60}, timeout=5)
        print_status(f"✅ Started failure simulation: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Failed to start simulation: {e}")
        return
    
    # Step 2: Process multiple logs to trigger circuit breakers
    print_status("📝 Processing logs to trigger circuit breakers...")
    for i in range(15):  # Process more logs to ensure failures
        try:
            response = requests.post("http://localhost:8000/api/process/logs", 
                                   json={"count": 1}, timeout=5)
            print_status(f"📝 Processed log batch {i+1}: {response.status_code}")
            
            # Check metrics after each batch
            if i % 3 == 0:  # Check every 3rd batch
                metrics = test_api_endpoint("/api/metrics", f"Metrics after batch {i+1}")
                if metrics:
                    cb_stats = metrics.get('circuit_breakers', {})
                    global_stats = cb_stats.get('global_stats', {})
                    open_circuits = global_stats.get('open_circuits', 0)
                    print_status(f"   📊 Open circuits: {open_circuits}")
                    
                    # Show individual circuit breakers
                    individual_cbs = cb_stats.get('circuit_breakers', {})
                    for name, stats in individual_cbs.items():
                        state = stats.get('state', 'UNKNOWN')
                        failed_calls = stats.get('failed_calls', 0)
                        if failed_calls > 0:
                            print_status(f"   🔥 {name}: {state} ({failed_calls} failures)")
            
        except requests.exceptions.RequestException as e:
            print_status(f"❌ Failed to process log batch {i+1}: {e}")
        
        time.sleep(0.5)  # Small delay between batches

def main():
    print("🔥 Circuit Breaker Activation Test")
    print("=" * 50)
    
    # Wait for services to be ready
    print_status("⏳ Waiting for services to start...")
    time.sleep(3)
    
    # Test initial state
    print_status("📊 Initial Circuit Breaker State:")
    initial_metrics = test_api_endpoint("/api/metrics", "Initial Metrics")
    
    if initial_metrics:
        cb_stats = initial_metrics.get('circuit_breakers', {})
        global_stats = cb_stats.get('global_stats', {})
        print(f"   Total Circuits: {global_stats.get('total_circuits', 0)}")
        print(f"   Closed Circuits: {global_stats.get('closed_circuits', 0)}")
        print(f"   Open Circuits: {global_stats.get('open_circuits', 0)}")
        print(f"   Half-Open Circuits: {global_stats.get('half_open_circuits', 0)}")
        
        # Show individual circuit breakers
        print("\n   Individual Circuit Breakers:")
        individual_cbs = cb_stats.get('circuit_breakers', {})
        for name, stats in individual_cbs.items():
            state = stats.get('state', 'UNKNOWN')
            success_rate = stats.get('success_rate', 0)
            print(f"     {name}: {state} - {success_rate}% success")
    
    # Trigger circuit breakers
    print("\n" + "=" * 50)
    trigger_circuit_breakers()
    
    # Wait for circuit breakers to potentially open
    print_status("⏳ Waiting for circuit breakers to potentially open...")
    time.sleep(5)
    
    # Check final state
    print("\n" + "=" * 50)
    print_status("📊 Final Circuit Breaker State:")
    final_metrics = test_api_endpoint("/api/metrics", "Final Metrics")
    
    if final_metrics:
        cb_stats = final_metrics.get('circuit_breakers', {})
        global_stats = cb_stats.get('global_stats', {})
        print(f"   Total Circuits: {global_stats.get('total_circuits', 0)}")
        print(f"   Closed Circuits: {global_stats.get('closed_circuits', 0)}")
        print(f"   Open Circuits: {global_stats.get('open_circuits', 0)}")
        print(f"   Half-Open Circuits: {global_stats.get('half_open_circuits', 0)}")
        
        # Show individual circuit breakers
        print("\n   Individual Circuit Breakers:")
        individual_cbs = cb_stats.get('circuit_breakers', {})
        for name, stats in individual_cbs.items():
            state = stats.get('state', 'UNKNOWN')
            success_rate = stats.get('success_rate', 0)
            failed_calls = stats.get('failed_calls', 0)
            total_calls = stats.get('total_calls', 0)
            print(f"     {name}: {state} - {success_rate}% success ({failed_calls}/{total_calls} failed)")
    
    print("\n" + "=" * 50)
    print_status("🎉 Test completed!")
    print_status("💡 Circuit breakers should open after multiple failures")
    print_status("🌐 Dashboard: http://localhost:8000")

if __name__ == "__main__":
    main() 