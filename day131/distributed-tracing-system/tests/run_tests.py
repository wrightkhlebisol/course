#!/usr/bin/env python3
"""
Test runner for the distributed tracing system
"""
import subprocess
import sys
import time
import pytest

def run_unit_tests():
    """Run unit tests"""
    print("🧪 Running unit tests...")
    result = pytest.main([
        "tests/unit/",
        "-v",
        "--tb=short"
    ])
    return result == 0

def run_integration_tests():
    """Run integration tests"""
    print("🔗 Running integration tests...")
    print("   Note: Services must be running for integration tests")
    result = pytest.main([
        "tests/integration/",
        "-v",
        "--tb=short"
    ])
    return result == 0

def check_services_running():
    """Check if services are running"""
    import httpx
    import asyncio
    
    async def check_service(url, name):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=2.0)
                if response.status_code == 200:
                    print(f"   ✅ {name} is running")
                    return True
                else:
                    print(f"   ❌ {name} returned status {response.status_code}")
                    return False
        except:
            print(f"   ❌ {name} is not accessible")
            return False
    
    async def check_all():
        services = [
            ("http://localhost:8001/", "API Gateway"),
            ("http://localhost:8002/", "User Service"),
            ("http://localhost:8003/", "Database Service"),
            ("http://localhost:8000/api/traces", "Dashboard")
        ]
        
        print("🔍 Checking service availability...")
        results = []
        for url, name in services:
            result = await check_service(url, name)
            results.append(result)
        
        return all(results)
    
    return asyncio.run(check_all())

def run_all_tests():
    """Run all tests"""
    print("🚀 Running Distributed Tracing System Tests")
    print("=" * 50)
    
    # Run unit tests first
    unit_success = run_unit_tests()
    
    if not unit_success:
        print("❌ Unit tests failed. Skipping integration tests.")
        return False
    
    print("✅ Unit tests passed!")
    
    # Check if services are running for integration tests
    services_running = check_services_running()
    
    if services_running:
        print("✅ All services are running. Running integration tests...")
        integration_success = run_integration_tests()
        
        if integration_success:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Integration tests failed.")
            return False
    else:
        print("⚠️  Some services are not running. Skipping integration tests.")
        print("   To run integration tests, start services with: python src/main.py")
        return unit_success

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
