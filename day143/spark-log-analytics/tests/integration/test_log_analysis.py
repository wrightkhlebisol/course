import pytest
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.spark_jobs.spark_manager import SparkManager
from src.spark_jobs.log_analyzer import LogAnalyzer

@pytest.fixture(scope="module")
def spark_session():
    """Create Spark session for tests"""
    manager = SparkManager()
    spark = manager.initialize_spark()
    yield spark
    manager.stop_spark()

@pytest.fixture(scope="module")
def sample_logs(spark_session, tmp_path_factory):
    """Create sample log data"""
    temp_dir = tmp_path_factory.mktemp("logs")
    log_file = temp_dir / "test_logs.json"
    
    logs = [
        {
            'timestamp': '2025-05-15T10:00:00',
            'level': 'INFO',
            'service': 'api-gateway',
            'message': 'Request processed',
            'response_time': 100,
            'status_code': 200,
            'user_id': 'user_1',
            'endpoint': '/api/users',
            'metadata': {'host': 'host-1'}
        },
        {
            'timestamp': '2025-05-15T10:01:00',
            'level': 'ERROR',
            'service': 'api-gateway',
            'message': 'Request failed',
            'response_time': 2000,
            'status_code': 500,
            'user_id': 'user_2',
            'endpoint': '/api/orders',
            'metadata': {'host': 'host-2'}
        }
    ]
    
    with open(log_file, 'w') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')
    
    return str(log_file)

def test_read_logs(spark_session, sample_logs):
    """Test reading logs from JSON"""
    analyzer = LogAnalyzer(spark_session)
    df = analyzer.read_logs_from_json(sample_logs)
    
    assert df.count() == 2
    assert 'timestamp' in df.columns
    assert 'service' in df.columns

def test_analyze_error_rates(spark_session, sample_logs):
    """Test error rate analysis"""
    analyzer = LogAnalyzer(spark_session)
    df = analyzer.read_logs_from_json(sample_logs)
    error_rates = analyzer.analyze_error_rates(df)
    
    assert error_rates.count() > 0
    assert 'error_rate' in error_rates.columns

def test_performance_metrics(spark_session, sample_logs):
    """Test performance metrics calculation"""
    analyzer = LogAnalyzer(spark_session)
    df = analyzer.read_logs_from_json(sample_logs)
    perf_metrics = analyzer.analyze_performance_metrics(df)
    
    assert perf_metrics.count() > 0
    assert 'avg_response_time' in perf_metrics.columns
