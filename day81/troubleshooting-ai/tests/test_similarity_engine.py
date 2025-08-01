"""
Tests for similarity engine functionality
"""
import pytest
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.incident import Incident, Solution
from ml.similarity_engine import SimilarityEngine

@pytest.fixture
def sample_incident():
    return Incident(
        id="test_001",
        title="Database Connection Error",
        description="Cannot connect to PostgreSQL database",
        error_type="database_connectivity",
        affected_service="user-service",
        severity="high",
        timestamp=datetime.now(),
        environment="production",
        logs=["ERROR: connection timeout", "SQLSTATE: 08006"],
        metrics={"response_time": 30000}
    )

@pytest.fixture
def sample_solution():
    return Solution(
        id="sol_001",
        incident_id="test_001",
        title="Restart Connection Pool",
        description="Reset database connection pool",
        steps=["Check DB status", "Restart pool", "Verify connection"],
        effectiveness_score=0.85,
        usage_count=10,
        success_rate=0.9,
        tags=["database", "connection"]
    )

@pytest.fixture
def similarity_engine():
    return SimilarityEngine()

def test_add_incident(similarity_engine, sample_incident, sample_solution):
    """Test adding incident to similarity engine"""
    similarity_engine.add_incident(sample_incident, sample_solution)
    
    assert len(similarity_engine.incidents) == 1
    assert len(similarity_engine.solutions) == 1
    assert len(similarity_engine.incident_embeddings) == 1

def test_find_similar_incidents(similarity_engine, sample_incident, sample_solution):
    """Test finding similar incidents"""
    # Add sample incident
    similarity_engine.add_incident(sample_incident, sample_solution)
    
    # Create similar incident
    similar_incident = Incident(
        id="test_002",
        title="DB Connection Timeout",
        description="Database connectivity issues in production",
        error_type="database_connectivity",
        affected_service="user-service",
        severity="high",
        timestamp=datetime.now(),
        environment="production",
        logs=["ERROR: connection failed", "timeout occurred"],
        metrics={"response_time": 25000}
    )
    
    similar_incidents = similarity_engine.find_similar_incidents(similar_incident, top_k=5)
    
    assert len(similar_incidents) > 0
    assert similar_incidents[0][1] > 0.5  # Similarity score should be decent

def test_contextual_similarity(similarity_engine, sample_incident):
    """Test contextual similarity calculation"""
    incident2 = Incident(
        id="test_002",
        title="Another DB Error",
        description="Different description",
        error_type="database_connectivity",  # Same error type
        affected_service="user-service",     # Same service
        severity="high",                     # Same severity
        timestamp=datetime.now(),
        environment="production",            # Same environment
        logs=["Different log"],
        metrics={}
    )
    
    similarity = similarity_engine.calculate_contextual_similarity(sample_incident, incident2)
    assert similarity == 1.0  # Perfect contextual match

def test_recommend_solutions(similarity_engine, sample_incident, sample_solution):
    """Test solution recommendations"""
    # Add sample data
    similarity_engine.add_incident(sample_incident, sample_solution)
    
    # Create new incident
    new_incident = Incident(
        id="test_new",
        title="Database Connectivity Problem",
        description="Unable to connect to database server",
        error_type="database_connectivity",
        affected_service="user-service",
        severity="high",
        timestamp=datetime.now(),
        environment="production",
        logs=["Connection error", "Timeout"],
        metrics={"response_time": 28000}
    )
    
    recommendations = similarity_engine.recommend_solutions(new_incident, top_k=3)
    
    assert len(recommendations) > 0
    assert recommendations[0].confidence_score > 0
    assert recommendations[0].solution.id == "sol_001"

def test_empty_database(similarity_engine):
    """Test behavior with empty database"""
    new_incident = Incident(
        id="test_empty",
        title="Some Error",
        description="An error occurred",
        error_type="unknown",
        affected_service="test-service",
        severity="low",
        timestamp=datetime.now(),
        environment="test",
        logs=[],
        metrics={}
    )
    
    recommendations = similarity_engine.recommend_solutions(new_incident)
    assert len(recommendations) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
