#!/usr/bin/env python3
"""
Continuously generate real-time metrics data for dashboard visualization
Run this in the background to simulate live metrics
"""
import os
import sys
import time
import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_batch

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'metrics'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

def generate_metrics_batch():
    """Generate a batch of current metrics"""
    services = ['api-gateway', 'user-service', 'payment-service', 'database']
    components = ['http-handler', 'auth', 'processor', 'cache']
    endpoints = ['/api/users', '/api/orders', '/api/products', '/api/payments']
    hosts = ['server-01', 'server-02', 'server-03']
    
    now = datetime.now()
    
    http_response_data = []
    http_status_data = []
    resource_usage_data = []
    
    # Generate multiple data points per service to simulate traffic
    for service in services:
        for _ in range(random.randint(5, 15)):  # 5-15 requests per service
            # Response time metrics
            base_response_time = random.gauss(150, 50)
            if random.random() < 0.1:  # 10% slow requests
                base_response_time += random.uniform(200, 500)
            response_time = max(1, base_response_time)
            
            http_response_data.append((
                now,
                service,
                random.choice(components),
                random.choice(endpoints),
                round(response_time, 2),
                random.choice(hosts)
            ))
            
            # Status metrics
            status_code = 200
            is_error = 0
            if random.random() < 0.05:  # 5% error rate
                status_code = random.choice([400, 404, 500, 503])
                is_error = 1
            
            http_status_data.append((
                now,
                service,
                random.choice(components),
                random.choice(endpoints),
                status_code,
                is_error,
                random.choice(hosts)
            ))
        
        # Resource usage (one per service per batch)
        cpu_percent = random.uniform(20, 80)
        memory_mb = random.uniform(200, 800)
        
        resource_usage_data.append((
            now,
            service,
            random.choice(components),
            round(cpu_percent, 2),
            round(memory_mb, 2),
            random.choice(hosts)
        ))
    
    return http_response_data, http_status_data, resource_usage_data

def insert_metrics(http_response_data, http_status_data, resource_usage_data):
    """Insert metrics into database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        if http_response_data:
            execute_batch(cur, """
                INSERT INTO http_response (time, service, component, endpoint, response_time_ms, host)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, http_response_data)
        
        if http_status_data:
            execute_batch(cur, """
                INSERT INTO http_status (time, service, component, endpoint, status_code, is_error, host)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, http_status_data)
        
        if resource_usage_data:
            execute_batch(cur, """
                INSERT INTO resource_usage (time, service, component, cpu_percent, memory_mb, host)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, resource_usage_data)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error inserting metrics: {e}")
        return False

def run_continuous_generation(interval=5):
    """Continuously generate metrics at specified interval (seconds)"""
    print(f"🔄 Starting continuous metrics generation (every {interval} seconds)...")
    print("   Press Ctrl+C to stop")
    
    batch_count = 0
    try:
        while True:
            batch_count += 1
            http_response, http_status, resource_usage = generate_metrics_batch()
            
            if insert_metrics(http_response, http_status, resource_usage):
                print(f"✅ Batch {batch_count}: Inserted {len(http_response)} responses, {len(http_status)} statuses, {len(resource_usage)} resource metrics")
            else:
                print(f"❌ Batch {batch_count}: Failed to insert metrics")
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n🛑 Stopped after {batch_count} batches")

if __name__ == '__main__':
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    run_continuous_generation(interval)

