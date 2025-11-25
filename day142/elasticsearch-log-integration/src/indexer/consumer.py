import asyncio
import json
import pika
from typing import Callable, Dict
import structlog

logger = structlog.get_logger()

class IndexingConsumer:
    """Consumes logs from RabbitMQ and sends to indexer"""
    
    def __init__(self, rabbitmq_config: Dict, indexer):
        self.config = rabbitmq_config
        self.indexer = indexer
        self.connection = None
        self.channel = None
        self.consuming = False
        
    def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.config['host'],
                    port=self.config['port']
                )
            )
            self.channel = self.connection.channel()
            
            # Declare exchange and queue
            self.channel.exchange_declare(
                exchange=self.config['exchange'],
                exchange_type='topic',
                durable=True
            )
            
            self.channel.queue_declare(
                queue=self.config['queue'],
                durable=True
            )
            
            self.channel.queue_bind(
                queue=self.config['queue'],
                exchange=self.config['exchange'],
                routing_key=self.config['routing_key']
            )
            
            logger.info("rabbitmq_connected", 
                       exchange=self.config['exchange'],
                       queue=self.config['queue'])
            return True
            
        except Exception as e:
            logger.error("rabbitmq_connection_failed", error=str(e))
            return False
    
    def start_consuming(self, callback: Callable):
        """Start consuming messages"""
        self.channel.basic_qos(prefetch_count=10)
        self.channel.basic_consume(
            queue=self.config['queue'],
            on_message_callback=callback,
            auto_ack=False
        )
        
        self.consuming = True
        logger.info("started_consuming", queue=self.config['queue'])
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop_consuming()
    
    def stop_consuming(self):
        """Stop consuming messages"""
        if self.channel and self.consuming:
            self.channel.stop_consuming()
            self.consuming = False
            logger.info("stopped_consuming")
    
    def close(self):
        """Close connection"""
        self.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("rabbitmq_closed")
