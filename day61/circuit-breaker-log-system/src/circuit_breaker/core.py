"""
Advanced Circuit Breaker Implementation with State Management
"""
import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional, Dict, Any
import logging
from dataclasses import dataclass, field
import threading

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception
    timeout_duration: float = 10.0
    half_open_max_calls: int = 3
    monitoring_window: int = 60

@dataclass
class CircuitBreakerStats:
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    timeouts: int = 0
    state_changes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    current_state: CircuitState = CircuitState.CLOSED
    
class CircuitBreakerOpenException(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreakerTimeoutException(Exception):
    """Raised when operation times out"""
    pass

class CircuitBreaker:
    """
    Production-ready circuit breaker with advanced monitoring
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self.lock = threading.Lock()
        self.listeners = []
        
    def add_listener(self, listener: Callable[[str, CircuitState, CircuitState], None]):
        """Add state change listener"""
        self.listeners.append(listener)
        
    def _notify_state_change(self, old_state: CircuitState, new_state: CircuitState):
        """Notify all listeners of state change"""
        for listener in self.listeners:
            try:
                listener(self.name, old_state, new_state)
            except Exception as e:
                logger.error(f"Error notifying listener: {e}")
    
    def _change_state(self, new_state: CircuitState):
        """Change circuit breaker state with notifications"""
        with self.lock:
            old_state = self.state
            if old_state != new_state:
                self.state = new_state
                self.stats.current_state = new_state
                self.stats.state_changes += 1
                logger.info(f"Circuit breaker '{self.name}' state changed: {old_state.value} -> {new_state.value}")
                self._notify_state_change(old_state, new_state)
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset to half-open"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _record_success(self):
        """Record successful call"""
        with self.lock:
            self.stats.total_calls += 1
            self.stats.successful_calls += 1
            self.stats.last_success_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
                if self.half_open_calls >= self.config.half_open_max_calls:
                    self._change_state(CircuitState.CLOSED)
                    self.failure_count = 0
                    self.half_open_calls = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0
    
    def _record_failure(self, exception: Exception):
        """Record failed call"""
        with self.lock:
            self.stats.total_calls += 1
            self.stats.failed_calls += 1
            self.stats.last_failure_time = datetime.now()
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if isinstance(exception, CircuitBreakerTimeoutException):
                self.stats.timeouts += 1
            
            if self.state == CircuitState.HALF_OPEN:
                self._change_state(CircuitState.OPEN)
                self.half_open_calls = 0
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self._change_state(CircuitState.OPEN)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self.lock:
            success_rate = 0
            if self.stats.total_calls > 0:
                success_rate = (self.stats.successful_calls / self.stats.total_calls) * 100
            
            return {
                'name': self.name,
                'state': self.state.value,
                'total_calls': self.stats.total_calls,
                'successful_calls': self.stats.successful_calls,
                'failed_calls': self.stats.failed_calls,
                'timeouts': self.stats.timeouts,
                'success_rate': round(success_rate, 2),
                'failure_count': self.failure_count,
                'state_changes': self.stats.state_changes,
                'last_failure_time': self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
                'last_success_time': self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
            }
    
    def __call__(self, func: Callable):
        """Decorator for circuit breaker functionality"""
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._change_state(CircuitState.HALF_OPEN)
                self.half_open_calls = 0
            else:
                raise CircuitBreakerOpenException(f"Circuit breaker '{self.name}' is OPEN")
        
        # Check if half-open and limit calls
        if self.state == CircuitState.HALF_OPEN and self.half_open_calls >= self.config.half_open_max_calls:
            raise CircuitBreakerOpenException(f"Circuit breaker '{self.name}' is HALF_OPEN with max calls reached")
        
        # Execute function with timeout
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > self.config.timeout_duration:
                raise CircuitBreakerTimeoutException(f"Function exceeded timeout of {self.config.timeout_duration}s")
            
            self._record_success()
            return result
            
        except self.config.expected_exception as e:
            self._record_failure(e)
            raise
        except Exception as e:
            self._record_failure(e)
            raise

# Circuit breaker registry for managing multiple circuit breakers
class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.global_stats = {
            'total_circuits': 0,
            'open_circuits': 0,
            'half_open_circuits': 0,
            'closed_circuits': 0,
            'total_calls': 0,
            'total_failures': 0
        }
    
    def register(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Register a new circuit breaker"""
        if name in self.circuit_breakers:
            return self.circuit_breakers[name]
        
        cb = CircuitBreaker(name, config)
        cb.add_listener(self._on_state_change)
        self.circuit_breakers[name] = cb
        self.global_stats['total_circuits'] += 1
        self.global_stats['closed_circuits'] += 1
        return cb
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.circuit_breakers.get(name)
    
    def _on_state_change(self, name: str, old_state: CircuitState, new_state: CircuitState):
        """Handle state changes for global stats"""
        # Update global state counts
        if old_state == CircuitState.CLOSED:
            self.global_stats['closed_circuits'] -= 1
        elif old_state == CircuitState.OPEN:
            self.global_stats['open_circuits'] -= 1
        elif old_state == CircuitState.HALF_OPEN:
            self.global_stats['half_open_circuits'] -= 1
        
        if new_state == CircuitState.CLOSED:
            self.global_stats['closed_circuits'] += 1
        elif new_state == CircuitState.OPEN:
            self.global_stats['open_circuits'] += 1
        elif new_state == CircuitState.HALF_OPEN:
            self.global_stats['half_open_circuits'] += 1
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all circuit breakers"""
        circuit_stats = {}
        total_calls = 0
        total_failures = 0
        
        for name, cb in self.circuit_breakers.items():
            stats = cb.get_stats()
            circuit_stats[name] = stats
            total_calls += stats['total_calls']
            total_failures += stats['failed_calls']
        
        self.global_stats['total_calls'] = total_calls
        self.global_stats['total_failures'] = total_failures
        
        return {
            'global_stats': self.global_stats,
            'circuit_breakers': circuit_stats,
            'timestamp': datetime.now().isoformat()
        }

# Global registry instance
registry = CircuitBreakerRegistry()
