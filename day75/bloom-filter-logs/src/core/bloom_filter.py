import mmh3
import math
from bitarray import bitarray
from typing import List, Any, Optional
import struct
import time
import json
from pathlib import Path

class BloomFilter:
    def __init__(self, expected_elements: int, false_positive_rate: float = 0.05):
        """
        Initialize bloom filter with optimal size and hash functions
        """
        self.expected_elements = expected_elements
        self.false_positive_rate = false_positive_rate
        
        # Calculate optimal bit array size
        self.size = self._calculate_size(expected_elements, false_positive_rate)
        # Calculate optimal number of hash functions
        self.hash_count = self._calculate_hash_count(self.size, expected_elements)
        
        # Initialize bit array
        self.bit_array = bitarray(self.size)
        self.bit_array.setall(0)
        
        # Track statistics
        self.elements_added = 0
        self.queries_made = 0
        self.false_positives = 0
        self.created_at = time.time()
        
    def _calculate_size(self, n: int, p: float) -> int:
        """Calculate optimal bit array size"""
        return int(-(n * math.log(p)) / (math.log(2) ** 2))
    
    def _calculate_hash_count(self, m: int, n: int) -> int:
        """Calculate optimal number of hash functions"""
        return int((m / n) * math.log(2))
    
    def _hash(self, item: str, seed: int) -> int:
        """Generate hash for item with given seed"""
        return mmh3.hash(item, seed) % self.size
    
    def add(self, item: str) -> None:
        """Add item to bloom filter"""
        for i in range(self.hash_count):
            index = self._hash(item, i)
            self.bit_array[index] = 1
        self.elements_added += 1
    
    def might_contain(self, item: str) -> bool:
        """Check if item might be in the filter"""
        self.queries_made += 1
        for i in range(self.hash_count):
            index = self._hash(item, i)
            if not self.bit_array[index]:
                return False
        return True
    
    def get_stats(self) -> dict:
        """Get filter statistics"""
        current_false_positive_rate = self._estimate_false_positive_rate()
        return {
            'size': self.size,
            'hash_count': self.hash_count,
            'elements_added': self.elements_added,
            'queries_made': self.queries_made,
            'false_positives': self.false_positives,
            'expected_false_positive_rate': self.false_positive_rate,
            'current_false_positive_rate': current_false_positive_rate,
            'memory_usage_bytes': len(self.bit_array.tobytes()),
            'uptime_seconds': time.time() - self.created_at
        }
    
    def _estimate_false_positive_rate(self) -> float:
        """Estimate current false positive rate"""
        if self.elements_added == 0:
            return 0.0
        
        # Probability that a bit is still 0 after adding n elements
        prob_zero = (1 - 1/self.size) ** (self.hash_count * self.elements_added)
        # Probability that all k bits are 1 (false positive)
        false_pos_rate = (1 - prob_zero) ** self.hash_count
        return false_pos_rate
    
    def save(self, filepath: str) -> None:
        """Save bloom filter to disk"""
        data = {
            'expected_elements': self.expected_elements,
            'false_positive_rate': self.false_positive_rate,
            'size': self.size,
            'hash_count': self.hash_count,
            'elements_added': self.elements_added,
            'queries_made': self.queries_made,
            'created_at': self.created_at,
            'bit_array': self.bit_array.tobytes().hex()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f)
    
    @classmethod
    def load(cls, filepath: str) -> 'BloomFilter':
        """Load bloom filter from disk"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        bf = cls.__new__(cls)
        bf.expected_elements = data['expected_elements']
        bf.false_positive_rate = data['false_positive_rate']
        bf.size = data['size']
        bf.hash_count = data['hash_count']
        bf.elements_added = data['elements_added']
        bf.queries_made = data['queries_made']
        bf.created_at = data['created_at']
        bf.false_positives = 0
        
        # Restore bit array
        bf.bit_array = bitarray()
        bf.bit_array.frombytes(bytes.fromhex(data['bit_array']))
        
        return bf

class LogBloomFilterManager:
    def __init__(self, config_path: str = "config/bloom_config.json"):
        self.config = self._load_config(config_path)
        self.filters = {}
        self._initialize_filters()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration for bloom filters"""
        default_config = {
            "filters": {
                "error_logs": {"expected_elements": 1000000, "false_positive_rate": 0.01},
                "access_logs": {"expected_elements": 5000000, "false_positive_rate": 0.05},
                "security_logs": {"expected_elements": 100000, "false_positive_rate": 0.001}
            },
            "persistence_path": "data/bloom_filters"
        }
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default config
            Path(config_path).parent.mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def _initialize_filters(self):
        """Initialize bloom filters for different log types"""
        for filter_name, config in self.config['filters'].items():
            self.filters[filter_name] = BloomFilter(
                expected_elements=config['expected_elements'],
                false_positive_rate=config['false_positive_rate']
            )
    
    def add_log_entry(self, log_type: str, log_key: str) -> bool:
        """Add log entry to appropriate bloom filter"""
        if log_type in self.filters:
            self.filters[log_type].add(log_key)
            return True
        return False
    
    def check_log_exists(self, log_type: str, log_key: str) -> Optional[bool]:
        """Check if log entry might exist"""
        if log_type in self.filters:
            return self.filters[log_type].might_contain(log_key)
        return None
    
    def get_all_stats(self) -> dict:
        """Get statistics for all filters"""
        return {
            filter_name: filter_obj.get_stats()
            for filter_name, filter_obj in self.filters.items()
        }
    
    def save_all(self) -> None:
        """Save all bloom filters to disk"""
        persistence_path = Path(self.config['persistence_path'])
        persistence_path.mkdir(exist_ok=True)
        
        for filter_name, filter_obj in self.filters.items():
            filepath = persistence_path / f"{filter_name}.json"
            filter_obj.save(str(filepath))
