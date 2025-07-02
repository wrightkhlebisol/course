import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend/src'))

import pytest
import asyncio
from indexing.inverted_index import InvertedIndex
from indexing.tokenizer import LogTokenizer
from search.query_engine import QueryEngine
from storage.index_storage import IndexStorage

@pytest.mark.asyncio
async def test_end_to_end_search():
    tokenizer = LogTokenizer()
    storage = IndexStorage("test_index.db")
    index = InvertedIndex(tokenizer, storage)
    query_engine = QueryEngine(index)
    
    # Add test documents
    test_docs = [
        {"id": "1", "message": "Authentication failed for user", "level": "ERROR"},
        {"id": "2", "message": "User login successful", "level": "INFO"},
        {"id": "3", "message": "Database connection timeout", "level": "WARNING"}
    ]
    
    for doc in test_docs:
        await index.add_document(doc)
    
    # Test search
    result = await query_engine.execute_search("authentication failed")
    
    assert result["metadata"]["total_results"] == 1
    assert result["results"][0]["id"] == "1"
    
    # Test filter search
    result = await query_engine.execute_search("user level:INFO")
    
    assert result["metadata"]["total_results"] == 1
    assert result["results"][0]["id"] == "2"
    
    # Cleanup
    if os.path.exists("test_index.db"):
        os.remove("test_index.db")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
