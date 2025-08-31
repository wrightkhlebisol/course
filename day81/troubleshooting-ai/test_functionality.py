#!/usr/bin/env python3
"""
Test script to demonstrate the AI Troubleshooting Assistant functionality
"""
import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
WEB_BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test API health endpoint"""
    print("🔍 Testing API Health Check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ API health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_get_stats():
    """Test getting system statistics"""
    print("\n📊 Testing System Statistics...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistics retrieved successfully!")
            print(f"   Total Incidents: {stats.get('total_incidents', 0)}")
            print(f"   Total Solutions: {stats.get('total_solutions', 0)}")
            print(f"   Model Status: {stats.get('model_status', 'Unknown')}")
            print(f"   Average Effectiveness: {stats.get('average_solution_effectiveness', 0):.2%}")
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats error: {e}")

def test_incident_recommendations():
    """Test incident submission and recommendations"""
    print("\n🚨 Testing Incident Recommendations...")
    
    # Test incident data
    test_incidents = [
        {
            "title": "Database Connection Issues",
            "description": "Application cannot connect to PostgreSQL database, getting timeout errors",
            "error_type": "database_connectivity",
            "affected_service": "user-service",
            "severity": "high",
            "environment": "production",
            "logs": [
                "ERROR: connection to server on socket timeout",
                "SQLSTATE: 08006 connection failure",
                "Connection attempt failed after 30 seconds"
            ],
            "metrics": {"response_time": 30000, "error_rate": 0.8}
        },
        {
            "title": "Memory Leak in API Gateway",
            "description": "API gateway service consuming excessive memory, causing performance issues",
            "error_type": "resource_exhaustion",
            "affected_service": "api-gateway",
            "severity": "medium",
            "environment": "production",
            "logs": [
                "WARNING: Memory usage at 92%",
                "GC pressure detected in thread pool",
                "OutOfMemoryError in worker threads"
            ],
            "metrics": {"memory_usage": 0.92, "cpu_usage": 0.75}
        },
        {
            "title": "SSL Certificate Expiration",
            "description": "SSL certificate has expired, causing HTTPS connection failures",
            "error_type": "authentication_failure",
            "affected_service": "web-frontend",
            "severity": "critical",
            "environment": "production",
            "logs": [
                "ERROR: SSL certificate expired on 2024-01-15",
                "WARNING: Security alert - certificate invalid",
                "HTTPS connections failing for all users"
            ],
            "metrics": {"ssl_errors": 1.0, "connection_failures": 0.95}
        }
    ]
    
    for i, incident in enumerate(test_incidents, 1):
        print(f"\n   Testing Incident {i}: {incident['title']}")
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/recommendations",
                json=incident,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Recommendations received in {result['processing_time_ms']}ms")
                print(f"   📋 Found {len(result['recommendations'])} recommendations")
                
                for j, rec in enumerate(result['recommendations'], 1):
                    solution = rec['solution']
                    confidence = rec['confidence_score']
                    print(f"      {j}. {solution['title']} (Confidence: {confidence:.1%})")
                
                # Test execution of first recommendation
                if result['recommendations']:
                    test_execute_solution(result['recommendations'][0]['solution']['id'], incident)
                
            else:
                print(f"   ❌ Failed to get recommendations: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_execute_solution(solution_id, incident_data):
    """Test solution execution"""
    print(f"\n   ⚡ Testing Solution Execution for: {solution_id}")
    try:
        execution_data = {
            "solution_id": solution_id,
            "incident_id": f"test_inc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "environment": incident_data.get("environment", "production")
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/execute",
            json=execution_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Execution completed in {result['execution_time_ms']}ms")
            print(f"   📊 Status: {result['status']}")
            print(f"   🎯 Success: {result['success']}")
            print(f"   📝 Steps executed: {len(result['steps_executed'])}")
            
            # Show execution details
            for step in result['steps_executed']:
                status_icon = "✅" if step['status'] == 'completed' else "❌"
                print(f"      {status_icon} Step {step['step_number']}: {step['description']}")
            
            # Show some logs
            if result['logs']:
                print(f"   📋 Sample logs:")
                for log in result['logs'][:3]:  # Show first 3 logs
                    print(f"      {log}")
                
        else:
            print(f"   ❌ Execution failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Execution error: {e}")

def test_feedback():
    """Test feedback submission"""
    print("\n💬 Testing Feedback Submission...")
    
    feedback_data = {
        "incident_id": "test_inc_001",
        "solution_id": "sol_001",
        "was_helpful": True,
        "resolution_time": 15,
        "comments": "This solution worked perfectly for our database connectivity issue"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/feedback",
            json=feedback_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Feedback submitted successfully!")
            print(f"   Response: {result}")
        else:
            print(f"❌ Feedback submission failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Feedback error: {e}")

def test_web_dashboard():
    """Test web dashboard accessibility"""
    print("\n🌐 Testing Web Dashboard...")
    try:
        response = requests.get(f"{WEB_BASE_URL}/")
        if response.status_code == 200:
            print("✅ Web dashboard is accessible!")
            print(f"   Dashboard URL: {WEB_BASE_URL}")
            print(f"   API Documentation: {API_BASE_URL}/docs")
        else:
            print(f"❌ Dashboard not accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

def main():
    """Run all tests"""
    print("🚀 AI Troubleshooting Assistant - Functionality Test")
    print("=" * 60)
    
    # Test basic functionality
    test_health_check()
    test_get_stats()
    
    # Test core features
    test_incident_recommendations()
    test_feedback()
    
    # Test web interface
    test_web_dashboard()
    
    print("\n" + "=" * 60)
    print("🎉 Testing Complete!")
    print("\n📋 Summary of Features Tested:")
    print("   ✅ API Health Check")
    print("   ✅ System Statistics")
    print("   ✅ Incident Recommendations")
    print("   ✅ Solution Execution")
    print("   ✅ Feedback Submission")
    print("   ✅ Web Dashboard Access")
    print("\n🔗 Access Points:")
    print(f"   Web Dashboard: {WEB_BASE_URL}")
    print(f"   API Documentation: {API_BASE_URL}/docs")
    print(f"   Health Check: {API_BASE_URL}/health")

if __name__ == "__main__":
    main() 