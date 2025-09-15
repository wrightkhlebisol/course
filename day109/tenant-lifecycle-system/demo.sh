#!/bin/bash
set -e

echo "🎬 Tenant Lifecycle Management Demo"
echo "=================================="

# Activate virtual environment
source venv/bin/activate

# Start backend server
echo "🚀 Starting backend server..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

sleep 5

echo "📊 Starting demonstration..."
echo ""

# Demo script
python3 << 'DEMO_SCRIPT'
import requests
import json
import time
import uuid

base_url = "http://localhost:8000/api"

print("1. 🏢 Creating demo tenants...")

# Create multiple demo tenants
tenants_data = [
    {
        "name": "Acme Corporation",
        "email": "admin@acme.com",
        "plan": "enterprise",
        "config": {"log_retention_days": 365, "custom_domain": "logs.acme.com"}
    },
    {
        "name": "StartupXYZ",
        "email": "tech@startupxyz.com", 
        "plan": "pro",
        "config": {"log_retention_days": 90}
    },
    {
        "name": "Small Business",
        "email": "owner@smallbiz.com",
        "plan": "basic",
        "config": {"log_retention_days": 30}
    }
]

created_tenants = []

for tenant_data in tenants_data:
    print(f"   Creating {tenant_data['name']}...")
    response = requests.post(f"{base_url}/tenants/onboard", json=tenant_data)
    if response.status_code == 200:
        result = response.json()
        created_tenants.append(result['tenant_id'])
        print(f"   ✅ Created tenant: {result['tenant_id']}")
    else:
        print(f"   ❌ Failed to create tenant: {response.text}")

print(f"\n2. 📈 Dashboard Statistics:")
time.sleep(2)  # Wait for onboarding to complete

response = requests.get(f"{base_url}/stats/dashboard")
if response.status_code == 200:
    stats = response.json()
    print(f"   📊 Total Tenants: {stats['total_tenants']}")
    print(f"   📊 State Distribution:")
    for state, count in stats['state_distribution'].items():
        print(f"      {state}: {count}")
else:
    print("   ❌ Failed to fetch dashboard stats")

print(f"\n3. 👥 Listing all tenants:")
response = requests.get(f"{base_url}/tenants")
if response.status_code == 200:
    tenants = response.json()
    for tenant in tenants:
        print(f"   🏢 {tenant['name']} ({tenant['plan']}) - {tenant['state']}")
else:
    print("   ❌ Failed to fetch tenants")

print(f"\n4. 🔍 Tenant details:")
if created_tenants:
    tenant_id = created_tenants[0]
    response = requests.get(f"{base_url}/tenants/{tenant_id}")
    if response.status_code == 200:
        tenant = response.json()
        print(f"   🏢 Name: {tenant['name']}")
        print(f"   📧 Email: {tenant['email']}")
        print(f"   📋 Plan: {tenant['plan']}")
        print(f"   🔑 API Key: {tenant.get('api_key', 'Not generated')}")
        print(f"   💾 Storage Used: {tenant['resources']['storage_used_gb']} GB")
        print(f"   📊 Logs Today: {tenant['resources']['logs_ingested_today']}")

print(f"\n5. 👋 Testing offboarding:")
if len(created_tenants) > 1:
    tenant_to_offboard = created_tenants[-1]  # Offboard the last tenant
    print(f"   Offboarding tenant: {tenant_to_offboard}")
    response = requests.post(f"{base_url}/tenants/{tenant_to_offboard}/offboard")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Offboarding initiated: {result['message']}")
    else:
        print(f"   ❌ Failed to initiate offboarding: {response.text}")

print(f"\n6. 📊 Final dashboard statistics:")
time.sleep(2)  # Wait for offboarding to start
response = requests.get(f"{base_url}/stats/dashboard")
if response.status_code == 200:
    stats = response.json()
    print(f"   📊 Total Tenants: {stats['total_tenants']}")
    print(f"   📊 State Distribution:")
    for state, count in stats['state_distribution'].items():
        print(f"      {state}: {count}")

print(f"\n🎉 Demo completed successfully!")
print(f"🌐 Web UI available at: http://localhost:5173")
print(f"📚 API Documentation: http://localhost:8000/docs")
DEMO_SCRIPT

# Keep server running for manual testing
echo ""
echo "🌐 Backend server is running at http://localhost:8000"
echo "📚 API Documentation available at http://localhost:8000/docs"
echo ""
echo "You can now:"
echo "  - Start frontend with: cd frontend && npm run dev"
echo "  - Test API endpoints manually"
echo "  - View tenant data in the database"
echo ""
echo "Press Ctrl+C to stop the server"

trap 'echo "🛑 Stopping demo server..."; kill $BACKEND_PID 2>/dev/null || true; exit 0' INT
wait
