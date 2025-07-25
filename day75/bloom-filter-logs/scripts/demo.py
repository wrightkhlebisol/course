#!/usr/bin/env python3

import requests
import time
import random
import string
from typing import List
import asyncio
import aiohttp

API_BASE = "http://localhost:8001"

class BloomFilterDemo:
    def __init__(self):
        self.session = requests.Session()
    
    def check_api_health(self) -> bool:
        """Check if API is available"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def populate_demo_data(self, count: int = 1000) -> dict:
        """Populate with demo data"""
        print(f"📊 Populating {count} demo log entries...")
        try:
            response = self.session.post(f"{API_BASE}/demo/populate", 
                                       params={"count": count}, timeout=30)
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            print(f"❌ Error populating data: {e}")
            return {}
    
    def run_performance_test(self) -> dict:
        """Run performance comparison test"""
        print("🚀 Running performance comparison test...")
        try:
            response = self.session.post(f"{API_BASE}/demo/performance-test", timeout=60)
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            print(f"❌ Error running performance test: {e}")
            return {}
    
    def interactive_demo(self):
        """Run interactive demo showing bloom filter capabilities"""
        print("\n🔍 Interactive Bloom Filter Demo")
        print("=" * 40)
        
        # Add some known entries
        known_entries = [
            ("error_logs", "sql_timeout_001"),
            ("access_logs", "192.168.1.100_session_abc123"),
            ("security_logs", "admin_login_attempt_001"),
            ("error_logs", "network_connection_failed"),
            ("access_logs", "192.168.1.101_session_def456")
        ]
        
        print("\n📝 Adding known log entries:")
        for log_type, log_key in known_entries:
            try:
                response = self.session.post(f"{API_BASE}/logs/add",
                                           json={"log_type": log_type, "log_key": log_key})
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Added {log_type}: {log_key} ({data['processing_time_ms']:.3f}ms)")
                else:
                    print(f"❌ Failed to add {log_type}: {log_key}")
            except Exception as e:
                print(f"❌ Error adding entry: {e}")
        
        print("\n🔍 Querying log entries:")
        
        # Query known entries (should return True)
        print("\n Known entries (should exist):")
        for log_type, log_key in known_entries[:3]:
            try:
                response = self.session.post(f"{API_BASE}/logs/query",
                                           json={"log_type": log_type, "log_key": log_key})
                if response.status_code == 200:
                    data = response.json()
                    result = "✅ FOUND" if data["might_exist"] else "❌ NOT FOUND"
                    print(f"{result}: {log_key} ({data['processing_time_ms']:.3f}ms)")
                else:
                    print(f"❌ Query failed for {log_key}")
            except Exception as e:
                print(f"❌ Error querying: {e}")
        
        # Query unknown entries (should return False)
        unknown_entries = [
            ("error_logs", "definitely_unknown_error_999"),
            ("access_logs", "192.168.1.999_unknown_session"),
            ("security_logs", "fake_security_event_001")
        ]
        
        print("\n Unknown entries (should not exist):")
        for log_type, log_key in unknown_entries:
            try:
                response = self.session.post(f"{API_BASE}/logs/query",
                                           json={"log_type": log_type, "log_key": log_key})
                if response.status_code == 200:
                    data = response.json()
                    result = "⚠️ MAYBE" if data["might_exist"] else "✅ NOT FOUND"
                    print(f"{result}: {log_key} ({data['processing_time_ms']:.3f}ms)")
                else:
                    print(f"❌ Query failed for {log_key}")
            except Exception as e:
                print(f"❌ Error querying: {e}")
    
    def show_statistics(self):
        """Display current filter statistics"""
        print("\n📊 Current Filter Statistics:")
        print("=" * 40)
        
        try:
            response = self.session.get(f"{API_BASE}/stats")
            if response.status_code == 200:
                stats = response.json()
                for filter_name, filter_stats in stats.items():
                    print(f"\n🔹 {filter_name.replace('_', ' ').title()}:")
                    print(f"   Elements added: {filter_stats['elements_added']:,}")
                    print(f"   Queries made: {filter_stats['queries_made']:,}")
                    print(f"   Memory usage: {filter_stats['memory_usage_bytes']/1024:.1f} KB")
                    print(f"   False positive rate: {filter_stats['current_false_positive_rate']:.4%}")
                    print(f"   Filter size: {filter_stats['size']:,} bits")
            else:
                print("❌ Failed to get statistics")
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")

def main():
    """Main demonstration function"""
    print("🔍 Bloom Filter Log Processing Demonstration")
    print("=" * 50)
    
    demo = BloomFilterDemo()
    
    # Check API health
    print("🏥 Checking API health...")
    if not demo.check_api_health():
        print("❌ API is not available. Please start the services first:")
        print("   bash start.sh")
        return
    
    print("✅ API is healthy!")
    
    # Populate demo data
    result = demo.populate_demo_data(5000)
    if result:
        print(f"✅ Populated {result.get('records_added', 0)} demo records")
    
    # Run interactive demo
    demo.interactive_demo()
    
    # Show statistics
    demo.show_statistics()
    
    # Run performance test
    perf_result = demo.run_performance_test()
    if perf_result:
        print("\n🚀 Performance Test Results:")
        print("=" * 40)
        bloom_perf = perf_result.get('bloom_filter_performance', {})
        traditional_perf = perf_result.get('traditional_lookup_performance', {})
        speed_improvement = perf_result.get('speed_improvement', {})
        accuracy = perf_result.get('accuracy_metrics', {})
        
        print(f"Bloom Filter Query Time: {bloom_perf.get('avg_time_per_query_ms', 0):.3f} ms")
        print(f"Traditional Query Time: {traditional_perf.get('avg_time_per_query_ms', 0):.1f} ms")
        print(f"Speed Improvement: {speed_improvement.get('times_faster', 0):.0f}x faster")
        print(f"False Positive Rate: {accuracy.get('false_positive_rate', 0):.2%}")
        print(f"Zero False Negatives: {accuracy.get('no_false_negatives', False)}")
    
    print("\n🎉 Demo completed!")
    print("\n📊 Open http://localhost:8002 to view the dashboard")
    print("🌐 Visit http://localhost:8001/docs for API documentation")

if __name__ == "__main__":
    main()
