import pytest
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.metrics_collector import MetricsCollector, SystemMetrics
from prediction.load_predictor import LoadPredictor, LoadPrediction
from orchestration.resource_orchestrator import ResourceOrchestrator, ScalingDecision

class TestMetricsCollector:
    def test_metrics_collection(self):
        """Test basic metrics collection"""
        config = {'interval_seconds': 1}
        collector = MetricsCollector(config)
        
        # Start collection
        collector.start_collection()
        time.sleep(2)  # Collect some metrics
        
        # Check metrics
        current = collector.get_current_metrics()
        assert current is not None
        assert 0 <= current.cpu_percent <= 100
        assert 0 <= current.memory_percent <= 100
        
        # Stop collection
        collector.stop_collection()
        
    def test_metrics_history(self):
        """Test metrics history retrieval"""
        config = {'interval_seconds': 0.5}
        collector = MetricsCollector(config)
        
        collector.start_collection()
        time.sleep(2)  # Collect multiple samples
        
        history = collector.get_metrics_history(1)  # Last 1 minute
        assert len(history) >= 2
        
        collector.stop_collection()

class TestLoadPredictor:
    def test_load_prediction(self):
        """Test load prediction with sample data"""
        config = {
            'window_size_minutes': 15,
            'prediction_horizon_minutes': 5,
            'trend_sensitivity': 0.1
        }
        predictor = LoadPredictor(config)
        
        # Create sample metrics
        base_time = datetime.now()
        metrics = []
        
        for i in range(10):
            metric = SystemMetrics(
                timestamp=base_time + timedelta(minutes=i),
                cpu_percent=50 + i * 2,  # Gradual increase
                memory_percent=40 + i,
                disk_usage_percent=30,
                network_bytes_sent=1000,
                network_bytes_recv=1000,
                active_connections=10,
                load_average=1.0,
                queue_depth=100
            )
            metrics.append(metric)
            
        # Test prediction
        prediction = predictor.predict_load(metrics)
        assert prediction is not None
        assert prediction.predicted_cpu > 50  # Should predict upward trend
        assert 0 <= prediction.confidence <= 1
        
    def test_anomaly_detection(self):
        """Test anomaly detection"""
        config = {'trend_sensitivity': 0.1}
        predictor = LoadPredictor(config)
        
        # Create metrics with anomaly
        base_time = datetime.now()
        metrics = []
        
        # Normal metrics
        for i in range(10):
            metric = SystemMetrics(
                timestamp=base_time + timedelta(minutes=i),
                cpu_percent=30,  # Normal level
                memory_percent=40,
                disk_usage_percent=30,
                network_bytes_sent=1000,
                network_bytes_recv=1000,
                active_connections=10,
                load_average=1.0
            )
            metrics.append(metric)
            
        # Anomalous metrics (spike)
        for i in range(5):
            metric = SystemMetrics(
                timestamp=base_time + timedelta(minutes=10 + i),
                cpu_percent=90,  # Sudden spike
                memory_percent=40,
                disk_usage_percent=30,
                network_bytes_sent=1000,
                network_bytes_recv=1000,
                active_connections=10,
                load_average=1.0
            )
            metrics.append(metric)
            
        anomalies = predictor.detect_anomalies(metrics)
        assert len(anomalies) > 0
        assert anomalies[0]['type'] == 'cpu_spike'

class TestResourceOrchestrator:
    def test_scaling_decision_scale_up(self):
        """Test scale up decision"""
        config = {
            'min_workers': 2,
            'max_workers': 10,
            'cpu_threshold_scale_up': 75,
            'memory_threshold_scale_up': 80,
            'cooldown_period_seconds': 0  # No cooldown for testing
        }
        
        orchestrator = ResourceOrchestrator(config)
        
        # High CPU metrics
        high_load_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=85,  # Above threshold
            memory_percent=50,
            disk_usage_percent=30,
            network_bytes_sent=1000,
            network_bytes_recv=1000,
            active_connections=10,
            load_average=2.0
        )
        
        decision = orchestrator.make_scaling_decision(high_load_metrics, None)
        assert decision.action == 'scale_up'
        assert decision.target_workers > orchestrator.resource_state.current_workers
        
    def test_scaling_decision_scale_down(self):
        """Test scale down decision"""
        config = {
            'min_workers': 2,
            'max_workers': 10,
            'cpu_threshold_scale_down': 30,
            'memory_threshold_scale_down': 40,
            'cooldown_period_seconds': 0
        }
        
        orchestrator = ResourceOrchestrator(config)
        orchestrator.resource_state.current_workers = 5  # Start with more workers
        
        # Low load metrics
        low_load_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=20,  # Below threshold
            memory_percent=30,  # Below threshold
            disk_usage_percent=30,
            network_bytes_sent=1000,
            network_bytes_recv=1000,
            active_connections=10,
            load_average=0.5
        )
        
        decision = orchestrator.make_scaling_decision(low_load_metrics, None)
        assert decision.action == 'scale_down'
        assert decision.target_workers < orchestrator.resource_state.current_workers
        
    def test_cooldown_period(self):
        """Test cooldown period enforcement"""
        config = {
            'min_workers': 2,
            'max_workers': 10,
            'cpu_threshold_scale_up': 75,
            'cooldown_period_seconds': 60
        }
        
        orchestrator = ResourceOrchestrator(config)
        orchestrator.resource_state.last_scaling_action = datetime.now()  # Recent action
        
        high_load_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=85,
            memory_percent=50,
            disk_usage_percent=30,
            network_bytes_sent=1000,
            network_bytes_recv=1000,
            active_connections=10,
            load_average=2.0
        )
        
        decision = orchestrator.make_scaling_decision(high_load_metrics, None)
        assert decision.action == 'no_action'
        assert 'cooldown' in decision.reason.lower()

class TestIntegration:
    def test_end_to_end_workflow(self):
        """Test complete workflow"""
        # Setup components
        metrics_config = {'interval_seconds': 1}
        prediction_config = {'window_size_minutes': 15}
        orchestration_config = {
            'min_workers': 2,
            'max_workers': 10,
            'cpu_threshold_scale_up': 75,
            'cooldown_period_seconds': 0
        }
        
        collector = MetricsCollector(metrics_config)
        predictor = LoadPredictor(prediction_config)
        orchestrator = ResourceOrchestrator(orchestration_config)
        
        try:
            # Start metrics collection
            collector.start_collection()
            time.sleep(2)
            
            # Get current metrics
            current_metrics = collector.get_current_metrics()
            assert current_metrics is not None
            
            # Get metrics history
            history = collector.get_metrics_history()
            assert len(history) > 0
            
            # Make prediction
            prediction = predictor.predict_load(history)
            # Prediction might be None with limited data, that's OK
            
            # Make scaling decision
            decision = orchestrator.make_scaling_decision(current_metrics, prediction)
            assert decision is not None
            assert decision.action in ['scale_up', 'scale_down', 'no_action']
            
        finally:
            collector.stop_collection()

if __name__ == '__main__':
    pytest.main([__file__])
