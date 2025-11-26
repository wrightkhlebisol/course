"""
RabbitMQ source for Flink stream processing
"""

import json
import pika
import logging
from typing import Callable, Dict, Any
import threading

logger = logging.getLogger(__name__)


class RabbitMQSource:
    """Consumes log messages from RabbitMQ"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.channel = None
        self.running = False
        
    def connect(self):
        """Establish connection to RabbitMQ"""
        credentials = pika.PlainCredentials(
            self.config['username'],
            self.config['password']
        )
        
        parameters = pika.ConnectionParameters(
            host=self.config['host'],
            port=self.config['port'],
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Declare queue
        self.channel.queue_declare(queue=self.config['queue'], durable=True)
        
        logger.info(f"✅ Connected to RabbitMQ: {self.config['host']}:{self.config['port']}")
        
    def consume(self, callback: Callable[[Dict], None]):
        """Start consuming messages"""
        self.running = True
        
        def on_message(ch, method, properties, body):
            try:
                log_entry = json.loads(body)
                callback(log_entry)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
        self.channel.basic_qos(prefetch_count=10)
        self.channel.basic_consume(
            queue=self.config['queue'],
            on_message_callback=on_message
        )
        
        logger.info(f"📥 Starting to consume from queue: {self.config['queue']}")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop()
            
    def stop(self):
        """Stop consuming and close connection"""
        self.running = False
        if self.channel and self.channel.is_open:
            self.channel.stop_consuming()
        if self.connection and self.connection.is_open:
            self.connection.close()
        logger.info("🛑 RabbitMQ source stopped")
