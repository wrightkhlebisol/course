#!/usr/bin/env python3
"""
Demo script showcasing the Execute functionality of the AI Troubleshooting Assistant
"""
import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

def demo_execute_functionality():
    """Demonstrate the execute functionality with different scenarios"""
    print("🚀 AI Troubleshooting Assistant - Execute Functionality Demo")
    print("=" * 70)
    
    # Demo 1: Database Connectivity Issue
    print("\n📊 Demo 1: Database Connectivity Issue")
    print("-" * 40)
    
    db_incident = {
        "title": "PostgreSQL Connection Pool Exhaustion",
        "description": "Database connection pool is exhausted, causing application timeouts",
        "error_type": "database_connectivity",
        "affected_service": "order-service",
        "severity": "high",
        "environment": "production",
        "logs": [
            "ERROR: No available connections in pool",
            "WARNING: Connection pool at 100% capacity",
            "Timeout waiting for available connection"
        ],
        "metrics": {"pool_usage": 1.0, "timeout_rate": 0.7}
    }
    
    # Get recommendations
    response = requests.post(f"{API_BASE_URL}/api/recommendations", json=db_incident)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found {len(result['recommendations'])} recommendations")
        
        # Execute the first recommendation
        if result['recommendations']:
            solution = result['recommendations'][0]['solution']
            print(f"🎯 Executing: {solution['title']}")
            print(f"📋 Description: {solution['description']}")
            
            # Execute the solution
            execute_response = requests.post(
                f"{API_BASE_URL}/api/execute",
                json={
                    "solution_id": solution['id'],
                    "incident_id": f"demo_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "environment": "production"
                }
            )
            
            if execute_response.status_code == 200:
                execution_result = execute_response.json()
                print(f"⚡ Execution completed in {execution_result['execution_time_ms']}ms")
                print(f"📊 Status: {execution_result['status']}")
                print(f"🎯 Success: {execution_result['success']}")
                
                # Show detailed execution steps
                print("\n📝 Execution Steps:")
                for step in execution_result['steps_executed']:
                    status_icon = "✅" if step['status'] == 'completed' else "❌"
                    print(f"   {status_icon} Step {step['step_number']}: {step['description']}")
                    print(f"      ⏱️  Duration: {step['execution_time_ms']}ms")
                    if step['logs']:
                        print(f"      📋 Logs: {step['logs'][0]}")  # Show first log
                    print()
    
    # Demo 2: Memory Exhaustion Issue
    print("\n📊 Demo 2: Memory Exhaustion Issue")
    print("-" * 40)
    
    memory_incident = {
        "title": "High Memory Usage in Microservice",
        "description": "Service consuming 98% of available memory, causing OOM errors",
        "error_type": "resource_exhaustion",
        "affected_service": "notification-service",
        "severity": "critical",
        "environment": "production",
        "logs": [
            "ERROR: OutOfMemoryError: Java heap space",
            "WARNING: Memory usage at 98%",
            "GC pressure detected, performance degraded"
        ],
        "metrics": {"memory_usage": 0.98, "gc_time": 0.3}
    }
    
    # Get recommendations
    response = requests.post(f"{API_BASE_URL}/api/recommendations", json=memory_incident)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found {len(result['recommendations'])} recommendations")
        
        # Execute the first recommendation
        if result['recommendations']:
            solution = result['recommendations'][0]['solution']
            print(f"🎯 Executing: {solution['title']}")
            print(f"📋 Description: {solution['description']}")
            
            # Execute the solution
            execute_response = requests.post(
                f"{API_BASE_URL}/api/execute",
                json={
                    "solution_id": solution['id'],
                    "incident_id": f"demo_mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "environment": "production"
                }
            )
            
            if execute_response.status_code == 200:
                execution_result = execute_response.json()
                print(f"⚡ Execution completed in {execution_result['execution_time_ms']}ms")
                print(f"📊 Status: {execution_result['status']}")
                print(f"🎯 Success: {execution_result['success']}")
                
                # Show execution logs
                print("\n📋 Execution Logs:")
                for log in execution_result['logs'][:5]:  # Show first 5 logs
                    print(f"   {log}")
    
    # Demo 3: SSL Certificate Issue
    print("\n📊 Demo 3: SSL Certificate Issue")
    print("-" * 40)
    
    ssl_incident = {
        "title": "SSL Certificate Expired",
        "description": "SSL certificate has expired, causing HTTPS connection failures",
        "error_type": "authentication_failure",
        "affected_service": "api-gateway",
        "severity": "critical",
        "environment": "production",
        "logs": [
            "ERROR: SSL certificate expired on 2024-01-20",
            "WARNING: Security alert - certificate invalid",
            "HTTPS connections failing for all endpoints"
        ],
        "metrics": {"ssl_errors": 1.0, "connection_failures": 0.95}
    }
    
    # Get recommendations
    response = requests.post(f"{API_BASE_URL}/api/recommendations", json=ssl_incident)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found {len(result['recommendations'])} recommendations")
        
        # Execute the first recommendation
        if result['recommendations']:
            solution = result['recommendations'][0]['solution']
            print(f"🎯 Executing: {solution['title']}")
            print(f"📋 Description: {solution['description']}")
            
            # Execute the solution
            execute_response = requests.post(
                f"{API_BASE_URL}/api/execute",
                json={
                    "solution_id": solution['id'],
                    "incident_id": f"demo_ssl_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "environment": "production"
                }
            )
            
            if execute_response.status_code == 200:
                execution_result = execute_response.json()
                print(f"⚡ Execution completed in {execution_result['execution_time_ms']}ms")
                print(f"📊 Status: {execution_result['status']}")
                print(f"🎯 Success: {execution_result['success']}")
                
                # Show step-by-step execution
                print("\n📝 Step-by-Step Execution:")
                for step in execution_result['steps_executed']:
                    status_icon = "✅" if step['status'] == 'completed' else "❌"
                    print(f"   {status_icon} Step {step['step_number']}: {step['description']}")
                    print(f"      ⏱️  Duration: {step['execution_time_ms']}ms")
                    print(f"      📊 Status: {step['status']}")
                    if step['logs']:
                        for log in step['logs']:
                            print(f"      📋 {log}")
                    print()

