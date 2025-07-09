import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from src.backend.nodes.log_processor import LogProcessorNode
from src.backend.controllers.failover_controller import FailoverController
from src.shared.models import NodeState, NodeRole, FailoverEvent

@pytest.mark.asyncio
class TestFailoverController:
    
    @pytest.fixture
    def failover_controller(self):
        callback = AsyncMock()
        return FailoverController("test_node", callback)
    
    async def test_controller_initialization(self, failover_controller):
        """Test failover controller initialization"""
        assert failover_controller.node_id == "test_node"
        assert not failover_controller.election_in_progress
        assert failover_controller.election_votes == {}
    
    async def test_trigger_election(self, failover_controller):
        """Test election triggering"""
        # Mock broadcast methods with AsyncMock
        failover_controller.broadcast_election_message = AsyncMock()
        failover_controller.broadcast_failover_event = AsyncMock()
        failover_controller.determine_election_winner = AsyncMock(return_value="test_node")
        
        # Start controller
        await failover_controller.start()
        
        # Trigger election
        await failover_controller.trigger_election()
        
        # Verify election was triggered
        assert failover_controller.broadcast_election_message.called
        assert failover_controller.broadcast_failover_event.called
        
        # Cleanup
        await failover_controller.stop()
    
    async def test_election_winner_determination(self, failover_controller):
        """Test election winner determination"""
        # Set up mock votes
        failover_controller.election_votes = {
            "node1": Mock(priority=100),
            "node2": Mock(priority=50),
            "node3": Mock(priority=200)
        }
        
        # Determine winner (lowest priority wins)
        winner = await failover_controller.determine_election_winner()
        
        assert winner == "node2"  # Lowest priority
    
    async def test_empty_election(self, failover_controller):
        """Test election with no votes"""
        failover_controller.election_votes = {}
        
        winner = await failover_controller.determine_election_winner()
        
        assert winner is None

@pytest.mark.asyncio
class TestLogProcessorNode:
    
    @pytest.fixture
    def log_processor(self):
        return LogProcessorNode("test_node", 8001, is_primary=False)
    
    async def test_node_initialization(self, log_processor):
        """Test log processor node initialization"""
        assert log_processor.node_id == "test_node"
        assert log_processor.port == 8001
        assert log_processor.role == NodeRole.STANDBY
        assert log_processor.state == NodeState.INACTIVE
    
    async def test_become_primary(self, log_processor):
        """Test transitioning to primary role"""
        # Mock dependencies with AsyncMock
        log_processor.load_state = AsyncMock()
        log_processor.start_request_handler = AsyncMock()
        
        await log_processor.become_primary()
        
        assert log_processor.role == NodeRole.PRIMARY
        assert log_processor.state == NodeState.PRIMARY
        assert log_processor.load_state.called
        assert log_processor.start_request_handler.called
    
    async def test_become_standby(self, log_processor):
        """Test transitioning to standby role"""
        # Mock dependencies with AsyncMock
        log_processor.stop_request_handler = AsyncMock()
        log_processor.monitor_primary = AsyncMock()
        
        await log_processor.become_standby()
        
        assert log_processor.role == NodeRole.STANDBY
        assert log_processor.state == NodeState.STANDBY
        assert log_processor.stop_request_handler.called
        assert log_processor.monitor_primary.called
    
    async def test_health_status(self, log_processor):
        """Test health status reporting"""
        log_processor.running = True
        log_processor.state = NodeState.PRIMARY
        
        health = log_processor.get_health_status()
        
        assert health['node_id'] == "test_node"
        assert health['state'] == "primary"
        assert health['healthy'] == True
        assert 'metrics' in health
