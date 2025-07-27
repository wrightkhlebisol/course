#!/bin/bash

# Day 77: Adaptive Resource Allocation - Complete Implementation Script
# Module 3: Advanced Log Processing Features | Week 11: Performance Optimization

set -e

PROJECT_NAME="day77-adaptive-resource-allocation"
PYTHON_VERSION="3.11"

echo "🚀 Day 77: Building Adaptive Resource Allocation System"
echo "=================================================="

# Create project structure
echo "📁 Creating project structure..."
mkdir -p $PROJECT_NAME/{src/{core,monitoring,prediction,orchestration,ui},tests,config,logs,docker,scripts}
cd $PROJECT_NAME

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python$PYTHON_VERSION -m venv venv
source venv/bin/activate

# Create requirements.txt
echo "📦 Creating requirements.txt..."
cat > requirements.txt << 'EOF'
# Core dependencies
psutil==5.9.8
flask==3.0.3
flask-socketio==5.3.6
flask-cors==4.0.0
redis==5.0.4
docker==7.1.0
pyyaml==6.0.1
numpy==1.26.4
pandas==2.2.2
requests==2.31.0

# Testing and development
pytest==8.2.1
pytest-asyncio==0.23.7
pytest-cov==5.0.0
black==24.4.2
flake8==7.0.0

# Frontend dependencies (for React dashboard)
# Note: Node.js and npm required separately
EOF

# Install Python dependencies
echo "⬇️ Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create configuration files
echo "⚙️ Creating configuration files..."
cat > config/resource_config.yaml << 'EOF'
resource_allocation:
  monitoring:
    interval_seconds: 5
    history_window_minutes: 15
    metrics_retention_hours: 24
  
  scaling:
    cpu_threshold_scale_up: 75
    cpu_threshold_scale_down: 30
    memory_threshold_scale_up: 80
    memory_threshold_scale_down: 40
    queue_depth_threshold: 1000
    
  prediction:
    window_size_minutes: 15
    prediction_horizon_minutes: 5
    trend_sensitivity: 0.1
    
  orchestration:
    min_workers: 2
    max_workers: 20
    scale_up_step: 2
    scale_down_step: 1
    cooldown_period_seconds: 60
    
  containers:
    base_image: "python:3.11-slim"
    cpu_limit: "1.0"
    memory_limit: "512Mi"
    
dashboard:
  host: "0.0.0.0"
  port: 8080
  refresh_interval_ms: 2000
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/resource_allocation.log"
EOF

# Create core metrics collector
echo "📊 Creating metrics collector..."
cat > src/core/metrics_collector.py << 'EOF'
import psutil
import time
import json
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    load_average: float
    queue_depth: int = 0
    processing_latency_ms: float = 0.0

class MetricsCollector:
    def __init__(self, config: Dict):
        self.config = config
        self.metrics_history: deque = deque(maxsize=1000)
        self.running = False
        self.collection_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
    def start_collection(self):
        """Start continuous metrics collection"""
        self.running = True
        self.collection_thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.collection_thread.start()
        print("✅ Metrics collection started")
        
    def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join()
        print("⏹️ Metrics collection stopped")
        
    def _collect_loop(self):
        """Main collection loop"""
        interval = self.config.get('interval_seconds', 5)
        
        while self.running:
            try:
                metrics = self._collect_system_metrics()
                with self.lock:
                    self.metrics_history.append(metrics)
                time.sleep(interval)
            except Exception as e:
                print(f"❌ Error collecting metrics: {e}")
                time.sleep(interval)
                
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        # Load average
        load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
        
        # Connection count
        try:
            connections = len(psutil.net_connections())
        except:
            connections = 0
            
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage_percent=disk_usage_percent,
            network_bytes_sent=net_io.bytes_sent,
            network_bytes_recv=net_io.bytes_recv,
            active_connections=connections,
            load_average=load_avg
        )
        
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get most recent metrics"""
        with self.lock:
            return self.metrics_history[-1] if self.metrics_history else None
            
    def get_metrics_history(self, minutes: int = 15) -> List[SystemMetrics]:
        """Get metrics history for specified duration"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            return [
                metrics for metrics in self.metrics_history 
                if metrics.timestamp >= cutoff_time
            ]
            
    def get_metrics_summary(self) -> Dict:
        """Get summary statistics of recent metrics"""
        recent_metrics = self.get_metrics_history(15)
        
        if not recent_metrics:
            return {}
            
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        return {
            'avg_cpu': sum(cpu_values) / len(cpu_values),
            'max_cpu': max(cpu_values),
            'avg_memory': sum(memory_values) / len(memory_values),
            'max_memory': max(memory_values),
            'sample_count': len(recent_metrics),
            'collection_period_minutes': 15
        }
EOF

# Create load predictor
echo "🔮 Creating load predictor..."
cat > src/prediction/load_predictor.py << 'EOF'
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
EOF

# Create resource orchestrator
echo "🎼 Creating resource orchestrator..."
cat > src/orchestration/resource_orchestrator.py << 'EOF'
import threading
import time
import docker
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from src.core.metrics_collector import SystemMetrics
from src.prediction.load_predictor import LoadPrediction

