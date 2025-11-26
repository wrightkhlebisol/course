"""Generate synthetic log data for training"""
import json
import random
from datetime import datetime, timedelta

def generate_log_entry(timestamp, is_failure=False):
    """Generate realistic log entry"""
    services = ['web', 'api', 'database', 'cache', 'worker']
    components = ['auth', 'payment', 'user-service', 'order-service', 'inventory']
    levels = ['INFO', 'WARNING', 'ERROR', 'CRITICAL'] if is_failure else ['INFO', 'DEBUG']
    
    service = random.choice(services)
    component = random.choice(components)
    level = random.choice(levels)
    
    # Simulate anomalous patterns
    if is_failure:
        response_time = random.uniform(5000, 15000)
        error_count = random.randint(10, 100)
        cpu_usage = random.uniform(80, 99)
    else:
        response_time = random.uniform(50, 500)
        error_count = random.randint(0, 2)
        cpu_usage = random.uniform(20, 60)
    
    messages = {
        'INFO': [
            'Request processed successfully',
            'Database query completed',
            'Cache hit for user data'
        ],
        'ERROR': [
            'Database connection timeout',
            'Failed to process payment',
            'Service unavailable',
            'Memory allocation failed'
        ]
    }
    
    return {
        'timestamp': timestamp.isoformat(),
        'level': level,
        'service': service,
        'component': component,
        'message': random.choice(messages.get(level, messages['INFO'])),
        'metrics': {
            'response_time': response_time,
            'request_count': random.randint(10, 1000),
            'error_count': error_count,
            'cpu_usage': cpu_usage,
            'memory_usage': random.uniform(30, 90)
        },
        'is_failure': int(is_failure)
    }

def generate_dataset(num_samples=10000, failure_rate=0.1):
    """Generate training dataset"""
    logs = []
    start_time = datetime.now() - timedelta(days=30)
    
    for i in range(num_samples):
        timestamp = start_time + timedelta(minutes=i * 5)
        is_failure = random.random() < failure_rate
        logs.append(generate_log_entry(timestamp, is_failure))
    
    return logs

if __name__ == "__main__":
    print("Generating training data...")
    logs = generate_dataset(num_samples=10000, failure_rate=0.15)
    
    with open("data/processed/training_logs.json", "w") as f:
        json.dump(logs, f)
    
    print(f"✅ Generated {len(logs)} log entries")
    print(f"   Failure rate: {sum(log['is_failure'] for log in logs) / len(logs) * 100:.1f}%")
