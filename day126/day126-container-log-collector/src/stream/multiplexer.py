import asyncio
from typing import Dict, Set, Callable
from collections import deque
import logging
import time

logger = logging.getLogger(__name__)

class LogStreamMultiplexer:
    """Multiplexes logs from multiple sources to multiple consumers"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.log_queue = asyncio.Queue(maxsize=config.get('buffer_size', 1000))
        self.consumers: Set[Callable] = set()
        self.buffer = deque(maxlen=100)  # Keep recent logs
        self.stats = {
            'total_logs': 0,
            'logs_per_source': {},
            'dropped_logs': 0,
            'logs_per_second': 0
        }
        self.running = False
        self.log_timestamps = deque(maxlen=100)  # Track log timestamps for rate calculation
    
    async def add_log(self, log_entry: Dict):
        """Add log entry to multiplexer"""
        try:
            await self.log_queue.put(log_entry)
            self.buffer.append(log_entry)
            self.stats['total_logs'] += 1
            
            # Track timestamp for rate calculation
            current_time = time.time()
            self.log_timestamps.append(current_time)
            
            # Calculate logs per second (logs in last second)
            cutoff_time = current_time - 1.0
            while self.log_timestamps and self.log_timestamps[0] < cutoff_time:
                self.log_timestamps.popleft()
            self.stats['logs_per_second'] = len(self.log_timestamps)
            
            source = log_entry.get('source', 'unknown')
            self.stats['logs_per_source'][source] = \
                self.stats['logs_per_source'].get(source, 0) + 1
        except asyncio.QueueFull:
            self.stats['dropped_logs'] += 1
            logger.warning("Log buffer full, dropping log")
    
    def add_consumer(self, consumer_func: Callable):
        """Register a log consumer"""
        self.consumers.add(consumer_func)
    
    def remove_consumer(self, consumer_func: Callable):
        """Unregister a log consumer"""
        self.consumers.discard(consumer_func)
    
    async def start(self):
        """Start distributing logs to consumers"""
        self.running = True
        logger.info("Log multiplexer started")
        
        while self.running:
            try:
                log_entry = await asyncio.wait_for(
                    self.log_queue.get(),
                    timeout=1.0
                )
                
                # Distribute to all consumers
                for consumer in list(self.consumers):
                    try:
                        await consumer(log_entry)
                    except Exception as e:
                        logger.error(f"Consumer error: {e}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Multiplexer error: {e}")
    
    def get_recent_logs(self, count: int = 50) -> list:
        """Get recent log entries from buffer"""
        return list(self.buffer)[-count:]
    
    def get_stats(self) -> Dict:
        """Get multiplexer statistics"""
        return self.stats.copy()
    
    def stop(self):
        """Stop the multiplexer"""
        self.running = False
