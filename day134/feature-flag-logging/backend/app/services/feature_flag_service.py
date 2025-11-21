from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.feature_flag import FeatureFlag
from app.services.logging_service import logging_service
from app.core.redis_client import redis_client
import json
import random

class FeatureFlagService:
    async def create_flag(
        self, 
        db: Session, 
        name: str, 
        description: str = None,
        enabled: bool = False,
        rollout_percentage: str = "0",
        target_groups: List[str] = None,
        metadata: Dict = None,
        created_by: str = None
    ) -> FeatureFlag:
        """Create new feature flag"""
        
        flag = FeatureFlag(
            name=name,
            description=description,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            target_groups=target_groups or [],
            flag_metadata=metadata or {},
            created_by=created_by
        )
        
        db.add(flag)
        db.commit()
        db.refresh(flag)
        
        # Log creation event
        await logging_service.log_flag_event(
            db=db,
            flag_id=flag.id,
            flag_name=flag.name,
            event_type="create",
            new_state=flag.to_dict(),
            user_id=created_by
        )
        
        # Cache the flag
        await redis_client.set_flag(flag.name, flag.to_dict())
        
        return flag
    
    async def update_flag(
        self,
        db: Session,
        flag_id: str,
        updates: Dict[str, Any],
        updated_by: str = None
    ) -> Optional[FeatureFlag]:
        """Update existing feature flag"""
        
        flag = db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
        if not flag:
            return None
        
        # Capture previous state
        previous_state = flag.to_dict()
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(flag, key):
                setattr(flag, key, value)
        
        if updated_by:
            flag.updated_by = updated_by
        
        db.commit()
        db.refresh(flag)
        
        # Log update event
        await logging_service.log_flag_event(
            db=db,
            flag_id=flag.id,
            flag_name=flag.name,
            event_type="update",
            previous_state=previous_state,
            new_state=flag.to_dict(),
            user_id=updated_by
        )
        
        # Update cache
        await redis_client.set_flag(flag.name, flag.to_dict())
        
        return flag
    
    async def evaluate_flag(
        self,
        db: Session,
        flag_name: str,
        user_context: Dict[str, Any],
        default_value: bool = False
    ) -> bool:
        """Evaluate feature flag for given user context"""
        
        # Try cache first
        cached_flag = await redis_client.get_flag(flag_name)
        
        if cached_flag:
            flag_data = cached_flag
        else:
            # Fallback to database
            flag = db.query(FeatureFlag).filter(FeatureFlag.name == flag_name).first()
            if not flag:
                return default_value
            flag_data = flag.to_dict()
            # Cache for next time
            await redis_client.set_flag(flag_name, flag_data)
        
        # Basic evaluation logic
        if not flag_data.get("enabled", False):
            result = False
        else:
            rollout_percentage = int(flag_data.get("rollout_percentage", "0"))
            if rollout_percentage >= 100:
                result = True
            elif rollout_percentage <= 0:
                result = False
            else:
                # Simple percentage-based rollout
                user_hash = hash(user_context.get("user_id", "anonymous")) % 100
                result = user_hash < rollout_percentage
        
        # Log evaluation
        await logging_service.log_flag_evaluation(
            db=db,
            flag_name=flag_name,
            result=result,
            user_context=user_context,
            evaluation_context={
                "flag_id": flag_data.get("id", "unknown"),
                "rollout_percentage": flag_data.get("rollout_percentage", "0")
            }
        )
        
        # Update metrics
        await redis_client.increment_evaluation_count(flag_name, user_context.get("user_id", "anonymous"))
        
        return result
    
    async def get_all_flags(self, db: Session) -> List[FeatureFlag]:
        """Get all feature flags"""
        return db.query(FeatureFlag).all()
    
    async def delete_flag(self, db: Session, flag_id: str, deleted_by: str = None) -> bool:
        """Delete feature flag"""
        flag = db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
        if not flag:
            return False
        
        # Log deletion
        await logging_service.log_flag_event(
            db=db,
            flag_id=flag.id,
            flag_name=flag.name,
            event_type="delete",
            previous_state=flag.to_dict(),
            user_id=deleted_by
        )
        
        # Remove from cache
        await redis_client.invalidate_flag(flag.name)
        
        # Delete from database
        db.delete(flag)
        db.commit()
        
        return True

flag_service = FeatureFlagService()
