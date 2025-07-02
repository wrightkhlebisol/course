import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend/src'))

import pytest
from indexing.tokenizer import LogTokenizer

def test_basic_tokenization():
    tokenizer = LogTokenizer()
    text = "Authentication failed for user john.doe@example.com"
    tokens = tokenizer.tokenize(text)
    
    assert "authentication" in tokens
    assert "failed" in tokens
    assert "user" in tokens
    assert "john.doe@example.com" in tokens

def test_technical_terms():
    tokenizer = LogTokenizer()
    text = "HTTP 500 error at /api/users from 192.168.1.100"
    tokens = tokenizer.tokenize(text)
    
    assert "192.168.1.100" in tokens
    assert "/api/users" in tokens
    assert "500" in tokens

def test_stop_words_removal():
    tokenizer = LogTokenizer()
    text = "The user is authenticated and has access"
    tokens = tokenizer.tokenize(text)
    
    assert "the" not in tokens
    assert "is" not in tokens
    assert "and" not in tokens
    assert "user" in tokens
    assert "authenticated" in tokens
    assert "access" in tokens

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
