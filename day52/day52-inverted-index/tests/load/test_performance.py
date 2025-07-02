import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend/src'))

import pytest
import asyncio
import time
from indexing.inverted_index import InvertedIndex
from indexing.tokenizer import LogTokenizer
from storage.index_storage import IndexStorage

@pytest.mark.asyncio
async def test_indexing_performance():
    tokenizer = LogTokenizer()
    storage = IndexStorage("perf_test_index.db")
    index = InvertedIndex(tokenizer, storage)
    
    # Generate test documents
    test_docs = []
    for i in range(1000):
        test_docs.append({
            "id": f"doc_{i}",
            "message": f"Test log message {i} with authentication error for user_{i}",
            "level": "ERROR" if i % 3 == 0 else "INFO"
        })
    
    # Test indexing performance
    start_time = time.time()
    
    for doc in test_docs:
        await index.add_document(doc)
    
    end_time = time.time()
    indexing_time = end_time - start_time
    
    print(f"Indexed {len(test_docs)} documents in {indexing_time:.2f} seconds")
    print(f"Indexing rate: {len(test_docs) / indexing_time:.2f} docs/second")
    
    # Test search performance
    search_start = time.time()
    results = await index.search("authentication error")
    search_end = time.time()
    
    search_time = (search_end - search_start) * 1000  # Convert to milliseconds
    print(f"Search completed in {search_time:.2f}ms")
    print(f"Found {len(results)} results")
    
    # Performance assertions
    assert indexing_time < 10.0  # Should index 1000 docs in under 10 seconds
    assert search_time < 100.0   # Search should complete in under 100ms
    assert len(results) > 0       # Should find matching documents
    
    # Cleanup
    if os.path.exists("perf_test_index.db"):
        os.remove("perf_test_index.db")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
