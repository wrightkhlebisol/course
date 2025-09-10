#!/usr/bin/env python3

"""
Demo script for Multi-Tenant Log Platform
Demonstrates tenant creation, user authentication, and log ingestion
"""

import requests
import json
import time
import random
from datetime import datetime

BASE_URL = "http://localhost:8000"

def create_demo_tenants():
    """Create demo tenants with sample data"""
    tenants = [
        {
            "name": "Acme Corp",
            "domain": "acme.com",
            "service_tier": "enterprise",
            "admin_email": "admin@acme.com",
            "admin_username": "acmeadmin",
            "admin_password": "demo_password_123"
        },
        {
            "name": "Beta Solutions",
            "domain": "beta.com",
            "service_tier": "premium",
            "admin_email": "admin@beta.com",
            "admin_username": "betaadmin",
            "admin_password": "demo_password_123"
        },
        {
            "name": "Gamma Inc",
            "domain": "gamma.com",
            "service_tier": "basic",
            "admin_email": "admin@gamma.com",
            "admin_username": "gammaadmin",
            "admin_password": "demo_password_123"
        }
    ]
    
    print("🏢 Creating demo tenants...")
    created_tenants = []
    
    for tenant_data in tenants:
        try:
            response = requests.post(f"{BASE_URL}/api/v1/tenants/", json=tenant_data)
            if response.status_code == 200:
                print(f"✅ Created tenant: {tenant_data['name']}")
                created_tenants.append(tenant_data)
            else:
                print(f"❌ Failed to create tenant {tenant_data['name']}: {response.text}")
        except Exception as e:
            print(f"❌ Error creating tenant {tenant_data['name']}: {e}")
    
    return created_tenants

def authenticate_tenant(tenant_data):
    """Authenticate and get JWT token for a tenant"""
    login_data = {
        "tenant_domain": tenant_data["domain"],
        "username": tenant_data["admin_username"],
        "password": tenant_data["admin_password"]
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/tenants/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Authentication failed for {tenant_data['domain']}: {response.text}")
        return None

def generate_sample_logs(tenant_name, count=50):
    """Generate sample log entries for demonstration"""
    services = ["auth-service", "api-gateway", "user-service", "payment-service", "notification-service"]
    sources = ["web-app", "mobile-app", "background-job", "webhook"]
    levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
    
    messages = [
        "User authentication successful",
        "API request processed",
        "Database query executed",
        "Cache miss occurred",
        "Payment processed successfully",
        "Email notification sent",
        "File upload completed",
        "Session expired",
        "Rate limit exceeded",
        "Configuration updated"
    ]
    
    logs = []
    for i in range(count):
        log = {
            "level": random.choice(levels),
            "message": f"[{tenant_name}] {random.choice(messages)} - Event #{i+1}",
            "source": random.choice(sources),
            "service": random.choice(services),
            "log_metadata": {
                "user_id": f"user_{random.randint(1000, 9999)}",
                "request_id": f"req_{random.randint(100000, 999999)}",
                "tenant": tenant_name,
                "demo": True
            }
        }
        logs.append(log)
    
    return logs

def ingest_logs_for_tenant(tenant_data, token):
    """Ingest sample logs for a tenant"""
    logs = generate_sample_logs(tenant_data["name"])
    
    # Split into smaller batches for better performance
    batch_size = 10
    total_logs = 0
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for i in range(0, len(logs), batch_size):
        batch = logs[i:i+batch_size]
        bulk_request = {"logs": batch}
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/logs/ingest/bulk", 
                                   json=bulk_request, headers=headers)
            if response.status_code == 200:
                total_logs += len(batch)
                print(f"📝 Ingested {len(batch)} logs for {tenant_data['name']} (Total: {total_logs})")
                time.sleep(0.1)  # Small delay to prevent overwhelming the system
            else:
                print(f"❌ Failed to ingest logs for {tenant_data['name']}: {response.text}")
        except Exception as e:
            print(f"❌ Error ingesting logs for {tenant_data['name']}: {e}")
    
    return total_logs

def demonstrate_tenant_isolation(tenants, tokens):
    """Demonstrate that tenants can only access their own data"""
    print("\n🔒 Demonstrating tenant isolation...")
    
    for i, (tenant_data, token) in enumerate(zip(tenants, tokens)):
        if token:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get tenant stats
            try:
                response = requests.get(f"{BASE_URL}/api/v1/tenants/me/stats", headers=headers)
                if response.status_code == 200:
                    stats = response.json()
                    print(f"📊 {tenant_data['name']} Stats:")
                    print(f"   - Total Logs: {stats['total_logs']}")
                    print(f"   - Service Tier: {stats['service_tier']}")
                    print(f"   - Status: {stats['status']}")
                
                # Get analytics
                analytics_response = requests.get(f"{BASE_URL}/api/v1/logs/analytics", headers=headers)
                if analytics_response.status_code == 200:
                    analytics = analytics_response.json()
                    print(f"   - Log Level Distribution: {analytics['level_distribution']}")
                    
            except Exception as e:
                print(f"❌ Error getting stats for {tenant_data['name']}: {e}")

def main():
    """Run the complete demo"""
    print("🚀 Multi-Tenant Log Platform Demo")
    print("=================================\n")
    
    # Check if backend is running
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code == 200:
            print("✅ Backend is running and healthy\n")
        else:
            print("❌ Backend health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend at {BASE_URL}")
        print("Please ensure the backend is running with: python backend/main.py")
        return
    
    # Create demo tenants
    tenants = create_demo_tenants()
    if not tenants:
        print("❌ No tenants created, exiting demo")
        return
    
    print(f"\n🔐 Authenticating {len(tenants)} tenants...")
    tokens = []
    for tenant_data in tenants:
        token = authenticate_tenant(tenant_data)
        tokens.append(token)
        if token:
            print(f"✅ Authenticated: {tenant_data['name']}")
    
    # Ingest logs for each tenant
    print(f"\n📝 Ingesting sample logs...")
    total_ingested = 0
    for tenant_data, token in zip(tenants, tokens):
        if token:
            ingested_count = ingest_logs_for_tenant(tenant_data, token)
            total_ingested += ingested_count
    
    print(f"\n✅ Total logs ingested: {total_ingested}")
    
    # Wait a moment for background processing
    print("\n⏳ Waiting for log processing...")
    time.sleep(3)
    
    # Demonstrate tenant isolation
    demonstrate_tenant_isolation(tenants, tokens)
    
    print("\n🎉 Demo completed successfully!")
    print("\n📱 You can now:")
    print(f"   - Open the frontend at http://localhost:3000")
    print(f"   - Login with any of the created tenants:")
    for tenant_data in tenants:
        print(f"     * Domain: {tenant_data['domain']}")
        print(f"       Username: {tenant_data['admin_username']}")
        print(f"       Password: {tenant_data['admin_password']}")

if __name__ == "__main__":
    main()
