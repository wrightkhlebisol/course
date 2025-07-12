"""
Backpressure Management System
Implements adaptive flow control and intelligent load shedding
"""
import asyncio
import time
import math
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()

class PressureLevel(Enum):
    NORMAL = "normal"
    PRESSURE = "pressure"
    OVERLOAD = "overload"
    RECOVERY = "recovery"

@dataclass
class PressureMetrics:
    queue_depth_ratio: float
    processing_lag: float
    resource_utilization: float
    timestamp: float
    
    @property
    def pressure_score(self) -> float:
        """Calculate combined pressure score (0.0 to 1.0)"""
        return min(1.0, max(
            self.queue_depth_ratio,
            self.processing_lag / 10.0,  # Normalize lag to 0-1 scale
            self.resource_utilization
        ))

class BackpressureManager:
    """Manages system backpressure through adaptive flow control"""
    
    def __init__(self, metrics_collector):
        self.metrics_collector = metrics_collector
        self.current_level = PressureLevel.NORMAL
        self.pressure_history: List[PressureMetrics] = []
        self.throttle_rate = 1.0  # 1.0 = no throttling, 0.0 = full throttling
        
        # Configuration
        self.pressure_thresholds = {
            PressureLevel.NORMAL: 0.7,
            PressureLevel.PRESSURE: 0.85,
            PressureLevel.OVERLOAD: 0.95
        }
        
        self.recovery_thresholds = {
            PressureLevel.OVERLOAD: 0.8,
            PressureLevel.PRESSURE: 0.6,
            PressureLevel.NORMAL: 0.5
        }
        
        self.max_queue_size = 10000
        self.current_queue_size = 0
        self.processing_start_times: Dict[str, float] = {}
        
        # Background task
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start background monitoring"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_pressure())
        logger.info("Backpressure manager started")
    
    async def stop(self):
        """Stop background monitoring"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Backpressure manager stopped")
    
    async def _monitor_pressure(self):
        """Continuously monitor system pressure"""
        while self._running:
            try:
                metrics = await self._collect_pressure_metrics()
                await self._update_pressure_level(metrics)
                await self._adjust_throttle_rate(metrics)
                
                # Store metrics for history
                self.pressure_history.append(metrics)
                if len(self.pressure_history) > 100:
                    self.pressure_history.pop(0)
                
                await asyncio.sleep(1)  # Monitor every second
                
            except Exception as e:
                logger.error("Error in pressure monitoring", error=str(e))
                await asyncio.sleep(5)
    
    async def _collect_pressure_metrics(self) -> PressureMetrics:
        """Collect current pressure metrics"""
        # Queue depth ratio
        queue_depth_ratio = self.current_queue_size / self.max_queue_size
        
        # Processing lag (average time in queue)
        current_time = time.time()
        if self.processing_start_times:
            lags = [current_time - start_time for start_time in self.processing_start_times.values()]
            avg_lag = sum(lags) / len(lags)
        else:
            avg_lag = 0.0
        
        # Resource utilization (CPU + Memory)
        resource_util = await self.metrics_collector.get_resource_utilization()
        
        return PressureMetrics(
            queue_depth_ratio=queue_depth_ratio,
            processing_lag=avg_lag,
            resource_utilization=resource_util,
            timestamp=current_time
        )
    
    async def _update_pressure_level(self, metrics: PressureMetrics):
        """Update current pressure level based on metrics"""
        score = metrics.pressure_score
        old_level = self.current_level
        
        # State transition logic with hysteresis
        if self.current_level == PressureLevel.NORMAL:
            if score > self.pressure_thresholds[PressureLevel.NORMAL]:
                self.current_level = PressureLevel.PRESSURE
        
        elif self.current_level == PressureLevel.PRESSURE:
            if score > self.pressure_thresholds[PressureLevel.PRESSURE]:
                self.current_level = PressureLevel.OVERLOAD
            elif score < self.recovery_thresholds[PressureLevel.NORMAL]:
                self.current_level = PressureLevel.RECOVERY
        
        elif self.current_level == PressureLevel.OVERLOAD:
            if score < self.recovery_thresholds[PressureLevel.OVERLOAD]:
                self.current_level = PressureLevel.RECOVERY
        
        elif self.current_level == PressureLevel.RECOVERY:
            if score > self.pressure_thresholds[PressureLevel.PRESSURE]:
                self.current_level = PressureLevel.OVERLOAD
            elif score < self.recovery_thresholds[PressureLevel.NORMAL]:
                self.current_level = PressureLevel.NORMAL
        
        if old_level != self.current_level:
            logger.info(
                "Pressure level changed",
                old_level=old_level.value,
                new_level=self.current_level.value,
                pressure_score=score
            )
    
    async def _adjust_throttle_rate(self, metrics: PressureMetrics):
        """Adjust throttle rate based on pressure level"""
        score = metrics.pressure_score
        
        if self.current_level == PressureLevel.NORMAL:
            self.throttle_rate = 1.0
        elif self.current_level == PressureLevel.PRESSURE:
            # Gentle exponential reduction
            self.throttle_rate = max(0.5, 1.0 - (score - 0.7) * 2)
        elif self.current_level == PressureLevel.OVERLOAD:
            # Aggressive throttling
            self.throttle_rate = max(0.1, 0.5 - (score - 0.85) * 3)
        elif self.current_level == PressureLevel.RECOVERY:
            # Gradual recovery with exponential backoff
            recovery_rate = min(0.8, self.throttle_rate * 1.1)
            self.throttle_rate = recovery_rate
    
    async def should_accept_request(self) -> bool:
        """Determine if new request should be accepted"""
        if self.current_level == PressureLevel.NORMAL:
            return True
        
        # Probabilistic acceptance based on throttle rate
        import random
        return random.random() < self.throttle_rate
    
    async def enqueue_message(self, message_id: str) -> bool:
        """Attempt to enqueue a message"""
        if self.current_queue_size >= self.max_queue_size:
            return False
        
        self.current_queue_size += 1
        self.processing_start_times[message_id] = time.time()
        return True
    
    async def dequeue_message(self, message_id: str):
        """Remove message from processing queue"""
        if message_id in self.processing_start_times:
            del self.processing_start_times[message_id]
        self.current_queue_size = max(0, self.current_queue_size - 1)
    
    def get_current_status(self) -> Dict:
        """Get current backpressure status"""
        latest_metrics = self.pressure_history[-1] if self.pressure_history else None
        
        return {
            "pressure_level": self.current_level.value,
            "throttle_rate": self.throttle_rate,
            "queue_size": self.current_queue_size,
            "max_queue_size": self.max_queue_size,
            "pressure_score": latest_metrics.pressure_score if latest_metrics else 0.0,
            "metrics": {
                "queue_depth_ratio": latest_metrics.queue_depth_ratio if latest_metrics else 0.0,
                "processing_lag": latest_metrics.processing_lag if latest_metrics else 0.0,
                "resource_utilization": latest_metrics.resource_utilization if latest_metrics else 0.0
            } if latest_metrics else {}
        }
