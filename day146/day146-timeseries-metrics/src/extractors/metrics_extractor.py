"""
Metrics Extractor - Parses logs and extracts time series metrics
"""
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class Metric:
    measurement: str
    tags: Dict[str, str]
    fields: Dict[str, float]
    timestamp: datetime
    
    def to_line_protocol(self) -> str:
        """Convert to InfluxDB line protocol format"""
        tag_str = ','.join([f"{k}={v}" for k, v in self.tags.items()])
        field_str = ','.join([f"{k}={v}" for k, v in self.fields.items()])
        ts = int(self.timestamp.timestamp() * 1000000000)  # nanoseconds
        return f"{self.measurement},{tag_str} {field_str} {ts}"

class MetricsExtractor:
    """Extract metrics from structured log messages"""
    
    def __init__(self):
        self.patterns = {
            'response_time': re.compile(r'response_time[:\s]+(\d+(?:\.\d+)?)\s*ms'),
            'status_code': re.compile(r'status[:\s]+(\d{3})'),
            'request_size': re.compile(r'request_size[:\s]+(\d+)'),
            'error_count': re.compile(r'error(?:s)?[:\s]+(\d+)'),
        }
    
    def extract_from_log(self, log_entry: Dict) -> List[Metric]:
        """Extract metrics from a log entry"""
        metrics = []
        timestamp = datetime.fromisoformat(log_entry.get('timestamp', datetime.now().isoformat()))
        
        # Extract service metadata
        service = log_entry.get('service', 'unknown')
        component = log_entry.get('component', 'unknown')
        level = log_entry.get('level', 'INFO')
        
        base_tags = {
            'service': service,
            'component': component,
            'level': level,
            'host': log_entry.get('host', 'localhost')
        }
        
        # Extract HTTP metrics
        if 'response_time' in log_entry:
            metrics.append(Metric(
                measurement='http_response',
                tags={**base_tags, 'endpoint': log_entry.get('endpoint', 'unknown')},
                fields={'response_time_ms': float(log_entry['response_time'])},
                timestamp=timestamp
            ))
        
        if 'status_code' in log_entry:
            metrics.append(Metric(
                measurement='http_status',
                tags={**base_tags, 'endpoint': log_entry.get('endpoint', 'unknown')},
                fields={
                    'status_code': float(log_entry['status_code']),
                    'is_error': 1.0 if int(log_entry['status_code']) >= 400 else 0.0
                },
                timestamp=timestamp
            ))
        
        # Extract resource metrics
        if 'cpu_usage' in log_entry:
            metrics.append(Metric(
                measurement='resource_usage',
                tags=base_tags,
                fields={'cpu_percent': float(log_entry['cpu_usage'])},
                timestamp=timestamp
            ))
        
        if 'memory_usage' in log_entry:
            metrics.append(Metric(
                measurement='resource_usage',
                tags=base_tags,
                fields={'memory_mb': float(log_entry['memory_usage'])},
                timestamp=timestamp
            ))
        
        # Extract business metrics
        if 'request_count' in log_entry:
            metrics.append(Metric(
                measurement='throughput',
                tags=base_tags,
                fields={'request_count': float(log_entry['request_count'])},
                timestamp=timestamp
            ))
        
        return metrics
    
    def extract_from_text(self, text: str, service: str = 'unknown') -> List[Metric]:
        """Extract metrics from unstructured log text"""
        metrics = []
        timestamp = datetime.now()
        
        base_tags = {'service': service, 'source': 'text_log'}
        
        # Parse using regex patterns
        for metric_name, pattern in self.patterns.items():
            match = pattern.search(text)
            if match:
                value = float(match.group(1))
                metrics.append(Metric(
                    measurement=metric_name,
                    tags=base_tags,
                    fields={'value': value},
                    timestamp=timestamp
                ))
        
        return metrics

if __name__ == '__main__':
    # Test extraction
    extractor = MetricsExtractor()
    
    test_log = {
        'timestamp': '2025-06-16T10:30:45.123Z',
        'service': 'api-gateway',
        'component': 'http-handler',
        'level': 'INFO',
        'endpoint': '/api/users',
        'response_time': 145.7,
        'status_code': 200,
        'cpu_usage': 45.3,
        'memory_usage': 512.8
    }
    
    metrics = extractor.extract_from_log(test_log)
    print(f"✅ Extracted {len(metrics)} metrics from test log")
    for m in metrics:
        print(f"   {m.measurement}: {m.fields}")
