import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from src.core.metrics_collector import SystemMetrics

@dataclass
class LoadPrediction:
    predicted_cpu: float
    predicted_memory: float
    predicted_queue_depth: int
    confidence: float
    horizon_minutes: int
    timestamp: datetime

class LoadPredictor:
    def __init__(self, config: Dict):
        self.config = config
        self.window_size = config.get('window_size_minutes', 15)
        self.horizon = config.get('prediction_horizon_minutes', 5)
        self.sensitivity = config.get('trend_sensitivity', 0.1)
        
    def predict_load(self, metrics_history: List[SystemMetrics]) -> Optional[LoadPrediction]:
        """Predict future load based on historical metrics"""
        if len(metrics_history) < 3:
            return None
            
        try:
            # Extract time series data
            cpu_values = [m.cpu_percent for m in metrics_history]
            memory_values = [m.memory_percent for m in metrics_history]
            queue_values = [m.queue_depth for m in metrics_history]
            
            # Calculate trends and predictions
            cpu_prediction = self._predict_metric(cpu_values)
            memory_prediction = self._predict_metric(memory_values)
            queue_prediction = self._predict_metric(queue_values, is_integer=True)
            
            # Calculate confidence based on data stability
            confidence = self._calculate_confidence(cpu_values, memory_values)
            
            return LoadPrediction(
                predicted_cpu=max(0, min(100, cpu_prediction)),
                predicted_memory=max(0, min(100, memory_prediction)),
                predicted_queue_depth=max(0, int(queue_prediction)),
                confidence=confidence,
                horizon_minutes=self.horizon,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"❌ Error in load prediction: {e}")
            return None
            
    def _predict_metric(self, values: List[float], is_integer: bool = False) -> float:
        """Predict next value using trend analysis"""
        if len(values) < 2:
            return values[0] if values else 0
            
        # Calculate recent trend
        recent_values = values[-5:]  # Use last 5 values for trend
        if len(recent_values) >= 2:
            trend = (recent_values[-1] - recent_values[0]) / len(recent_values)
        else:
            trend = 0
            
        # Apply exponential smoothing
        alpha = self.sensitivity
        smoothed = values[0]
        for value in values[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed
            
        # Predict next value
        prediction = smoothed + (trend * self.horizon)
        
        return int(prediction) if is_integer else prediction
        
    def _calculate_confidence(self, *value_series) -> float:
        """Calculate prediction confidence based on data stability"""
        total_variance = 0
        count = 0
        
        for values in value_series:
            if len(values) >= 2:
                variance = np.var(values[-10:])  # Variance of last 10 values
                total_variance += variance
                count += 1
                
        if count == 0:
            return 0.5
            
        avg_variance = total_variance / count
        # Convert variance to confidence (lower variance = higher confidence)
        confidence = max(0.1, min(1.0, 1.0 - (avg_variance / 100)))
        return confidence
        
    def detect_anomalies(self, metrics_history: List[SystemMetrics]) -> List[Dict]:
        """Detect anomalous patterns in metrics"""
        if len(metrics_history) < 10:
            return []
            
        anomalies = []
        
        # Check for sudden spikes
        recent_metrics = metrics_history[-5:]
        older_metrics = metrics_history[-15:-5]
        
        if recent_metrics and older_metrics:
            recent_avg_cpu = np.mean([m.cpu_percent for m in recent_metrics])
            older_avg_cpu = np.mean([m.cpu_percent for m in older_metrics])
            
            if recent_avg_cpu > older_avg_cpu * 1.5:  # 50% increase
                anomalies.append({
                    'type': 'cpu_spike',
                    'severity': 'high' if recent_avg_cpu > 80 else 'medium',
                    'description': f'CPU usage spiked to {recent_avg_cpu:.1f}%',
                    'timestamp': datetime.now()
                })
                
        return anomalies
