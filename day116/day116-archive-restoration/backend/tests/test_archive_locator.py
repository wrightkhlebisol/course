import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from archive.locator import ArchiveLocator
from restoration.models import QueryRequest

@pytest.fixture
def archive_locator():
    # Create temporary directories
    temp_dir = Path(tempfile.mkdtemp())
    archive_dir = temp_dir / "archives"
    index_dir = temp_dir / "indexes"
    
    archive_dir.mkdir(parents=True)
    index_dir.mkdir(parents=True)
    
    # Create test archive files
    test_files = [
        "logs_2024-01-01T00-00-00_2024-01-01T23-59-59.archive",
        "logs_2024-01-02T00-00-00_2024-01-02T23-59-59.archive",
        "logs_2024-01-03T00-00-00_2024-01-03T23-59-59.archive"
    ]
    
    for filename in test_files:
        (archive_dir / filename).write_text("test data")
    
    locator = ArchiveLocator(str(archive_dir), str(index_dir))
    
    yield locator
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_find_relevant_archives(archive_locator):
    query = QueryRequest(
        start_time=datetime(2024, 1, 1, 12, 0, 0),
        end_time=datetime(2024, 1, 2, 12, 0, 0)
    )
    
    archives = await archive_locator.find_relevant_archives(query)
    
    assert len(archives) == 2  # Should find 2 overlapping archives
    assert all("2024-01-01" in a.file_path or "2024-01-02" in a.file_path for a in archives)

@pytest.mark.asyncio
async def test_index_rebuild(archive_locator):
    await archive_locator._rebuild_index()
    
    assert len(archive_locator.metadata_cache) == 3
    assert archive_locator.last_scan is not None

@pytest.mark.asyncio
async def test_index_persistence(archive_locator):
    await archive_locator._rebuild_index()
    original_count = len(archive_locator.metadata_cache)
    
    # Create new locator instance
    new_locator = ArchiveLocator(archive_locator.base_path, archive_locator.index_path)
    await new_locator._ensure_index_loaded()
    
    assert len(new_locator.metadata_cache) == original_count
