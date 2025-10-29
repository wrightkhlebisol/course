"""Log Batch Processor and Sender"""
import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from asyncio import Queue
import aiohttp
import structlog


class LogBatch:
    def __init__(self, max_size: int = 100, max_age: float = 5.0):
        self.logs: List[Dict[str, Any]] = []
        self.max_size = max_size
        self.max_age = max_age
        self.created_at = time.time()
        self.total_size = 0
    
    def add_log(self, log_entry) -> bool:
        """Add log to batch, return True if batch is full"""
        log_dict = {
            'timestamp': log_entry.timestamp,
            'content': log_entry.content,
            'source_path': log_entry.source_path,
            'log_type': log_entry.log_type,
            'metadata': log_entry.metadata,
            'size': log_entry.size
        }
        
        self.logs.append(log_dict)
        self.total_size += log_entry.size
        
        return len(self.logs) >= self.max_size
    
    def is_ready(self) -> bool:
        """Check if batch is ready for sending"""
        return (len(self.logs) >= self.max_size or 
                time.time() - self.created_at >= self.max_age)
    
    def is_empty(self) -> bool:
        """Check if batch is empty"""
        return len(self.logs) == 0


class BatchProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = structlog.get_logger("batch_processor")
        
        # Configuration
        collector_config = config.get('collector', {})
        self.batch_size = collector_config.get('batch_size', 100)
        self.batch_timeout = collector_config.get('batch_timeout', 2.0)
        
        output_config = config.get('output', {})
        self.endpoint = output_config.get('endpoint', 'http://localhost:8080/api/logs')
        self.timeout = output_config.get('timeout', 30)
        self.retry_attempts = output_config.get('retry_attempts', 3)
        
        # State
        self.current_batch = LogBatch(self.batch_size, self.batch_timeout)
        self.stats = {
            'batches_sent': 0,
            'logs_sent': 0,
            'bytes_sent': 0,
            'send_errors': 0,
            'last_send_time': None,
            'last_batch_size': 0
        }
        
    async def start_processing(self, log_queue: Queue) -> None:
        """Start processing logs from queue"""
        self.logger.info("Starting batch processor", 
                        endpoint=self.endpoint, batch_size=self.batch_size)
        
        # Start background sender
        sender_task = asyncio.create_task(self._batch_sender())
        
        try:
            while True:
                try:
                    # Get log from queue with timeout
                    log_entry = await asyncio.wait_for(log_queue.get(), timeout=1.0)
                    
                    # Add to current batch
                    if self.current_batch.add_log(log_entry):
                        # Batch is full, queue it for sending
                        await self._queue_batch_for_sending()
                    
                except asyncio.TimeoutError:
                    # Check if current batch should be sent due to age
                    if self.current_batch.is_ready() and not self.current_batch.is_empty():
                        await self._queue_batch_for_sending()
                
        except Exception as e:
            self.logger.error("Processing error", error=str(e))
        finally:
            sender_task.cancel()
    
    async def _queue_batch_for_sending(self) -> None:
        """Queue current batch for sending and create new batch"""
        if not self.current_batch.is_empty():
            # Send current batch in background
            asyncio.create_task(self._send_batch(self.current_batch))
            
            # Create new batch
            self.current_batch = LogBatch(self.batch_size, self.batch_timeout)
    
    async def _batch_sender(self) -> None:
        """Background task to send aged batches"""
        while True:
            await asyncio.sleep(1.0)
            
            if self.current_batch.is_ready() and not self.current_batch.is_empty():
                await self._queue_batch_for_sending()
    
    async def _send_batch(self, batch: LogBatch) -> None:
        """Send batch to configured endpoint"""
        payload = {
            'collector_id': self.config.get('collector', {}).get('name', 'linux-collector'),
            'collector_version': self.config.get('collector', {}).get('version', '1.0.0'),
            'batch_id': f"batch_{int(time.time() * 1000)}",
            'timestamp': time.time(),
            'logs': batch.logs,
            'stats': {
                'log_count': len(batch.logs),
                'total_size': batch.total_size,
                'batch_age': time.time() - batch.created_at
            }
        }
        
        for attempt in range(self.retry_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.endpoint,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                        headers={'Content-Type': 'application/json'}
                    ) as response:
                        if response.status == 200:
                            self.stats['batches_sent'] += 1
                            self.stats['logs_sent'] += len(batch.logs)
                            self.stats['bytes_sent'] += batch.total_size
                            self.stats['last_send_time'] = time.time()
                            self.stats['last_batch_size'] = len(batch.logs)
                            
                            self.logger.debug("Batch sent successfully", 
                                           logs=len(batch.logs), 
                                           size=batch.total_size,
                                           attempt=attempt + 1)
                            return
                        else:
                            self.logger.warning("Send failed", 
                                              status=response.status, 
                                              attempt=attempt + 1)
                            
            except Exception as e:
                self.logger.warning("Send error", 
                                  error=str(e), 
                                  attempt=attempt + 1)
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All attempts failed
        self.stats['send_errors'] += 1
        self.logger.error("Failed to send batch after all attempts", 
                         logs=len(batch.logs))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return dict(self.stats)
