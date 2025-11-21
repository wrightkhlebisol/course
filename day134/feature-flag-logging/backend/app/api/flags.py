from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.services.feature_flag_service import flag_service
from app.models.flag_log import FlagLog
from pydantic import BaseModel

router = APIRouter()

class FlagCreate(BaseModel):
    name: str
    description: str = None
    enabled: bool = False
    rollout_percentage: str = "0"
    target_groups: List[str] = []
    metadata: Dict[str, Any] = {}

class FlagUpdate(BaseModel):
    description: str = None
    enabled: bool = None
    rollout_percentage: str = None
    target_groups: List[str] = None
    metadata: Dict[str, Any] = None

class FlagEvaluation(BaseModel):
    flag_name: str
    user_context: Dict[str, Any]
    default_value: bool = False

@router.post("/flags")
async def create_flag(flag_data: FlagCreate, db: Session = Depends(get_db)):
    """Create a new feature flag"""
    try:
        flag = await flag_service.create_flag(
            db=db,
            name=flag_data.name,
            description=flag_data.description,
            enabled=flag_data.enabled,
            rollout_percentage=flag_data.rollout_percentage,
            target_groups=flag_data.target_groups,
            metadata=flag_data.metadata,
            created_by="api_user"  # In real app, get from auth
        )
        return flag.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/flags")
async def get_flags(db: Session = Depends(get_db)):
    """Get all feature flags"""
    flags = await flag_service.get_all_flags(db)
    return [flag.to_dict() for flag in flags]

@router.put("/flags/{flag_id}")
async def update_flag(flag_id: str, flag_updates: FlagUpdate, db: Session = Depends(get_db)):
    """Update feature flag"""
    updates = flag_updates.dict(exclude_unset=True)
    flag = await flag_service.update_flag(
        db=db,
        flag_id=flag_id,
        updates=updates,
        updated_by="api_user"
    )
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return flag.to_dict()

@router.delete("/flags/{flag_id}")
async def delete_flag(flag_id: str, db: Session = Depends(get_db)):
    """Delete feature flag"""
    success = await flag_service.delete_flag(db, flag_id, "api_user")
    if not success:
        raise HTTPException(status_code=404, detail="Flag not found")
    return {"message": "Flag deleted successfully"}

@router.post("/flags/evaluate")
async def evaluate_flag(evaluation: FlagEvaluation, db: Session = Depends(get_db)):
    """Evaluate feature flag for user context"""
    result = await flag_service.evaluate_flag(
        db=db,
        flag_name=evaluation.flag_name,
        user_context=evaluation.user_context,
        default_value=evaluation.default_value
    )
    return {"flag_name": evaluation.flag_name, "enabled": result}

@router.get("/flags/{flag_name}/logs")
async def get_flag_logs(flag_name: str, db: Session = Depends(get_db)):
    """Get logs for specific flag"""
    logs = db.query(FlagLog).filter(FlagLog.flag_name == flag_name).order_by(FlagLog.timestamp.desc()).limit(100).all()
    return [log.to_dict() for log in logs]

@router.get("/logs/recent")
async def get_recent_logs(db: Session = Depends(get_db)):
    """Get recent flag activity logs"""
    logs = db.query(FlagLog).order_by(FlagLog.timestamp.desc()).limit(50).all()
    return [log.to_dict() for log in logs]
