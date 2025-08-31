import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.bloom_filter import BloomFilter, LogBloomFilterManager
import tempfile
import json

class TestBloomFilter:
    def test_initialization(self):
        bf = BloomFilter(expected_elements=1000, false_positive_rate=0.05)
        assert bf.expected_elements == 1000
        assert bf.false_positive_rate == 0.05
        assert bf.size > 0
        assert bf.hash_count > 0
        assert bf.elements_added == 0
    
    def test_add_and_query(self):
        bf = BloomFilter(expected_elements=100, false_positive_rate=0.05)
        
        # Add some elements
        test_items = ["error_001", "error_002", "access_192.168.1.1"]
        for item in test_items:
            bf.add(item)
        
        # Test positive cases (should return True)
        for item in test_items:
            assert bf.might_contain(item) == True
        
        # Test some items that weren't added (should return False most of the time)
        non_existent_items = ["error_999", "access_10.0.0.1", "security_admin"]
        false_positives = 0
        for item in non_existent_items:
            if bf.might_contain(item):
                false_positives += 1
        
        # Should have low false positive rate
        false_positive_rate = false_positives / len(non_existent_items)
        assert false_positive_rate <= 0.2  # Allow some margin for small test
    
    def test_statistics(self):
        bf = BloomFilter(expected_elements=100, false_positive_rate=0.05)
        
        # Add some elements
        for i in range(10):
            bf.add(f"test_item_{i}")
        
        # Query some elements
        for i in range(5):
            bf.might_contain(f"test_item_{i}")
        
        stats = bf.get_stats()
        assert stats['elements_added'] == 10
        assert stats['queries_made'] == 5
        assert stats['memory_usage_bytes'] > 0
    
    def test_save_and_load(self):
        bf1 = BloomFilter(expected_elements=100, false_positive_rate=0.05)
        test_items = ["test1", "test2", "test3"]
        
        for item in test_items:
            bf1.add(item)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            bf1.save(f.name)
            temp_file = f.name
        
        # Load from file
        bf2 = BloomFilter.load(temp_file)
        
        # Test that loaded filter works the same
        for item in test_items:
            assert bf2.might_contain(item) == True
        
        assert bf2.elements_added == bf1.elements_added
        assert bf2.size == bf1.size
        
        # Clean up
        os.unlink(temp_file)

class TestLogBloomFilterManager:
    def test_initialization(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.json")
            manager = LogBloomFilterManager(config_path)
            
            # Should have default filters
            assert "error_logs" in manager.filters
            assert "access_logs" in manager.filters
            assert "security_logs" in manager.filters
    
    def test_add_and_query_logs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.json")
            manager = LogBloomFilterManager(config_path)
            
            # Add log entries
            assert manager.add_log_entry("error_logs", "sql_error_001") == True
            assert manager.add_log_entry("access_logs", "192.168.1.100") == True
            assert manager.add_log_entry("unknown_type", "test") == False
            
            # Query log entries
            assert manager.check_log_exists("error_logs", "sql_error_001") == True
            assert manager.check_log_exists("error_logs", "non_existent") == False
            assert manager.check_log_exists("unknown_type", "test") is None
    
    def test_statistics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.json")
            manager = LogBloomFilterManager(config_path)
            
            # Add some entries
            for i in range(5):
                manager.add_log_entry("error_logs", f"error_{i}")
            
            stats = manager.get_all_stats()
            assert "error_logs" in stats
            assert stats["error_logs"]["elements_added"] == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
