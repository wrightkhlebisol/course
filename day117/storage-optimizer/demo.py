#!/usr/bin/env python3

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def demo_storage_optimization():
    """Demonstrate storage optimization system"""
    
    print("🚀 Storage Optimization Demo")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api"
    
    async with aiohttp.ClientSession() as session:
        # 1. Get initial metrics
        print("\n📊 Initial Storage Metrics:")
        async with session.get(f"{base_url}/cost/realtime") as response:
            metrics = await response.json()
            print(f"  Current Monthly Cost: ${metrics['current_monthly_cost']}")
            print(f"  Optimization Score: {metrics['optimization_score']}%")
            print(f"  Storage Efficiency: {metrics['storage_efficiency']}%")
        
        # 2. Show available policies
        print("\n📋 Available Optimization Policies:")
        async with session.get(f"{base_url}/policies") as response:
            policies = await response.json()
            for name, policy in policies.items():
                print(f"  {name}: {policy['name']}")
        
        # 3. Switch to aggressive policy
        print("\n🎯 Switching to Aggressive Cost Savings policy...")
        async with session.post(f"{base_url}/policies/set", 
                               json={"policy_name": "aggressive"}) as response:
            result = await response.json()
            print(f"  {result['message']}")
        
        # 4. Trigger optimization
        print("\n⚡ Triggering Storage Optimization...")
        async with session.post(f"{base_url}/optimize") as response:
            optimization = await response.json()
            print(f"  Optimized {optimization['optimized_entries']} entries")
            print(f"  Cost Savings: ${optimization['cost_savings']:.2f}")
        
        # 5. Wait and show updated metrics
        print("\n⏳ Waiting for optimization to complete...")
        await asyncio.sleep(3)
        
        print("\n📈 Updated Storage Metrics:")
        async with session.get(f"{base_url}/cost/realtime") as response:
            updated_metrics = await response.json()
            print(f"  Current Monthly Cost: ${updated_metrics['current_monthly_cost']}")
            print(f"  Potential Savings: ${updated_metrics['potential_monthly_savings']}")
            print(f"  Savings Percentage: {updated_metrics['savings_percentage']}%")
            print(f"  Optimization Score: {updated_metrics['optimization_score']}%")
        
        # 6. Show tier breakdown
        print("\n🗂️  Storage Tier Breakdown:")
        async with session.get(f"{base_url}/cost/tiers") as response:
            tiers = await response.json()
            for tier_name, tier_data in tiers.items():
                print(f"  {tier_name.replace('_', ' ').title()}: ${tier_data['cost']:.2f} ({tier_data['percentage']}%)")
    
    print("\n✅ Demo completed successfully!")
    print("\n🌐 Open http://localhost:3000 to view the dashboard")

if __name__ == "__main__":
    asyncio.run(demo_storage_optimization())
