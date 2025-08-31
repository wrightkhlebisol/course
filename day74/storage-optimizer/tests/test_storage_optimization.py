"""
Comprehensive test suite for storage format optimization
"""
import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, 'src')

from storage.storage_engine import AdaptiveStorageEngine, StorageFormat
from analyzer.pattern_analyzer import AccessPatternAnalyzer

class TestStorageEngine:
    @pytest.fixture
    def temp_dir(self):
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def storage_engine(self, temp_dir):
        return AdaptiveStorageEngine(temp_dir)
    
    @pytest.fixture
    def sample_logs(self):
        return [
            {
                'id': 'log_001',
                'timestamp': datetime.now().isoformat(),
                'service': 'web-api',
                'level': 'INFO',
                'message': 'User logged in',
                'user_id': 'user_123',
                'duration_ms': 45
            },
            {
                'id': 'log_002',
                'timestamp': datetime.now().isoformat(),
                'service': 'payment',
                'level': 'ERROR',
                'message': 'Payment failed',
                'user_id': 'user_456',
                'duration_ms': 1200
            }
        ]
    
    @pytest.mark.asyncio
    async def test_write_logs(self, storage_engine, sample_logs):
        """Test writing logs to storage"""
        result = await storage_engine.write_logs(sample_logs, "test_partition")
        assert result is True
        
        # Verify logs were written
        stats = storage_engine.get_optimization_stats()
        assert 'test_partition' in stats['partitions']
        assert stats['partitions']['test_partition']['writes'] == 2
    
    @pytest.mark.asyncio
    async def test_read_logs(self, storage_engine, sample_logs):
        """Test reading logs from storage"""
        # First write some logs
        await storage_engine.write_logs(sample_logs, "test_partition")
        
        # Then read them back
        query = {'level': 'INFO'}
        results = await storage_engine.read_logs(query, "test_partition")
        
        assert len(results) == 1
        assert results[0]['level'] == 'INFO'
        assert results[0]['service'] == 'web-api'
    
    @pytest.mark.asyncio
    async def test_query_filtering(self, storage_engine, sample_logs):
        """Test query filtering functionality"""
        await storage_engine.write_logs(sample_logs, "test_partition")
        
        # Test service filter
        query = {'service': 'payment'}
        results = await storage_engine.read_logs(query, "test_partition")
        assert len(results) == 1
        assert results[0]['service'] == 'payment'
        
        # Test level filter
        query = {'level': 'ERROR'}
        results = await storage_engine.read_logs(query, "test_partition")
        assert len(results) == 1
        assert results[0]['level'] == 'ERROR'
    
    def test_optimization_stats(self, storage_engine):
        """Test optimization statistics"""
        stats = storage_engine.get_optimization_stats()
        
        assert 'partitions' in stats
        assert 'total_storage_mb' in stats
        assert 'compression_savings' in stats
        assert 'format_distribution' in stats

class TestPatternAnalyzer:
    @pytest.fixture
    def pattern_analyzer(self):
        return AccessPatternAnalyzer()
    
    def test_record_query(self, pattern_analyzer):
        """Test query recording functionality"""
        query = {'level': 'ERROR', 'service': 'web-api'}
        pattern_analyzer.record_query("test_partition", query, 0.1, 5)
        
        recommendations = pattern_analyzer.get_recommendations("test_partition")
        assert 'recommended_format' in recommendations
        assert 'confidence' in recommendations
    
    def test_analytical_query_classification(self, pattern_analyzer):
        """Test analytical query pattern detection"""
        # Record multiple analytical queries
        for _ in range(10):
            query = {
                'columns': ['timestamp', 'duration_ms'],
                'aggregation': True
            }
            pattern_analyzer.record_query("analytics_partition", query, 0.2, 1000)
        
        recommendations = pattern_analyzer.get_recommendations("analytics_partition")
        assert recommendations['recommended_format'] == 'columnar'
        assert recommendations['analytical_ratio'] > 0.5
    
    def test_full_record_query_classification(self, pattern_analyzer):
        """Test full record query pattern detection"""
        # Record multiple full record queries
        for _ in range(10):
            query = {'level': 'INFO'}  # Full record query (no column specification)
            pattern_analyzer.record_query("logs_partition", query, 0.1, 10)
        
        recommendations = pattern_analyzer.get_recommendations("logs_partition")
        assert recommendations['recommended_format'] == 'row_oriented'
        assert recommendations['full_record_ratio'] > 0.5
    
    def test_mixed_query_pattern(self, pattern_analyzer):
        """Test mixed query pattern detection"""
        # Record mixed query patterns
        for i in range(10):
            if i % 2 == 0:
                query = {'columns': ['timestamp', 'level']}  # Analytical
            else:
                query = {'service': 'web-api'}  # Full record
            
            pattern_analyzer.record_query("mixed_partition", query, 0.15, 20)
        
        recommendations = pattern_analyzer.get_recommendations("mixed_partition")
        assert recommendations['recommended_format'] == 'hybrid'
    
    def test_optimization_insights(self, pattern_analyzer):
        """Test optimization insights generation"""
        # Record some queries
        query = {'level': 'ERROR'}
        pattern_analyzer.record_query("test_partition", query, 0.1, 5)
        
        insights = pattern_analyzer.get_optimization_insights()
        
        assert 'partitions_analyzed' in insights
        assert 'total_queries' in insights
        assert 'recommendations' in insights
        assert insights['partitions_analyzed'] >= 1
        assert insights['total_queries'] >= 1

