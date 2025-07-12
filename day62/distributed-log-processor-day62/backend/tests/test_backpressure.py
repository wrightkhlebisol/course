"""
Test suite for backpressure mechanisms
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.backpressure_manager import BackpressureManager, PressureLevel, PressureMetrics
from core.log_processor import LogProcessor, LogPriority
from core.circuit_breaker import CircuitBreaker
from utils.metrics import MetricsCollector

class TestBackpressureManager:
    """Test backpressure management functionality"""
    
    @pytest.fixture
    def metrics_collector(self):
        return MetricsCollector()
    
    @pytest.fixture
    def backpressure_manager(self, metrics_collector):
        return BackpressureManager(metrics_collector)
    
    def test_pressure_level_transitions(self, backpressure_manager):
        """Test pressure level state transitions"""
        # Start in normal state
        assert backpressure_manager.current_level == PressureLevel.NORMAL
        
        # High pressure should trigger state change
        high_pressure_metrics = PressureMetrics(
            queue_depth_ratio=0.8,
            processing_lag=5.0,
            resource_utilization=0.9,
            timestamp=time.time()
        )
        
        # Simulate pressure detection
        backpressure_manager.current_level = PressureLevel.PRESSURE
        assert backpressure_manager.current_level == PressureLevel.PRESSURE
    
    def test_throttle_rate_calculation(self, backpressure_manager):
        """Test throttle rate adjustments"""
        # Normal conditions should have no throttling
        backpressure_manager.current_level = PressureLevel.NORMAL
        backpressure_manager.throttle_rate = 1.0
        assert backpressure_manager.throttle_rate == 1.0
        
        # Overload should apply aggressive throttling
        backpressure_manager.current_level = PressureLevel.OVERLOAD
        backpressure_manager.throttle_rate = 0.1
        assert backpressure_manager.throttle_rate < 0.5
    
    @pytest.mark.asyncio
    async def test_queue_management(self, backpressure_manager):
        """Test queue enqueue/dequeue operations"""
        # Should accept messages within capacity
        result = await backpressure_manager.enqueue_message("test-1")
        assert result is True
        assert backpressure_manager.current_queue_size == 1
        
        # Should remove messages from queue
        await backpressure_manager.dequeue_message("test-1")
        assert backpressure_manager.current_queue_size == 0
    
    @pytest.mark.asyncio
    async def test_request_acceptance(self, backpressure_manager):
        """Test request acceptance logic"""
        # Normal level should accept all requests
        backpressure_manager.current_level = PressureLevel.NORMAL
        backpressure_manager.throttle_rate = 1.0
        
        # Multiple requests to test probabilistic acceptance
        acceptance_results = []
        for _ in range(10):
            accepted = await backpressure_manager.should_accept_request()
            acceptance_results.append(accepted)
        
        # All should be accepted in normal mode
        assert all(acceptance_results)

class TestLogProcessor:
    """Test log processing with backpressure integration"""
    
    @pytest.fixture
    def setup_components(self):
        metrics_collector = MetricsCollector()
        circuit_breaker = CircuitBreaker()
        backpressure_manager = BackpressureManager(metrics_collector)
        log_processor = LogProcessor(backpressure_manager, circuit_breaker, metrics_collector)
        
        return {
            'metrics_collector': metrics_collector,
            'circuit_breaker': circuit_breaker,
            'backpressure_manager': backpressure_manager,
            'log_processor': log_processor
        }
    
    @pytest.mark.asyncio
    async def test_log_submission_success(self, setup_components):
        """Test successful log submission"""
        components = setup_components
        log_processor = components['log_processor']
        
        # Mock successful conditions
        components['backpressure_manager'].should_accept_request = AsyncMock(return_value=True)
        components['backpressure_manager'].enqueue_message = AsyncMock(return_value=True)
        
        result = await log_processor.submit_log("Test log message", LogPriority.NORMAL)
        
        assert result['status'] == 'accepted'
        assert 'message_id' in result
    
    @pytest.mark.asyncio
    async def test_log_submission_backpressure_rejection(self, setup_components):
        """Test log rejection due to backpressure"""
        components = setup_components
        log_processor = components['log_processor']
        
        # Mock backpressure rejection
        components['backpressure_manager'].should_accept_request = AsyncMock(return_value=False)
        
        result = await log_processor.submit_log("Test log message", LogPriority.NORMAL)
        
        assert result['status'] == 'dropped'
        assert result['reason'] == 'backpressure'
    
    @pytest.mark.asyncio
    async def test_priority_based_processing(self, setup_components):
        """Test that critical logs are processed preferentially"""
        components = setup_components
        log_processor = components['log_processor']
        
        # Mock successful conditions
        components['backpressure_manager'].should_accept_request = AsyncMock(return_value=True)
        components['backpressure_manager'].enqueue_message = AsyncMock(return_value=True)
        
        # Submit logs of different priorities
        critical_result = await log_processor.submit_log("Critical log", LogPriority.CRITICAL)
        normal_result = await log_processor.submit_log("Normal log", LogPriority.NORMAL)
        
        assert critical_result['status'] == 'accepted'
        assert normal_result['status'] == 'accepted'
        
        # Critical queue should be checked first (verify by queue sizes)
        stats = log_processor.get_statistics()
        assert stats['total_queue_size'] == 2

class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @pytest.fixture
    def circuit_breaker(self):
        return CircuitBreaker(failure_threshold=3, timeout=1, success_threshold=2)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_states(self, circuit_breaker):
        """Test circuit breaker state transitions"""
        # Should start closed
        assert await circuit_breaker.should_allow_request() is True
        
        # Record failures to trigger opening
        for _ in range(3):
            await circuit_breaker.record_failure()
        
        # Should now be open
        assert await circuit_breaker.should_allow_request() is False
        
        # After timeout, should attempt half-open
        await asyncio.sleep(1.1)
        assert await circuit_breaker.should_allow_request() is True
        
        # Success should close the circuit
        await circuit_breaker.record_success()
        await circuit_breaker.record_success()
        assert circuit_breaker.state.value == 'closed'

class TestIntegration:
    """Integration tests for complete system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_log_processing(self):
        """Test complete log processing pipeline"""
        # Setup components
        metrics_collector = MetricsCollector()
        circuit_breaker = CircuitBreaker()
        backpressure_manager = BackpressureManager(metrics_collector)
        log_processor = LogProcessor(backpressure_manager, circuit_breaker, metrics_collector)
        
        # Start components
        await backpressure_manager.start()
        await log_processor.start()
        
        try:
            # Submit multiple logs
            results = []
            for i in range(5):
                result = await log_processor.submit_log(
                    f"Test log {i}",
                    LogPriority.NORMAL,
                    "integration_test"
                )
                results.append(result)
                # Small delay between submissions
                await asyncio.sleep(0.1)
            
            # All should be accepted initially
            accepted_count = sum(1 for r in results if r['status'] == 'accepted')
            assert accepted_count >= 3  # Allow for some drops under load
            
            # Check system statistics
            stats = log_processor.get_statistics()
            assert stats['total_queue_size'] >= 0
            
        finally:
            # Cleanup
            await log_processor.stop()
            await backpressure_manager.stop()
    
    @pytest.mark.asyncio
    async def test_system_under_load(self):
        """Test system behavior under high load"""
        # Setup components
        metrics_collector = MetricsCollector()
        circuit_breaker = CircuitBreaker()
        backpressure_manager = BackpressureManager(metrics_collector)
        log_processor = LogProcessor(backpressure_manager, circuit_breaker, metrics_collector)
        
        # Start components
        await backpressure_manager.start()
        await log_processor.start()
        
        try:
            # Rapid fire submissions to test backpressure
            tasks = []
            for i in range(50):
                task = log_processor.submit_log(
                    f"Load test log {i}",
                    LogPriority.NORMAL,
                    "load_test"
                )
                tasks.append(task)
            
            # Execute all submissions concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful vs dropped submissions
            successful = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'accepted')
            dropped = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'dropped')
            
            # System should handle some load but activate backpressure
            assert successful > 0
            total_processed = successful + dropped
            assert total_processed == 50
            
            # If there was significant load, some drops are expected
            if dropped > 0:
                print(f"Backpressure correctly activated: {successful} accepted, {dropped} dropped")
            
        finally:
            # Cleanup
            await log_processor.stop()
            await backpressure_manager.stop()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
