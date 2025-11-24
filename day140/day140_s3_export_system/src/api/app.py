"""FastAPI application for export management."""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import yaml
import structlog
import os

from src.storage.client import StorageClient
from src.export.engine import ExportEngine
from src.scheduler.job_scheduler import ExportScheduler

logger = structlog.get_logger()

app = FastAPI(title="S3 Export System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
storage_client = None
export_engine = None
scheduler = None
config = {}

class ExportRequest(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class ExportResponse(BaseModel):
    status: str
    records_exported: int
    message: str


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global storage_client, export_engine, scheduler, config
    
    # Load configuration
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize storage client
    storage_config = config['storage']
    storage_client = StorageClient(
        bucket_name=storage_config['bucket_name'],
        region=storage_config.get('region', 'us-east-1'),
        endpoint_url=storage_config.get('endpoint_url'),
        access_key=os.getenv('AWS_ACCESS_KEY_ID'),
        secret_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    # Initialize export engine
    export_engine = ExportEngine(config, storage_client)
    
    # Initialize scheduler
    scheduler = ExportScheduler(config)
    
    # Add scheduled export job
    cron_expr = config['export'].get('schedule_interval', '0 2 * * *')
    scheduler.add_export_job(
        'daily_export',
        lambda: export_engine.export_logs(),
        cron_expr
    )
    
    scheduler.start()
    
    logger.info("Export system initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if scheduler:
        scheduler.shutdown()
    logger.info("Export system shutdown")


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "service": "S3 Export System",
        "version": "1.0.0",
        "status": "operational"
    }


@app.post("/api/export/manual", response_model=ExportResponse)
async def trigger_manual_export(
    request: ExportRequest,
    background_tasks: BackgroundTasks
):
    """Trigger manual export."""
    try:
        start_time = datetime.fromisoformat(request.start_time) if request.start_time else None
        end_time = datetime.fromisoformat(request.end_time) if request.end_time else None
        
        # Trigger export in background
        result = export_engine.export_logs(start_time, end_time)
        
        return ExportResponse(
            status=result['status'],
            records_exported=result.get('records_exported', 0),
            message="Export completed successfully" if result['status'] == 'success' else result.get('error', 'Export failed')
        )
        
    except Exception as e:
        logger.error(f"Manual export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/status")
async def get_export_status():
    """Get export system status."""
    try:
        last_export = export_engine.get_last_export_time()
        bucket_size = storage_client.get_bucket_size()
        
        # Handle last_export_time - could be datetime or string
        if last_export:
            if hasattr(last_export, 'isoformat'):
                last_export = last_export.isoformat()
            elif isinstance(last_export, str):
                last_export = last_export  # Already a string
        else:
            last_export = None
        
        return {
            "last_export_time": last_export,
            "bucket_size_bytes": bucket_size,
            "bucket_size_gb": round(bucket_size / (1024**3), 2),
            "scheduled_jobs": scheduler.list_jobs()
        }
    except Exception as e:
        logger.error(f"Get status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/history")
async def get_export_history(limit: int = 10):
    """Get recent export history."""
    try:
        from sqlalchemy import text
        
        with export_engine.metadata_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT export_id, export_time, s3_key, record_count, 
                       file_size, status, error_message
                FROM export_metadata
                ORDER BY export_time DESC
                LIMIT :limit
            """), {'limit': limit})
            
            history = []
            for row in result:
                # Handle export_time - could be datetime or string
                export_time = row[1]
                if export_time:
                    if hasattr(export_time, 'isoformat'):
                        export_time = export_time.isoformat()
                    elif isinstance(export_time, str):
                        export_time = export_time  # Already a string
                else:
                    export_time = None
                
                history.append({
                    'export_id': row[0],
                    'export_time': export_time,
                    's3_key': row[2],
                    'record_count': row[3],
                    'file_size': row[4],
                    'file_size_mb': round(row[4] / (1024**2), 2) if row[4] else 0,
                    'status': row[5],
                    'error_message': row[6]
                })
            
            return {'history': history}
            
    except Exception as e:
        logger.error(f"Get history failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/storage/objects")
async def list_storage_objects(prefix: str = ""):
    """List objects in storage."""
    try:
        objects = storage_client.list_objects(prefix)
        
        return {
            'objects': [
                {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'size_mb': round(obj['Size'] / (1024**2), 2),
                    'last_modified': obj['LastModified'].isoformat()
                }
                for obj in objects[:100]  # Limit to 100
            ],
            'total_count': len(objects)
        }
    except Exception as e:
        logger.error(f"List objects failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
