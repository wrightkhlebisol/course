import pytest
import asyncio
import gzip
import tempfile
from pathlib import Path

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from restoration.decompressor import StreamingDecompressor
from restoration.models import CompressionType

@pytest.fixture
def test_data():
    return b"This is test data for compression testing.\n" * 100

@pytest.fixture
def temp_files(test_data):
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create raw file
    raw_file = temp_dir / "test.raw"
    raw_file.write_bytes(test_data)
    
    # Create gzip file
    gzip_file = temp_dir / "test.gz"
    with gzip.open(gzip_file, 'wb') as f:
        f.write(test_data)
    
    yield {
        'dir': temp_dir,
        'raw': raw_file,
        'gzip': gzip_file,
        'data': test_data
    }
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_raw_decompression(temp_files):
    decompressor = StreamingDecompressor(chunk_size=100)
    
    result = b""
    async for chunk in decompressor.decompress_stream(
        temp_files['raw'], CompressionType.RAW
    ):
        result += chunk
    
    assert result == temp_files['data']

@pytest.mark.asyncio
async def test_gzip_decompression(temp_files):
    decompressor = StreamingDecompressor(chunk_size=100)
    
    result = b""
    async for chunk in decompressor.decompress_stream(
        temp_files['gzip'], CompressionType.GZIP
    ):
        result += chunk
    
    assert result == temp_files['data']

@pytest.mark.asyncio
async def test_size_estimation(temp_files):
    decompressor = StreamingDecompressor()
    
    raw_size = await decompressor.get_decompressed_size_estimate(
        temp_files['raw'], CompressionType.RAW
    )
    
    gzip_size = await decompressor.get_decompressed_size_estimate(
        temp_files['gzip'], CompressionType.GZIP
    )
    
    assert raw_size == len(temp_files['data'])
    assert gzip_size > 0  # Should provide an estimate
