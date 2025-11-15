"""Tests for error grouping service"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.grouping import grouping_service

@pytest.mark.asyncio
async def test_process_error():
    """Test error processing and grouping - requires database"""
    # This test requires a real database connection
    # Skip for unit tests, run as integration test instead
    pytest.skip("Requires database connection - run as integration test")
