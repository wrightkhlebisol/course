"""Error collection and management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Optional
from datetime import datetime

from app.core.database import get_db_session
from app.services.grouping import grouping_service
from app.services.websocket_manager import websocket_manager
from app.models.error import Error, ErrorGroup

router = APIRouter()

@router.post("/collect")
async def collect_error(
    error_data: Dict,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session)
):
    """Collect and process a new error"""
    try:
        # Process error through grouping service
        result = await grouping_service.process_error(session, error_data)
        
        # Send real-time update
        background_tasks.add_task(
            websocket_manager.send_error_update,
            {
                "event": "new_error",
                "error_id": result["error_id"],
                "group_id": result["group_id"],
                "fingerprint": result["fingerprint"]
            }
        )
        
        return {
            "success": True,
            "error_id": result["error_id"],
            "group_id": result["group_id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing failed: {str(e)}")

@router.get("/groups")
async def get_error_groups(
    status: Optional[str] = None,
    level: Optional[str] = None,
    platform: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get list of error groups with optional filters"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if level:
            filters["level"] = level  
        if platform:
            filters["platform"] = platform
        
        groups = await grouping_service.get_groups_summary(session, filters)
        # Ensure we always return a list, even if empty
        if groups is None:
            groups = []
        return {"groups": groups}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Error in get_error_groups: {str(e)}")
        print(error_trace)
        # Return empty list instead of 500 error to prevent frontend crashes
        # Log the error but don't break the UI
        return {"groups": [], "error": str(e)}

@router.get("/groups/{group_id}")
async def get_error_group_detail(
    group_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """Get detailed information about an error group"""
    # Get group info
    result = await session.execute(
        select(ErrorGroup).where(ErrorGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Error group not found")
    
    # Get recent errors in group
    result = await session.execute(
        select(Error)
        .where(Error.group_id == group_id)
        .order_by(Error.timestamp.desc())
        .limit(50)
    )
    errors = result.scalars().all()
    
    error_list = []
    for error in errors:
        error_list.append({
            "id": error.event_id,
            "message": error.message,
            "timestamp": error.timestamp.isoformat(),
            "level": error.level,
            "platform": error.platform,
            "release": error.release,
            "environment": error.environment,
            "user_id": error.user_id,
            "trace_id": error.trace_id,
            "context": error.context,
            "tags": error.tags
        })
    
    return {
        "group": {
            "id": group.id,
            "fingerprint": group.fingerprint,
            "title": group.title,
            "status": group.status,
            "count": group.count,
            "level": group.level,
            "platform": group.platform,
            "first_seen": group.first_seen.isoformat(),
            "last_seen": group.last_seen.isoformat(),
            "assigned_to": group.assigned_to,
            "tags": group.tags
        },
        "errors": error_list
    }

@router.put("/groups/{group_id}/status")
async def update_group_status(
    group_id: int,
    status_data: Dict,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session)
):
    """Update error group status"""
    status = status_data.get("status")
    assigned_to = status_data.get("assigned_to")
    
    if not status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    if status not in ["new", "acknowledged", "resolved", "ignored"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    success = await grouping_service.update_group_status(session, group_id, status, assigned_to)
    
    if not success:
        raise HTTPException(status_code=404, detail="Error group not found")
    
    # Send real-time update
    background_tasks.add_task(
        websocket_manager.send_group_update,
        {
            "event": "status_updated",
            "group_id": group_id,
            "status": status,
            "assigned_to": assigned_to
        }
    )
    
    return {"success": True, "message": "Status updated successfully"}

@router.get("/search")
async def search_errors(
    query: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Search errors by message content"""
    result = await session.execute(
        select(Error)
        .join(ErrorGroup)
        .where(Error.message.ilike(f"%{query}%"))
        .order_by(Error.timestamp.desc())
        .limit(100)
    )
    
    errors = result.scalars().all()
    
    search_results = []
    for error in errors:
        search_results.append({
            "error_id": error.event_id,
            "group_id": error.group_id,
            "message": error.message,
            "timestamp": error.timestamp.isoformat(),
            "level": error.level,
            "platform": error.platform
        })
    
    return {"results": search_results, "count": len(search_results)}
