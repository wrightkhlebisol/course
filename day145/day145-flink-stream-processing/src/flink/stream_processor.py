"""
Apache Flink Stream Processing Job
Implements complex event processing on log streams
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict, deque
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventTimeExtractor:
    """Extract event time from log messages"""
    
    @staticmethod
    def extract_timestamp(log_entry: Dict[str, Any]) -> int:
        """Extract timestamp in milliseconds"""
        if 'timestamp' in log_entry:
            if isinstance(log_entry['timestamp'], (int, float)):
                return int(log_entry['timestamp'] * 1000)
            else:
                # Parse ISO format
                dt = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                return int(dt.timestamp() * 1000)
        return int(time.time() * 1000)


class WindowState:
    """Manages windowed state for stream processing"""
    
    def __init__(self, window_size_seconds: int):
        self.window_size = window_size_seconds * 1000  # Convert to ms
        self.windows = defaultdict(lambda: defaultdict(list))
        self.lock = threading.Lock()
        
    def add_event(self, key: str, event: Dict[str, Any], timestamp: int):
        """Add event to appropriate window"""
        window_start = (timestamp // self.window_size) * self.window_size
        
        with self.lock:
            self.windows[key][window_start].append(event)
            
    def get_window(self, key: str, timestamp: int) -> List[Dict]:
        """Get events in window containing timestamp"""
        window_start = (timestamp // self.window_size) * self.window_size
        
        with self.lock:
            return self.windows[key].get(window_start, [])
            
    def cleanup_old_windows(self, current_timestamp: int):
        """Remove windows older than 2x window size"""
        cutoff = current_timestamp - (2 * self.window_size)
        
        with self.lock:
            for key in list(self.windows.keys()):
                for window_start in list(self.windows[key].keys()):
                    if window_start < cutoff:
                        del self.windows[key][window_start]


class AuthenticationSpikeDetector:
    """Detects authentication failure spikes"""
    
    def __init__(self, window_seconds: int = 60, threshold: int = 10):
        self.window_state = WindowState(window_seconds)
        self.threshold = threshold
        self.detected_patterns = []
        
    def process(self, log_entry: Dict[str, Any]) -> List[Dict]:
        """Process log entry and detect spikes"""
        if log_entry.get('event_type') != 'authentication' or log_entry.get('status') != 'failed':
            return []
            
        user_id = log_entry.get('user_id', 'unknown')
        timestamp = EventTimeExtractor.extract_timestamp(log_entry)
        
        self.window_state.add_event(user_id, log_entry, timestamp)
        
        # Check if threshold exceeded
        window_events = self.window_state.get_window(user_id, timestamp)
        
        if len(window_events) >= self.threshold:
            alert = {
                'pattern': 'authentication_spike',
                'user_id': user_id,
                'count': len(window_events),
                'threshold': self.threshold,
                'window_start': datetime.fromtimestamp(timestamp / 1000).isoformat(),
                'detected_at': datetime.now().isoformat()
            }
            self.detected_patterns.append(alert)
            logger.warning(f"🚨 Authentication spike detected: {user_id} - {len(window_events)} failures")
            return [alert]
            
        return []


class LatencyDegradationDetector:
    """Detects API latency degradation"""
    
    def __init__(self, window_seconds: int = 300, threshold_percent: float = 50.0):
        self.window_state = WindowState(window_seconds)
        self.threshold_percent = threshold_percent
        self.baseline_latencies = defaultdict(lambda: deque(maxlen=100))
        self.detected_patterns = []
        
    def process(self, log_entry: Dict[str, Any]) -> List[Dict]:
        """Process log entry and detect latency issues"""
        if log_entry.get('event_type') != 'api_call':
            return []
            
        endpoint = log_entry.get('endpoint', 'unknown')
        latency = log_entry.get('latency_ms', 0)
        timestamp = EventTimeExtractor.extract_timestamp(log_entry)
        
        self.window_state.add_event(endpoint, log_entry, timestamp)
        
        # Calculate current window average
        window_events = self.window_state.get_window(endpoint, timestamp)
        if len(window_events) < 5:  # Need minimum samples
            return []
            
        current_avg = sum(e.get('latency_ms', 0) for e in window_events) / len(window_events)
        
        # Update baseline
        self.baseline_latencies[endpoint].append(current_avg)
        
        if len(self.baseline_latencies[endpoint]) < 10:
            return []
            
        baseline_avg = sum(self.baseline_latencies[endpoint]) / len(self.baseline_latencies[endpoint])
        
        # Check for degradation
        increase_percent = ((current_avg - baseline_avg) / baseline_avg) * 100
        
        if increase_percent > self.threshold_percent:
            alert = {
                'pattern': 'latency_degradation',
                'endpoint': endpoint,
                'baseline_ms': round(baseline_avg, 2),
                'current_ms': round(current_avg, 2),
                'increase_percent': round(increase_percent, 2),
                'detected_at': datetime.now().isoformat()
            }
            self.detected_patterns.append(alert)
            logger.warning(f"🚨 Latency degradation detected: {endpoint} - {increase_percent:.1f}% increase")
            return [alert]
            
        return []


class CascadingFailureDetector:
    """Detects cascading failures across services"""
    
    def __init__(self, window_seconds: int = 30, min_services: int = 2):
        self.window_state = WindowState(window_seconds)
        self.min_services = min_services
        self.detected_patterns = []
        
    def process(self, log_entry: Dict[str, Any]) -> List[Dict]:
        """Process log entry and detect cascading failures"""
        if log_entry.get('level') != 'error':
            return []
            
        service = log_entry.get('service', 'unknown')
        timestamp = EventTimeExtractor.extract_timestamp(log_entry)
        
        # Use a global key for cross-service correlation
        self.window_state.add_event('global', log_entry, timestamp)
        
        # Check for errors across multiple services
        window_events = self.window_state.get_window('global', timestamp)
        
        services_with_errors = set(e.get('service') for e in window_events if e.get('service'))
        
        if len(services_with_errors) >= self.min_services:
            # Count errors per service
            service_errors = defaultdict(int)
            for event in window_events:
                service_errors[event.get('service')] += 1
                
            alert = {
                'pattern': 'cascading_failure',
                'affected_services': list(services_with_errors),
                'service_error_counts': dict(service_errors),
                'total_errors': len(window_events),
                'detected_at': datetime.now().isoformat()
            }
            self.detected_patterns.append(alert)
            logger.warning(f"🚨 Cascading failure detected: {len(services_with_errors)} services affected")
            return [alert]
            
        return []


class FlinkStreamProcessor:
    """Main Flink-style stream processor"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.auth_detector = AuthenticationSpikeDetector(
            window_seconds=config['patterns']['authentication_spike']['window_size'],
            threshold=config['patterns']['authentication_spike']['threshold']
        )
        self.latency_detector = LatencyDegradationDetector(
            window_seconds=config['patterns']['latency_degradation']['window_size'],
            threshold_percent=config['patterns']['latency_degradation']['threshold_percent']
        )
        self.cascade_detector = CascadingFailureDetector(
            window_seconds=config['patterns']['cascading_failure']['window_size'],
            min_services=config['patterns']['cascading_failure']['min_services']
        )
        
        self.processed_count = 0
        self.alert_count = 0
        self.start_time = time.time()
        
    def process_event(self, log_entry: Dict[str, Any]) -> List[Dict]:
        """Process single log event through all detectors"""
        self.processed_count += 1
        
        alerts = []
        
        # Run through all pattern detectors
        alerts.extend(self.auth_detector.process(log_entry))
        alerts.extend(self.latency_detector.process(log_entry))
        alerts.extend(self.cascade_detector.process(log_entry))
        
        if alerts:
            self.alert_count += len(alerts)
            
        return alerts
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        runtime = time.time() - self.start_time
        throughput = self.processed_count / runtime if runtime > 0 else 0
        
        return {
            'processed_count': self.processed_count,
            'alert_count': self.alert_count,
            'runtime_seconds': round(runtime, 2),
            'throughput_per_second': round(throughput, 2),
            'auth_alerts': len(self.auth_detector.detected_patterns),
            'latency_alerts': len(self.latency_detector.detected_patterns),
            'cascade_alerts': len(self.cascade_detector.detected_patterns)
        }
