"""
Incident data model and processing utilities
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import hashlib

@dataclass
class Incident:
    id: str
    title: str
    description: str
    error_type: str
    affected_service: str
    severity: str
    timestamp: datetime
    environment: str
    logs: List[str]
    metrics: Dict[str, float]
    resolution: Optional[str] = None
    resolution_time: Optional[int] = None  # minutes
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def get_fingerprint(self) -> str:
        """Generate unique fingerprint for incident matching"""
        content = f"{self.error_type}:{self.affected_service}:{self.description[:100]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_text_features(self) -> str:
        """Extract text features for embedding"""
        return f"{self.title} {self.description} {self.error_type} {' '.join(self.logs[:3])}"

@dataclass
class Solution:
    id: str
    incident_id: str
    title: str
    description: str
    steps: List[str]
    effectiveness_score: float
    usage_count: int
    success_rate: float
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Recommendation:
    solution: Solution
    confidence_score: float
    similarity_score: float
    context_match: float
    reasoning: str
    similar_incidents: List[str]
