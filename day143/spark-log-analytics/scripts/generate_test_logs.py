import json
import random
from datetime import datetime, timedelta
import os

def generate_log_entry(timestamp, services, endpoints):
    """Generate a single log entry"""
    service = random.choice(services)
    level = random.choices(
        ['INFO', 'WARN', 'ERROR', 'DEBUG'],
        weights=[70, 15, 10, 5]
    )[0]
    
    endpoint = random.choice(endpoints) if random.random() > 0.3 else None
    status_code = random.choice([200, 201, 400, 404, 500, 503])
    
    # Simulate correlation between errors and slow response times
    if level == 'ERROR':
        response_time = random.randint(1000, 5000)
    else:
        response_time = random.randint(10, 500)
    
    log = {
        'timestamp': timestamp.isoformat(),
        'level': level,
        'service': service,
        'message': f'{level} in {service}',
        'response_time': response_time,
        'status_code': status_code,
        'user_id': f'user_{random.randint(1, 1000)}',
        'endpoint': endpoint,
        'metadata': {
            'host': f'host-{random.randint(1, 10)}',
            'version': f'v{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}'
        }
    }
    
    return log

def generate_test_data(num_logs=100000, output_dir='data/input'):
    """Generate test log data"""
    print(f"Generating {num_logs} test log entries...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    services = ['api-gateway', 'user-service', 'order-service', 'payment-service', 'notification-service']
    endpoints = ['/api/users', '/api/orders', '/api/payments', '/api/products', '/api/checkout']
    
    # Generate logs over last 7 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    logs = []
    for i in range(num_logs):
        # Random timestamp in range
        random_seconds = random.randint(0, int((end_time - start_time).total_seconds()))
        timestamp = start_time + timedelta(seconds=random_seconds)
        
        log = generate_log_entry(timestamp, services, endpoints)
        logs.append(log)
        
        if (i + 1) % 10000 == 0:
            print(f"Generated {i + 1} logs...")
    
    # Write to JSON file
    output_file = f"{output_dir}/logs.json"
    with open(output_file, 'w') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')
    
    print(f"✓ Generated {num_logs} logs in {output_file}")
    
    # Generate statistics
    stats = {
        'total_logs': num_logs,
        'services': services,
        'time_range': {
            'start': start_time.isoformat(),
            'end': end_time.isoformat()
        },
        'level_distribution': {
            'INFO': sum(1 for log in logs if log['level'] == 'INFO'),
            'WARN': sum(1 for log in logs if log['level'] == 'WARN'),
            'ERROR': sum(1 for log in logs if log['level'] == 'ERROR'),
            'DEBUG': sum(1 for log in logs if log['level'] == 'DEBUG')
        }
    }
    
    print("\nDataset Statistics:")
    print(json.dumps(stats, indent=2))
    
    return output_file

if __name__ == '__main__':
    generate_test_data()
