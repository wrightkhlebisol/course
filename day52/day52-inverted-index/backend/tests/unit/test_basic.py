import pytest

def test_basic():
    """Basic test to ensure test suite runs"""
    assert True

def test_imports():
    """Test that core modules can be imported"""
    try:
        from src.indexing.inverted_index import InvertedIndex
        from src.storage.index_storage import IndexStorage
        from src.search.query_engine import QueryEngine
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import module: {e}") 