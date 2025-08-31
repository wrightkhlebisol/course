#!/usr/bin/env python3
"""
Force a circuit breaker to open by directly testing the log processor
"""
import sys
import os
sys.path.insert(0, '.')

from src.services.log_processor import LogProcessorService
from src.circuit_breaker.core import registry
import time

def print_status(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def main():
    print("🔥 Force Circuit Breaker to Open")
    print("=" * 50)
    
    # Create log processor
    processor = LogProcessorService()
    
    # Check initial state
    print_status("📊 Initial circuit breaker states:")
    stats = registry.get_all_stats()
    for name, cb_stats in stats['circuit_breakers'].items():
        if name != 'global_stats':
            state = cb_stats['state']
            failed_calls = cb_stats['failed_calls']
            print(f"   {name}: {state} ({failed_calls} failures)")
    
    # Force the API circuit breaker to fail by setting it to always fail
    print_status("🔥 Setting API to always fail...")
    processor.external_api.set_down(True)  # This makes the API always fail
    
    # Process logs to trigger failures
    print_status("📝 Processing logs to trigger API failures...")
    for i in range(5):
        log_data = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'level': 'ERROR',
            'message': f'Test log {i+1}',
            'service': 'test-service'
        }
        
        try:
            result = processor.process_log(log_data)
            print_status(f"   Processed log {i+1}: {result['processing_status']}")
        except Exception as e:
            print_status(f"   Log {i+1} failed: {e}")
        
        # Check circuit breaker state after each log
        stats = registry.get_all_stats()
        api_stats = stats['circuit_breakers'].get('api_enrichment', {})
        state = api_stats.get('state', 'UNKNOWN')
        failed_calls = api_stats.get('failed_calls', 0)
        print_status(f"   🔥 API circuit breaker: {state} ({failed_calls} failures)")
        
        if state == 'OPEN':
            print_status("🎉 SUCCESS! API circuit breaker opened!")
            break
        
        time.sleep(0.5)
    
    # Show final state
    print_status("📊 Final circuit breaker states:")
    stats = registry.get_all_stats()
    for name, cb_stats in stats['circuit_breakers'].items():
        if name != 'global_stats':
            state = cb_stats['state']
            failed_calls = cb_stats['failed_calls']
            total_calls = cb_stats['total_calls']
            print(f"   {name}: {state} ({failed_calls}/{total_calls} failed)")
    
    print("\n" + "=" * 50)
    print_status("🎉 Test completed!")

if __name__ == "__main__":
    main() 