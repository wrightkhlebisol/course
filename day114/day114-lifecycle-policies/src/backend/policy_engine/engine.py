import asyncio
import json
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import LogEntry, PolicyRule, PolicyExecution
from ..database import SessionLocal
import structlog

logger = structlog.get_logger(__name__)

class PolicyEngine:
    def __init__(self):
        self.storage_config = self._load_storage_config()
        self.default_policies = self._load_default_policies()
        self.running = False
        
    def _load_storage_config(self) -> Dict[str, Any]:
        with open('./config/storage_tiers.json', 'r') as f:
            return json.load(f)
            
    def _load_default_policies(self) -> Dict[str, Any]:
        with open('./config/default_policies.json', 'r') as f:
            return json.load(f)
    
    async def start(self):
        """Start the policy evaluation loop"""
        self.running = True
        logger.info("Policy engine started")
        
        while self.running:
            try:
                await self._evaluate_policies()
                await asyncio.sleep(int(os.getenv('POLICY_EVALUATION_INTERVAL', '30')))
            except Exception as e:
                logger.error(f"Policy evaluation error: {e}")
                await asyncio.sleep(5)
    
    async def _evaluate_policies(self):
        """Evaluate all policies against current log entries"""
        db = SessionLocal()
        try:
            # Get all active policy rules
            active_policies = db.query(PolicyRule).filter(PolicyRule.enabled == True).all()
            
            for policy in active_policies:
                await self._execute_policy(policy, db)
                
        finally:
            db.close()
    
    async def _execute_policy(self, policy: PolicyRule, db: Session):
        """Execute a specific policy rule"""
        # Get log entries matching this policy
        log_entries = db.query(LogEntry).filter(
            LogEntry.log_type == policy.log_type
        ).all()
        
        for entry in log_entries:
            action_needed = self._evaluate_log_against_policy(entry, policy)
            if action_needed:
                await self._execute_action(entry, policy, action_needed, db)
    
    def _evaluate_log_against_policy(self, entry: LogEntry, policy: PolicyRule) -> Optional[str]:
        """Check if a log entry needs action based on policy"""
        conditions = policy.conditions
        now = datetime.utcnow()
        
        if policy.rule_type == "time_based":
            age_hours = (now - entry.created_at).total_seconds() / 3600
            
            # Check for tier transitions
            if entry.current_tier == "hot" and age_hours > conditions.get('hot_max_hours', 168):  # 7 days
                return "move_to_warm"
            elif entry.current_tier == "warm" and age_hours > conditions.get('warm_max_hours', 2160):  # 90 days
                return "move_to_cold"
            elif entry.current_tier == "cold" and conditions.get('archive_after_hours'):
                if age_hours > conditions['archive_after_hours']:
                    return "archive"
            
            # Check for deletion
            if conditions.get('delete_after_hours') and age_hours > conditions['delete_after_hours']:
                return "delete"
        
        elif policy.rule_type == "size_based":
            tier_config = self.storage_config[entry.current_tier]
            tier_usage = self._calculate_tier_usage(entry.current_tier)
            
            if tier_usage > tier_config.get('max_size_gb', float('inf')) * 0.8:  # 80% threshold
                return self._get_next_tier_action(entry.current_tier)
        
        return None
    
    async def _execute_action(self, entry: LogEntry, policy: PolicyRule, action: str, db: Session):
        """Execute the determined action on a log entry"""
        logger.info(f"Executing {action} for log {entry.log_id}")
        
        execution = PolicyExecution(
            policy_id=policy.id,
            log_entry_id=entry.id,
            action_taken=action
        )
        
        try:
            if action == "move_to_warm":
                await self._move_log_to_tier(entry, "warm")
            elif action == "move_to_cold":
                await self._move_log_to_tier(entry, "cold")
            elif action == "archive":
                await self._move_log_to_tier(entry, "archive")
            elif action == "delete":
                await self._delete_log(entry)
            
            execution.success = True
            execution.cost_impact = self._calculate_cost_impact(entry, action)
            
        except Exception as e:
            execution.success = False
            execution.error_message = str(e)
            logger.error(f"Action execution failed: {e}")
        
        db.add(execution)
        db.commit()
    
    async def _move_log_to_tier(self, entry: LogEntry, target_tier: str):
        """Move a log file to a different storage tier"""
        source_path = entry.file_path
        target_config = self.storage_config[target_tier]
        target_path = os.path.join(target_config['path'], os.path.basename(source_path))
        
        # Ensure target directory exists
        os.makedirs(target_config['path'], exist_ok=True)
        
        # Move the file
        shutil.move(source_path, target_path)
        
        # Update database record
        db = SessionLocal()
        try:
            entry.current_tier = target_tier
            entry.file_path = target_path
            db.commit()
        finally:
            db.close()
    
    async def _delete_log(self, entry: LogEntry):
        """Delete a log file and its database record"""
        if os.path.exists(entry.file_path):
            os.remove(entry.file_path)
        
        db = SessionLocal()
        try:
            db.delete(entry)
            db.commit()
        finally:
            db.close()
    
    def _calculate_tier_usage(self, tier: str) -> float:
        """Calculate current usage of a storage tier in GB"""
        tier_path = self.storage_config[tier]['path']
        total_size = 0
        
        if os.path.exists(tier_path):
            for dirpath, dirnames, filenames in os.walk(tier_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
        
        return total_size / (1024**3)  # Convert to GB
    
    def _get_next_tier_action(self, current_tier: str) -> str:
        """Get the next tier action for size-based policies"""
        tier_hierarchy = ["hot", "warm", "cold", "archive"]
        current_index = tier_hierarchy.index(current_tier)
        
        if current_index < len(tier_hierarchy) - 1:
            next_tier = tier_hierarchy[current_index + 1]
            return f"move_to_{next_tier}"
        
        return "archive"
    
    def _calculate_cost_impact(self, entry: LogEntry, action: str) -> float:
        """Calculate the cost impact of an action"""
        file_size_gb = entry.file_size_bytes / (1024**3)
        
        if action.startswith("move_to_"):
            target_tier = action.replace("move_to_", "")
            old_cost = file_size_gb * self.storage_config[entry.current_tier]['cost_per_gb']
            new_cost = file_size_gb * self.storage_config[target_tier]['cost_per_gb']
            return old_cost - new_cost  # Positive means cost savings
        
        return 0.0
    
    def stop(self):
        """Stop the policy engine"""
        self.running = False
        logger.info("Policy engine stopped")
