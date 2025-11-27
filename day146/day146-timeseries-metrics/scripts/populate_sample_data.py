#!/usr/bin/env python3
"""
Populate database with sample metrics data for dashboard visualization
"""
import os
import sys
import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_batch

# Database configuration - read from environment or use defaults
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'metrics'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

def generate_sample_data():
    """Generate sample metrics data for the last hour"""
    services = ['api-gateway', 'user-service', 'payment-service', 'database']
    components = ['http-handler', 'auth', 'processor', 'cache']
    endpoints = ['/api/users', '/api/orders', '/api/products', '/api/payments']
    hosts = ['server-01', 'server-02', 'server-03']
    
    # Generate data for the last hour, with 1-minute intervals
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    
    http_response_data = []
    http_status_data = []
    resource_usage_data = []
    
    # Generate data points every 10 seconds for the last hour (more dense data)
    current_time = one_hour_ago
    while current_time <= now:
        for service in services:
            # Generate multiple data points per service per time interval to simulate traffic
            for _ in range(random.randint(3, 8)):  # 3-8 requests per service per interval
            # Response time metrics
            base_response_time = random.gauss(150, 50)
            if random.random() < 0.1:  # 10% slow requests
                base_response_time += random.uniform(200, 500)
            response_time = max(1, base_response_time)
            
            http_response_data.append((
                current_time,
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
                current_time,
                service,
                random.choice(components),
                random.choice(endpoints),
                status_code,
                is_error,
                random.choice(hosts)
            ))
            
            # Resource usage metrics
            cpu_percent = random.uniform(20, 80)
            memory_mb = random.uniform(200, 800)
            
            resource_usage_data.append((
                current_time,
                service,
                random.choice(components),
                round(cpu_percent, 2),
                round(memory_mb, 2),
                random.choice(hosts)
            ))
        
        # Move to next 10 seconds
        current_time += timedelta(seconds=10)
    
    return http_response_data, http_status_data, resource_usage_data

def populate_database():
    """Insert sample data into the database"""
    try:
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("📊 Generating sample data...")
        http_response_data, http_status_data, resource_usage_data = generate_sample_data()
        
        print(f"📝 Inserting {len(http_response_data)} response time records...")
        execute_batch(cur, """
            INSERT INTO http_response (time, service, component, endpoint, response_time_ms, host)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, http_response_data)
        
        print(f"📝 Inserting {len(http_status_data)} status records...")
        execute_batch(cur, """
            INSERT INTO http_status (time, service, component, endpoint, status_code, is_error, host)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, http_status_data)
        
        print(f"📝 Inserting {len(resource_usage_data)} resource usage records...")
        execute_batch(cur, """
            INSERT INTO resource_usage (time, service, component, cpu_percent, memory_mb, host)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, resource_usage_data)
        
        conn.commit()
        conn.close()
        
        print("✅ Sample data populated successfully!")
        print(f"   - {len(http_response_data)} response time metrics")
        print(f"   - {len(http_status_data)} status metrics")
        print(f"   - {len(resource_usage_data)} resource usage metrics")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        sys.exit(1)

if __name__ == '__main__':
    populate_database()

