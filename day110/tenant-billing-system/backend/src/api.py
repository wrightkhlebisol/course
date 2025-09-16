from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, date, timedelta
from typing import Optional
import sqlite3
import uvicorn

from usage_collector import UsageCollector
from billing_engine import BillingEngine
from report_generator import ReportGenerator
from quota_enforcer import QuotaEnforcer
from models import UsageMetric, PricingTier

app = FastAPI(title="Tenant Usage Reporting & Billing API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
usage_collector = UsageCollector()
billing_engine = BillingEngine()
report_generator = ReportGenerator()
quota_enforcer = QuotaEnforcer()

@app.on_event("startup")
async def startup_event():
    """Initialize database and start usage simulation"""
    # Create sample tenants
    conn = sqlite3.connect("usage.db")
    cursor = conn.cursor()
    
    tenants = [
        ('tenant_1', 'Acme Corp', 'starter'),
        ('tenant_2', 'TechStart Inc', 'professional'),
        ('tenant_3', 'Scale Systems', 'professional'),
        ('tenant_enterprise', 'Enterprise Corp', 'enterprise')
    ]
    
    for tenant_id, name, tier in tenants:
        cursor.execute(
            'INSERT OR IGNORE INTO tenants (id, name, tier) VALUES (?, ?, ?)',
            (tenant_id, name, tier)
        )
    
    conn.commit()
    conn.close()
    
    # Start usage data simulation
    usage_collector.start_simulation()
    print("✅ Usage data simulation started")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown"""
    usage_collector.stop_simulation()

@app.get("/")
async def root():
    return {"message": "Tenant Usage Reporting & Billing API", "version": "1.0.0"}

@app.get("/tenants")
async def get_tenants():
    """Get all tenants"""
    conn = sqlite3.connect("usage.db")
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, tier FROM tenants')
    tenants = [{'id': row[0], 'name': row[1], 'tier': row[2]} for row in cursor.fetchall()]
    conn.close()
    return tenants

@app.get("/usage/{tenant_id}/current")
async def get_current_usage(tenant_id: str):
    """Get current usage for a tenant"""
    current_usage = usage_collector.get_current_usage(tenant_id)
    return current_usage

@app.get("/usage/{tenant_id}/billing")
async def get_billing(
    tenant_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get billing calculation for a tenant"""
    if not start_date:
        start_date = date.today().replace(day=1)  # First day of current month
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        
    if not end_date:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    billing = billing_engine.calculate_billing(tenant_id, start_date, end_date)
    return billing.dict()

@app.get("/usage/{tenant_id}/report")
async def get_usage_report(
    tenant_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    format: str = Query("json", description="Report format: json, csv")
):
    """Generate usage report for a tenant"""
    if not start_date:
        start_date = date.today().replace(day=1)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        
    if not end_date:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    report = report_generator.generate_usage_report(tenant_id, start_date, end_date)
    
    if format.lower() == "csv":
        csv_content = report_generator.export_report_csv(report)
        return JSONResponse(
            content={"csv_data": csv_content},
            headers={"Content-Type": "application/json"}
        )
    
    return report.dict()

@app.get("/usage/{tenant_id}/quota")
async def get_quota_status(tenant_id: str):
    """Get quota status for a tenant"""
    quota_status = quota_enforcer.get_tenant_quota_status(tenant_id)
    return quota_status.dict()

@app.post("/usage/{tenant_id}/check-quota")
async def check_quota(tenant_id: str, operation: str = Query(...), bytes_size: Optional[int] = None):
    """Check quota before operation"""
    if operation == "ingestion" and bytes_size:
        within_quota, quota_info = quota_enforcer.check_ingestion_quota(tenant_id, bytes_size)
        return {"within_quota": within_quota, "quota_info": quota_info}
    elif operation == "query":
        within_quota, quota_info = quota_enforcer.check_query_quota(tenant_id)
        return {"within_quota": within_quota, "quota_info": quota_info}
    else:
        raise HTTPException(status_code=400, detail="Invalid operation or missing parameters")

@app.get("/usage/{tenant_id}/summary")
async def get_executive_summary(
    tenant_id: str,
    month: Optional[int] = Query(None, description="Month (1-12)"),
    year: Optional[int] = Query(None, description="Year")
):
    """Get executive summary for a tenant"""
    if not month:
        month = date.today().month
    if not year:
        year = date.today().year
        
    summary = report_generator.generate_executive_summary(tenant_id, month, year)
    return summary

@app.get("/dashboard/overview")
async def get_dashboard_overview():
    """Get overview data for dashboard"""
    tenants = []
    
    conn = sqlite3.connect("usage.db")
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, tier FROM tenants')
    
    for tenant_id, name, tier in cursor.fetchall():
        current_usage = usage_collector.get_current_usage(tenant_id)
        
        # Get current month billing
        today = date.today()
        start_of_month = today.replace(day=1)
        billing = billing_engine.calculate_billing(tenant_id, start_of_month, today)
        
        tenants.append({
            'tenant_id': tenant_id,
            'name': name,
            'tier': tier,
            'daily_bytes_gb': round(current_usage['daily_bytes_ingested'] / (1024**3), 4),
            'monthly_cost': billing.total_cost,
            'storage_gb': round(current_usage['current_storage_used'] / (1024**3), 4),
            'daily_queries': current_usage['daily_queries_processed']
        })
    
    conn.close()
    
    # Calculate totals
    total_cost = sum(t['monthly_cost'] for t in tenants)
    total_storage = sum(t['storage_gb'] for t in tenants)
    total_queries = sum(t['daily_queries'] for t in tenants)
    
    return {
        'tenants': tenants,
        'totals': {
            'total_monthly_cost': round(total_cost, 2),
            'total_storage_gb': round(total_storage, 2),
            'total_daily_queries': total_queries,
            'active_tenants': len(tenants)
        },
        'generated_at': datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
