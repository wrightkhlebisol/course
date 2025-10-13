import pytest
import asyncio
from src.storage.optimizer import StorageOptimizer, StorageTier
from datetime import datetime, timedelta

@pytest.mark.asyncio
class TestStorageOptimizer:
    
    @pytest.fixture
    async def optimizer(self):
        opt = StorageOptimizer()
        await opt.initialize()
        return opt
    
    async def test_initialization(self, optimizer):
        """Test optimizer initializes with sample data"""
        assert len(optimizer.log_entries) > 0
        assert optimizer.metrics is not None
        
    async def test_optimize_storage(self, optimizer):
        """Test storage optimization process"""
        result = await optimizer.optimize_storage()
        
        assert "optimized_entries" in result
        assert "cost_savings" in result
        assert "total_entries" in result
        assert result["total_entries"] > 0
        
    async def test_metrics_calculation(self, optimizer):
        """Test metrics calculation"""
        metrics = await optimizer.get_metrics()
        
        required_fields = [
            "total_size_gb", "hot_size_gb", "warm_size_gb", 
            "cold_size_gb", "monthly_cost", "compression_savings"
        ]
        
        for field in required_fields:
            assert field in metrics
            assert isinstance(metrics[field], (int, float))
            
    async def test_log_entry_retrieval(self, optimizer):
        """Test log entry retrieval"""
        entries = await optimizer.get_log_entries(10)
        
        assert len(entries) <= 10
        assert all("id" in entry for entry in entries)
        assert all("tier" in entry for entry in entries)

if __name__ == "__main__":
    pytest.main([__file__])
