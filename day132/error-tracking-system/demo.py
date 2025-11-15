#!/usr/bin/env python3
"""
Demo script to showcase error tracking system
Generates various types of errors to demonstrate functionality
"""

import asyncio
import aiohttp
import json
import random
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

# Sample error templates
ERROR_TEMPLATES = [
    {
        "message": "Database connection timeout after {timeout}s",
        "stack_trace": "at database.py line 123\n  at connection_pool.get() line 45\n  at service.connect() line 67",
        "type": "ConnectionTimeoutError",
        "level": "error",
        "platform": "python"
    },
    {
        "message": "User {user_id} not found in database",
        "stack_trace": "at user_service.py line 89\n  at get_user() line 23\n  at api.users() line 156",
        "type": "UserNotFoundError", 
        "level": "warning",
        "platform": "python"
    },
    {
        "message": "Payment processing failed: Invalid card number",
        "stack_trace": "at payment.py line 234\n  at validate_card() line 12\n  at process_payment() line 45",
        "type": "PaymentError",
        "level": "critical",
        "platform": "python"
    },
    {
        "message": "Memory allocation failed: Out of memory",
        "stack_trace": "at memory.c line 567\n  at malloc() line 34\n  at allocate_buffer() line 78",
        "type": "MemoryError",
        "level": "critical",
        "platform": "c++"
    },
    {
        "message": "API rate limit exceeded: {rate}/minute",
        "stack_trace": "at rate_limiter.py line 45\n  at check_limit() line 23\n  at api_middleware() line 89",
        "type": "RateLimitError",
        "level": "warning",
        "platform": "python"
    }
]

async def generate_error(session, template):
    """Generate a single error based on template"""
    # Fill in template variables
    error_data = template.copy()
    
    if "{timeout}" in error_data["message"]:
        error_data["message"] = error_data["message"].format(timeout=random.randint(10, 60))
    
    if "{user_id}" in error_data["message"]:
        error_data["message"] = error_data["message"].format(user_id=f"user_{random.randint(1000, 9999)}")
    
    if "{rate}" in error_data["message"]:
        error_data["message"] = error_data["message"].format(rate=random.randint(100, 500))
    
    # Add random context
    error_data.update({
        "timestamp": datetime.now().isoformat(),
        "request_id": f"req_{random.randint(10000, 99999)}",
        "trace_id": f"trace_{random.randint(100000, 999999)}",
        "environment": random.choice(["production", "staging", "development"]),
        "release": f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
        "context": {
            "url": random.choice(["/api/users", "/api/payments", "/api/orders", "/api/products"]),
            "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "ip": f"192.168.1.{random.randint(1, 255)}"
        },
        "tags": {
            "service": random.choice(["user-service", "payment-service", "order-service"]),
            "version": f"{random.randint(1, 3)}.{random.randint(0, 9)}"
        }
    })
    
    # Send to error tracking system
    try:
        async with session.post(f"{BASE_URL}/errors/collect", json=error_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Created error: {result.get('error_id')} -> Group {result.get('group_id')}")
                return True
            else:
                print(f"❌ Failed to create error: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Exception creating error: {e}")
        return False

async def run_demo():
    """Run the error tracking demo"""
    print("🎭 Error Tracking System Demo")
    print("=" * 50)
    print(f"🎯 Target API: {BASE_URL}")
    print()
    
    # Check if API is available
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"http://localhost:8000/health") as response:
                if response.status != 200:
                    print("❌ Backend API is not running!")
                    print("   Run: python backend/main.py")
                    return
        except:
            print("❌ Cannot connect to backend API!")
            print("   Make sure the backend is running on port 8000")
            return
    
    print("✅ Backend API is running")
    print()
    
    # Generate errors
    async with aiohttp.ClientSession() as session:
        print("📊 Generating demo errors...")
        
        # Create multiple instances of each error type
        success_count = 0
        total_count = 0
        
        for round_num in range(3):  # 3 rounds
            print(f"\n🔄 Round {round_num + 1}/3")
            
            for template in ERROR_TEMPLATES:
                # Create 2-5 instances of each error type
                instances = random.randint(2, 5)
                
                for i in range(instances):
                    success = await generate_error(session, template)
                    if success:
                        success_count += 1
                    total_count += 1
                    
                    # Small delay between errors
                    await asyncio.sleep(0.1)
        
        print(f"\n📈 Demo Results:")
        print(f"   Generated: {success_count}/{total_count} errors")
        print(f"   Success rate: {(success_count/total_count)*100:.1f}%")
    
    # Show how to access the results
    print(f"\n🌐 View Results:")
    print(f"   Frontend Dashboard: http://localhost:3000")
    print(f"   API Documentation: http://localhost:8000/docs")
    print(f"   Error Groups API: {BASE_URL}/errors/groups")
    print()
    print("🎯 Check the dashboard to see how similar errors are grouped together!")

if __name__ == "__main__":
    asyncio.run(run_demo())
