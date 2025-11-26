import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.spark_jobs.spark_manager import SparkManager

def test_spark_manager_initialization():
    """Test SparkManager initialization"""
    manager = SparkManager()
    assert manager is not None
    assert manager.spark is None
    
def test_load_config():
    """Test configuration loading"""
    manager = SparkManager()
    assert 'spark' in manager.config
    assert 'elasticsearch' in manager.config

@pytest.mark.integration
def test_spark_session_creation():
    """Test Spark session creation"""
    manager = SparkManager()
    spark = manager.initialize_spark()
    
    assert spark is not None
    assert spark.sparkContext is not None
    
    info = manager.get_cluster_info()
    assert info['status'] == 'running'
    
    manager.stop_spark()
