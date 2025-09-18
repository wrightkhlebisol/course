#!/usr/bin/env python3
"""Demo script to showcase enterprise authentication features"""

import asyncio
import aiohttp
import json
import time

API_BASE = "http://localhost:8000"

async def demo_authentication():
    """Demonstrate authentication flow"""
    print("🚀 Enterprise Authentication Demo")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test health check
        print("\n1. Health Check:")
        async with session.get(f"{API_BASE}/api/health") as resp:
            health = await resp.json()
            print(f"   System Status: {health['status']}")
            print(f"   LDAP: {health['services']['ldap']}")
            print(f"   Database: {health['services']['database']}")
        
        # Test authentication
        print("\n2. User Authentication:")
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        async with session.post(f"{API_BASE}/api/auth/login", json=login_data) as resp:
            if resp.status == 200:
                auth_result = await resp.json()
                print("   ✅ Authentication successful!")
                print(f"   User: {auth_result['user']['full_name']}")
                print(f"   Department: {auth_result['user']['department']}")
                print(f"   Roles: {', '.join(auth_result['user']['roles'])}")
                
                token = auth_result['token']
                
                # Test profile access
                print("\n3. Profile Access:")
                headers = {"Authorization": f"Bearer {token}"}
                async with session.get(f"{API_BASE}/api/auth/profile", headers=headers) as resp:
                    if resp.status == 200:
                        profile = await resp.json()
                        print("   ✅ Profile accessed successfully!")
                        print(f"   Groups: {len(profile['groups'])}")
                        for group in profile['groups']:
                            print(f"   - {group['name']} ({group['role']})")
                    else:
                        print("   ❌ Profile access failed")
                
                # Test admin functions if user has admin role
                if 'Admin' in auth_result['user']['roles']:
                    print("\n4. Admin Functions:")
                    async with session.get(f"{API_BASE}/api/admin/stats", headers=headers) as resp:
                        if resp.status == 200:
                            stats = await resp.json()
                            print("   ✅ Admin stats accessed!")
                            print(f"   Total Users: {stats['total_users']}")
                            print(f"   Active Sessions: {stats['active_sessions']}")
                            print(f"   24h Logins: {stats['logins_24h']}")
                        else:
                            print("   ❌ Admin access failed")
                
            else:
                print("   ❌ Authentication failed!")
                error = await resp.text()
                print(f"   Error: {error}")
        
        # Test invalid credentials
        print("\n5. Invalid Credentials Test:")
        bad_login = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        async with session.post(f"{API_BASE}/api/auth/login", json=bad_login) as resp:
            if resp.status == 401:
                print("   ✅ Invalid credentials correctly rejected")
            else:
                print("   ❌ Security issue: invalid credentials accepted")

def print_summary():
    """Print demo summary"""
    print("\n" + "=" * 50)
    print("🎉 Enterprise Authentication Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("✅ LDAP/Active Directory authentication")
    print("✅ User profile synchronization")
    print("✅ Group-based role mapping")
    print("✅ JWT token-based sessions")
    print("✅ Admin access controls")
    print("✅ Security validation")
    print("\n🌐 Web Interface: http://localhost:8000")
    print("📊 LDAP Admin: http://localhost:8080")
    print("\nTest Credentials:")
    print("• testuser / password123 (Admin, Analyst, Viewer)")
    print("• admin / admin123 (Admin)")
    print("• analyst / analyst123 (Analyst)")

async def main():
    try:
        await demo_authentication()
        print_summary()
    except aiohttp.ClientError as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the service is running: python src/api/main.py")
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
