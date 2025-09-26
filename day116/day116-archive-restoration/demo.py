#!/usr/bin/env python3
"""
Demo script for Archive Restoration System
Demonstrates key functionality with sample data
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

async def run_demo():
    print("🎬 Archive Restoration System Demo")
    print("=================================")
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("\n1. 📦 Creating sample archives...")
        async with session.post(f"{base_url}/api/demo/create-sample-archives") as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ Created {len(result['files'])} sample archives")
                for file_info in result['files']:
                    print(f"      - {file_info['file']}: {file_info['records']} records")
            else:
                print(f"   ❌ Failed to create archives: {resp.status}")
                return
        
        print("\n2. 📊 Checking system stats...")
        async with session.get(f"{base_url}/api/stats") as resp:
            if resp.status == 200:
                stats = await resp.json()
                print(f"   📁 Archives: {stats['archives']['total']}")
                print(f"   💾 Cache hit rate: {stats['cache']['hit_rate']:.1%}")
                print(f"   ⚡ Active jobs: {stats['active_jobs']}")
            else:
                print(f"   ❌ Failed to get stats: {resp.status}")
        
        print("\n3. 🔍 Testing archive query...")
        query_data = {
            "start_time": (datetime.now() - timedelta(days=2)).isoformat(),
            "end_time": (datetime.now() - timedelta(hours=1)).isoformat(),
            "filters": {"level": "ERROR"},
            "page_size": 10,
            "include_archived": True
        }
        
        async with session.post(f"{base_url}/api/query", json=query_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ Query completed in {result['processing_time_ms']}ms")
                print(f"   📋 Found {result['total_count']} records")
                print(f"   💾 Cache hit: {'Yes' if result['cache_hit'] else 'No'}")
                print(f"   📁 Sources: {len(result['sources'])} archive(s)")
                
                if result['records']:
                    print(f"   📄 Sample record:")
                    sample = result['records'][0]
                    print(f"      Timestamp: {sample.get('timestamp', 'N/A')}")
                    print(f"      Level: {sample.get('level', 'N/A')}")
                    print(f"      Service: {sample.get('service', 'N/A')}")
                    print(f"      Message: {sample.get('message', 'N/A')[:50]}...")
            else:
                print(f"   ❌ Query failed: {resp.status}")
        
        print("\n4. 📁 Listing available archives...")
        async with session.get(f"{base_url}/api/archives") as resp:
            if resp.status == 200:
                archives = await resp.json()
                print(f"   📦 Total archives: {archives['total']}")
                for archive in archives['archives'][:3]:  # Show first 3
                    size_mb = archive['size_mb']
                    print(f"      - {archive['file_path'].split('/')[-1]}")
                    print(f"        📊 {archive['record_count']} records, {size_mb:.2f} MB")
                    print(f"        🕐 {archive['start_time']} to {archive['end_time']}")
            else:
                print(f"   ❌ Failed to list archives: {resp.status}")
        
        print("\n5. 🧪 Testing cache performance...")
        # Run same query again to test cache
        async with session.post(f"{base_url}/api/query", json=query_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ⚡ Second query: {result['processing_time_ms']}ms")
                print(f"   💾 Cache hit: {'Yes' if result['cache_hit'] else 'No'}")
            else:
                print(f"   ❌ Cache test failed: {resp.status}")
    
    print("\n✅ Demo completed successfully!")
    print(f"\n🌐 Access the full dashboard at: {base_url}")
    print("   - Query historical data")
    print("   - Monitor system performance") 
    print("   - Browse available archives")

if __name__ == "__main__":
    asyncio.run(run_demo())
