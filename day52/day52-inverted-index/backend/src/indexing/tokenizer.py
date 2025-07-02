import re
from typing import List, Set
from collections import defaultdict

class LogTokenizer:
    def __init__(self):
        self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could'}
        
        self.technical_patterns = [
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP addresses
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',  # Email
            r'\b[a-zA-Z]+://[^\s]+\b',  # URLs
            r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?\b',  # ISO timestamps
            r'\b[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+\b',  # Service names
            r'\b/[a-zA-Z0-9/_-]+\b',  # API paths
            r'\bHTTP/\d\.\d\b',  # HTTP versions
            r'\b\d{3}\b',  # HTTP status codes
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.technical_patterns]
    
    def tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        
        technical_terms = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            technical_terms.extend(matches)
        
        text_lower = text.lower()
        word_tokens = re.findall(r'\b[a-zA-Z0-9_]+\b', text_lower)
        word_tokens = [token for token in word_tokens if token not in self.stop_words and len(token) >= 2]
        
        all_tokens = technical_terms + word_tokens
        seen = set()
        unique_tokens = []
        for token in all_tokens:
            if token.lower() not in seen:
                seen.add(token.lower())
                unique_tokens.append(token.lower())
        
        return unique_tokens
