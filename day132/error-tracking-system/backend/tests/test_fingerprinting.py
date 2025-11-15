"""Tests for error fingerprinting service"""

import pytest
from app.services.fingerprinting import fingerprinter

def test_generate_fingerprint():
    """Test fingerprint generation"""
    error_data = {
        "message": "Database connection failed: Connection timeout after 30s",
        "stack_trace": "at line 123 in database.py",
        "type": "ConnectionError"
    }
    
    fingerprint = fingerprinter.generate_fingerprint(error_data)
    assert len(fingerprint) == 16
    assert isinstance(fingerprint, str)

def test_fingerprint_consistency():
    """Test that same error generates same fingerprint"""
    error_data = {
        "message": "User 12345 not found",
        "stack_trace": "at line 100 in user_service.py",
        "type": "UserNotFoundError"
    }
    
    fingerprint1 = fingerprinter.generate_fingerprint(error_data)
    fingerprint2 = fingerprinter.generate_fingerprint(error_data)
    assert fingerprint1 == fingerprint2

def test_normalize_message():
    """Test message normalization"""
    original = "User 12345 failed to login at 192.168.1.1"
    normalized = fingerprinter._normalize_message(original)
    assert "12345" not in normalized
    assert "192.168.1.1" not in normalized
    assert "<DYNAMIC>" in normalized

def test_calculate_similarity():
    """Test similarity calculation between errors"""
    error1 = {
        "message": "Database timeout",
        "stack_trace": "at database.connect() line 100"
    }
    error2 = {
        "message": "Database timeout", 
        "stack_trace": "at database.connect() line 101"
    }
    
    similarity = fingerprinter.calculate_similarity(error1, error2)
    assert similarity > 0.8  # Should be highly similar
