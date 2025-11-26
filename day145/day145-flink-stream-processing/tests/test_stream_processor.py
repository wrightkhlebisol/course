"""
Test suite for stream processor
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flink.stream_processor import (
    FlinkStreamProcessor,
    AuthenticationSpikeDetector,
    LatencyDegradationDetector,
    CascadingFailureDetector
)


class TestAuthenticationSpikeDetector:
    """Test authentication spike detection"""
    
    def test_spike_detection(self):
        """Test that spikes are detected"""
        detector = AuthenticationSpikeDetector(window_seconds=60, threshold=5)
        
        # Generate spike
        for i in range(6):
            log = {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'authentication',
                'status': 'failed',
                'user_id': 'test_user'
            }
            alerts = detector.process(log)
            
        # Should have at least one alert
        assert len(detector.detected_patterns) > 0
        
    def test_no_false_positives(self):
        """Test that normal traffic doesn't trigger alerts"""
        detector = AuthenticationSpikeDetector(window_seconds=60, threshold=10)
        
        # Generate normal traffic
        for i in range(5):
            log = {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'authentication',
                'status': 'failed',
                'user_id': 'test_user'
            }
            detector.process(log)
            
        assert len(detector.detected_patterns) == 0


class TestLatencyDegradationDetector:
    """Test latency degradation detection"""
    
    def test_degradation_detection(self):
        """Test latency degradation is detected"""
        detector = LatencyDegradationDetector(
            window_seconds=60,
            threshold_percent=50.0
        )
        
        # Establish baseline
        for i in range(15):
            log = {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'api_call',
                'endpoint': '/api/test',
                'latency_ms': 50
            }
            detector.process(log)
            
        # Inject high latency
        for i in range(10):
            log = {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'api_call',
                'endpoint': '/api/test',
                'latency_ms': 200
            }
            alerts = detector.process(log)
            
        assert len(detector.detected_patterns) > 0


class TestCascadingFailureDetector:
    """Test cascading failure detection"""
    
    def test_cascade_detection(self):
        """Test cascading failures are detected"""
        detector = CascadingFailureDetector(
            window_seconds=30,
            min_services=2
        )
        
        # Generate errors across multiple services
        services = ['service-a', 'service-b', 'service-c']
        
        for service in services:
            for i in range(3):
                log = {
                    'timestamp': datetime.now().isoformat(),
                    'event_type': 'error',
                    'level': 'error',
                    'service': service
                }
                alerts = detector.process(log)
                
        assert len(detector.detected_patterns) > 0


class TestFlinkStreamProcessor:
    """Test complete stream processor"""
    
    def test_event_processing(self):
        """Test basic event processing"""
        config = {
            'patterns': {
                'authentication_spike': {
                    'window_size': 60,
                    'threshold': 5
                },
                'latency_degradation': {
                    'window_size': 300,
                    'threshold_percent': 50.0
                },
                'cascading_failure': {
                    'window_size': 30,
                    'min_services': 2
                }
            }
        }
        
        processor = FlinkStreamProcessor(config)
        
        log = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'api_call',
            'endpoint': '/api/test',
            'latency_ms': 50
        }
        
        alerts = processor.process_event(log)
        assert processor.processed_count == 1
        
    def test_statistics(self):
        """Test statistics collection"""
        config = {
            'patterns': {
                'authentication_spike': {
                    'window_size': 60,
                    'threshold': 5
                },
                'latency_degradation': {
                    'window_size': 300,
                    'threshold_percent': 50.0
                },
                'cascading_failure': {
                    'window_size': 30,
                    'min_services': 2
                }
            }
        }
        
        processor = FlinkStreamProcessor(config)
        
        # Process some events
        for i in range(10):
            log = {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'api_call',
                'endpoint': '/api/test',
                'latency_ms': 50
            }
            processor.process_event(log)
            
        stats = processor.get_statistics()
        assert stats['processed_count'] == 10
        assert 'throughput_per_second' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
