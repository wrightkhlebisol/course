from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import structlog
import asyncio
import json
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.spark_jobs.spark_manager import SparkManager
from src.spark_jobs.log_analyzer import LogAnalyzer

logger = structlog.get_logger()

app = FastAPI(title="Spark Log Analytics API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Spark
spark_manager = SparkManager()
analyzer = None

# WebSocket connections
active_connections: List[WebSocket] = []

class AnalysisRequest(BaseModel):
    input_path: str
    output_path: Optional[str] = "data/output"

@app.on_event("startup")
async def startup_event():
    """Initialize Spark on startup"""
    global analyzer
    logger.info("Starting Spark Log Analytics API")
    spark = spark_manager.initialize_spark()
    analyzer = LogAnalyzer(spark)
    logger.info("Spark initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Spark")
    spark_manager.stop_spark()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Spark Log Analytics",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    dashboard_path = os.path.join(os.path.dirname(__file__), '../dashboard/index.html')
    with open(dashboard_path, 'r') as f:
        return f.read()

@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon to prevent 404 errors"""
    return Response(content="", media_type="image/x-icon")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    cluster_info = spark_manager.get_cluster_info()
    return {
        "status": "healthy",
        "spark_cluster": cluster_info
    }

@app.get("/cluster/info")
async def cluster_info():
    """Get Spark cluster information"""
    return spark_manager.get_cluster_info()

@app.post("/analyze")
async def run_analysis(request: AnalysisRequest):
    """Run full log analysis"""
    try:
        logger.info("Starting analysis", input_path=request.input_path)
        
        # Run analysis
        summary = analyzer.run_full_analysis(request.input_path, request.output_path)
        
        # Record in job history
        spark_manager.record_job_execution(
            job_name="full_analysis",
            status="success",
            records_processed=summary['total_records_processed'],
            duration=summary['duration_seconds'],
            details=summary
        )
        
        # Notify WebSocket clients
        await broadcast_message({
            "type": "analysis_complete",
            "data": summary
        })
        
        return {
            "status": "success",
            "summary": summary
        }
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error("Analysis failed", error=str(e), traceback=error_trace)
        spark_manager.record_job_execution(
            job_name="full_analysis",
            status="failed",
            records_processed=0,
            duration=0,
            details={"error": str(e), "traceback": error_trace}
        )
        raise HTTPException(status_code=500, detail=f"{str(e)}\n\n{error_trace}")

@app.get("/jobs/history")
async def job_history(limit: int = 10):
    """Get job execution history"""
    return {
        "jobs": spark_manager.get_job_history(limit)
    }

@app.get("/results/{analysis_type}")
async def get_results(analysis_type: str, limit: int = 100):
    """Get analysis results"""
    try:
        if analyzer and analysis_type in analyzer.results:
            df = analyzer.results[analysis_type]
            results = df.limit(limit).toPandas().to_dict(orient='records')
            return {
                "analysis_type": analysis_type,
                "count": len(results),
                "data": results
            }
        else:
            return {
                "analysis_type": analysis_type,
                "count": 0,
                "data": [],
                "message": "No results available"
            }
    except Exception as e:
        logger.error("Failed to get results", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
            
            # Send periodic updates
            cluster_info = spark_manager.get_cluster_info()
            await websocket.send_json({
                "type": "status_update",
                "data": cluster_info
            })
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket disconnected")

async def broadcast_message(message: Dict):
    """Broadcast message to all WebSocket connections"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
