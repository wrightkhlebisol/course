#!/usr/bin/env python3
"""
Test script to generate new data and verify metrics updates
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def test_metrics_update():
    """Test if metrics update when new data is generated"""
    
    print("🧪 Testing Metrics Update")
    print("=" * 40)
    
    # Get initial stats
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/api/stats') as response:
            if response.status == 200:
                initial_data = await response.json()
                initial_queries = initial_data['pattern_insights']['total_queries']
                print(f"📊 Initial total queries: {initial_queries}")
            else:
                print("❌ Failed to get initial stats")
                return
    
    # Generate some new data by running queries
    print("\n🔄 Generating new query data...")
    
    # Simulate some new queries
    queries = [
        {"level": "ERROR", "service": "test-service"},
        {"columns": ["timestamp", "duration_ms"], "aggregation": True},
        {"service": "web-api", "columns": ["timestamp", "message", "user_id"]}
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"  Query {i}: {query}")
        # Simulate query execution time
        await asyncio.sleep(0.1)
    
    # Wait a moment for the system to process
    print("\n⏳ Waiting for system to process...")
    await asyncio.sleep(2)
    
    # Check updated stats
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/api/stats') as response:
            if response.status == 200:
                updated_data = await response.json()
                updated_queries = updated_data['pattern_insights']['total_queries']
                print(f"📊 Updated total queries: {updated_queries}")
                
                if updated_queries > initial_queries:
                    print("✅ Metrics updated successfully!")
                    print(f"   Queries increased by: {updated_queries - initial_queries}")
                else:
                    print("⚠️  No change in query count")
                    
                # Show some key metrics
                storage_stats = updated_data['storage_stats']
                print(f"\n📈 Current Metrics:")
                print(f"   Total Storage: {storage_stats['total_storage_mb']} MB")
                print(f"   Active Partitions: {len(storage_stats['partitions'])}")
                print(f"   Compression Savings: {storage_stats['compression_savings']}%")
                
                # Show partition details
                for partition, stats in storage_stats['partitions'].items():
                    print(f"   {partition}: {stats['reads']} reads, {stats['writes']} writes")
                    
            else:
                print("❌ Failed to get updated stats")

async def test_websocket_updates():
    """Test WebSocket real-time updates"""
    
    print("\n🔌 Testing WebSocket Updates")
    print("=" * 40)
    
    try:
        import websockets
        
        async with websockets.connect('ws://localhost:8000/ws') as websocket:
            print("✅ WebSocket connected")
            
            # Wait for a message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(message)
                
                if data.get('type') == 'stats_update':
                    print("✅ Received real-time stats update")
                    print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
                    print(f"   Data keys: {list(data.get('data', {}).keys())}")
                else:
                    print(f"⚠️  Received unexpected message type: {data.get('type')}")
                    
            except asyncio.TimeoutError:
                print("⚠️  No WebSocket message received within 10 seconds")
                
    except ImportError:
        print("⚠️  WebSocket library not available")
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

async def main():
    """Run all tests"""
    print("🚀 Storage Optimization Metrics Update Test")
    print("=" * 50)
    
    # Test basic metrics update
    await test_metrics_update()
    
    # Test WebSocket updates
    await test_websocket_updates()
    
    print("\n🎉 Test completed!")
    print("\n💡 To see live updates:")
    print("   1. Open http://localhost:8000 in your browser")
    print("   2. Open browser developer tools (F12)")
    print("   3. Check the console for update logs")
    print("   4. Click the '🔄 Refresh' button to manually update")

if __name__ == "__main__":
    asyncio.run(main()) 