import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.insert(0, 'src')

from collectors.docker_collector import DockerLogCollector

def test_docker_collector_init():
    config = {'socket_path': '/var/run/docker.sock', 'poll_interval': 5}
    collector = DockerLogCollector(config)
    assert collector.config == config
    assert collector.client is None

def test_extract_metadata():
    collector = DockerLogCollector({})
    mock_container = Mock()
    mock_container.id = '1234567890abcdef'
    mock_container.name = 'test-container'
    mock_container.image.tags = ['nginx:latest']
    mock_container.labels = {'app': 'web'}
    
    metadata = collector._extract_metadata(mock_container)
    
    assert metadata['container_id'] == '1234567890ab'
    assert metadata['container_name'] == 'test-container'
    assert metadata['image'] == 'nginx:latest'
    assert metadata['labels'] == {'app': 'web'}

print("✅ Docker collector tests passed")
