import pytest
import asyncio
import sys
sys.path.insert(0, 'src')

from stream.multiplexer import LogStreamMultiplexer

@pytest.mark.asyncio
async def test_multiplexer():
    config = {'buffer_size': 100}
    multiplexer = LogStreamMultiplexer(config)
    
    # Add test log
    test_log = {
        'timestamp': '2025-05-16T10:00:00Z',
        'message': 'Test log entry',
        'source': 'test'
    }
    
    await multiplexer.add_log(test_log)
    
    assert multiplexer.stats['total_logs'] == 1
    assert 'test' in multiplexer.stats['logs_per_source']
    
    recent = multiplexer.get_recent_logs(10)
    assert len(recent) == 1
    assert recent[0]['message'] == 'Test log entry'

print("✅ Integration tests passed")
