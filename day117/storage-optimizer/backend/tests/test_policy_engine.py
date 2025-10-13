import pytest
import asyncio
from src.policy.engine import PolicyEngine

@pytest.mark.asyncio
class TestPolicyEngine:
    
    @pytest.fixture
    async def engine(self):
        engine = PolicyEngine()
        await engine.start()
        return engine
    
    async def test_policy_switching(self, engine):
        """Test policy switching functionality"""
        # Test setting valid policy
        success = await engine.set_policy("aggressive")
        assert success is True
        
        active = await engine.get_active_policy()
        assert active["name"] == "Aggressive Cost Savings"
        
        # Test setting invalid policy
        success = await engine.set_policy("invalid")
        assert success is False
        
    async def test_get_all_policies(self, engine):
        """Test getting all policies"""
        policies = await engine.get_all_policies()
        
        expected_policies = ["aggressive", "balanced", "conservative"]
        for policy_name in expected_policies:
            assert policy_name in policies
            assert "name" in policies[policy_name]
            assert "tier_transition_days" in policies[policy_name]

if __name__ == "__main__":
    pytest.main([__file__])
