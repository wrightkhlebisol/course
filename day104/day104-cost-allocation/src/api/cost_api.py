from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
import yaml

# Load configuration
with open('../config/cost_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Adjust database path for running from src directory
if 'database' in config and 'path' in config['database']:
    if not config['database']['path'].startswith('/'):
        config['database']['path'] = '../' + config['database']['path']

# Initialize components
from cost_engine.core import CostEngine
from collectors.usage_collector import UsageCollector
from reporting.report_generator import ReportGenerator

cost_engine = CostEngine(config)
usage_collector = UsageCollector(cost_engine, config)
report_generator = ReportGenerator(cost_engine, config)

app = FastAPI(title="Cost Allocation API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UsageRequest(BaseModel):
    tenant_id: str
    resource_type: str
    amount: float
    unit: str
    metadata: Optional[Dict[str, Any]] = None

class CostCalculationRequest(BaseModel):
    start_date: str
    end_date: str
    tenant_ids: Optional[List[str]] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logging.basicConfig(level=logging.INFO)
    # Start usage collection in background
    import asyncio
    asyncio.create_task(usage_collector.start_collection())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await usage_collector.stop_collection()

@app.get("/")
async def root():
    return {"message": "Cost Allocation API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/usage/track")
async def track_usage(usage_request: UsageRequest):
    """Track resource usage for a tenant"""
    try:
        from cost_engine.core import ResourceUsage
        usage = ResourceUsage(
            tenant_id=usage_request.tenant_id,
            resource_type=usage_request.resource_type,
            amount=usage_request.amount,
            unit=usage_request.unit,
            timestamp=datetime.now(),
            metadata=usage_request.metadata
        )
        
        success = await cost_engine.track_usage(usage)
        if success:
            return {"status": "success", "message": "Usage tracked successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to track usage")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/costs/calculate")
async def calculate_costs(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Calculate costs for a date range"""
    try:
        start_time = datetime.fromisoformat(start_date)
        end_time = datetime.fromisoformat(end_date)
        
        costs = await cost_engine.calculate_costs(start_time, end_time)
        
        return {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "costs": costs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tenants/{tenant_id}/costs")
async def get_tenant_costs(
    tenant_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get detailed cost breakdown for a specific tenant"""
    try:
        start_time = datetime.fromisoformat(start_date)
        end_time = datetime.fromisoformat(end_date)
        
        tenant_costs = await cost_engine.get_tenant_costs(tenant_id, start_time, end_time)
        
        return tenant_costs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tenants/{tenant_id}/usage/realtime")
async def get_realtime_usage(tenant_id: str):
    """Get real-time usage metrics for a tenant"""
    try:
        usage_data = await cost_engine.get_realtime_usage(tenant_id)
        return {
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "usage": usage_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/daily")
async def generate_daily_report(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today")
):
    """Generate daily cost report"""
    try:
        report_date = datetime.fromisoformat(date) if date else None
        report = await report_generator.generate_daily_report(report_date)
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/weekly")
async def generate_weekly_report(
    week_start: Optional[str] = Query(None, description="Week start date (YYYY-MM-DD)")
):
    """Generate weekly cost report"""
    try:
        start_date = datetime.fromisoformat(week_start) if week_start else None
        report = await report_generator.generate_weekly_report(start_date)
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/monthly")
async def generate_monthly_report(
    month_start: Optional[str] = Query(None, description="Month start date (YYYY-MM-DD)")
):
    """Generate monthly cost report"""
    try:
        start_date = datetime.fromisoformat(month_start) if month_start else None
        report = await report_generator.generate_monthly_report(start_date)
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/data")
async def get_dashboard_data():
    """Get real-time dashboard data"""
    try:
        dashboard_data = await report_generator.get_realtime_dashboard_data()
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tenants")
async def list_tenants():
    """List all configured tenants"""
    return {
        "tenants": list(config['cost_allocation']['tenants'].keys()),
        "pricing_models": list(config['cost_allocation']['pricing_models'].keys())
    }

@app.get("/config")
async def get_configuration():
    """Get current cost allocation configuration"""
    return config['cost_allocation']

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config['api']['host'], port=config['api']['port'])
