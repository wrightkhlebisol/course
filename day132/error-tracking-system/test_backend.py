#!/usr/bin/env python3
"""Quick test script to check if backend is working"""

import requests
import sys

def test_backend():
    base_url = "http://localhost:8000"
    
    print("Testing backend endpoints...")
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=2)
        print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        print(f"✅ Health endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False
    
    # Test database health
    try:
        response = requests.get(f"{base_url}/health/db", timeout=2)
        print(f"✅ DB Health endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ DB Health endpoint failed: {e}")
    
    # Test groups endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/errors/groups", timeout=5)
        print(f"✅ Groups endpoint: {response.status_code}")
        data = response.json()
        print(f"   Groups count: {len(data.get('groups', []))}")
        if 'error' in data:
            print(f"   ⚠️ Error in response: {data['error']}")
    except Exception as e:
        print(f"❌ Groups endpoint failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_backend()
    sys.exit(0 if success else 1)

