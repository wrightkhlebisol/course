"""Error grouping and lifecycle management service"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc
import json

from app.models.error import Error, ErrorGroup
from app.services.fingerprinting import fingerprinter
from app.core.config import settings

class ErrorGroupingService:
    """Service for managing error groups and lifecycle"""
    
    def __init__(self):
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
    
    async def process_error(self, session: AsyncSession, error_data: Dict) -> Dict:
        """Process a new error and assign it to a group"""
        # Generate fingerprint
        fingerprint = fingerprinter.generate_fingerprint(error_data)
        
        # Check if error group exists
        group = await self._find_or_create_group(session, fingerprint, error_data)
        
        # Create error record
        error = Error(
            group_id=group.id,
            message=error_data.get('message', ''),
            stack_trace=error_data.get('stack_trace', ''),
            level=error_data.get('level', 'error'),
            platform=error_data.get('platform', ''),
            release=error_data.get('release', ''),
            environment=error_data.get('environment', 'production'),
            user_id=error_data.get('user_id'),
            request_id=error_data.get('request_id'),
            trace_id=error_data.get('trace_id'),
            span_id=error_data.get('span_id'),
            context=error_data.get('context', {}),
            tags=error_data.get('tags', {}),
            extra=error_data.get('extra', {}),
        )
        
        session.add(error)
        
        # Update group statistics
        await self._update_group_stats(session, group)
        
        await session.commit()
        
        return {
            "error_id": error.event_id,
            "group_id": group.id,
            "fingerprint": fingerprint,
            "status": group.status
        }
    
    async def _find_or_create_group(self, session: AsyncSession, fingerprint: str, error_data: Dict) -> ErrorGroup:
        """Find existing group or create new one"""
        # Try exact fingerprint match first
        result = await session.execute(
            select(ErrorGroup).where(ErrorGroup.fingerprint == fingerprint)
        )
        group = result.scalar_one_or_none()
        
        if group:
            return group
        
        # Create new group
        group = ErrorGroup(
            fingerprint=fingerprint,
            title=self._generate_title(error_data),
            status="new",
            level=error_data.get('level', 'error'),
            platform=error_data.get('platform', ''),
            tags=error_data.get('tags', {})
        )
        
        session.add(group)
        await session.flush()
        return group
    
    async def _update_group_stats(self, session: AsyncSession, group: ErrorGroup):
        """Update group occurrence count and last seen"""
        group.count += 1
        group.last_seen = datetime.utcnow()
        
        # Check for regression
        if group.status == "resolved" and group.count > 0:
            group.status = "regressed"
    
    def _generate_title(self, error_data: Dict) -> str:
        """Generate a human-readable title for the error group"""
        message = error_data.get('message', '')
        error_type = error_data.get('type', '')
        
        # Try to extract meaningful title from message
        if message:
            # Normalize the message for title
            title = fingerprinter._normalize_message(message)
            if len(title) > 100:
                title = title[:97] + "..."
            return title
        
        if error_type:
            return f"{error_type}"
        
        return "Unknown Error"
    
    async def get_groups_summary(self, session: AsyncSession, filters: Dict = None) -> List[Dict]:
        """Get summary of error groups with filters"""
        try:
            # Check if table exists by trying a simple query
            query = select(ErrorGroup)
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    query = query.where(ErrorGroup.status == filters['status'])
                if filters.get('level'):
                    query = query.where(ErrorGroup.level == filters['level'])
                if filters.get('platform'):
                    query = query.where(ErrorGroup.platform == filters['platform'])
            
            # Order by last seen desc (handle case where last_seen might be None)
            try:
                query = query.order_by(desc(ErrorGroup.last_seen))
            except:
                # If ordering fails, just get results without ordering
                pass
            
            result = await session.execute(query)
            groups = result.scalars().all()
            
            # If no groups, return empty list
            if not groups:
                return []
            
            summary = []
            for group in groups:
                try:
                    summary.append({
                        "id": group.id,
                        "fingerprint": group.fingerprint,
                        "title": group.title,
                        "status": group.status,
                        "count": group.count or 0,
                        "level": group.level,
                        "platform": group.platform,
                        "first_seen": group.first_seen.isoformat() if group.first_seen else None,
                        "last_seen": group.last_seen.isoformat() if group.last_seen else None,
                        "resolved_at": group.resolved_at.isoformat() if group.resolved_at else None,
                        "assigned_to": group.assigned_to,
                    })
                except Exception as e:
                    # Skip groups that can't be serialized
                    print(f"⚠️ Error serializing group {group.id}: {str(e)}")
                    continue
            
            return summary
        except Exception as e:
            # Log the error for debugging
            import traceback
            error_msg = f"Error in get_groups_summary: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            # Return empty list instead of raising to prevent 500 errors
            return []
    
    async def update_group_status(self, session: AsyncSession, group_id: int, status: str, assigned_to: str = None) -> bool:
        """Update error group status and assignment"""
        update_data = {"status": status}
        
        if assigned_to:
            update_data["assigned_to"] = assigned_to
            
        if status == "resolved":
            update_data["resolved_at"] = datetime.utcnow()
        
        result = await session.execute(
            update(ErrorGroup)
            .where(ErrorGroup.id == group_id)
            .values(**update_data)
        )
        
        await session.commit()
        return result.rowcount > 0

# Global instance
grouping_service = ErrorGroupingService()