def demo_full_functionality():
    """Demonstrate the full functionality overview"""
    print("\n" + "=" * 70)
    print("🎯 Full Functionality Overview")
    print("=" * 70)
    
    print("\n📋 Available Features:")
    print("   1. 🧠 AI-Powered Incident Analysis")
    print("      - Natural language processing")
    print("      - Semantic similarity matching")
    print("      - Context-aware recommendations")
    print("      - Confidence scoring")
    
    print("\n   2. ⚡ Solution Execution Engine")
    print("      - One-click solution execution")
    print("      - Real-time step-by-step progress")
    print("      - Detailed execution logs")
    print("      - Success/failure tracking")
    
    print("\n   3. 📊 Learning & Improvement")
    print("      - Feedback collection system")
    print("      - Solution effectiveness tracking")
    print("      - Continuous model improvement")
    print("      - Performance analytics")
    
    print("\n   4. 🏢 Enterprise Features")
    print("      - Multi-environment support")
    print("      - Severity-based prioritization")
    print("      - Comprehensive logging")
    print("      - API integration ready")
    
    print("\n🔗 Access Points:")
    print(f"   🌐 Web Dashboard: http://localhost:5000")
    print(f"   📚 API Documentation: {API_BASE_URL}/docs")
    print(f"   🔍 Health Check: {API_BASE_URL}/health")
    
    print("\n💡 How to Use:")
    print("   1. Fill out the incident form with details about your issue")
    print("   2. Click 'Get AI Recommendations' to receive intelligent solutions")
    print("   3. Review the recommended solutions and their confidence scores")
    print("   4. Click 'Execute' on any solution to see the full resolution process")
    print("   5. Provide feedback to help improve future recommendations")

if __name__ == "__main__":
    demo_execute_functionality()
    demo_full_functionality()
    
    print("\n" + "=" * 70)
    print("🎉 Demo Complete! The AI Troubleshooting Assistant is ready to help!")
    print("=" * 70) 