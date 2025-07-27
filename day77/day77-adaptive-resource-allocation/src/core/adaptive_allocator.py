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
