from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from datetime import datetime
import uuid
import json

from models.tenant import TenantModel, TenantState
from services.provisioning import ProvisioningService
from services.security import SecurityService
from services.monitoring import MonitoringService
from utils.database import get_db, init_database
from workflows.tenant_orchestrator import TenantOrchestrator

# Initialize services
provisioning_service = ProvisioningService()
security_service = SecurityService()
monitoring_service = MonitoringService()
orchestrator = TenantOrchestrator(provisioning_service, security_service, monitoring_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_database()
    print("🚀 Tenant Lifecycle Management API started")
    yield
    # Shutdown (if needed)

app = FastAPI(title="Tenant Lifecycle Management", version="1.0.0", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/tenants/onboard")
async def onboard_tenant(tenant_data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Initiate tenant onboarding process"""
    try:
        tenant_id = str(uuid.uuid4())
        
        # Create tenant record
        tenant = TenantModel(
            id=tenant_id,
            name=tenant_data["name"],
            email=tenant_data["email"],
            plan=tenant_data.get("plan", "basic"),
            state=TenantState.PROVISIONING,
            created_at=datetime.now(),
            config=tenant_data.get("config", {})
        )
        
        db.add(tenant)
        db.commit()
        
        # Start onboarding workflow in background
        background_tasks.add_task(orchestrator.onboard_tenant, tenant_id, tenant_data)
        
        return {
            "tenant_id": tenant_id,
            "status": "provisioning_started",
            "message": "Tenant onboarding initiated"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Onboarding failed: {str(e)}")

@app.post("/api/tenants/{tenant_id}/offboard")
async def offboard_tenant(tenant_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Initiate tenant offboarding process"""
    try:
        tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Update state to deprovisioning
        tenant.state = TenantState.DEPROVISIONING
        tenant.updated_at = datetime.now()
        db.commit()
        
        # Start offboarding workflow in background
        background_tasks.add_task(orchestrator.offboard_tenant, tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "status": "deprovisioning_started",
            "message": "Tenant offboarding initiated"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Offboarding failed: {str(e)}")

@app.get("/api/tenants")
async def list_tenants(db: Session = Depends(get_db)):
    """List all tenants with their current state"""
    tenants = db.query(TenantModel).all()
    return [{
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "plan": tenant.plan,
        "state": tenant.state.value,
        "created_at": tenant.created_at.isoformat(),
        "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None
    } for tenant in tenants]

@app.get("/api/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Get detailed tenant information"""
    tenant = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "plan": tenant.plan,
        "state": tenant.state.value,
        "config": tenant.config,
        "api_key": tenant.api_key,
        "created_at": tenant.created_at.isoformat(),
        "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None,
        "resources": await orchestrator.get_tenant_resources(tenant_id)
    }

@app.get("/api/stats/dashboard")
async def dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    from sqlalchemy import func
    
    stats = db.query(
        TenantModel.state,
        func.count(TenantModel.id).label('count')
    ).group_by(TenantModel.state).all()
    
    total_tenants = db.query(func.count(TenantModel.id)).scalar()
    
    return {
        "total_tenants": total_tenants,
        "state_distribution": {stat.state.value: stat.count for stat in stats},
        "recent_activity": await monitoring_service.get_recent_activity()
    }

# Serve React frontend
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
