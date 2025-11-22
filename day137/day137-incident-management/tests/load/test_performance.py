import pytest
import asyncio
import time
from datetime import datetime, timezone

from src.core.alert_router import AlertRouter
from src.integrations.incident_manager import IncidentManager

@pytest.mark.asyncio
async def test_high_volume_alert_processing():
    """Test system performance under high alert volume"""
    incident_manager = IncidentManager("test_key", "test_key")
    alert_router = AlertRouter(incident_manager)
    
    await alert_router.load_escalation_policies()
    
    # Generate high volume of alerts
    num_alerts = 100
    alerts = []
    
    for i in range(num_alerts):
        alert_data = {
            "id": f"load_test_{i:04d}",
            "title": f"Load Test Alert {i}",
            "description": f"High volume load test - alert {i}",
            "source": "application",
            "severity": "medium",
            "service_name": f"load-test-service-{i % 5}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"load_test": True, "batch": i // 10}
        }
        alerts.append(alert_data)
    
    # Process alerts with timing
    start_time = time.time()
    
    # Process in batches to avoid overwhelming the system
    batch_size = 10
    for i in range(0, num_alerts, batch_size):
        batch = alerts[i:i+batch_size]
        tasks = [alert_router.process_alert(alert) for alert in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Small delay between batches
        await asyncio.sleep(0.1)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Performance assertions
    alerts_per_second = num_alerts / processing_time
    
    print(f"Processed {num_alerts} alerts in {processing_time:.2f} seconds")
    print(f"Throughput: {alerts_per_second:.2f} alerts/second")
    
    # Should handle at least 10 alerts per second
    assert alerts_per_second > 10, f"Performance too low: {alerts_per_second:.2f} alerts/second"

@pytest.mark.asyncio
async def test_memory_usage_stability():
    """Test memory usage remains stable under sustained load"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    incident_manager = IncidentManager("test_key", "test_key")
    alert_router = AlertRouter(incident_manager)
    
    await alert_router.load_escalation_policies()
    
    # Process alerts continuously for a period
    num_iterations = 50
    
    for iteration in range(num_iterations):
        alert_data = {
            "id": f"memory_test_{iteration}",
            "title": f"Memory Test Alert {iteration}",
            "description": "Memory usage stability test",
            "source": "application",
            "severity": "low",
            "service_name": "memory-test-service",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await alert_router.process_alert(alert_data)
        
        # Check memory every 10 iterations
        if iteration % 10 == 0:
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            print(f"Iteration {iteration}: Memory usage: {current_memory:.1f} MB (+{memory_increase:.1f} MB)")
            
            # Memory should not increase by more than 50MB
            assert memory_increase < 50, f"Memory leak detected: {memory_increase:.1f} MB increase"