class TestStorageFormats:
    @pytest.fixture
    def temp_dir(self):
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.mark.asyncio
    async def test_row_storage(self, temp_dir):
        """Test row-oriented storage"""
        from storage.storage_engine import RowStorage
        
        storage = RowStorage(Path(temp_dir))
        logs = [
            {'id': '1', 'message': 'test1'},
            {'id': '2', 'message': 'test2'}
        ]
        
        # Test write
        result = await storage.write(logs, "test")
        assert result is True
        
        # Test read
        results = await storage.read({}, "test")
        assert len(results) == 2
        assert results[0]['id'] == '1'
    
    @pytest.mark.asyncio
    async def test_columnar_storage(self, temp_dir):
        """Test columnar storage"""
        from storage.storage_engine import ColumnarStorage
        
        storage = ColumnarStorage(Path(temp_dir))
        logs = [
            {'id': 1, 'message': 'test1', 'level': 'INFO'},
            {'id': 2, 'message': 'test2', 'level': 'ERROR'}
        ]
        
        # Test write
        result = await storage.write(logs, "test")
        assert result is True
        
        # Test read with column pruning
        results = await storage.read({'columns': ['id', 'level']}, "test")
        assert len(results) == 2
        assert 'id' in results[0]
        assert 'level' in results[0]
    
    @pytest.mark.asyncio
    async def test_hybrid_storage(self, temp_dir):
        """Test hybrid storage"""
        from storage.storage_engine import HybridStorage
        
        storage = HybridStorage(Path(temp_dir))
        logs = [
            {'id': '1', 'message': 'test1'},
            {'id': '2', 'message': 'test2'}
        ]
        
        # Test write (should go to hot storage)
        result = await storage.write(logs, "test")
        assert result is True
        
        # Test read (should read from hot storage)
        results = await storage.read({}, "test")
        assert len(results) == 2

# Performance benchmarks
class TestPerformance:
    @pytest.mark.asyncio
    async def test_write_performance(self):
        """Test write performance across formats"""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_engine = AdaptiveStorageEngine(temp_dir)
            
            # Generate test data
            logs = []
            for i in range(1000):
                logs.append({
                    'id': f'log_{i}',
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Test message {i}',
                    'level': 'INFO',
                    'service': 'test-service'
                })
            
            # Measure write time
            start_time = time.time()
            result = await storage_engine.write_logs(logs, "performance_test")
            write_time = time.time() - start_time
            
            assert result is True
            assert write_time < 2.0  # Should complete within 2 seconds
            print(f"✅ Write performance: {len(logs)} logs in {write_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_read_performance(self):
        """Test read performance"""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_engine = AdaptiveStorageEngine(temp_dir)
            
            # Write test data
            logs = [
                {
                    'id': f'log_{i}',
                    'level': 'INFO' if i % 2 == 0 else 'ERROR',
                    'service': f'service_{i % 3}',
                    'message': f'Message {i}'
                }
                for i in range(100)
            ]
            await storage_engine.write_logs(logs, "perf_test")
            
            # Measure read time
            start_time = time.time()
            results = await storage_engine.read_logs({'level': 'INFO'}, "perf_test")
            read_time = time.time() - start_time
            
            assert len(results) == 50  # Half should be INFO level
            assert read_time < 1.0  # Should complete within 1 second
            print(f"✅ Read performance: {len(results)} results in {read_time:.3f}s")

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
