from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
import os

from services.log_monitor import LogMonitor

# Create routers
retention_router = APIRouter()
compliance_router = APIRouter()
storage_router = APIRouter()
logs_router = APIRouter()

logger = logging.getLogger(__name__)

# Initialize log monitor
storage_dirs = {
    'hot': '/tmp/logs/hot',
    'warm': '/tmp/logs/warm', 
    'cold': '/tmp/logs/cold'
}
log_monitor = LogMonitor(storage_dirs)

# Mock data for demonstration
SAMPLE_POLICIES = [
    {
        "id": "policy_001",
        "name": "application_logs_30_days",
        "retention_days": 30,
        "action": "delete",
        "priority": 1,
        "conditions": {
            "source": "application",
            "level": ["debug", "info"]
        }
    },
    {
        "id": "policy_002", 
        "name": "security_logs_7_years",
        "retention_days": 2555,
        "action": "archive",
        "priority": 10,
        "conditions": {
            "source": "security",
            "level": ["warning", "error"]
        }
    },
    {
        "id": "policy_003",
        "name": "financial_logs_7_years",
        "retention_days": 2555,
        "action": "archive",
        "priority": 10,
        "conditions": {
            "category": "financial"
        }
    }
]

# Simulation state
SIMULATION_STATE = {
    "active_jobs": 2,
    "storage_freed_gb": 0.1567,
    "compliance_score": 95.5,
    "logs_processed_today": 1250,
    "logs_deleted_today": 45,
    "logs_archived_today": 12,
    "storage_saved_mb": 156.7
}

# Retention endpoints
@retention_router.get("/")
async def get_retention_policies():
    """Get all retention policies"""
    return {
        "policies": SAMPLE_POLICIES,
        "total": len(SAMPLE_POLICIES),
        "timestamp": datetime.utcnow().isoformat()
    }

@retention_router.get("/policies/")
async def get_policies():
    """Get all retention policies (for frontend)"""
    policies_with_metadata = []
    for i, policy in enumerate(SAMPLE_POLICIES):
        policies_with_metadata.append({
            "id": i + 1,
            "name": policy["name"],
            "retention_days": policy["retention_days"],
            "action": policy["action"],
            "priority": policy["priority"],
            "compliance_tag": "SOX" if policy["priority"] == 10 else None,
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-15T10:00:00Z",
            "is_active": True
        })
    return policies_with_metadata

@retention_router.get("/policies/{policy_id}")
async def get_policy(policy_id: str):
    """Get specific retention policy"""
    for policy in SAMPLE_POLICIES:
        if policy["id"] == policy_id:
            return policy
    raise HTTPException(status_code=404, detail="Policy not found")

@retention_router.post("/policies/")
async def create_policy(policy: Dict[str, Any]):
    """Create new retention policy"""
    new_policy = {
        "id": f"policy_{len(SAMPLE_POLICIES) + 1:03d}",
        "created_at": datetime.utcnow().isoformat(),
        **policy
    }
    SAMPLE_POLICIES.append(new_policy)
    return new_policy

@retention_router.get("/metrics")
async def get_retention_metrics():
    """Get retention system metrics"""
    return {
        "total_policies": len(SAMPLE_POLICIES),
        "active_jobs": SIMULATION_STATE["active_jobs"],
        "storage_freed_gb": SIMULATION_STATE["storage_freed_gb"],
        "compliance_score": SIMULATION_STATE["compliance_score"],
        "logs_processed_today": SIMULATION_STATE["logs_processed_today"],
        "logs_deleted_today": SIMULATION_STATE["logs_deleted_today"],
        "logs_archived_today": SIMULATION_STATE["logs_archived_today"],
        "storage_saved_mb": SIMULATION_STATE["storage_saved_mb"],
        "timestamp": datetime.utcnow().isoformat()
    }

# Simulation endpoints
@retention_router.post("/simulate/start")
async def start_simulation():
    """Start retention job simulation"""
    SIMULATION_STATE["active_jobs"] += 1
    logger.info("Simulation: Started new retention job")
    return {
        "message": "Retention job started",
        "active_jobs": SIMULATION_STATE["active_jobs"],
        "timestamp": datetime.utcnow().isoformat()
    }

