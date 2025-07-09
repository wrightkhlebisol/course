from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from enum import Enum
import json
import time

class NodeState(Enum):
    INACTIVE = "inactive"
    STANDBY = "standby"
    PRIMARY = "primary"
    ELECTION = "election"
    FAILED = "failed"

class NodeRole(Enum):
    STANDBY = "standby"
    PRIMARY = "primary"

@dataclass
class HeartbeatMessage:
    node_id: str
    timestamp: float
    state: NodeState
    role: NodeRole
    data: Dict[str, Any]
    
    def to_json(self) -> str:
        data = asdict(self)
        data['state'] = self.state.value
        data['role'] = self.role.value
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'HeartbeatMessage':
        data = json.loads(json_str)
        return cls(
            node_id=data['node_id'],
            timestamp=data['timestamp'],
            state=NodeState(data['state']),
            role=NodeRole(data['role']),
            data=data['data']
        )

@dataclass
class ElectionMessage:
    candidate_id: str
    timestamp: float
    priority: int
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ElectionMessage':
        data = json.loads(json_str)
        return cls(**data)

@dataclass
class FailoverEvent:
    event_type: str
    from_node: Optional[str]
    to_node: Optional[str]
    timestamp: float
    duration: float
    metadata: Dict[str, Any]
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
