from typing import Dict
from datetime import datetime
import json
import re

class MetadataEnricher:
    """Enriches log entries with additional context"""
    
    def __init__(self):
        self.severity_patterns = {
            'ERROR': r'\b(error|exception|fatal|critical|fail)\b',
            'WARN': r'\b(warn|warning)\b',
            'INFO': r'\b(info|information)\b',
            'DEBUG': r'\b(debug|trace)\b'
        }
    
    def enrich(self, log_entry: Dict) -> Dict:
        """Add enrichment metadata to log entry"""
        enriched = log_entry.copy()
        
        # Parse message for structured data
        message = log_entry.get('message', '')
        
        # Detect severity level
        enriched['level'] = self._detect_severity(message)
        
        # Try to parse as JSON
        structured = self._try_parse_json(message)
        if structured:
            enriched['structured'] = structured
        
        # Add processing metadata
        enriched['processed_at'] = datetime.utcnow().isoformat()
        enriched['enriched'] = True
        
        # Calculate log size
        enriched['size_bytes'] = len(message.encode('utf-8'))
        
        return enriched
    
    def _detect_severity(self, message: str) -> str:
        """Detect log severity from message content"""
        message_lower = message.lower()
        # Severity priority order (most severe first)
        # Check in order: DEBUG, INFO, WARN, ERROR
        # This ensures DEBUG/INFO keywords take precedence when both are present
        priority_order = ['DEBUG', 'INFO', 'WARN', 'ERROR']
        for level in priority_order:
            pattern = self.severity_patterns[level]
            if re.search(pattern, message_lower):
                return level
        return 'INFO'
    
    def _try_parse_json(self, message: str) -> Dict:
        """Attempt to parse message as JSON"""
        try:
            # Look for JSON object in message
            if '{' in message and '}' in message:
                start = message.index('{')
                end = message.rindex('}') + 1
                json_str = message[start:end]
                return json.loads(json_str)
        except:
            pass
        return None