@retention_router.post("/simulate/process")
async def process_simulation():
    """Process logs simulation"""
    # Generate actual logs during simulation
    try:
        log_monitor.generate_sample_logs(50)  # Generate 50 new logs
        logger.info("Simulation: Generated sample logs")
    except Exception as e:
        logger.warning(f"Simulation: Could not generate logs: {e}")
    
    # Simulate processing logs
    new_logs_processed = 500
    new_logs_deleted = 25
    new_logs_archived = 8
    
    SIMULATION_STATE["logs_processed_today"] += new_logs_processed
    SIMULATION_STATE["logs_deleted_today"] += new_logs_deleted
    SIMULATION_STATE["logs_archived_today"] += new_logs_archived
    
    logger.info(f"Simulation: Processed {new_logs_processed} logs")
    return {
        "message": f"Processed {new_logs_processed} logs",
        "logs_processed": new_logs_processed,
        "logs_deleted": new_logs_deleted,
        "logs_archived": new_logs_archived,
        "timestamp": datetime.utcnow().isoformat()
    }

@retention_router.post("/simulate/storage")
async def update_storage_simulation():
    """Update storage simulation"""
    # Simulate storage updates
    storage_freed_mb = 75.3
    storage_freed_gb = storage_freed_mb / 1024
    
    SIMULATION_STATE["storage_freed_gb"] += storage_freed_gb
    SIMULATION_STATE["storage_saved_mb"] += storage_freed_mb
    
    logger.info(f"Simulation: Freed {storage_freed_mb} MB of storage")
    return {
        "message": f"Freed {storage_freed_mb} MB of storage",
        "storage_freed_mb": storage_freed_mb,
        "storage_freed_gb": storage_freed_gb,
        "timestamp": datetime.utcnow().isoformat()
    }

@retention_router.post("/simulate/complete")
async def complete_simulation():
    """Complete simulation"""
    # Complete the job
    SIMULATION_STATE["active_jobs"] = max(0, SIMULATION_STATE["active_jobs"] - 1)
    
    # Slightly improve compliance score
    SIMULATION_STATE["compliance_score"] = min(100, SIMULATION_STATE["compliance_score"] + 0.5)
    
    logger.info("Simulation: Completed retention job")
    return {
        "message": "Retention job completed",
        "active_jobs": SIMULATION_STATE["active_jobs"],
        "compliance_score": SIMULATION_STATE["compliance_score"],
        "timestamp": datetime.utcnow().isoformat()
    }

@retention_router.post("/simulate/reset")
async def reset_simulation():
    """Reset simulation state"""
    global SIMULATION_STATE
    SIMULATION_STATE = {
        "active_jobs": 2,
        "storage_freed_gb": 0.1567,
        "compliance_score": 95.5,
        "logs_processed_today": 1250,
        "logs_deleted_today": 45,
        "logs_archived_today": 12,
        "storage_saved_mb": 156.7
    }
    
    logger.info("Simulation: Reset to initial state")
    return {
        "message": "Simulation reset to initial state",
        "state": SIMULATION_STATE,
        "timestamp": datetime.utcnow().isoformat()
    }

@retention_router.get("/jobs/")
async def get_retention_jobs():
    """Get retention jobs"""
    return [
        {
            "id": 1,
            "job_id": "job_001",
            "policy_name": "application_logs_30_days",
            "status": "completed",
            "logs_processed": 1250,
            "bytes_freed": 164000000,  # 156.7 MB in bytes
            "started_at": "2025-07-18T04:00:00Z",
            "completed_at": "2025-07-18T04:15:00Z",
            "error_message": None
        },
        {
            "id": 2,
            "job_id": "job_002", 
            "policy_name": "security_logs_7_years",
            "status": "running",
            "logs_processed": 500,
            "bytes_freed": 0,
            "started_at": "2025-07-18T04:20:00Z",
            "completed_at": None,
            "error_message": None
        },
        {
            "id": 3,
            "job_id": "job_003",
            "policy_name": "financial_logs_7_years", 
            "status": "failed",
            "logs_processed": 0,
            "bytes_freed": 0,
            "started_at": "2025-07-18T04:10:00Z",
            "completed_at": "2025-07-18T04:12:00Z",
            "error_message": "Storage quota exceeded"
        }
    ]

