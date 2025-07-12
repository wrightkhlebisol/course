"""
Log Processing Engine with Backpressure Integration
"""
import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional
from enum import Enum
import structlog

logger = structlog.get_logger()

class LogPriority(Enum):
    CRITICAL = 1    # Error logs, security events (never dropped)
    HIGH = 2        # Business-critical logs (dropped last)
    NORMAL = 3      # Standard application logs
    LOW = 4         # Debug and trace logs (dropped first)

class LogMessage:
    def __init__(self, content: str, priority: LogPriority = LogPriority.NORMAL, 
                 source: str = "unknown", timestamp: Optional[float] = None):
        self.id = str(uuid.uuid4())
        self.content = content
        self.priority = priority
        self.source = source
        self.timestamp = timestamp or time.time()
        self.processing_start = None
        self.processing_end = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "priority": self.priority.name,
            "source": self.source,
            "timestamp": self.timestamp,
            "processing_time": self.processing_end - self.processing_start if self.processing_end else None
        }

class LogProcessor:
    """Main log processing engine with backpressure awareness"""
    
    def __init__(self, backpressure_manager, circuit_breaker, metrics_collector):
        self.backpressure_manager = backpressure_manager
        self.circuit_breaker = circuit_breaker
        self.metrics_collector = metrics_collector
        
        # Processing queues by priority
        self.priority_queues = {
            LogPriority.CRITICAL: asyncio.Queue(maxsize=1000),
            LogPriority.HIGH: asyncio.Queue(maxsize=2000),
            LogPriority.NORMAL: asyncio.Queue(maxsize=5000),
            LogPriority.LOW: asyncio.Queue(maxsize=2000)
        }
        
        # Statistics
        self.processed_count = 0
        self.dropped_count = 0
        self.error_count = 0
        
        # Worker pool
        self.workers: List[asyncio.Task] = []
        self.worker_count = 4
        self._running = False
    
    async def start(self):
        """Start processing workers"""
        self._running = True
        
        # Start worker tasks
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Started {self.worker_count} log processing workers")
    
    async def stop(self):
        """Stop all workers"""
        self._running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("All log processing workers stopped")
    
    async def submit_log(self, content: str, priority: LogPriority = LogPriority.NORMAL, 
                        source: str = "api") -> Dict:
        """Submit a log message for processing"""
        message = LogMessage(content, priority, source)
        
        # Check if we should accept this message
        if not await self.backpressure_manager.should_accept_request():
            self.dropped_count += 1
            await self.metrics_collector.increment_counter("logs_dropped_backpressure")
            return {
                "status": "dropped",
                "reason": "backpressure",
                "message_id": message.id
            }
        
        # Try to enqueue in backpressure manager
        if not await self.backpressure_manager.enqueue_message(message.id):
            self.dropped_count += 1
            await self.metrics_collector.increment_counter("logs_dropped_queue_full")
            return {
                "status": "dropped",
                "reason": "queue_full",
                "message_id": message.id
            }
        
        # Attempt to add to priority queue
        try:
            queue = self.priority_queues[priority]
            queue.put_nowait(message)
            await self.metrics_collector.increment_counter("logs_accepted")
            
            return {
                "status": "accepted",
                "message_id": message.id,
                "queue_size": queue.qsize()
            }
            
        except asyncio.QueueFull:
            # Apply intelligent dropping based on priority
            dropped = await self._apply_intelligent_dropping(message)
            await self.backpressure_manager.dequeue_message(message.id)
            
            if dropped:
                self.dropped_count += 1
                await self.metrics_collector.increment_counter("logs_dropped_priority")
                return {
                    "status": "dropped",
                    "reason": "priority_queue_full",
                    "message_id": message.id
                }
            else:
                return {
                    "status": "accepted",
                    "message_id": message.id,
                    "queue_size": queue.qsize()
                }
    
    async def _apply_intelligent_dropping(self, new_message: LogMessage) -> bool:
        """Apply intelligent dropping strategy"""
        # Never drop critical messages
        if new_message.priority == LogPriority.CRITICAL:
            return False
        
        # Try to drop lower priority messages to make room
        for priority in [LogPriority.LOW, LogPriority.NORMAL, LogPriority.HIGH]:
            if priority.value >= new_message.priority.value:
                break
                
            queue = self.priority_queues[priority]
            if not queue.empty():
                try:
                    # Drop one message from lower priority queue
                    dropped_msg = queue.get_nowait()
                    await self.backpressure_manager.dequeue_message(dropped_msg.id)
                    
                    # Add new message
                    new_queue = self.priority_queues[new_message.priority]
                    new_queue.put_nowait(new_message)
                    
                    logger.info(
                        "Intelligent drop applied",
                        dropped_priority=priority.name,
                        accepted_priority=new_message.priority.name
                    )
                    return False  # New message was accepted
                    
                except asyncio.QueueEmpty:
                    continue
        
        return True  # Message was dropped
    
    async def _worker(self, worker_id: str):
        """Worker process for handling log messages"""
        logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Process messages in priority order
                message = await self._get_next_message()
                
                if message:
                    await self._process_message(message, worker_id)
                else:
                    # No messages available, short sleep
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Worker {worker_id} error", error=str(e))
                self.error_count += 1
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _get_next_message(self) -> Optional[LogMessage]:
        """Get next message in priority order"""
        # Check queues in priority order
        for priority in [LogPriority.CRITICAL, LogPriority.HIGH, LogPriority.NORMAL, LogPriority.LOW]:
            queue = self.priority_queues[priority]
            try:
                return queue.get_nowait()
            except asyncio.QueueEmpty:
                continue
        
        return None
    
    async def _process_message(self, message: LogMessage, worker_id: str):
        """Process a single log message"""
        message.processing_start = time.time()
        
        try:
            # Circuit breaker check
            if not await self.circuit_breaker.should_allow_request():
                raise Exception("Circuit breaker open")
            
            # Simulate processing work (adaptive based on system pressure)
            pressure_status = self.backpressure_manager.get_current_status()
            base_delay = 0.1  # Base processing time
            
            # Adjust processing time based on pressure
            if pressure_status["pressure_level"] == "overload":
                # Process faster during overload
                delay = base_delay * 0.5
            elif pressure_status["pressure_level"] == "pressure":
                # Normal processing
                delay = base_delay
            else:
                # Can afford more thorough processing
                delay = base_delay * 1.5
            
            await asyncio.sleep(delay)
            
            # Record success
            await self.circuit_breaker.record_success()
            self.processed_count += 1
            await self.metrics_collector.increment_counter("logs_processed_success")
            
            message.processing_end = time.time()
            
            logger.info(
                "Log processed",
                message_id=message.id,
                priority=message.priority.name,
                worker=worker_id,
                processing_time=message.processing_end - message.processing_start
            )
            
        except Exception as e:
            # Record failure
            await self.circuit_breaker.record_failure()
            self.error_count += 1
            await self.metrics_collector.increment_counter("logs_processed_error")
            
            logger.error(
                "Log processing failed",
                message_id=message.id,
                error=str(e),
                worker=worker_id
            )
        
        finally:
            # Remove from backpressure tracking
            await self.backpressure_manager.dequeue_message(message.id)
    
    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        total_queue_size = sum(queue.qsize() for queue in self.priority_queues.values())
        
        return {
            "processed_count": self.processed_count,
            "dropped_count": self.dropped_count,
            "error_count": self.error_count,
            "total_queue_size": total_queue_size,
            "queue_sizes": {
                priority.name: queue.qsize() 
                for priority, queue in self.priority_queues.items()
            },
            "worker_count": len(self.workers)
        }
