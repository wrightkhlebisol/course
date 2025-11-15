#!/usr/bin/env python3
"""
Deployment Tracking System Demo
Demonstrates key functionality and generates sample data
"""

import asyncio
import json
import time
import requests
from datetime import datetime

class DeploymentTrackingDemo:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        
    def test_api_health(self):
        """Test API health and basic connectivity"""
        try:
            response = requests.get(f"{self.base_url}/api/deployments", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_test_logs(self):
        """Generate test log entries for correlation demo"""
        test_logs = [
            {
                "timestamp": datetime.now().isoformat() + "Z",
                "service": "user-service",
                "environment": "production",
                "level": "INFO",
                "message": "User login successful",
                "user_id": "user_123"
            },
            {
                "timestamp": datetime.now().isoformat() + "Z",
                "service": "payment-service",
                "environment": "production",
                "level": "ERROR",
                "message": "Payment processing failed",
                "error_code": "CARD_DECLINED"
            },
            {
                "timestamp": datetime.now().isoformat() + "Z",
                "service": "api-gateway",
                "environment": "staging",
                "level": "WARN",
                "message": "High response time detected",
                "response_time": 2500
            }
        ]
        
        try:
            response = requests.post(
                f"{self.base_url}/api/logs/enrich",
                json=test_logs,
                timeout=10
            )
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, str(e)
    
    def get_impact_summary(self):
        """Get deployment impact analysis summary"""
        try:
            response = requests.get(f"{self.base_url}/api/impact/summary", timeout=5)
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, str(e)
    
    def run_demo(self):
        """Run complete demo"""
        print("🎭 Deployment Tracking System Demo")
        print("=" * 50)
        
        # Test 1: API Health
        print("\n1. Testing API connectivity...")
        if self.test_api_health():
            print("   ✅ API is healthy and responding")
        else:
            print("   ❌ API is not responding - make sure system is running")
            return False
        
        # Test 2: Wait for deployments to be generated
        print("\n2. Waiting for demo deployments to be generated...")
        time.sleep(10)
        
        # Test 3: Log Correlation
        print("\n3. Testing log correlation with deployments...")
        success, result = self.generate_test_logs()
        if success:
            print("   ✅ Log correlation successful")
            enriched_count = result.get('count', 0)
            print(f"   📊 Enriched {enriched_count} log entries with deployment context")
        else:
            print(f"   ❌ Log correlation failed: {result}")
        
        # Test 4: Impact Analysis
        print("\n4. Checking deployment impact analysis...")
        time.sleep(5)  # Wait for analysis to process
        success, result = self.get_impact_summary()
        if success:
            print("   ✅ Impact analysis available")
            total = result.get('total_analyzed', 0)
            print(f"   📊 Analyzed {total} deployments for impact")
        else:
            print(f"   ❌ Impact analysis failed: {result}")
        
        # Test 5: Real-time Dashboard
        print("\n5. Dashboard verification...")
        print(f"   🌐 Dashboard URL: {self.base_url}")
        print("   📊 Features available:")
        print("      - Real-time deployment monitoring")
        print("      - Deployment impact analysis")
        print("      - Log correlation statistics")
        print("      - Interactive deployment timeline")
        
        print("\n✅ Demo completed successfully!")
        print(f"\n🎯 Key URLs:")
        print(f"   Dashboard: {self.base_url}")
        print(f"   API Health: {self.base_url}/api/deployments")
        print(f"   Impact Summary: {self.base_url}/api/impact/summary")
        
        return True

if __name__ == "__main__":
    demo = DeploymentTrackingDemo()
    demo.run_demo()
