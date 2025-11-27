#!/usr/bin/env python3

import asyncio
import requests
import time
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def check_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE}/health")
        return response.status_code == 200
    except:
        return False

def send_test_alerts():
    """Send a series of test alerts"""
    severities = ["info", "warning", "error", "critical"]
    
    print("🚀 Sending test alerts...")
    
    for i, severity in enumerate(severities):
        print(f"📧 Sending {severity} alert...")
        
        try:
            response = requests.post(f"{API_BASE}/api/alerts/test?severity={severity}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Sent: {data['alert']['title']}")
                print(f"   📍 Status: {data['status']['status']}")
                print(f"   📢 Channel: {data['status']['channel']}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(2)  # Rate limiting

def get_stats():
    """Get current system statistics"""
    try:
        response = requests.get(f"{API_BASE}/api/stats")
        if response.status_code == 200:
            stats = response.json()
            print("\n📊 Current Statistics:")
            print(f"   Rate: {stats['current_rate_per_minute']}/{stats['max_rate_per_minute']} per minute")
            print(f"   Recent notifications: {stats['recent_notifications']}")
            print(f"   Queued alerts: {stats['queued_alerts']}")
            print(f"   Dedup window: {stats['deduplication_window_minutes']} minutes")
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

def main():
    print("🎭 Slack Integration Demo")
    print("========================")
    
    # Check if API is running
    if not check_health():
        print("❌ API is not running. Please start the system first:")
        print("   ./start.sh")
        return
    
    print("✅ API is running")
    
    # Get initial stats
    get_stats()
    
    # Send test alerts
    send_test_alerts()
    
    # Get final stats
    print("\n" + "="*50)
    get_stats()
    
    print("\n🎉 Demo completed!")
    print("\n📊 Check the dashboard at: http://localhost:3000")
    print("📋 View API docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
