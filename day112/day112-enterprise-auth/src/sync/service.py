import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from src.auth.models import User, UserGroup, AuthLog
from src.ldap.service import ldap_service
import structlog
from typing import List, Dict, Optional
from config.settings import settings
from datetime import datetime
import re

logger = structlog.get_logger()

class UserSyncService:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.role_mapping = {
            'administrators': 'Admin',
            'log-analysts': 'Analyst', 
            'log-viewers': 'Viewer',
            'domain admins': 'Admin',
            'it-team': 'Admin'
        }
    
    def map_group_to_role(self, group_name: str) -> str:
        """Map LDAP group name to application role"""
        group_name_lower = group_name.lower()
        
        # Direct mapping
        if group_name_lower in self.role_mapping:
            return self.role_mapping[group_name_lower]
        
        # Pattern matching
        if 'admin' in group_name_lower:
            return 'Admin'
        elif 'analyst' in group_name_lower or 'developer' in group_name_lower:
            return 'Analyst'
        else:
            return 'Viewer'
    
    async def sync_user(self, username: str) -> bool:
        """Synchronize a single user from LDAP"""
        try:
            # First authenticate to get user info (using a dummy password check)
            # In production, you'd have a service account or admin query
            with Session(self.engine) as db:
                # Check if user exists
                existing_user = db.execute(
                    select(User).where(User.username == username)
                ).scalar_one_or_none()
                
                if existing_user:
                    # Update last sync time
                    existing_user.last_sync = datetime.utcnow()
                    
                    # Get user's current groups from LDAP
                    if existing_user.full_name:  # If we have user DN
                        user_dn = f"cn={username},{settings.LDAP_BASE_DN}"
                        groups = await ldap_service.get_user_groups(user_dn)
                        
                        # Update group memberships
                        # Delete existing groups
                        db.query(UserGroup).filter(UserGroup.user_id == existing_user.id).delete()
                        
                        # Add current groups
                        for group in groups:
                            role = self.map_group_to_role(group['name'])
                            user_group = UserGroup(
                                user_id=existing_user.id,
                                group_dn=group['dn'],
                                group_name=group['name'],
                                role=role
                            )
                            db.add(user_group)
                    
                    db.commit()
                    
                    # Log sync activity
                    auth_log = AuthLog(
                        username=username,
                        action='sync',
                        success=True,
                        message='User synchronized successfully'
                    )
                    db.add(auth_log)
                    db.commit()
                    
                    logger.info("User synchronized", username=username)
                    return True
                else:
                    logger.warning("User not found in database", username=username)
                    return False
                    
        except Exception as e:
            logger.error("Error syncing user", username=username, error=str(e))
            return False
    
    async def sync_all_users(self) -> Dict[str, int]:
        """Synchronize all users from database with LDAP"""
        stats = {'success': 0, 'failed': 0, 'total': 0}
        
        try:
            with Session(self.engine) as db:
                users = db.execute(select(User).where(User.is_active == True)).scalars().all()
                stats['total'] = len(users)
                
                # Process users in batches
                batch_size = settings.BATCH_SIZE
                for i in range(0, len(users), batch_size):
                    batch = users[i:i + batch_size]
                    tasks = [self.sync_user(user.username) for user in batch]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, Exception):
                            stats['failed'] += 1
                        elif result:
                            stats['success'] += 1
                        else:
                            stats['failed'] += 1
                    
                    # Small delay between batches
                    await asyncio.sleep(1)
            
            logger.info("Batch sync completed", stats=stats)
            return stats
            
        except Exception as e:
            logger.error("Error in batch sync", error=str(e))
            stats['failed'] = stats['total']
            return stats
    
    async def create_user_from_ldap(self, user_info: Dict) -> Optional[User]:
        """Create new user from LDAP information"""
        try:
            with Session(self.engine) as db:
                user = User(
                    username=user_info['username'],
                    email=user_info.get('email'),
                    full_name=user_info.get('full_name'),
                    department=user_info.get('department'),
                    manager=user_info.get('manager'),
                    is_active=True,
                    last_sync=datetime.utcnow()
                )
                
                db.add(user)
                db.commit()
                db.refresh(user)
                
                # Get and add user groups
                if user_info.get('dn'):
                    groups = await ldap_service.get_user_groups(user_info['dn'])
                    for group in groups:
                        role = self.map_group_to_role(group['name'])
                        user_group = UserGroup(
                            user_id=user.id,
                            group_dn=group['dn'],
                            group_name=group['name'],
                            role=role
                        )
                        db.add(user_group)
                
                db.commit()
                logger.info("User created from LDAP", username=user.username)
                return user
                
        except Exception as e:
            logger.error("Error creating user from LDAP", error=str(e), user_info=user_info)
            return None

# Global sync service instance
sync_service = UserSyncService()
