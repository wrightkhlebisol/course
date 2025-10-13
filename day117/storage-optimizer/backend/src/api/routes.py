from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

# This will be injected from main.py
storage_optimizer = None
policy_engine = None
cost_analyzer = None

class PolicyRequest(BaseModel):
    policy_name: str

@router.get("/metrics")
async def get_metrics():
    """Get current storage metrics"""
    from main import storage_optimizer
    return await storage_optimizer.get_metrics()

@router.get("/cost/realtime")
async def get_realtime_cost():
    """Get real-time cost metrics"""
    from main import cost_analyzer
    return await cost_analyzer.get_real_time_metrics()

@router.get("/cost/history/{days}")
async def get_cost_history(days: int):
    """Get cost history for specified days"""
    from main import cost_analyzer
    return await cost_analyzer.get_cost_history(days)

@router.get("/cost/tiers")
async def get_tier_costs():
    """Get cost breakdown by storage tier"""
    from main import cost_analyzer
    return await cost_analyzer.get_tier_costs()

@router.post("/optimize")
async def trigger_optimization():
    """Manually trigger storage optimization"""
    from main import storage_optimizer
    return await storage_optimizer.optimize_storage()

@router.get("/policies")
async def get_policies():
    """Get all available policies"""
    from main import policy_engine
    return await policy_engine.get_all_policies()

@router.get("/policies/active")
async def get_active_policy():
    """Get currently active policy"""
    from main import policy_engine
    return await policy_engine.get_active_policy()

@router.post("/policies/set")
async def set_policy(request: PolicyRequest):
    """Set active optimization policy"""
    from main import policy_engine
    success = await policy_engine.set_policy(request.policy_name)
    if success:
        return {"message": f"Policy set to {request.policy_name}"}
    raise HTTPException(status_code=400, detail="Invalid policy name")

@router.get("/logs")
async def get_log_entries():
    """Get sample log entries"""
    from main import storage_optimizer
    return await storage_optimizer.get_log_entries()
