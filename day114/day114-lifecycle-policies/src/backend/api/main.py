from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import asyncio
import json
import os
import random
from datetime import datetime

from ..database import get_db, create_tables
from ..models import LogEntry, PolicyRule
from ..policy_engine.engine import PolicyEngine
from ..policy_engine.manager import PolicyManager

app = FastAPI(title="Data Lifecycle Policy Engine", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "build")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")

# Global instances
policy_engine = PolicyEngine()
policy_manager = PolicyManager()
engine_task = None

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    global engine_task
    
    # Create database tables
    create_tables()
    
    # Create default policies
    policy_manager.create_default_policies()
    
    # Start policy engine
    engine_task = asyncio.create_task(policy_engine.start())
    
    # Generate sample data for demo
    await generate_sample_logs()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global engine_task
    
    policy_engine.stop()
    if engine_task:
        engine_task.cancel()

@app.get("/")
async def serve_dashboard():
    """Serve the React dashboard"""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "build")
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        return {"message": "Dashboard not found. Please build the frontend first."}

@app.get("/api/policies")
async def get_policies():
    """Get all policies with statistics"""
    return policy_manager.get_policies()

@app.get("/api/tier-stats")
async def get_tier_statistics():
    """Get storage tier statistics"""
    return policy_manager.get_tier_statistics()

@app.get("/api/compliance-report")
async def get_compliance_report(days: int = 30):
    """Get compliance report"""
    return policy_manager.get_compliance_report(days)

@app.get("/api/logs")
async def get_logs(tier: str = None, log_type: str = None, db: Session = Depends(get_db)):
    """Get log entries with optional filtering"""
    query = db.query(LogEntry)
    
    if tier:
        query = query.filter(LogEntry.current_tier == tier)
    if log_type:
        query = query.filter(LogEntry.log_type == log_type)
    
    logs = query.limit(100).all()
    
    return [{
        "id": log.id,
        "log_id": log.log_id,
        "log_type": log.log_type,
        "current_tier": log.current_tier,
        "file_size_mb": round((log.file_size_bytes or 0) / (1024*1024), 2),
        "created_at": log.created_at.isoformat(),
        "last_accessed": log.last_accessed.isoformat(),
        "access_count": log.access_count
    } for log in logs]

@app.post("/api/generate-logs")
async def generate_logs(count: int = 100, db: Session = Depends(get_db)):
    """Generate sample log entries for testing"""
    log_types = ["customer_activity", "transaction_logs", "debug_logs", "security_logs"]
    
    generated = 0
    for i in range(count):
        log_type = random.choice(log_types)
        log_id = f"{log_type}_{datetime.now().strftime('%Y%m%d')}_{i:06d}"
        
        # Create file in hot tier
        file_path = f"./storage/hot/{log_id}.log"
        os.makedirs("./storage/hot", exist_ok=True)
        
        # Generate sample log content
        content = json.dumps({
            "timestamp": datetime.now().isoformat(),
            "log_type": log_type,
            "message": f"Sample {log_type} message {i}",
            "log_metadata": {"sample": True}
        })
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Create database entry
        log_entry = LogEntry(
            log_id=log_id,
            log_type=log_type,
            current_tier="hot",
            file_path=file_path,
            file_size_bytes=len(content.encode()),
            created_at=datetime.now(),
            log_metadata={"generated": True}
        )
        
        db.add(log_entry)
        generated += 1
    
    db.commit()
    return {"message": f"Generated {generated} sample logs"}

async def generate_sample_logs():
    """Generate initial sample data"""
    from ..database import SessionLocal
    
    db = SessionLocal()
    try:
        # Check if we already have sample data
        existing_logs = db.query(LogEntry).first()
        if existing_logs:
            return
        
        log_types = ["customer_activity", "transaction_logs", "debug_logs", "security_logs"]
        
        for i in range(50):
            log_type = random.choice(log_types)
            log_id = f"{log_type}_{datetime.now().strftime('%Y%m%d')}_{i:06d}"
            
            # Create file in hot tier
            file_path = f"./storage/hot/{log_id}.log"
            os.makedirs("./storage/hot", exist_ok=True)
            
            content = json.dumps({
                "timestamp": datetime.now().isoformat(),
                "log_type": log_type,
                "message": f"Sample {log_type} message {i}",
                "log_metadata": {"sample": True}
            })
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            log_entry = LogEntry(
                log_id=log_id,
                log_type=log_type,
                current_tier="hot",
                file_path=file_path,
                file_size_bytes=len(content.encode()),
                created_at=datetime.now(),
                log_metadata={"generated": True}
            )
            
            db.add(log_entry)
        
        db.commit()
        
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
