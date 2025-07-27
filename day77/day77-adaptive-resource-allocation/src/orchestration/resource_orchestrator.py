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
