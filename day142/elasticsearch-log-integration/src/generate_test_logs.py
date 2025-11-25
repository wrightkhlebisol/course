import json
import random
import pika
from datetime import datetime, timedelta

class LogGenerator:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost', 5672)
        )
        self.channel = self.connection.channel()
        
        self.channel.exchange_declare(
            exchange='logs_topic',
            exchange_type='topic',
            durable=True
        )
        
        self.services = ['api', 'database', 'auth', 'payment']
        self.levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
        self.messages = [
            'User login successful',
            'Database query executed',
            'Payment processed',
            'Authentication failed',
            'Connection timeout',
            'Invalid request format',
            'Cache miss',
            'Rate limit exceeded'
        ]
    
    def generate_log(self) -> dict:
        service = random.choice(self.services)
        level = random.choice(self.levels)
        
        return {
            'timestamp': (datetime.now() - timedelta(
                minutes=random.randint(0, 60)
            )).isoformat(),
            'level': level,
            'service': service,
            'component': f'{service}_handler',
            'message': random.choice(self.messages),
            'metadata': {
                'response_time': random.randint(10, 500),
                'status_code': random.choice([200, 400, 404, 500]),
                'user_id': f'user_{random.randint(1000, 9999)}'
            },
            'tags': [service, level.lower()]
        }
    
    def send_logs(self, count: int = 100):
        print(f"Generating {count} test logs...")
        
        for i in range(count):
            log = self.generate_log()
            routing_key = f"logs.{log['service']}.{log['level'].lower()}"
            
            self.channel.basic_publish(
                exchange='logs_topic',
                routing_key=routing_key,
                body=json.dumps(log)
            )
            
            if (i + 1) % 10 == 0:
                print(f"Sent {i + 1}/{count} logs")
        
        print(f"✅ Successfully sent {count} logs")
        self.connection.close()

if __name__ == "__main__":
    generator = LogGenerator()
    generator.send_logs(100)
