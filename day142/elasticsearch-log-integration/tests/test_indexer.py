import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from indexer.log_indexer import LogIndexer

@pytest.mark.asyncio
async def test_log_indexer_initialization():
    """Test indexer initialization"""
    mock_es = AsyncMock()
    config = {'index_prefix': 'test-logs', 'batch_size': 10}
    
    indexer = LogIndexer(mock_es, config)
    
    assert indexer.index_prefix == 'test-logs'
    assert indexer.batch_size == 10
    assert len(indexer.batch) == 0

@pytest.mark.asyncio  
async def test_add_log():
    """Test adding log to batch"""
    mock_es = AsyncMock()
    config = {'index_prefix': 'logs', 'batch_size': 100}
    
    indexer = LogIndexer(mock_es, config)
    
    log = {
        'timestamp': datetime.now().isoformat(),
        'level': 'INFO',
        'message': 'Test log',
        'service': 'test'
    }
    
    result = await indexer.add_log(log)
    
    assert result == True
    assert len(indexer.batch) == 1

@pytest.mark.asyncio
async def test_batch_flush():
    """Test batch flushing"""
    mock_es = AsyncMock()
    config = {'index_prefix': 'logs', 'batch_size': 2}
    
    with patch('elasticsearch.helpers.async_bulk', return_value=(2, [])):
        indexer = LogIndexer(mock_es, config)
        
        await indexer.add_log({'message': 'test1', 'level': 'INFO', 'service': 'test'})
        await indexer.add_log({'message': 'test2', 'level': 'INFO', 'service': 'test'})
        
        assert indexer.stats['indexed'] >= 0

@pytest.mark.asyncio
async def test_document_preparation():
    """Test document preparation"""
    mock_es = AsyncMock()
    config = {'index_prefix': 'logs', 'batch_size': 100}
    
    indexer = LogIndexer(mock_es, config)
    
    log = {
        'timestamp': '2025-06-16T10:00:00',
        'level': 'ERROR',
        'message': 'Test error',
        'service': 'api',
        'component': 'handler',
        'metadata': {'response_time': 250}
    }
    
    doc = indexer._prepare_document(log)
    
    assert '_index' in doc
    assert doc['_index'].startswith('logs-2025')
    assert doc['_source']['level'] == 'ERROR'
    assert doc['_source']['response_time_ms'] == 250