@dataclass
class ScalingDecision:
    action: str  # 'scale_up', 'scale_down', 'no_action'
    target_workers: int
    reason: str
    confidence: float
    timestamp: datetime

@dataclass
class ResourceState:
    current_workers: int
    target_workers: int
    cpu_utilization: float
    memory_utilization: float
    last_scaling_action: Optional[datetime]
    scaling_in_progress: bool

class ResourceOrchestrator:
    def __init__(self, config: Dict):
        self.config = config
        self.resource_state = ResourceState(
            current_workers=config.get('min_workers', 2),
            target_workers=config.get('min_workers', 2),
            cpu_utilization=0,
            memory_utilization=0,
            last_scaling_action=None,
            scaling_in_progress=False
        )
        
        self.min_workers = config.get('min_workers', 2)
        self.max_workers = config.get('max_workers', 20)
        self.scale_up_step = config.get('scale_up_step', 2)
        self.scale_down_step = config.get('scale_down_step', 1)
        self.cooldown_period = config.get('cooldown_period_seconds', 60)
        
        # Scaling thresholds
        self.cpu_scale_up = config.get('cpu_threshold_scale_up', 75)
        self.cpu_scale_down = config.get('cpu_threshold_scale_down', 30)
        self.memory_scale_up = config.get('memory_threshold_scale_up', 80)
        self.memory_scale_down = config.get('memory_threshold_scale_down', 40)
        
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except:
            print("⚠️ Docker not available - using simulation mode")
            
    def make_scaling_decision(self, current_metrics: SystemMetrics, 
                            prediction: Optional[LoadPrediction]) -> ScalingDecision:
        """Make intelligent scaling decision based on current and predicted metrics"""
        
        # Check cooldown period
        if self._in_cooldown_period():
            return ScalingDecision(
                action='no_action',
                target_workers=self.resource_state.current_workers,
                reason='Cooldown period active',
                confidence=1.0,
                timestamp=datetime.now()
            )
            
        # Update current state
        self.resource_state.cpu_utilization = current_metrics.cpu_percent
        self.resource_state.memory_utilization = current_metrics.memory_percent
        
        # Determine scaling need based on current metrics
        current_scaling_need = self._evaluate_current_metrics(current_metrics)
        
        # Factor in predictions if available
        predicted_scaling_need = 'no_action'
        if prediction and prediction.confidence > 0.7:
            predicted_scaling_need = self._evaluate_prediction(prediction)
            
        # Make final decision
        final_action = self._combine_scaling_signals(current_scaling_need, predicted_scaling_need)
        
        # Calculate target workers
        target_workers = self._calculate_target_workers(final_action)
        
        # Determine reason and confidence
        reason = self._get_scaling_reason(final_action, current_metrics, prediction)
        confidence = prediction.confidence if prediction else 0.8
        
        return ScalingDecision(
            action=final_action,
            target_workers=target_workers,
            reason=reason,
            confidence=confidence,
            timestamp=datetime.now()
        )
        
    def execute_scaling(self, decision: ScalingDecision) -> bool:
        """Execute the scaling decision"""
        if decision.action == 'no_action':
            return True
            
        print(f"🎯 Executing scaling: {decision.action} to {decision.target_workers} workers")
        print(f"   Reason: {decision.reason}")
        
        try:
            self.resource_state.scaling_in_progress = True
            
            if decision.action == 'scale_up':
                success = self._scale_up_workers(decision.target_workers)
            elif decision.action == 'scale_down':
                success = self._scale_down_workers(decision.target_workers)
            else:
                success = True
                
            if success:
                self.resource_state.current_workers = decision.target_workers
                self.resource_state.target_workers = decision.target_workers
                self.resource_state.last_scaling_action = datetime.now()
                print(f"✅ Scaling completed: {self.resource_state.current_workers} workers active")
                
            return success
            
        except Exception as e:
            print(f"❌ Scaling failed: {e}")
            return False
        finally:
            self.resource_state.scaling_in_progress = False
            
    def _in_cooldown_period(self) -> bool:
        """Check if we're in cooldown period"""
        if not self.resource_state.last_scaling_action:
            return False
            
        time_since_last = datetime.now() - self.resource_state.last_scaling_action
        return time_since_last.total_seconds() < self.cooldown_period
        
    def _evaluate_current_metrics(self, metrics: SystemMetrics) -> str:
        """Evaluate current metrics for scaling need"""
        cpu = metrics.cpu_percent
        memory = metrics.memory_percent
        
        # Scale up conditions
        if cpu > self.cpu_scale_up or memory > self.memory_scale_up:
            return 'scale_up'
            
        # Scale down conditions (both must be low)
        if cpu < self.cpu_scale_down and memory < self.memory_scale_down:
            return 'scale_down'
            
        return 'no_action'
        
    def _evaluate_prediction(self, prediction: LoadPrediction) -> str:
        """Evaluate prediction for scaling need"""
        pred_cpu = prediction.predicted_cpu
        pred_memory = prediction.predicted_memory
        
        # Predictive scale up (lower threshold for predictions)
        if pred_cpu > self.cpu_scale_up * 0.8 or pred_memory > self.memory_scale_up * 0.8:
            return 'scale_up'
            
        return 'no_action'
        
    def _combine_scaling_signals(self, current: str, predicted: str) -> str:
        """Combine current and predicted scaling signals"""
        if current == 'scale_up' or predicted == 'scale_up':
            return 'scale_up'
        elif current == 'scale_down' and predicted != 'scale_up':
            return 'scale_down'
        else:
            return 'no_action'
            
    def _calculate_target_workers(self, action: str) -> int:
        """Calculate target number of workers"""
        current = self.resource_state.current_workers
        
        if action == 'scale_up':
            target = min(self.max_workers, current + self.scale_up_step)
        elif action == 'scale_down':
            target = max(self.min_workers, current - self.scale_down_step)
        else:
            target = current
            
        return target
        
    def _get_scaling_reason(self, action: str, metrics: SystemMetrics, 
                          prediction: Optional[LoadPrediction]) -> str:
        """Generate human-readable scaling reason"""
        if action == 'no_action':
            return "System resources within optimal range"
        elif action == 'scale_up':
            reasons = []
            if metrics.cpu_percent > self.cpu_scale_up:
                reasons.append(f"CPU {metrics.cpu_percent:.1f}% > {self.cpu_scale_up}%")
            if metrics.memory_percent > self.memory_scale_up:
                reasons.append(f"Memory {metrics.memory_percent:.1f}% > {self.memory_scale_up}%")
            if prediction and prediction.predicted_cpu > self.cpu_scale_up * 0.8:
                reasons.append(f"Predicted CPU spike to {prediction.predicted_cpu:.1f}%")
            return "Scale up: " + ", ".join(reasons)
        else:  # scale_down
            return f"Scale down: CPU {metrics.cpu_percent:.1f}% and Memory {metrics.memory_percent:.1f}% below thresholds"
            
    def _scale_up_workers(self, target_workers: int) -> bool:
        """Scale up worker processes/containers"""
        current = self.resource_state.current_workers
        needed = target_workers - current
        
        print(f"📈 Scaling up: Adding {needed} workers")
        
        # Simulate container creation (replace with actual Docker commands)
        for i in range(needed):
            worker_name = f"log-processor-{current + i + 1}"
            if self.docker_client:
                try:
                    # In production, run actual log processing containers
                    container = self.docker_client.containers.run(
                        "python:3.11-slim",
                        f"python -c 'import time; print(\"Worker {worker_name} started\"); time.sleep(3600)'",
                        name=worker_name,
                        detach=True,
                        remove=True
                    )
                    print(f"✅ Started container: {worker_name}")
                except Exception as e:
                    print(f"⚠️ Container creation simulated: {worker_name}")
            else:
                print(f"✅ Worker simulated: {worker_name}")
                time.sleep(0.5)  # Simulate startup time
                
        return True
        
    def _scale_down_workers(self, target_workers: int) -> bool:
        """Scale down worker processes/containers"""
        current = self.resource_state.current_workers
        to_remove = current - target_workers
        
        print(f"📉 Scaling down: Removing {to_remove} workers")
        
        # Simulate container removal
        for i in range(to_remove):
            worker_name = f"log-processor-{current - i}"
            if self.docker_client:
                try:
                    container = self.docker_client.containers.get(worker_name)
                    container.stop()
                    print(f"✅ Stopped container: {worker_name}")
                except:
                    print(f"⚠️ Container removal simulated: {worker_name}")
            else:
                print(f"✅ Worker removed: {worker_name}")
                
        return True
        
    def get_resource_status(self) -> Dict:
        """Get current resource allocation status"""
        return {
            'current_workers': self.resource_state.current_workers,
            'target_workers': self.resource_state.target_workers,
            'cpu_utilization': self.resource_state.cpu_utilization,
            'memory_utilization': self.resource_state.memory_utilization,
            'scaling_in_progress': self.resource_state.scaling_in_progress,
            'last_scaling_action': self.resource_state.last_scaling_action.isoformat() if self.resource_state.last_scaling_action else None,
            'min_workers': self.min_workers,
            'max_workers': self.max_workers
        }
