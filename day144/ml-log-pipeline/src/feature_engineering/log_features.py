"""Feature extraction from log entries"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import re

class LogFeatureExtractor:
    """Extract ML-ready features from raw logs"""
    
    def __init__(self, window_size_minutes: int = 10):
        self.window_size = timedelta(minutes=window_size_minutes)
        self.feature_names = []
        
    def extract_temporal_features(self, timestamp: datetime) -> Dict[str, float]:
        """Extract time-based features"""
        return {
            'hour': timestamp.hour / 24.0,
            'day_of_week': timestamp.weekday() / 7.0,
            'is_weekend': float(timestamp.weekday() >= 5),
            'is_business_hours': float(9 <= timestamp.hour < 17)
        }
    
    def extract_log_level_features(self, log_level: str) -> Dict[str, float]:
        """One-hot encode log levels"""
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        return {f'level_{level}': float(log_level == level) for level in levels}
    
    def extract_service_features(self, service: str, component: str) -> Dict[str, float]:
        """Encode service and component information"""
        services = ['web', 'api', 'database', 'cache', 'worker']
        features = {f'service_{s}': float(service == s) for s in services}
        features['component_hash'] = hash(component) % 1000 / 1000.0
        return features
    
    def extract_message_features(self, message: str) -> Dict[str, float]:
        """Extract features from log message text"""
        return {
            'message_length': min(len(message) / 1000.0, 1.0),
            'has_error_keyword': float(bool(re.search(r'error|fail|exception', message, re.I))),
            'has_timeout_keyword': float(bool(re.search(r'timeout|slow|latency', message, re.I))),
            'has_number': float(bool(re.search(r'\d+', message))),
            'uppercase_ratio': sum(1 for c in message if c.isupper()) / max(len(message), 1)
        }
    
    def extract_metric_features(self, metrics: Dict) -> Dict[str, float]:
        """Extract numerical metrics from log metadata"""
        return {
            'response_time_ms': metrics.get('response_time', 0) / 10000.0,
            'request_count': min(metrics.get('request_count', 0) / 1000.0, 1.0),
            'error_count': min(metrics.get('error_count', 0) / 100.0, 1.0),
            'cpu_usage': metrics.get('cpu_usage', 0) / 100.0,
            'memory_usage': metrics.get('memory_usage', 0) / 100.0
        }
    
    def extract_all_features(self, log_entry: Dict) -> np.ndarray:
        """Extract complete feature vector from log entry"""
        features = {}
        
        # Parse timestamp
        timestamp = datetime.fromisoformat(log_entry.get('timestamp', datetime.now().isoformat()))
        features.update(self.extract_temporal_features(timestamp))
        
        # Extract categorical features
        features.update(self.extract_log_level_features(log_entry.get('level', 'INFO')))
        features.update(self.extract_service_features(
            log_entry.get('service', 'unknown'),
            log_entry.get('component', 'unknown')
        ))
        
        # Extract text features
        features.update(self.extract_message_features(log_entry.get('message', '')))
        
        # Extract metrics
        features.update(self.extract_metric_features(log_entry.get('metrics', {})))
        
        # Store feature names for consistency
        if not self.feature_names:
            self.feature_names = sorted(features.keys())
        
        # Return as ordered array
        return np.array([features[name] for name in self.feature_names], dtype=np.float32)
    
    def extract_batch(self, log_entries: List[Dict]) -> np.ndarray:
        """Extract features from batch of logs"""
        return np.array([self.extract_all_features(log) for log in log_entries])
    
    def create_time_windows(self, log_df: pd.DataFrame, window_size: timedelta = None) -> List[np.ndarray]:
        """Create sliding time windows for sequential models"""
        if window_size is None:
            window_size = self.window_size
        
        log_df['timestamp'] = pd.to_datetime(log_df['timestamp'])
        log_df = log_df.sort_values('timestamp')
        
        windows = []
        start_time = log_df['timestamp'].min()
        end_time = log_df['timestamp'].max()
        
        current = start_time
        while current < end_time:
            window_end = current + window_size
            window_logs = log_df[
                (log_df['timestamp'] >= current) & 
                (log_df['timestamp'] < window_end)
            ]
            
            if len(window_logs) > 0:
                features = self.extract_batch(window_logs.to_dict('records'))
                windows.append(features)
            
            current += window_size / 2  # 50% overlap
        
        return windows

class FeatureStore:
    """Cache and serve extracted features"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        import redis
        self.redis = redis.from_url(redis_url, decode_responses=False)
        self.ttl_seconds = 3600  # 1 hour cache
        
    def store_features(self, log_id: str, features: np.ndarray) -> None:
        """Store features in cache"""
        key = f"features:{log_id}"
        self.redis.setex(key, self.ttl_seconds, features.tobytes())
    
    def get_features(self, log_id: str) -> np.ndarray:
        """Retrieve cached features"""
        key = f"features:{log_id}"
        data = self.redis.get(key)
        if data:
            return np.frombuffer(data, dtype=np.float32)
        return None
    
    def store_batch(self, features_dict: Dict[str, np.ndarray]) -> None:
        """Store batch of features"""
        pipe = self.redis.pipeline()
        for log_id, features in features_dict.items():
            key = f"features:{log_id}"
            pipe.setex(key, self.ttl_seconds, features.tobytes())
        pipe.execute()
