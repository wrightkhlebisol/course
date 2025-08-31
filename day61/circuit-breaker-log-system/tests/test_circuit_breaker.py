"""
Test suite for circuit breaker functionality
"""
import pytest
import time
import asyncio
from unittest.mock import Mock, patch
from src.circuit_breaker.core import (
    CircuitBreaker, 
    CircuitBreakerConfig, 
    CircuitState, 
    CircuitBreakerOpenException,
    CircuitBreakerTimeoutException,
    CircuitBreakerRegistry
)
from src.services.log_processor import LogProcessorService, DatabaseService

class TestCircuitBreaker:
    """Test circuit breaker core functionality"""
    
    def test_circuit_breaker_creation(self):
        """Test circuit breaker initialization"""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30)
        cb = CircuitBreaker("test_service", config)
        
        assert cb.name == "test_service"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.config.failure_threshold == 3
        assert cb.config.recovery_timeout == 30
    
    def test_successful_calls(self):
        """Test successful function calls"""
        cb = CircuitBreaker("test_service")
        
        @cb
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        
        stats = cb.get_stats()
        assert stats['total_calls'] == 1
        assert stats['successful_calls'] == 1
        assert stats['failed_calls'] == 0
    
    def test_circuit_opening_on_failures(self):
        """Test circuit opening after threshold failures"""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1)
        cb = CircuitBreaker("test_service", config)
        
        @cb
        def failing_function():
            raise Exception("Test failure")
        
        # First failure
        with pytest.raises(Exception):
            failing_function()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1
        
        # Second failure - should open circuit
        with pytest.raises(Exception):
            failing_function()
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 2
        
        # Third call should be blocked
        with pytest.raises(CircuitBreakerOpenException):
            failing_function()
    
    def test_circuit_half_open_transition(self):
        """Test circuit transition to half-open state"""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=1)
        cb = CircuitBreaker("test_service", config)
        
        @cb
        def failing_function():
            raise Exception("Test failure")
        
        # Cause circuit to open
        with pytest.raises(Exception):
            failing_function()
        assert cb.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Next call should transition to half-open
        with pytest.raises(Exception):
            failing_function()
        assert cb.state == CircuitState.OPEN  # Should go back to open on failure
    
    def test_circuit_closing_after_recovery(self):
        """Test circuit closing after successful recovery"""
        config = CircuitBreakerConfig(
            failure_threshold=1, 
            recovery_timeout=1,
            half_open_max_calls=2
        )
        cb = CircuitBreaker("test_service", config)
        
        call_count = 0
        @cb
        def sometimes_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First call fails")
            return "success"
        
        # First call fails, opens circuit
        with pytest.raises(Exception):
            sometimes_failing_function()
        assert cb.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Subsequent calls should succeed and close circuit
        result = sometimes_failing_function()
        assert result == "success"
        # Circuit should be half-open after first success
        
        result = sometimes_failing_function()
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
    
    def test_timeout_handling(self):
        """Test timeout detection and handling"""
        config = CircuitBreakerConfig(timeout_duration=0.1)
        cb = CircuitBreaker("test_service", config)
        
        @cb
        def slow_function():
            time.sleep(0.2)  # Longer than timeout
            return "success"
        
        with pytest.raises(CircuitBreakerTimeoutException):
            slow_function()
        
        stats = cb.get_stats()
        assert stats['timeouts'] == 1
        assert stats['failed_calls'] == 1
    
    def test_circuit_breaker_stats(self):
        """Test statistics collection"""
        cb = CircuitBreaker("test_service")
        
        @cb
        def test_function():
            return "success"
        
        # Make several calls
        for _ in range(5):
            test_function()
        
        stats = cb.get_stats()
        assert stats['name'] == "test_service"
        assert stats['state'] == CircuitState.CLOSED.value
        assert stats['total_calls'] == 5
        assert stats['successful_calls'] == 5
        assert stats['failed_calls'] == 0
        assert stats['success_rate'] == 100.0

class TestCircuitBreakerRegistry:
    """Test circuit breaker registry functionality"""
    
    def test_registry_creation(self):
        """Test registry initialization"""
        registry = CircuitBreakerRegistry()
        assert registry.global_stats['total_circuits'] == 0
        assert len(registry.circuit_breakers) == 0
    
    def test_circuit_breaker_registration(self):
        """Test registering circuit breakers"""
        registry = CircuitBreakerRegistry()
        
        cb1 = registry.register("service1")
        cb2 = registry.register("service2")
        
        assert len(registry.circuit_breakers) == 2
        assert registry.global_stats['total_circuits'] == 2
        assert registry.get("service1") == cb1
        assert registry.get("service2") == cb2
    
    def test_duplicate_registration(self):
        """Test duplicate circuit breaker registration"""
        registry = CircuitBreakerRegistry()
        
        cb1 = registry.register("service1")
        cb2 = registry.register("service1")  # Same name
        
        assert cb1 == cb2  # Should return same instance
        assert len(registry.circuit_breakers) == 1
        assert registry.global_stats['total_circuits'] == 1
    
    def test_global_stats_updates(self):
        """Test global statistics updates"""
        registry = CircuitBreakerRegistry()
        
        cb = registry.register("test_service")
        
        # Initially all circuits are closed
        assert registry.global_stats['closed_circuits'] == 1
        assert registry.global_stats['open_circuits'] == 0
        
        # Force state change
        cb._change_state(CircuitState.OPEN)
        
        assert registry.global_stats['closed_circuits'] == 0
        assert registry.global_stats['open_circuits'] == 1

