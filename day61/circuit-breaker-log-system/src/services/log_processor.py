"""
Log processing service with circuit breaker integration
"""
import asyncio
import logging
import time
import random
from datetime import datetime
from typing import Dict, Any, List
import json

from src.circuit_breaker.core import CircuitBreaker, CircuitBreakerConfig, registry

logger = logging.getLogger(__name__)

class DatabaseService:
    """Simulated database service with failure injection"""
    
    def __init__(self, name: str, failure_rate: float = 0.1):
        self.name = name
        self.failure_rate = failure_rate
        self.is_down = False
        self.response_delay = 0.1
        
        # Register circuit breaker
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            timeout_duration=5.0
        )
        self.circuit_breaker = registry.register(f"database_{name}", config)
    
    def set_failure_rate(self, rate: float):
        """Set failure rate for testing"""
        self.failure_rate = rate
        logger.info(f"Database {self.name} failure rate set to {rate}")
    
    def set_down(self, down: bool):
        """Simulate database downtime"""
        self.is_down = down
        logger.info(f"Database {self.name} {'DOWN' if down else 'UP'}")
    
    def set_response_delay(self, delay: float):
        """Set response delay for testing"""
        self.response_delay = delay
        logger.info(f"Database {self.name} response delay set to {delay}s")
    
    @property
    def _should_fail(self) -> bool:
        """Determine if this call should fail"""
        if self.is_down:
            return True
        return random.random() < self.failure_rate
    
    def _execute_query(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """Simulate database query execution"""
        if self.response_delay > 0:
            time.sleep(self.response_delay)
        
        if self._should_fail:
            raise Exception(f"Database {self.name} connection failed")
        
        return {
            'query': query,
            'params': params or {},
            'timestamp': datetime.now().isoformat(),
            'database': self.name,
            'execution_time': self.response_delay
        }
    
    def insert_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert log entry with circuit breaker protection"""
        query = "INSERT INTO logs (timestamp, level, message, service) VALUES (?, ?, ?, ?)"
        params = {
            'timestamp': log_data.get('timestamp'),
            'level': log_data.get('level'),
            'message': log_data.get('message'),
            'service': log_data.get('service')
        }
        
        return self.circuit_breaker.call(self._execute_query, query, params)
    
    def get_logs(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get logs with circuit breaker protection"""
        query = "SELECT * FROM logs WHERE created_at > ?"
        params = filters or {}
        
        result = self.circuit_breaker.call(self._execute_query, query, params)
        # Simulate returning multiple log entries
        return [result] * random.randint(1, 5)

class MessageQueueService:
    """Simulated message queue service with circuit breaker"""
    
    def __init__(self, name: str, failure_rate: float = 0.05):
        self.name = name
        self.failure_rate = failure_rate
        self.is_down = False
        self.queue_delay = 0.05
        
        # Register circuit breaker
        config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=20,
            timeout_duration=3.0
        )
        self.circuit_breaker = registry.register(f"queue_{name}", config)
    
    def set_failure_rate(self, rate: float):
        """Set failure rate for testing"""
        self.failure_rate = rate
        logger.info(f"Queue {self.name} failure rate set to {rate}")
    
    def set_down(self, down: bool):
        """Simulate queue downtime"""
        self.is_down = down
        logger.info(f"Queue {self.name} {'DOWN' if down else 'UP'}")
    
    @property
    def _should_fail(self) -> bool:
        """Determine if this call should fail"""
        if self.is_down:
            return True
        return random.random() < self.failure_rate
    
    def _publish_message(self, topic: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate message publishing"""
        if self.queue_delay > 0:
            time.sleep(self.queue_delay)
        
        if self._should_fail:
            raise Exception(f"Message queue {self.name} publish failed")
        
        return {
            'topic': topic,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'queue': self.name,
            'message_id': f"msg_{random.randint(1000, 9999)}"
        }
    
    def publish_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish log with circuit breaker protection"""
        topic = f"logs.{log_data.get('service', 'unknown')}"
        return self.circuit_breaker.call(self._publish_message, topic, log_data)

class ExternalAPIService:
    """Simulated external API service with circuit breaker"""
    
    def __init__(self, name: str, failure_rate: float = 0.15):
        self.name = name
        self.failure_rate = failure_rate
        self.is_down = False
        self.api_delay = 0.2
        
        # Register circuit breaker with more conservative settings
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=60,
            timeout_duration=10.0
        )
        self.circuit_breaker = registry.register(f"api_{name}", config)
    
    def set_failure_rate(self, rate: float):
        """Set failure rate for testing"""
        self.failure_rate = rate
        logger.info(f"API {self.name} failure rate set to {rate}")
    
    def set_down(self, down: bool):
        """Simulate API downtime"""
        self.is_down = down
        logger.info(f"API {self.name} {'DOWN' if down else 'UP'}")
    
    @property
    def _should_fail(self) -> bool:
        """Determine if this call should fail"""
        if self.is_down:
            return True
        return random.random() < self.failure_rate
    
    def _make_api_call(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate API call"""
        if self.api_delay > 0:
            time.sleep(self.api_delay)
        
        if self._should_fail:
            raise Exception(f"API {self.name} call failed")
        
        return {
            'endpoint': endpoint,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'api': self.name,
            'status': 'success',
            'response_time': self.api_delay
        }
    
    def enrich_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich log data with external API call"""
        endpoint = "/api/v1/enrich"
        return self.circuit_breaker.call(self._make_api_call, endpoint, log_data)

class LogProcessorService:
    """Main log processor with circuit breaker protection"""
    
    def __init__(self):
        self.database = DatabaseService("primary")
        self.backup_database = DatabaseService("backup")
        self.message_queue = MessageQueueService("main")
        self.external_api = ExternalAPIService("enrichment")
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'fallback_responses': 0,
            'start_time': datetime.now()
        }
    
    def process_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process log entry with circuit breaker protection"""
        result = {
            'original_log': log_data,
            'processed_at': datetime.now().isoformat(),
            'processing_steps': [],
            'fallbacks_used': []
        }
        
        try:
            # Step 1: Store in primary database
            try:
                db_result = self.database.insert_log(log_data)
                result['processing_steps'].append({
                    'step': 'database_insert',
                    'status': 'success',
                    'details': db_result
                })
            except Exception as e:
                # Fallback to backup database
                try:
                    backup_result = self.backup_database.insert_log(log_data)
                    result['processing_steps'].append({
                        'step': 'database_insert',
                        'status': 'fallback_success',
                        'details': backup_result
                    })
                    result['fallbacks_used'].append('backup_database')
                    self.stats['fallback_responses'] += 1
                except Exception as backup_e:
                    result['processing_steps'].append({
                        'step': 'database_insert',
                        'status': 'failed',
                        'error': str(backup_e)
                    })
                    # Continue processing even if storage fails
            
            # Step 2: Publish to message queue
            try:
                queue_result = self.message_queue.publish_log(log_data)
                result['processing_steps'].append({
                    'step': 'message_queue_publish',
                    'status': 'success',
                    'details': queue_result
                })
            except Exception as e:
                result['processing_steps'].append({
                    'step': 'message_queue_publish',
                    'status': 'failed',
                    'error': str(e)
                })
                # Continue processing even if queue fails
            
            # Step 3: Enrich with external API (optional)
            try:
                api_result = self.external_api.enrich_log(log_data)
                result['processing_steps'].append({
                    'step': 'external_enrichment',
                    'status': 'success',
                    'details': api_result
                })
                result['enriched_data'] = api_result
            except Exception as e:
                result['processing_steps'].append({
                    'step': 'external_enrichment',
                    'status': 'failed',
                    'error': str(e)
                })
                # Provide fallback enrichment
                result['enriched_data'] = {
                    'fallback': True,
                    'enrichment_status': 'unavailable',
                    'timestamp': datetime.now().isoformat()
                }
                result['fallbacks_used'].append('enrichment_fallback')
                self.stats['fallback_responses'] += 1
            
            # Update statistics
            self.stats['total_processed'] += 1
            successful_steps = sum(1 for step in result['processing_steps'] if step['status'] in ['success', 'fallback_success'])
            if successful_steps > 0:
                self.stats['successful_processed'] += 1
            else:
                self.stats['failed_processed'] += 1
            
            result['processing_status'] = 'completed'
            return result
            
        except Exception as e:
            self.stats['total_processed'] += 1
            self.stats['failed_processed'] += 1
            result['processing_status'] = 'failed'
            result['error'] = str(e)
            return result
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        uptime = datetime.now() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_seconds': uptime.total_seconds(),
            'processing_rate': self.stats['total_processed'] / max(uptime.total_seconds(), 1),
            'success_rate': (self.stats['successful_processed'] / max(self.stats['total_processed'], 1)) * 100
        }
    
    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """Get all circuit breaker statistics"""
        return registry.get_all_stats()
    
    def simulate_failures(self, duration: int = 30):
        """Simulate various failure scenarios for testing"""
        logger.info(f"Starting failure simulation for {duration} seconds")
        
        # Simulate database issues
        self.database.set_failure_rate(0.3)
        
        # Simulate API downtime
        self.external_api.set_down(True)
        
        # Wait for specified duration
        time.sleep(duration)
        
        # Restore normal operation
        self.database.set_failure_rate(0.1)
        self.external_api.set_down(False)
        
        logger.info("Failure simulation completed")
