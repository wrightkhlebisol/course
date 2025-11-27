"""
Log Generator - Creates realistic log entries for testing
"""
import random
import time
import json
from datetime import datetime
from typing import List, Dict

class LogGenerator:
    """Generate realistic log entries with metrics"""
    
    def __init__(self):
        self.services = ['api-gateway', 'user-service', 'payment-service', 'database']
        self.components = ['http-handler', 'auth', 'processor', 'cache']
        self.endpoints = ['/api/users', '/api/orders', '/api/products', '/api/payments']
        self.hosts = ['server-01', 'server-02', 'server-03']
    
    def generate_log(self) -> Dict:
        """Generate a single log entry with metrics"""
        service = random.choice(self.services)
        component = random.choice(self.components)
        endpoint = random.choice(self.endpoints)
        
        # Simulate realistic patterns
        response_time = random.gauss(150, 50)  # Normal distribution around 150ms
        if random.random() < 0.1:  # 10% slow requests
            response_time += random.uniform(200, 500)
        
        status_code = 200
        if random.random() < 0.05:  # 5% error rate
            status_code = random.choice([400, 404, 500, 503])
        
        return {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'component': component,
            'level': 'ERROR' if status_code >= 400 else 'INFO',
            'endpoint': endpoint,
            'response_time': max(1, response_time),
            'status_code': status_code,
            'cpu_usage': random.uniform(20, 80),
            'memory_usage': random.uniform(200, 800),
            'request_count': random.randint(1, 10),
            'host': random.choice(self.hosts)
        }
    
    def generate_batch(self, count: int = 100) -> List[Dict]:
        """Generate a batch of log entries"""
        return [self.generate_log() for _ in range(count)]
    
    def stream_logs(self, rate: int = 10, duration: int = 60):
        """Stream logs at specified rate"""
        total_generated = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            batch = self.generate_batch(rate)
            for log in batch:
                print(json.dumps(log))
                total_generated += 1
            
            time.sleep(1)
        
        return total_generated

if __name__ == '__main__':
    generator = LogGenerator()
    print(f"🔄 Generating test logs...")
    count = generator.stream_logs(rate=10, duration=10)
    print(f"✅ Generated {count} log entries")
