from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import uuid
from services.compliance_service import ComplianceReportGenerator
from apscheduler.schedulers.background import BackgroundScheduler
import json

app = FastAPI(
    title="Compliance Reports API",
    description="Automated compliance reporting system for distributed log processing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
report_generator = ComplianceReportGenerator()
scheduler = BackgroundScheduler()

# Pydantic models
class ReportRequest(BaseModel):
    framework: str
    period_start: datetime
    period_end: datetime
    export_format: str = "pdf"  # pdf, csv, json, xml
    title: Optional[str] = None
    description: Optional[str] = None

class ScheduledReportRequest(BaseModel):
    framework: str
    export_format: str
    schedule_type: str  # daily, weekly, monthly
    recipients: List[str]
    enabled: bool = True

# In-memory storage for demo
reports_database = {}
scheduled_reports = {}

@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    scheduler.start()
    print("🚀 Compliance Reports API started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    scheduler.shutdown()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Compliance Reports API",
        "version": "1.0.0",
        "frameworks": ["SOX", "HIPAA", "PCI_DSS", "GDPR"],
        "formats": ["pdf", "csv", "json", "xml"]
    }

@app.get("/frameworks")
async def get_frameworks():
    """Get supported compliance frameworks"""
    return {
        "frameworks": [
            {
                "name": "SOX",
                "description": "Sarbanes-Oxley Act - Financial reporting controls",
                "retention_days": 2555,  # 7 years
                "required_fields": ["financial_transactions", "admin_access", "approval_workflows"]
            },
            {
                "name": "HIPAA",
                "description": "Health Insurance Portability and Accountability Act",
                "retention_days": 2190,  # 6 years
                "required_fields": ["patient_access", "security_incidents", "audit_logs"]
            },
            {
                "name": "PCI_DSS",
                "description": "Payment Card Industry Data Security Standard",
                "retention_days": 365,  # 1 year minimum
                "required_fields": ["payment_transactions", "cardholder_access", "security_logs"]
            },
            {
                "name": "GDPR",
                "description": "General Data Protection Regulation",
                "retention_days": 1095,  # 3 years
                "required_fields": ["personal_data_access", "consent_logs", "data_breaches"]
            }
        ]
    }

@app.post("/reports/generate")
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """Generate a compliance report"""
    
    # Validate framework
    supported_frameworks = ["SOX", "HIPAA", "PCI_DSS", "GDPR"]
    if request.framework not in supported_frameworks:
        raise HTTPException(status_code=400, detail=f"Framework {request.framework} not supported")
    
    # Generate unique report ID
    report_id = str(uuid.uuid4())
    
    # Initialize report record
    report_record = {
        "id": report_id,
        "framework": request.framework,
        "period_start": request.period_start,
        "period_end": request.period_end,
        "export_format": request.export_format,
        "status": "processing",
        "created_at": datetime.now(),
        "title": request.title or f"{request.framework} Compliance Report",
        "description": request.description or f"Automated {request.framework} compliance report"
    }
    
    reports_database[report_id] = report_record
    
    # Schedule background report generation
    background_tasks.add_task(process_report, report_id, request)
    
    return {
        "report_id": report_id,
        "status": "processing",
        "message": "Report generation started",
        "estimated_completion": datetime.now() + timedelta(minutes=2)
    }

async def process_report(report_id: str, request: ReportRequest):
    """Background task to process report generation"""
    
    try:
        # Update status
        reports_database[report_id]["status"] = "generating"
        
        # Generate report based on framework
        if request.framework == "SOX":
            report_data = await report_generator.generate_sox_report(
                request.period_start, request.period_end
            )
        elif request.framework == "HIPAA":
            report_data = await report_generator.generate_hipaa_report(
                request.period_start, request.period_end
            )
        else:
            # Simulate other frameworks
            report_data = {
                "framework": request.framework,
                "period": f"{request.period_start.date()} to {request.period_end.date()}",
                "summary": {"total_events": 100, "compliance_violations": 2},
                "findings": [f"Sample finding for {request.framework}"],
                "data": {"sample_logs": [{"id": 1, "message": "Sample log entry"}]}
            }
        
        # Export based on format
        filename = f"{request.framework}_{report_id}"
        
        if request.export_format == "pdf":
            filepath = await report_generator.export_to_pdf(report_data, filename)
        elif request.export_format == "csv":
            filepath = await report_generator.export_to_csv(report_data, filename)
        elif request.export_format == "json":
            filepath = os.path.join(report_generator.storage_path, f"{filename}.json")
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {request.export_format}")
        
        # Generate signature
        signature = report_generator.generate_signature(report_data)
        
        # Update report record
        reports_database[report_id].update({
            "status": "completed",
            "filepath": filepath,
            "signature": signature,
            "data_summary": report_data.get("summary", {}),
            "findings_count": len(report_data.get("findings", [])),
            "completed_at": datetime.now()
        })
        
    except Exception as e:
        reports_database[report_id].update({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now()
        })

@app.get("/reports")
async def list_reports():
    """List all reports"""
    return {
        "reports": list(reports_database.values()),
        "total": len(reports_database)
    }

@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get specific report details"""
    if report_id not in reports_database:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return reports_database[report_id]

@app.get("/reports/{report_id}/download")
async def download_report(report_id: str):
    """Download report file"""
    if report_id not in reports_database:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = reports_database[report_id]
    
    if report["status"] != "completed":
        raise HTTPException(status_code=400, detail="Report not ready for download")
    
    filepath = report["filepath"]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    filename = os.path.basename(filepath)
    return FileResponse(filepath, filename=filename)

@app.post("/reports/schedule")
async def schedule_report(request: ScheduledReportRequest):
    """Schedule automated report generation"""
    
    schedule_id = str(uuid.uuid4())
    
    scheduled_reports[schedule_id] = {
        "id": schedule_id,
        "framework": request.framework,
        "export_format": request.export_format,
        "schedule_type": request.schedule_type,
        "recipients": request.recipients,
        "enabled": request.enabled,
        "created_at": datetime.now(),
        "next_run": None
    }
    
    # Add to scheduler based on schedule type
    if request.schedule_type == "daily":
        scheduler.add_job(
            func=generate_scheduled_report,
            trigger="cron",
            hour=9,
            args=[schedule_id],
            id=schedule_id
        )
    elif request.schedule_type == "weekly":
        scheduler.add_job(
            func=generate_scheduled_report,
            trigger="cron",
            day_of_week="mon",
            hour=9,
            args=[schedule_id],
            id=schedule_id
        )
    elif request.schedule_type == "monthly":
        scheduler.add_job(
            func=generate_scheduled_report,
            trigger="cron",
            day=1,
            hour=9,
            args=[schedule_id],
            id=schedule_id
        )
    
    return {
        "schedule_id": schedule_id,
        "message": "Report scheduled successfully",
        "next_execution": "Next business day at 9:00 AM"
    }

def generate_scheduled_report(schedule_id: str):
    """Generate scheduled report"""
    if schedule_id not in scheduled_reports:
        return
    
    schedule = scheduled_reports[schedule_id]
    
    # Generate report for last period
    end_date = datetime.now()
    if schedule["schedule_type"] == "daily":
        start_date = end_date - timedelta(days=1)
    elif schedule["schedule_type"] == "weekly":
        start_date = end_date - timedelta(days=7)
    else:  # monthly
        start_date = end_date - timedelta(days=30)
    
    # Create report request
    report_request = ReportRequest(
        framework=schedule["framework"],
        period_start=start_date,
        period_end=end_date,
        export_format=schedule["export_format"],
        title=f"Scheduled {schedule['framework']} Report",
        description=f"Automated {schedule['schedule_type']} compliance report"
    )
    
    # Generate report (simplified for demo)
    print(f"Generating scheduled report: {schedule_id}")

@app.get("/reports/schedule")
async def list_scheduled_reports():
    """List all scheduled reports"""
    return {
        "scheduled_reports": list(scheduled_reports.values()),
        "total": len(scheduled_reports)
    }

@app.delete("/reports/schedule/{schedule_id}")
async def delete_scheduled_report(schedule_id: str):
    """Delete scheduled report"""
    if schedule_id not in scheduled_reports:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    
    # Remove from scheduler
    try:
        scheduler.remove_job(schedule_id)
    except:
        pass
    
    # Remove from database
    del scheduled_reports[schedule_id]
    
    return {"message": "Scheduled report deleted successfully"}

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    
    total_reports = len(reports_database)
    completed_reports = len([r for r in reports_database.values() if r["status"] == "completed"])
    failed_reports = len([r for r in reports_database.values() if r["status"] == "failed"])
    processing_reports = len([r for r in reports_database.values() if r["status"] == "processing"])
    
    framework_stats = {}
    for report in reports_database.values():
        framework = report["framework"]
        if framework not in framework_stats:
            framework_stats[framework] = 0
        framework_stats[framework] += 1
    
    return {
        "summary": {
            "total_reports": total_reports,
            "completed_reports": completed_reports,
            "failed_reports": failed_reports,
            "processing_reports": processing_reports,
            "success_rate": (completed_reports / total_reports * 100) if total_reports > 0 else 0
        },
        "by_framework": framework_stats,
        "scheduled_reports": len(scheduled_reports),
        "recent_reports": sorted(
            reports_database.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )[:5]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