@retention_router.post("/process")
async def process_logs(background_tasks: BackgroundTasks, logs: List[Dict[str, Any]]):
    """Process logs for retention evaluation"""
    background_tasks.add_task(process_logs_background, logs)
    return {
        "message": f"Processing {len(logs)} logs in background",
        "job_id": f"job_{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow().isoformat()
    }

async def process_logs_background(logs: List[Dict[str, Any]]):
    """Background task to process logs"""
    logger.info(f"Processing {len(logs)} logs in background")
    # Simulate processing
    await asyncio.sleep(2)
    logger.info("Log processing completed")

# Compliance endpoints
@compliance_router.get("/")
async def get_compliance_status():
    """Get overall compliance status"""
    return {
        "compliance_score": 95.5,
        "frameworks": {
            "gdpr": {
                "status": "compliant",
                "score": 98.0,
                "last_audit": "2024-01-15T10:00:00Z"
            },
            "sox": {
                "status": "compliant", 
                "score": 92.0,
                "last_audit": "2024-01-10T14:30:00Z"
            },
            "hipaa": {
                "status": "not_applicable",
                "score": 0.0,
                "last_audit": None
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@compliance_router.get("/report")
async def generate_compliance_report():
    """Generate compliance report"""
    return {
        "report_id": f"report_{datetime.utcnow().timestamp()}",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_policies": len(SAMPLE_POLICIES),
            "compliant_policies": len(SAMPLE_POLICIES) - 1,
            "violations": 1
        },
        "details": {
            "gdpr_violations": [],
            "sox_violations": ["policy_001: retention period too short"],
            "hipaa_violations": []
        }
    }

# Storage endpoints
@storage_router.get("/")
async def get_storage_status():
    """Get storage tier status"""
    return {
        "storage_tiers": {
            "hot": {
                "path": "/tmp/logs/hot",
                "size_mb": 45.2,
                "file_count": 1250,
                "status": "healthy"
            },
            "warm": {
                "path": "/tmp/logs/warm", 
                "size_mb": 234.7,
                "file_count": 5670,
                "status": "healthy"
            },
            "cold": {
                "path": "/tmp/logs/cold",
                "size_mb": 1245.8,
                "file_count": 23450,
                "status": "healthy"
            }
        },
        "total_size_mb": 1525.7,
        "timestamp": datetime.utcnow().isoformat()
    }

@storage_router.post("/migrate")
async def migrate_data(source_tier: str, target_tier: str, file_ids: List[str]):
    """Migrate data between storage tiers"""
    return {
        "migration_id": f"mig_{datetime.utcnow().timestamp()}",
        "source_tier": source_tier,
        "target_tier": target_tier,
        "files_migrated": len(file_ids),
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat()
    }

# Log monitoring endpoints
@logs_router.post("/generate")
async def generate_sample_logs(count: int = Query(100, ge=1, le=1000)):
    """Generate sample log files"""
    try:
        log_monitor.generate_sample_logs(count)
        logger.info(f"Generated {count} sample log files")
        return {
            "message": f"Generated {count} sample log files",
            "count": count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@logs_router.get("/stats")
async def get_log_stats():
    """Get log statistics"""
    try:
        stats = log_monitor.get_log_stats()
        return {
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting log stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@logs_router.get("/search")
async def search_logs(
    storage_type: Optional[str] = Query(None, description="Storage type: hot, warm, cold"),
    log_type: Optional[str] = Query(None, description="Log type: application, security, system, error, access"),
    level: Optional[str] = Query(None, description="Log level: debug, info, warning, error, critical"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return")
):
    """Search logs by criteria"""
    try:
        logs = log_monitor.get_logs_by_criteria(
            storage_type=storage_type,
            log_type=log_type,
            level=level,
            limit=limit
        )
        return {
            "logs": logs,
            "count": len(logs),
            "filters": {
                "storage_type": storage_type,
                "log_type": log_type,
                "level": level
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@logs_router.post("/cleanup")
async def cleanup_old_logs(days_to_keep: int = Query(30, ge=1, le=365)):
    """Clean up old log files"""
    try:
        result = log_monitor.cleanup_old_logs(days_to_keep)
        logger.info(f"Cleanup completed: {result['deleted_files']} files deleted, {result['freed_space_mb']:.2f} MB freed")
        return {
            "message": "Log cleanup completed",
            "deleted_files": result['deleted_files'],
            "freed_space_mb": result['freed_space_mb'],
            "days_to_keep": days_to_keep,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 