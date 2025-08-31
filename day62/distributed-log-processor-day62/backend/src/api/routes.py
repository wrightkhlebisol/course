"""
API Routes for Backpressure System
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import time
import random

from core.log_processor import LogPriority

router = APIRouter()

class LogSubmission(BaseModel):
    content: str
    priority: str = "NORMAL"
    source: str = "api"

class LoadTestConfig(BaseModel):
    duration_seconds: int = 30
    requests_per_second: int = 100
    spike_multiplier: float = 5.0

@router.post("/logs/submit")
async def submit_log(log_data: LogSubmission, request: Request):
    """Submit a log message for processing"""
    try:
        priority = LogPriority[log_data.priority.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid priority level")
    
    log_processor = request.app.state.log_processor
    result = await log_processor.submit_log(
        content=log_data.content,
        priority=priority,
        source=log_data.source
    )
    
    return result

@router.get("/system/status")
async def get_system_status(request: Request):
    """Get current system status and metrics"""
    backpressure_manager = request.app.state.backpressure_manager
    log_processor = request.app.state.log_processor
    circuit_breaker = request.app.state.circuit_breaker
    metrics_collector = request.app.state.metrics_collector
    
    return {
        "backpressure": backpressure_manager.get_current_status(),
        "processor": log_processor.get_statistics(),
        "circuit_breaker": circuit_breaker.get_state(),
        "metrics": await metrics_collector.get_all_metrics(),
        "timestamp": time.time()
    }

@router.get("/system/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@router.post("/test/load")
async def start_load_test(config: LoadTestConfig, request: Request, background_tasks: BackgroundTasks):
    """Start a load test to demonstrate backpressure"""
    background_tasks.add_task(_run_load_test, request.app.state, config)
    return {
        "status": "started",
        "config": config.dict(),
        "message": "Load test started in background"
    }

@router.post("/test/spike")
async def create_traffic_spike(request: Request, background_tasks: BackgroundTasks):
    """Create a sudden traffic spike"""
    config = LoadTestConfig(duration_seconds=10, requests_per_second=50, spike_multiplier=10.0)
    background_tasks.add_task(_run_spike_test, request.app.state, config)
    return {"status": "spike_initiated", "message": "Traffic spike started"}

async def _run_load_test(app_state, config: LoadTestConfig):
    """Background task to run load test"""
    log_processor = app_state.log_processor
    
    # Normal load phase
    normal_rps = config.requests_per_second
    spike_rps = int(normal_rps * config.spike_multiplier)
    
    # Run normal load for half duration
    normal_duration = config.duration_seconds // 2
    await _generate_load(log_processor, normal_rps, normal_duration, "normal")
    
    # Run spike load for remaining duration
    spike_duration = config.duration_seconds - normal_duration
    await _generate_load(log_processor, spike_rps, spike_duration, "spike")

async def _run_spike_test(app_state, config: LoadTestConfig):
    """Background task to run spike test"""
    log_processor = app_state.log_processor
    await _generate_load(log_processor, int(config.requests_per_second * config.spike_multiplier), 
                        config.duration_seconds, "spike")

async def _generate_load(log_processor, rps: int, duration: int, phase: str):
    """Generate synthetic load"""
    interval = 1.0 / rps
    end_time = time.time() + duration
    
    priorities = [LogPriority.CRITICAL, LogPriority.HIGH, LogPriority.NORMAL, LogPriority.LOW]
    priority_weights = [0.05, 0.15, 0.65, 0.15]  # Distribution of priorities
    
    while time.time() < end_time:
        # Select random priority based on weights
        priority = random.choices(priorities, weights=priority_weights)[0]
        
        # Generate log content
        content = f"Load test log - {phase} phase - {time.time():.3f}"
        
        # Submit log
        await log_processor.submit_log(
            content=content,
            priority=priority,
            source=f"load_test_{phase}"
        )
        
        await asyncio.sleep(interval)
