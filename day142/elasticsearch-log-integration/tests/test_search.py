import pytest
from unittest.mock import AsyncMock
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from search.search_engine import SearchEngine

@pytest.mark.asyncio
async def test_search_engine_initialization():
    """Test search engine initialization"""
    mock_es = AsyncMock()
    config = {'index_prefix': 'logs', 'max_results': 100}
    
    engine = SearchEngine(mock_es, config)
    
    assert engine.index_prefix == 'logs'
    assert engine.max_results == 100

@pytest.mark.asyncio
async def test_search_logs():
    """Test log searching"""
    mock_es = AsyncMock()
    mock_es.search = AsyncMock(return_value={
        'hits': {
            'total': {'value': 1},
            'hits': [{
                '_id': '1',
                '_source': {
                    '@timestamp': '2025-06-16T10:00:00',
                    'level': 'ERROR',
                    'message': 'Test error',
                    'service': 'api'
                },
                '_score': 1.0
            }]
        },
        'took': 15
    })
    
    config = {'index_prefix': 'logs', 'max_results': 100}
    engine = SearchEngine(mock_es, config)
    
    result = await engine.search_logs(query='error', level='ERROR')
    
    assert result['total'] == 1
    assert len(result['logs']) == 1
    assert result['logs'][0]['level'] == 'ERROR'

@pytest.mark.asyncio
async def test_aggregate_by_level():
    """Test level aggregation"""
    mock_es = AsyncMock()
    mock_es.search = AsyncMock(return_value={
        'aggregations': {
            'levels': {
                'buckets': [
                    {'key': 'ERROR', 'doc_count': 10},
                    {'key': 'INFO', 'doc_count': 50}
                ]
            }
        }
    })
    
    config = {'index_prefix': 'logs'}
    engine = SearchEngine(mock_es, config)
    
    result = await engine.aggregate_by_level()
    
    assert result['ERROR'] == 10
    assert result['INFO'] == 50
