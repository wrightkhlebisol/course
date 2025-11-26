"""
Generates synthetic log streams for testing
"""

import json
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pika
import logging

logger = logging.getLogger(__name__)


class LogGenerator:
    """Generates realistic log entries for testing"""
    
    SERVICES = ['api-gateway', 'auth-service', 'database', 'cache', 'payment']
    ENDPOINTS = ['/api/users', '/api/orders', '/api/products', '/api/payments']
    USERS = [f'user_{i}' for i in range(100)]
    
    def __init__(self, rabbitmq_config: Dict[str, Any]):
        self.config = rabbitmq_config
        self.connection = None
        self.channel = None
        
    def connect(self):
        """Connect to RabbitMQ"""
        credentials = pika.PlainCredentials(
            self.config['username'],
            self.config['password']
        )
        
        parameters = pika.ConnectionParameters(
            host=self.config['host'],
            port=self.config['port'],
            credentials=credentials
        )
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.config['queue'], durable=True)
        
        logger.info("✅ Log generator connected to RabbitMQ")
        
    def generate_auth_log(self, failed: bool = False) -> Dict[str, Any]:
        """Generate authentication log"""
        return {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'authentication',
            'user_id': random.choice(self.USERS),
            'status': 'failed' if failed else 'success',
            'service': 'auth-service',
            'ip_address': f"192.168.1.{random.randint(1, 255)}"
        }
        
    def generate_api_log(self, high_latency: bool = False) -> Dict[str, Any]:
        """Generate API call log"""
        base_latency = 50
        latency = random.randint(200, 500) if high_latency else random.randint(20, 100)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'api_call',
            'endpoint': random.choice(self.ENDPOINTS),
            'latency_ms': latency,
            'status_code': 200,
            'service': 'api-gateway'
        }
        
    def generate_error_log(self, service: str) -> Dict[str, Any]:
        """Generate error log"""
        return {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'error',
            'level': 'error',
            'service': service,
            'message': f'Error occurred in {service}',
            'error_code': f'ERR_{random.randint(1000, 9999)}'
        }
        
    def inject_auth_spike(self, user: str, count: int = 15):
        """Inject authentication spike pattern"""
        logger.info(f"💉 Injecting auth spike: {user} - {count} failures")
        for _ in range(count):
            log = self.generate_auth_log(failed=True)
            log['user_id'] = user
            self.publish(log)
            time.sleep(0.1)
            
    def inject_latency_spike(self, duration_seconds: int = 60):
        """Inject latency degradation pattern"""
        logger.info(f"💉 Injecting latency spike for {duration_seconds}s")
        end_time = time.time() + duration_seconds
        
        while time.time() < end_time:
            log = self.generate_api_log(high_latency=True)
            self.publish(log)
            time.sleep(0.5)
            
    def inject_cascading_failure(self):
        """Inject cascading failure pattern"""
        logger.info("💉 Injecting cascading failure across services")
        for service in random.sample(self.SERVICES, 3):
            for _ in range(5):
                log = self.generate_error_log(service)
                self.publish(log)
                time.sleep(0.2)
                
    def publish(self, log_entry: Dict[str, Any]):
        """Publish log to RabbitMQ"""
        self.channel.basic_publish(
            exchange='',
            routing_key=self.config['queue'],
            body=json.dumps(log_entry),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
    def generate_normal_traffic(self, duration_seconds: int = 300, rate: int = 10):
        """Generate normal log traffic"""
        logger.info(f"📊 Generating normal traffic: {rate} logs/sec for {duration_seconds}s")
        end_time = time.time() + duration_seconds
        count = 0
        
        while time.time() < end_time:
            # Mix of different log types
            log_type = random.choices(
                ['auth', 'api', 'error'],
                weights=[0.6, 0.3, 0.1]
            )[0]
            
            if log_type == 'auth':
                # 95% success rate
                log = self.generate_auth_log(failed=random.random() > 0.95)
            elif log_type == 'api':
                log = self.generate_api_log()
            else:
                log = self.generate_error_log(random.choice(self.SERVICES))
                
            self.publish(log)
            count += 1
            
            time.sleep(1.0 / rate)
            
        logger.info(f"✅ Generated {count} log entries")
        
    def close(self):
        """Close connection"""
        if self.connection and self.connection.is_open:
            self.connection.close()
