#!/usr/bin/env python3
"""
Verification script for Archive Restoration System
Checks all components are working correctly
"""

import asyncio
import aiohttp
import sys
import os
from pathlib import Path

async def verify_system():
    print("🔍 Verifying Archive Restoration System")
    print("======================================")
    
    verification_results = []
    
    # Check directory structure
    print("\n1. 📁 Checking directory structure...")
    required_dirs = [
        "backend/src/restoration",
        "backend/src/archive", 
        "backend/src/cache",
        "backend/src/query",
        "backend/config",
        "backend/tests",
        "frontend/src/components",
        "data/archives",
        "data/cache",
        "data/indexes"
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"   ✅ {dir_path}")
            verification_results.append(True)
        else:
            print(f"   ❌ {dir_path} - MISSING")
            verification_results.append(False)
    
    # Check required files
    print("\n2. 📄 Checking required files...")
    required_files = [
        "backend/src/restoration/models.py",
        "backend/src/restoration/decompressor.py", 
        "backend/src/restoration/api.py",
        "backend/src/archive/locator.py",
        "backend/src/cache/manager.py",
        "backend/src/query/processor.py",
        "backend/src/main.py",
        "frontend/src/App.js",
        "requirements.txt",
        "build.sh",
        "start.sh",
        "stop.sh"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
            verification_results.append(True)
        else:
            print(f"   ❌ {file_path} - MISSING")
            verification_results.append(False)
    
    # Check if server is running
    print("\n3. 🌐 Checking server connectivity...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/", timeout=5) as resp:
                if resp.status == 200:
                    print("   ✅ Server is running and responding")
                    verification_results.append(True)
                else:
                    print(f"   ⚠️  Server responded with status {resp.status}")
                    verification_results.append(False)
    except Exception as e:
        print(f"   ❌ Server not accessible: {e}")
        print("      Run './start.sh' to start the server")
        verification_results.append(False)
    
    # Check API endpoints
    if verification_results[-1]:  # Only if server is running
        print("\n4. 🔌 Testing API endpoints...")
        endpoints = [
            ("/api/stats", "Statistics endpoint"),
            ("/api/archives", "Archives listing"),
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in endpoints:
                try:
                    async with session.get(f"http://localhost:8000{endpoint}", timeout=5) as resp:
                        if resp.status == 200:
                            print(f"   ✅ {description}")
                            verification_results.append(True)
                        else:
                            print(f"   ❌ {description} - Status {resp.status}")
                            verification_results.append(False)
                except Exception as e:
                    print(f"   ❌ {description} - Error: {e}")
                    verification_results.append(False)
    
    # Summary
    print("\n📊 Verification Summary")
    print("======================")
    total_checks = len(verification_results)
    passed_checks = sum(verification_results)
    success_rate = (passed_checks / total_checks) * 100
    
    print(f"Passed: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 System verification PASSED!")
        print("\n🚀 Your Archive Restoration System is ready!")
        print("   Access the dashboard at: http://localhost:8000")
        return True
    else:
        print("❌ System verification FAILED!")
        print("   Please check the failed items above")
        return False

if __name__ == "__main__":
    result = asyncio.run(verify_system())
    sys.exit(0 if result else 1)