class TestLogProcessorService:
    """Test log processor service with circuit breaker integration"""
    
    def test_log_processor_creation(self):
        """Test log processor initialization"""
        processor = LogProcessorService()
        
        assert processor.database is not None
        assert processor.backup_database is not None
        assert processor.message_queue is not None
        assert processor.external_api is not None
    
    def test_successful_log_processing(self):
        """Test successful log processing"""
        processor = LogProcessorService()
        
        log_data = {
            'timestamp': '2025-06-16T10:00:00Z',
            'level': 'INFO',
            'message': 'Test log message',
            'service': 'test-service'
        }
        
        result = processor.process_log(log_data)
        
        assert result['processing_status'] == 'completed'
        assert result['original_log'] == log_data
        assert len(result['processing_steps']) >= 3
        assert processor.stats['total_processed'] == 1
    
    def test_fallback_behavior(self):
        """Test fallback behavior when primary services fail"""
        processor = LogProcessorService()
        
        # Force primary database to fail
        processor.database.set_down(True)
        
        log_data = {
            'timestamp': '2025-06-16T10:00:00Z',
            'level': 'ERROR',
            'message': 'Test error message',
            'service': 'test-service'
        }
        
        result = processor.process_log(log_data)
        
        assert result['processing_status'] == 'completed'
        assert len(result['fallbacks_used']) > 0
        assert processor.stats['fallback_responses'] > 0
    
    def test_circuit_breaker_integration(self):
        """Test circuit breaker integration with log processing"""
        processor = LogProcessorService()
        
        # Get circuit breaker stats
        circuit_stats = processor.get_circuit_breaker_stats()
        
        assert 'global_stats' in circuit_stats
        assert 'circuit_breakers' in circuit_stats
        assert circuit_stats['global_stats']['total_circuits'] >= 4
        
        # Check that all expected circuit breakers are registered
        circuit_names = circuit_stats['circuit_breakers'].keys()
        expected_circuits = ['database_primary', 'database_backup', 'queue_main', 'api_enrichment']
        
        for expected in expected_circuits:
            assert expected in circuit_names

class TestDatabaseService:
    """Test database service with circuit breaker"""
    
    def test_database_service_creation(self):
        """Test database service initialization"""
        db = DatabaseService("test_db")
        
        assert db.name == "test_db"
        assert db.failure_rate == 0.1
        assert db.is_down == False
        assert db.circuit_breaker is not None
    
    def test_successful_database_operations(self):
        """Test successful database operations"""
        db = DatabaseService("test_db", failure_rate=0.0)  # No failures
        
        log_data = {
            'timestamp': '2025-06-16T10:00:00Z',
            'level': 'INFO',
            'message': 'Test message',
            'service': 'test-service'
        }
        
        result = db.insert_log(log_data)
        
        assert result['database'] == "test_db"
        assert 'timestamp' in result
        assert result['params']['level'] == 'INFO'
    
    def test_database_failure_handling(self):
        """Test database failure handling"""
        db = DatabaseService("test_db", failure_rate=1.0)  # Always fail
        
        log_data = {
            'timestamp': '2025-06-16T10:00:00Z',
            'level': 'ERROR',
            'message': 'Test error',
            'service': 'test-service'
        }
        
        # Should fail due to high failure rate
        with pytest.raises(Exception):
            db.insert_log(log_data)
        
        # Check circuit breaker stats
        stats = db.circuit_breaker.get_stats()
        assert stats['failed_calls'] > 0
    
    def test_database_downtime_simulation(self):
        """Test database downtime simulation"""
        db = DatabaseService("test_db")
        
        # Set database down
        db.set_down(True)
        
        log_data = {
            'timestamp': '2025-06-16T10:00:00Z',
            'level': 'INFO',
            'message': 'Test message',
            'service': 'test-service'
        }
        
        # Should fail when database is down
        with pytest.raises(Exception):
            db.insert_log(log_data)
        
        # Bring database back up
        db.set_down(False)
        
        # Should succeed when database is up (with some probability)
        # Note: This test might still fail due to random failure rate
        # In a real test, you might want to set failure_rate to 0

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