EOF

# Create main orchestration service
echo "🚀 Creating main orchestration service..."
cat > src/core/adaptive_allocator.py << 'EOF'
import yaml
import logging
import time
import threading
from typing import Dict, Optional
from datetime import datetime

from src.core.metrics_collector import MetricsCollector
from src.prediction.load_predictor import LoadPredictor
from src.orchestration.resource_orchestrator import ResourceOrchestrator

class AdaptiveResourceAllocator:
    def __init__(self, config_path: str = 'config/resource_config.yaml'):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.metrics_collector = MetricsCollector(self.config['resource_allocation']['monitoring'])
        self.load_predictor = LoadPredictor(self.config['resource_allocation']['prediction'])
        self.resource_orchestrator = ResourceOrchestrator(self.config['resource_allocation'])
        
        # Control variables
        self.running = False
        self.allocation_thread: Optional[threading.Thread] = None
        
        self.logger.info("🎯 Adaptive Resource Allocator initialized")
        
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.FileHandler(log_config.get('file', 'logs/resource_allocation.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        """Start the adaptive resource allocation system"""
        self.logger.info("🚀 Starting Adaptive Resource Allocation System")
        
        # Start metrics collection
        self.metrics_collector.start_collection()
        
        # Start allocation loop
        self.running = True
        self.allocation_thread = threading.Thread(target=self._allocation_loop, daemon=True)
        self.allocation_thread.start()
        
        self.logger.info("✅ Adaptive Resource Allocator started successfully")
        
    def stop(self):
        """Stop the adaptive resource allocation system"""
        self.logger.info("⏹️ Stopping Adaptive Resource Allocation System")
        
        self.running = False
        
        # Stop metrics collection
        self.metrics_collector.stop_collection()
        
        # Wait for allocation thread to finish
        if self.allocation_thread:
            self.allocation_thread.join()
            
        self.logger.info("✅ Adaptive Resource Allocator stopped")
        
    def _allocation_loop(self):
        """Main allocation decision loop"""
        check_interval = self.config['resource_allocation']['monitoring']['interval_seconds']
        
        while self.running:
            try:
                # Get current metrics
                current_metrics = self.metrics_collector.get_current_metrics()
                if not current_metrics:
                    time.sleep(check_interval)
                    continue
                    
                # Get metrics history for prediction
                metrics_history = self.metrics_collector.get_metrics_history()
                
                # Generate load prediction
                prediction = self.load_predictor.predict_load(metrics_history)
                
                # Make scaling decision
                decision = self.resource_orchestrator.make_scaling_decision(
                    current_metrics, prediction
                )
                
                # Log decision
                self.logger.info(
                    f"📊 Metrics: CPU {current_metrics.cpu_percent:.1f}%, "
                    f"Memory {current_metrics.memory_percent:.1f}%"
                )
                
                if prediction:
                    self.logger.info(
                        f"🔮 Prediction: CPU {prediction.predicted_cpu:.1f}%, "
                        f"Memory {prediction.predicted_memory:.1f}% (confidence: {prediction.confidence:.2f})"
                    )
                    
                self.logger.info(f"🎯 Decision: {decision.action} - {decision.reason}")
                
                # Execute scaling if needed
                if decision.action != 'no_action':
                    success = self.resource_orchestrator.execute_scaling(decision)
                    if success:
                        self.logger.info(f"✅ Scaling executed successfully")
                    else:
                        self.logger.error(f"❌ Scaling execution failed")
                        
                # Check for anomalies
                anomalies = self.load_predictor.detect_anomalies(metrics_history)
                for anomaly in anomalies:
                    self.logger.warning(f"🚨 Anomaly detected: {anomaly['description']}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error in allocation loop: {e}")
                
            time.sleep(check_interval)
            
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        current_metrics = self.metrics_collector.get_current_metrics()
        metrics_summary = self.metrics_collector.get_metrics_summary()
        resource_status = self.resource_orchestrator.get_resource_status()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'current_metrics': {
                'cpu_percent': current_metrics.cpu_percent if current_metrics else 0,
                'memory_percent': current_metrics.memory_percent if current_metrics else 0,
                'load_average': current_metrics.load_average if current_metrics else 0,
                'active_connections': current_metrics.active_connections if current_metrics else 0
            },
            'metrics_summary': metrics_summary,
            'resource_allocation': resource_status,
            'system_running': self.running
        }
        
    def force_scaling_action(self, action: str) -> bool:
        """Manually trigger scaling action (for testing)"""
        try:
            current_metrics = self.metrics_collector.get_current_metrics()
            if not current_metrics:
                return False
                
            # Create manual scaling decision
            from src.orchestration.resource_orchestrator import ScalingDecision
            
            if action == 'scale_up':
                target = min(
                    self.resource_orchestrator.max_workers,
                    self.resource_orchestrator.resource_state.current_workers + 
                    self.resource_orchestrator.scale_up_step
                )
            elif action == 'scale_down':
                target = max(
                    self.resource_orchestrator.min_workers,
                    self.resource_orchestrator.resource_state.current_workers - 
                    self.resource_orchestrator.scale_down_step
                )
            else:
                return False
                
            decision = ScalingDecision(
                action=action,
                target_workers=target,
                reason=f"Manual {action} triggered",
                confidence=1.0,
                timestamp=datetime.now()
            )
            
            return self.resource_orchestrator.execute_scaling(decision)
            
        except Exception as e:
            self.logger.error(f"❌ Force scaling failed: {e}")
            return False
EOF

# Create web dashboard
echo "🌐 Creating web dashboard..."
cat > src/ui/dashboard.py << 'EOF'
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import threading
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'adaptive-resource-allocation-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global allocator instance
allocator = None

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get current system status"""
    if allocator:
        return jsonify(allocator.get_system_status())
    else:
        return jsonify({'error': 'Allocator not initialized'}), 500

@app.route('/api/metrics')
def get_metrics():
    """Get detailed metrics"""
    if allocator:
        status = allocator.get_system_status()
        return jsonify({
            'current': status['current_metrics'],
            'summary': status['metrics_summary'],
            'resources': status['resource_allocation']
        })
    else:
        return jsonify({'error': 'Allocator not initialized'}), 500

@app.route('/api/scaling', methods=['POST'])
def trigger_scaling():
    """Manually trigger scaling action"""
    if not allocator:
        return jsonify({'error': 'Allocator not initialized'}), 500
        
    data = request.get_json()
    action = data.get('action')
    
    if action not in ['scale_up', 'scale_down']:
        return jsonify({'error': 'Invalid action'}), 400
        
    success = allocator.force_scaling_action(action)
    return jsonify({'success': success, 'action': action})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'data': 'Connected to Adaptive Resource Allocation Dashboard'})

@socketio.on('request_update')
def handle_request_update():
    """Handle real-time update request"""
    if allocator:
        status = allocator.get_system_status()
        emit('status_update', status)

def start_real_time_updates():
    """Send periodic updates to connected clients"""
    def update_loop():
        while True:
            if allocator:
                try:
                    status = allocator.get_system_status()
                    socketio.emit('status_update', status)
                except Exception as e:
                    print(f"Error sending update: {e}")
            time.sleep(5)  # Update every 5 seconds
            
    update_thread = threading.Thread(target=update_loop, daemon=True)
    update_thread.start()

def set_allocator(allocator_instance):
    """Set the allocator instance for the dashboard"""
    global allocator
    allocator = allocator_instance

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)
EOF

# Create HTML template for dashboard
mkdir -p src/ui/templates
cat > src/ui/templates/dashboard.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adaptive Resource Allocation Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            color: #4a5568;
            font-size: 1.8rem;
            font-weight: 600;
        }
        
        .dashboard-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        }
        
        .card h3 {
            color: #2d3748;
            margin-bottom: 1rem;
            font-size: 1.2rem;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 0.5rem;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .metric-item {
            text-align: center;
            padding: 1rem;
            background: #f7fafc;
            border-radius: 8px;
            border-left: 4px solid #4299e1;
        }
        
        .metric-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #2b6cb0;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #718096;
            margin-top: 0.25rem;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-running { background: #48bb78; }
        .status-stopped { background: #f56565; }
        .status-scaling { background: #ed8936; }
        
        .control-buttons {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            flex: 1;
        }
        
        .btn-primary {
            background: #4299e1;
            color: white;
        }
        
        .btn-primary:hover {
            background: #3182ce;
            transform: translateY(-2px);
        }
        
        .btn-warning {
            background: #ed8936;
            color: white;
        }
        
        .btn-warning:hover {
            background: #dd6b20;
            transform: translateY(-2px);
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 1rem;
        }
        
        .timestamp {
            font-size: 0.8rem;
            color: #a0aec0;
            text-align: center;
            margin-top: 1rem;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .updating {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Adaptive Resource Allocation Dashboard</h1>
        <div class="timestamp" id="lastUpdate">Last updated: --</div>
    </div>
    
    <div class="dashboard-container">
        <!-- System Status -->
        <div class="card">
            <h3>🖥️ System Status</h3>
            <div class="metric-grid">
                <div class="metric-item">
                    <div class="metric-value" id="cpuUsage">--</div>
                    <div class="metric-label">CPU Usage (%)</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="memoryUsage">--</div>
                    <div class="metric-label">Memory Usage (%)</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="loadAverage">--</div>
                    <div class="metric-label">Load Average</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="connections">--</div>
                    <div class="metric-label">Active Connections</div>
                </div>
            </div>
            <div>
                <span class="status-indicator" id="systemStatus"></span>
                <span id="systemStatusText">Initializing...</span>
            </div>
        </div>
        
        <!-- Resource Allocation -->
        <div class="card">
            <h3>⚙️ Resource Allocation</h3>
            <div class="metric-grid">
                <div class="metric-item">
                    <div class="metric-value" id="currentWorkers">--</div>
                    <div class="metric-label">Current Workers</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="targetWorkers">--</div>
                    <div class="metric-label">Target Workers</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="minWorkers">--</div>
                    <div class="metric-label">Min Workers</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="maxWorkers">--</div>
                    <div class="metric-label">Max Workers</div>
                </div>
            </div>
            <div class="control-buttons">
                <button class="btn btn-primary" onclick="triggerScaling('scale_up')">Scale Up</button>
                <button class="btn btn-warning" onclick="triggerScaling('scale_down')">Scale Down</button>
            </div>
        </div>
        
        <!-- Performance Metrics -->
        <div class="card">
            <h3>📊 Performance Metrics</h3>
            <div class="chart-container">
                <canvas id="metricsChart"></canvas>
            </div>
        </div>
        
        <!-- System Summary -->
        <div class="card">
            <h3>📈 Summary Statistics</h3>
            <div class="metric-grid">
                <div class="metric-item">
                    <div class="metric-value" id="avgCpu">--</div>
                    <div class="metric-label">Avg CPU (15min)</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="maxCpu">--</div>
                    <div class="metric-label">Max CPU (15min)</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="avgMemory">--</div>
                    <div class="metric-label">Avg Memory (15min)</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="maxMemory">--</div>
                    <div class="metric-label">Max Memory (15min)</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection
        const socket = io();
        
        // Chart setup
        const ctx = document.getElementById('metricsChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU Usage',
                    data: [],
                    borderColor: '#4299e1',
                    backgroundColor: 'rgba(66, 153, 225, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Memory Usage',
                    data: [],
                    borderColor: '#48bb78',
                    backgroundColor: 'rgba(72, 187, 120, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
        
        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to dashboard');
            socket.emit('request_update');
        });
        
        socket.on('status_update', function(data) {
            updateDashboard(data);
        });
        
        function updateDashboard(data) {
            // Update system metrics
            const current = data.current_metrics;
            document.getElementById('cpuUsage').textContent = current.cpu_percent.toFixed(1);
            document.getElementById('memoryUsage').textContent = current.memory_percent.toFixed(1);
            document.getElementById('loadAverage').textContent = current.load_average.toFixed(2);
            document.getElementById('connections').textContent = current.active_connections;
            
            // Update resource allocation
            const resources = data.resource_allocation;
            document.getElementById('currentWorkers').textContent = resources.current_workers;
            document.getElementById('targetWorkers').textContent = resources.target_workers;
            document.getElementById('minWorkers').textContent = resources.min_workers;
            document.getElementById('maxWorkers').textContent = resources.max_workers;
            
            // Update summary statistics
            const summary = data.metrics_summary;
            if (summary && summary.avg_cpu !== undefined) {
                document.getElementById('avgCpu').textContent = summary.avg_cpu.toFixed(1);
                document.getElementById('maxCpu').textContent = summary.max_cpu.toFixed(1);
                document.getElementById('avgMemory').textContent = summary.avg_memory.toFixed(1);
                document.getElementById('maxMemory').textContent = summary.max_memory.toFixed(1);
            }
            
            // Update system status
            const statusIndicator = document.getElementById('systemStatus');
            const statusText = document.getElementById('systemStatusText');
            
            if (data.system_running) {
                if (resources.scaling_in_progress) {
                    statusIndicator.className = 'status-indicator status-scaling';
                    statusText.textContent = 'Scaling in progress...';
                } else {
                    statusIndicator.className = 'status-indicator status-running';
                    statusText.textContent = 'System running normally';
                }
            } else {
                statusIndicator.className = 'status-indicator status-stopped';
                statusText.textContent = 'System stopped';
            }
            
            // Update chart
            const now = new Date().toLocaleTimeString();
            chart.data.labels.push(now);
            chart.data.datasets[0].data.push(current.cpu_percent);
            chart.data.datasets[1].data.push(current.memory_percent);
            
            // Keep only last 20 data points
            if (chart.data.labels.length > 20) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
                chart.data.datasets[1].data.shift();
            }
            
            chart.update('none');
            
            // Update timestamp
            document.getElementById('lastUpdate').textContent = 
                `Last updated: ${new Date().toLocaleString()}`;
        }
        
        function triggerScaling(action) {
            fetch('/api/scaling', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({action: action})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(`Scaling ${action} triggered successfully`);
                } else {
                    console.error(`Scaling ${action} failed`);
                }
            })
            .catch(error => {
                console.error('Error triggering scaling:', error);
            });
        }
        
        // Request updates every 5 seconds
        setInterval(() => {
            socket.emit('request_update');
        }, 5000);
    </script>
</body>
</html>
EOF

# Create main application
echo "🎯 Creating main application..."
cat > src/main.py << 'EOF'
#!/usr/bin/env python3

import sys
import signal
import time
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core.adaptive_allocator import AdaptiveResourceAllocator
from ui.dashboard import app, socketio, set_allocator, start_real_time_updates

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutdown signal received")
    if hasattr(signal_handler, 'allocator'):
        signal_handler.allocator.stop()
    sys.exit(0)

def main():
    """Main application entry point"""
    print("🚀 Starting Adaptive Resource Allocation System")
    print("=" * 50)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Initialize allocator
        allocator = AdaptiveResourceAllocator()
        signal_handler.allocator = allocator
        
        # Set allocator for dashboard
        set_allocator(allocator)
        
        # Start allocator
        allocator.start()
        
        # Start real-time updates
        start_real_time_updates()
        
        print("\n✅ System started successfully!")
        print("🌐 Dashboard available at: http://localhost:8080")
        print("📊 Metrics collection active")
        print("🎯 Adaptive scaling enabled")
        print("\nPress Ctrl+C to stop...")
        
        # Start web dashboard
        socketio.run(app, debug=False, host='0.0.0.0', port=8080)
        
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal")
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        return 1
    finally:
        if hasattr(signal_handler, 'allocator'):
            signal_handler.allocator.stop()
            
    return 0

if __name__ == '__main__':
    exit(main())
EOF

# Create load simulator for testing
echo "🔄 Creating load simulator..."
cat > src/monitoring/load_simulator.py << 'EOF'
import psutil
import time
import threading
import random
import multiprocessing as mp
from typing import Optional

class LoadSimulator:
    def __init__(self):
        self.cpu_load_process: Optional[mp.Process] = None
        self.memory_hog_process: Optional[mp.Process] = None
        self.running = False
        
    def simulate_cpu_load(self, target_percent: int = 70, duration: int = 60):
        """Simulate CPU load for testing"""
        print(f"🔥 Simulating {target_percent}% CPU load for {duration} seconds")
        
        def cpu_worker():
            end_time = time.time() + duration
            while time.time() < end_time:
                # Busy work to consume CPU
                for _ in range(10000):
                    _ = sum(range(100))
                    
                # Check current CPU and adjust
                current_cpu = psutil.cpu_percent(interval=0.1)
                if current_cpu < target_percent:
                    # Work harder
                    for _ in range(50000):
                        _ = sum(range(100))
                else:
                    # Rest a bit
                    time.sleep(0.01)
                    
        self.cpu_load_process = mp.Process(target=cpu_worker)
        self.cpu_load_process.start()
        
    def simulate_memory_load(self, target_mb: int = 500, duration: int = 60):
        """Simulate memory load for testing"""
        print(f"🧠 Simulating {target_mb}MB memory usage for {duration} seconds")
        
        def memory_worker():
            # Allocate memory
            data = []
            chunk_size = 1024 * 1024  # 1MB chunks
            
            for _ in range(target_mb):
                data.append(bytearray(chunk_size))
                time.sleep(0.1)  # Gradual allocation
                
            # Hold memory for duration
            time.sleep(duration)
            
            # Cleanup
            del data
            
        self.memory_load_process = mp.Process(target=memory_worker)
        self.memory_load_process.start()
        
    def simulate_variable_load(self, duration: int = 300):
        """Simulate variable load patterns"""
        print(f"📊 Simulating variable load for {duration} seconds")
        
        def variable_load_worker():
            start_time = time.time()
            
            while time.time() - start_time < duration:
                # Random load spikes
                if random.random() < 0.3:  # 30% chance of spike
                    spike_duration = random.randint(10, 30)
                    target_cpu = random.randint(60, 90)
                    
                    print(f"⚡ Load spike: {target_cpu}% CPU for {spike_duration}s")
                    
                    spike_end = time.time() + spike_duration
                    while time.time() < spike_end:
                        for _ in range(100000):
                            _ = sum(range(50))
                        time.sleep(0.01)
                else:
                    # Normal load
                    time.sleep(random.uniform(5, 15))
                    
        load_thread = threading.Thread(target=variable_load_worker, daemon=True)
        load_thread.start()
        
    def stop_simulation(self):
        """Stop all load simulations"""
        print("⏹️ Stopping load simulation")
        
        if self.cpu_load_process and self.cpu_load_process.is_alive():
            self.cpu_load_process.terminate()
            self.cpu_load_process.join()
            
        if self.memory_load_process and self.memory_load_process.is_alive():
            self.memory_load_process.terminate()
            self.memory_load_process.join()
            
        print("✅ Load simulation stopped")

def main():
    """Demo load simulation"""
    simulator = LoadSimulator()
    
    try:
        print("🎬 Starting load simulation demo")
        print("This will generate various load patterns for 2 minutes")
        
        # Start variable load
        simulator.simulate_variable_load(120)
        
        # Wait for completion
        time.sleep(120)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping simulation")
    finally:
        simulator.stop_simulation()

if __name__ == '__main__':
    main()
EOF

# Create comprehensive test suite
echo "🧪 Creating test suite..."
cat > tests/test_adaptive_allocation.py << 'EOF'
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
EOF

# Create demo script
echo "🎬 Creating demo script..."
cat > scripts/demo.py << 'EOF'
#!/usr/bin/env python3

import sys
import time
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.adaptive_allocator import AdaptiveResourceAllocator
from monitoring.load_simulator import LoadSimulator

def run_demo():
    """Run comprehensive system demonstration"""
    print("🎬 Adaptive Resource Allocation System Demo")
    print("=" * 50)
    
    # Initialize components
    allocator = AdaptiveResourceAllocator()
    simulator = LoadSimulator()
    
    try:
        print("\n1️⃣ Starting system...")
        allocator.start()
        time.sleep(5)
        
        print("\n2️⃣ System baseline (30 seconds)...")
        for i in range(6):
            status = allocator.get_system_status()
            current = status['current_metrics']
            resources = status['resource_allocation']
            
            print(f"   [{i*5:2d}s] CPU: {current['cpu_percent']:5.1f}% | "
                  f"Memory: {current['memory_percent']:5.1f}% | "
                  f"Workers: {resources['current_workers']}")
            time.sleep(5)
            
        print("\n3️⃣ Simulating high CPU load...")
        simulator.simulate_cpu_load(target_percent=80, duration=60)
        
        print("   Monitoring scaling response (60 seconds)...")
        for i in range(12):
            status = allocator.get_system_status()
            current = status['current_metrics']
            resources = status['resource_allocation']
            
            print(f"   [{i*5:2d}s] CPU: {current['cpu_percent']:5.1f}% | "
                  f"Memory: {current['memory_percent']:5.1f}% | "
                  f"Workers: {resources['current_workers']} | "
                  f"Scaling: {'Yes' if resources['scaling_in_progress'] else 'No'}")
            time.sleep(5)
            
        print("\n4️⃣ Load spike complete, monitoring scale-down...")
        for i in range(12):
            status = allocator.get_system_status()
            current = status['current_metrics']
            resources = status['resource_allocation']
            
            print(f"   [{i*5:2d}s] CPU: {current['cpu_percent']:5.1f}% | "
                  f"Memory: {current['memory_percent']:5.1f}% | "
                  f"Workers: {resources['current_workers']} | "
                  f"Scaling: {'Yes' if resources['scaling_in_progress'] else 'No'}")
            time.sleep(5)
            
        print("\n5️⃣ Testing manual scaling...")
        print("   Manual scale up...")
        success = allocator.force_scaling_action('scale_up')
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        time.sleep(10)
        
        print("   Manual scale down...")
        success = allocator.force_scaling_action('scale_down')
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        time.sleep(10)
        
        print("\n6️⃣ Final system status...")
        status = allocator.get_system_status()
        current = status['current_metrics']
        resources = status['resource_allocation']
        summary = status['metrics_summary']
        
        print(f"   Current CPU: {current['cpu_percent']:.1f}%")
        print(f"   Current Memory: {current['memory_percent']:.1f}%")
        print(f"   Active Workers: {resources['current_workers']}")
        print(f"   Load Average: {current['load_average']:.2f}")
        
        if summary:
            print(f"   Avg CPU (15min): {summary['avg_cpu']:.1f}%")
            print(f"   Max CPU (15min): {summary['max_cpu']:.1f}%")
            
        print("\n✅ Demo completed successfully!")
        print("🌐 Web dashboard available at: http://localhost:8080")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    finally:
        print("\n🧹 Cleaning up...")
        simulator.stop_simulation()
        allocator.stop()
        print("✅ Cleanup complete")

if __name__ == '__main__':
    run_demo()
EOF

# Create Docker setup
echo "🐳 Creating Docker configuration..."
cat > docker/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY tests/ ./tests/
COPY scripts/ ./scripts/

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "src/main.py"]
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  adaptive-allocator:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8080:8080"
    volumes:
      - ./logs:/app/logs
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - PYTHONPATH=/app/src
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    
volumes:
  logs:
EOF

# Create start script
echo "🏁 Creating start script..."
cat > start.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Day 77: Adaptive Resource Allocation System"
echo "======================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run the main setup script first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "✅ Virtual environment activated"

# Create logs directory
mkdir -p logs

# Set Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo "📊 Starting metrics collection and adaptive allocation..."

# Start the main application
python src/main.py &
MAIN_PID=$!

echo "🌐 Web dashboard will be available at: http://localhost:8080"
echo "📊 System monitoring active"
echo "🎯 Adaptive scaling enabled"
echo ""
echo "🎬 To run the demo, open another terminal and run:"
echo "   source venv/bin/activate"
echo "   python scripts/demo.py"
echo ""
echo "Press Ctrl+C to stop the system..."

# Wait for main process
wait $MAIN_PID
EOF

# Create stop script
cat > stop.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping Adaptive Resource Allocation System"

# Kill processes
pkill -f "python src/main.py"
pkill -f "python scripts/demo.py"

# Stop Docker containers if running
docker-compose down 2>/dev/null || true

echo "✅ System stopped"
EOF

# Make scripts executable
chmod +x start.sh stop.sh scripts/demo.py

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Build and test
echo "🔨 Building and testing system..."

# Set Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Test imports
echo "🔍 Testing imports..."
python -c "
import sys
sys.path.insert(0, 'src')
from core.adaptive_allocator import AdaptiveResourceAllocator
from core.metrics_collector import MetricsCollector
from prediction.load_predictor import LoadPredictor
from orchestration.resource_orchestrator import ResourceOrchestrator
print('✅ All imports successful')
"

# Quick functionality test
echo "⚡ Running quick functionality test..."
python -c "
import sys
sys.path.insert(0, 'src')
import time
from core.metrics_collector import MetricsCollector

print('Testing metrics collection...')
config = {'interval_seconds': 1}
collector = MetricsCollector(config)
collector.start_collection()
time.sleep(3)
current = collector.get_current_metrics()
collector.stop_collection()

if current:
    print(f'✅ CPU: {current.cpu_percent:.1f}%, Memory: {current.memory_percent:.1f}%')
else:
    print('❌ No metrics collected')
"

echo ""
echo "🎉 Build and Test Complete!"
echo "=========================="
echo ""
echo "📋 Next Steps:"
echo "1. Start the system:     ./start.sh"
echo "2. Open dashboard:       http://localhost:8080"
echo "3. Run demo:             python scripts/demo.py"
echo "4. Run tests:            python -m pytest tests/ -v"
echo "5. Stop system:          ./stop.sh"
echo ""
echo "🐳 Docker Alternative:"
echo "   docker-compose up --build"
echo ""
echo "📊 The system will automatically:"
echo "   - Monitor CPU, memory, and system metrics"
echo "   - Predict load patterns"
echo "   - Scale resources up/down based on demand"
echo "   - Provide real-time dashboard"
echo ""
echo "✅ Day 77 Implementation Complete!"
EOF

chmod +x $PROJECT_NAME/*.sh