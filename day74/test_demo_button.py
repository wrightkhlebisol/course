#!/usr/bin/env python3
"""
Test script to demonstrate the demo button functionality
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_demo_functionality():
    """Test the demo button functionality"""
    
    print("🎬 Testing Demo Button Functionality")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Get initial stats
        print("📊 Getting initial stats...")
        async with session.get('http://localhost:8000/api/stats') as response:
            if response.status == 200:
                initial_data = await response.json()
                initial_queries = initial_data['pattern_insights']['total_queries']
                print(f"   Initial total queries: {initial_queries}")
            else:
                print("❌ Failed to get initial stats")
                return
        
        # Run the demo
        print("\n🎬 Running metrics demo...")
        async with session.post('http://localhost:8000/api/demo/metrics') as response:
            if response.status == 200:
                demo_result = await response.json()
                print(f"   ✅ Demo completed: {demo_result['message']}")
                print(f"   📈 New queries: {demo_result['new_queries']}")
                print(f"   🎯 Optimizations: {demo_result['optimizations_triggered']}")
            else:
                print("❌ Demo failed")
                return
        
        # Wait a moment for processing
        await asyncio.sleep(2)
        
        # Get updated stats
        print("\n📊 Getting updated stats...")
        async with session.get('http://localhost:8000/api/stats') as response:
            if response.status == 200:
                updated_data = await response.json()
                updated_queries = updated_data['pattern_insights']['total_queries']
                print(f"   Updated total queries: {updated_queries}")
                print(f"   Query increase: {updated_queries - initial_queries}")
                
                # Show some key metrics
                storage_stats = updated_data['storage_stats']
                print(f"\n📈 Updated Metrics:")
                print(f"   Total Storage: {storage_stats['total_storage_mb']} MB")
                print(f"   Active Partitions: {len(storage_stats['partitions'])}")
                print(f"   Compression Savings: {storage_stats['compression_savings']}%")
                
                # Show partition details
                for partition, stats in storage_stats['partitions'].items():
                    print(f"   {partition}: {stats['reads']} reads, {stats['writes']} writes")
                    
            else:
                print("❌ Failed to get updated stats")

async def test_multiple_demos():
    """Test running multiple demos to see cumulative effects"""
    
    print("\n🔄 Testing Multiple Demo Runs")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        for run in range(1, 4):
            print(f"\n🔄 Demo Run {run}:")
            
            # Get current stats
            async with session.get('http://localhost:8000/api/stats') as response:
                if response.status == 200:
                    data = await response.json()
                    current_queries = data['pattern_insights']['total_queries']
                    print(f"   Current queries: {current_queries}")
            
            # Run demo
            async with session.post('http://localhost:8000/api/demo/metrics') as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Demo {run} completed")
                else:
                    print(f"   ❌ Demo {run} failed")
            
            # Wait between runs
            await asyncio.sleep(1)
        
        # Final stats
        print(f"\n📊 Final Stats:")
        async with session.get('http://localhost:8000/api/stats') as response:
            if response.status == 200:
                data = await response.json()
                final_queries = data['pattern_insights']['total_queries']
                print(f"   Final total queries: {final_queries}")

async def main():
    """Run all tests"""
    print("🚀 Demo Button Functionality Test")
    print("=" * 50)
    print("This will test the new demo button functionality")
    print("Watch the dashboard at http://localhost:8000 for live updates")
    print()
    
    # Test single demo
    await test_demo_functionality()
    
    # Test multiple demos
    await test_multiple_demos()
    
    print("\n🎉 Test completed!")
    print("\n💡 Dashboard Features:")
    print("   • 🎬 Demo Metrics button - generates live data")
    print("   • 🔄 Refresh button - manually update metrics")
    print("   • 🚀 Optimize All button - trigger optimizations")
    print("   • Real-time WebSocket updates")
    print("   • Visual update indicators")
    print("   • Performance charts")

if __name__ == "__main__":
    asyncio.run(main()) 