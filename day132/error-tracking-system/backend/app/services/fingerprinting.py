"""Error fingerprinting and similarity calculation service"""

import hashlib
import re
from typing import Dict, List, Optional, Tuple
import json
from difflib import SequenceMatcher

class ErrorFingerprinter:
    """Service for generating error fingerprints and calculating similarity"""
    
    def __init__(self):
        self.stack_trace_patterns = [
            r'\b\d+\b',  # Line numbers
            r'0x[0-9a-fA-F]+',  # Memory addresses
            r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',  # UUIDs
            r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\b',  # ISO timestamps
        ]
        
        self.message_patterns = [
            r'\b\d+\b',  # Numbers
            r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',  # UUIDs
            r'\b[\w._%+-]+@[\w.-]+\.\w+\b',  # Email addresses
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP addresses
        ]
    
    def generate_fingerprint(self, error_data: Dict) -> str:
        """Generate a unique fingerprint for an error"""
        # Extract key components
        message = self._normalize_message(error_data.get('message', ''))
        stack_trace = self._normalize_stack_trace(error_data.get('stack_trace', ''))
        error_type = error_data.get('type', '')
        
        # Create fingerprint components
        components = [
            error_type,
            message[:200],  # First 200 chars of normalized message
            self._get_stack_trace_signature(stack_trace)
        ]
        
        # Generate hash
        fingerprint_string = '|'.join(filter(None, components))
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]
    
    def _normalize_message(self, message: str) -> str:
        """Normalize error message by removing dynamic content"""
        normalized = message
        for pattern in self.message_patterns:
            normalized = re.sub(pattern, '<DYNAMIC>', normalized)
        return normalized.strip()
    
    def _normalize_stack_trace(self, stack_trace: str) -> str:
        """Normalize stack trace by removing dynamic content"""
        if not stack_trace:
            return ""
        
        normalized = stack_trace
        for pattern in self.stack_trace_patterns:
            normalized = re.sub(pattern, '<NUM>', normalized)
        
        return normalized
    
    def _get_stack_trace_signature(self, stack_trace: str) -> str:
        """Extract a signature from the stack trace (top 3 frames)"""
        if not stack_trace:
            return ""
        
        lines = stack_trace.strip().split('\n')
        # Take first 3 meaningful lines
        signature_lines = []
        for line in lines[:10]:  # Look at first 10 lines
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract function/method names
                if 'at ' in line:
                    parts = line.split('at ')
                    if len(parts) > 1:
                        signature_lines.append(parts[1].split('(')[0])
                elif 'in ' in line:
                    parts = line.split('in ')
                    if len(parts) > 1:
                        signature_lines.append(parts[1])
                
                if len(signature_lines) >= 3:
                    break
        
        return '->'.join(signature_lines)
    
    def calculate_similarity(self, error1: Dict, error2: Dict) -> float:
        """Calculate similarity score between two errors (0.0 - 1.0)"""
        # Message similarity (40% weight)
        message1 = self._normalize_message(error1.get('message', ''))
        message2 = self._normalize_message(error2.get('message', ''))
        message_sim = SequenceMatcher(None, message1, message2).ratio()
        
        # Stack trace similarity (50% weight)
        stack1 = self._normalize_stack_trace(error1.get('stack_trace', ''))
        stack2 = self._normalize_stack_trace(error2.get('stack_trace', ''))
        stack_sim = SequenceMatcher(None, stack1, stack2).ratio()
        
        # Context similarity (10% weight)
        context1 = error1.get('context', {})
        context2 = error2.get('context', {})
        context_sim = self._calculate_context_similarity(context1, context2)
        
        # Weighted average
        total_similarity = (message_sim * 0.4) + (stack_sim * 0.5) + (context_sim * 0.1)
        return round(total_similarity, 3)
    
    def _calculate_context_similarity(self, ctx1: Dict, ctx2: Dict) -> float:
        """Calculate similarity between error contexts"""
        if not ctx1 and not ctx2:
            return 1.0
        if not ctx1 or not ctx2:
            return 0.0
        
        # Compare common keys
        common_keys = set(ctx1.keys()) & set(ctx2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            if ctx1[key] == ctx2[key]:
                matches += 1
        
        return matches / len(common_keys)

# Global instance
fingerprinter = ErrorFingerprinter()
