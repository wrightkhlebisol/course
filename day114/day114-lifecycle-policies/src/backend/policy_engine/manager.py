from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import PolicyRule, LogEntry, PolicyExecution
from ..database import SessionLocal
from datetime import datetime, timedelta
import json

class PolicyManager:
    def __init__(self):
        self.default_policies = self._load_default_policies()
    
    def _load_default_policies(self) -> Dict[str, Any]:
        with open('./config/default_policies.json', 'r') as f:
            return json.load(f)
    
    def create_default_policies(self):
        """Create default policies from configuration"""
        db = SessionLocal()
        try:
            for log_type, config in self.default_policies.items():
                # Time-based policy for tier transitions
                policy_rule = PolicyRule(
                    name=f"{log_type}_lifecycle",
                    log_type=log_type,
                    rule_type="time_based",
                    conditions={
                        "hot_max_hours": (config.get("hot_retention_days") or 7) * 24,
                        "warm_max_hours": (config.get("warm_retention_days") or 90) * 24,
                        "cold_max_hours": (config.get("cold_retention_days") or 730) * 24,
                        "archive_after_hours": config.get("archive_retention_days"),
                        "delete_after_hours": config.get("delete_after_days") and config["delete_after_days"] * 24
                    },
                    action="lifecycle_management",
                    enabled=True
                )
                
                # Check if policy already exists
                existing = db.query(PolicyRule).filter(
                    PolicyRule.name == policy_rule.name
                ).first()
                
                if not existing:
                    db.add(policy_rule)
            
            db.commit()
            
        finally:
            db.close()
    
    def get_policies(self) -> List[Dict[str, Any]]:
        """Get all policies with their statistics"""
        db = SessionLocal()
        try:
            policies = db.query(PolicyRule).all()
            result = []
            
            for policy in policies:
                # Get execution statistics
                executions = db.query(PolicyExecution).filter(
                    PolicyExecution.policy_id == policy.id
                ).all()
                
                total_executions = len(executions)
                successful_executions = len([e for e in executions if e.success])
                total_cost_savings = sum(e.cost_impact for e in executions if e.cost_impact)
                
                result.append({
                    "id": policy.id,
                    "name": policy.name,
                    "log_type": policy.log_type,
                    "rule_type": policy.rule_type,
                    "enabled": policy.enabled,
                    "conditions": policy.conditions,
                    "statistics": {
                        "total_executions": total_executions,
                        "success_rate": successful_executions / max(total_executions, 1),
                        "cost_savings": total_cost_savings
                    }
                })
            
            return result
            
        finally:
            db.close()
    
    def get_tier_statistics(self) -> Dict[str, Any]:
        """Get statistics for each storage tier"""
        db = SessionLocal()
        try:
            stats = {}
            
            for tier in ["hot", "warm", "cold", "archive"]:
                logs_in_tier = db.query(LogEntry).filter(
                    LogEntry.current_tier == tier
                ).all()
                
                total_files = len(logs_in_tier)
                total_size_bytes = sum(log.file_size_bytes or 0 for log in logs_in_tier)
                total_size_gb = total_size_bytes / (1024**3)
                
                # Get tier configuration for cost calculation
                with open('./config/storage_tiers.json', 'r') as f:
                    tier_config = json.load(f)[tier]
                
                monthly_cost = total_size_gb * tier_config['cost_per_gb']
                
                stats[tier] = {
                    "file_count": total_files,
                    "size_gb": round(total_size_gb, 2),
                    "monthly_cost": round(monthly_cost, 2),
                    "max_size_gb": tier_config.get("max_size_gb"),
                    "utilization_percent": round((total_size_gb / max(tier_config.get("max_size_gb", 1), 1)) * 100, 1) if tier_config.get("max_size_gb") else 0
                }
            
            return stats
            
        finally:
            db.close()
    
    def get_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate compliance report for the specified period"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get policy executions in the period
            executions = db.query(PolicyExecution).filter(
                PolicyExecution.execution_time >= cutoff_date
            ).all()
            
            # Analyze compliance
            total_actions = len(executions)
            successful_actions = len([e for e in executions if e.success])
            failed_actions = total_actions - successful_actions
            
            # Group by action type
            action_stats = {}
            for execution in executions:
                action = execution.action_taken
                if action not in action_stats:
                    action_stats[action] = {"count": 0, "success": 0}
                action_stats[action]["count"] += 1
                if execution.success:
                    action_stats[action]["success"] += 1
            
            # Total cost impact
            total_cost_savings = sum(e.cost_impact for e in executions if e.cost_impact and e.success)
            
            return {
                "period_days": days,
                "total_policy_actions": total_actions,
                "successful_actions": successful_actions,
                "failed_actions": failed_actions,
                "success_rate": successful_actions / max(total_actions, 1),
                "total_cost_savings": round(total_cost_savings, 2),
                "action_breakdown": action_stats,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
