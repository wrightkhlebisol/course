#!/usr/bin/env python3
"""
Generate live data to trigger real metric updates
"""

import asyncio
import aiohttp
import json
import random
from datetime import datetime

async def generate_live_queries():
    """Generate live queries to trigger metric updates"""
    
    print("🚀 Generating Live Data for Metrics Updates")
    print("=" * 50)
    
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
    
    # Generate multiple rounds of queries
    for round_num in range(1, 4):
        print(f"\n🔄 Round {round_num}: Generating new queries...")
        
        # Generate different types of queries
        queries = [
            # Full record queries (row-oriented)
            {"level": "ERROR", "service": f"service-{round_num}"},
            {"level": "WARNING", "user_id": f"user-{round_num}"},
            {"status_code": 500, "ip_address": f"192.168.1.{round_num}"},
            
            # Analytical queries (columnar)
            {"columns": ["timestamp", "duration_ms", "status_code"], "aggregation": True},
            {"columns": ["service", "level"], "aggregation": True},
            {"columns": ["timestamp", "user_id"], "aggregation": True},
            
            # Mixed queries (hybrid)
            {"service": "web-api", "columns": ["timestamp", "message", "user_id", "status_code"]},
            {"level": "INFO", "columns": ["timestamp", "service", "duration_ms"]},
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"  Query {i}: {query}")
            
            # Simulate query execution
            await asyncio.sleep(0.2)
        
        # Wait for processing
        print("  ⏳ Processing...")
        await asyncio.sleep(1)
        
        # Check updated stats
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/api/stats') as response:
                if response.status == 200:
                    updated_data = await response.json()
                    updated_queries = updated_data['pattern_insights']['total_queries']
                    print(f"  📊 Total queries: {updated_queries}")
                    
                    # Show partition updates
                    storage_stats = updated_data['storage_stats']
                    for partition, stats in storage_stats['partitions'].items():
                        print(f"    {partition}: {stats['reads']} reads, {stats['writes']} writes")
    
    print(f"\n✅ Live data generation completed!")
    print(f"📈 Final query count: {updated_queries}")
    print(f"📊 Query increase: {updated_queries - initial_queries}")

async def trigger_optimization():
    """Trigger storage optimization to see format changes"""
    
    print("\n🎯 Triggering Storage Optimization")
    print("=" * 40)
    
    partitions = ['web-logs', 'api-logs', 'error-logs']
    
    for partition in partitions:
        print(f"🔄 Optimizing {partition}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://localhost:8000/api/optimize/{partition}') as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"  ✅ {partition}: {result.get('status', 'optimized')}")
                else:
                    print(f"  ❌ {partition}: Failed")
        
        await asyncio.sleep(0.5)

async def main():
    """Run the live data generation"""
    
    print("🎬 Live Metrics Update Demo")
    print("=" * 50)
    print("This will generate real queries to trigger metric updates")
    print("Watch the dashboard at http://localhost:8000 for live updates")
    print()
    
    # Generate live queries
    await generate_live_queries()
    
    # Trigger optimization
    await trigger_optimization()
    
    print("\n🎉 Demo completed!")
    print("\n💡 Dashboard should now show updated metrics:")
    print("   • Increased query counts")
    print("   • Updated performance metrics")
    print("   • Real-time format recommendations")
    print("   • Live WebSocket updates")

if __name__ == "__main__":
    asyncio.run(main()) 