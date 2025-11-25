from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

@router.get("/dashboard")
async def serve_dashboard():
    """Serve the dashboard HTML"""
    dashboard_path = Path(__file__).parent.parent / "dashboard" / "dashboard.html"
    return FileResponse(dashboard_path)
