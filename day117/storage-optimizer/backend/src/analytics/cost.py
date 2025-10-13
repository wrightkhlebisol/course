import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List
import json

class CostAnalyzer:
    def __init__(self):
        self.cost_history = []
        self.monitoring_active = False
        
    async def start_monitoring(self):
        """Start cost monitoring"""
        self.monitoring_active = True
        asyncio.create_task(self._monitoring_loop())
        
    async def get_real_time_metrics(self) -> Dict:
        """Get real-time cost and optimization metrics"""
        current_time = datetime.now()
        
        # Simulate cost reduction over time
        base_cost = 1000.0
        optimization_factor = min(0.7, 0.1 + (len(self.cost_history) * 0.02))
        current_cost = base_cost * optimization_factor
        
        # Calculate savings
        potential_savings = base_cost - current_cost
        savings_percentage = (potential_savings / base_cost) * 100
        
        return {
            "timestamp": current_time.isoformat(),
            "current_monthly_cost": round(current_cost, 2),
            "potential_monthly_savings": round(potential_savings, 2),
            "savings_percentage": round(savings_percentage, 1),
            "optimization_score": round(optimization_factor * 100, 1),
            "storage_efficiency": round(random.uniform(75, 95), 1),
            "compression_ratio": round(random.uniform(2.5, 4.0), 1),
            "active_optimizations": random.randint(5, 25)
        }
        
    async def get_cost_history(self, days: int = 30) -> List[Dict]:
        """Get historical cost data"""
        history = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            base_cost = 1000.0
            optimization = min(0.7, 0.1 + (i * 0.01))
            cost = base_cost * optimization
            
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "cost": round(cost + random.uniform(-50, 50), 2),
                "savings": round((base_cost - cost), 2)
            })
            
        return list(reversed(history))
        
    async def get_tier_costs(self) -> Dict:
        """Get cost breakdown by storage tier"""
        return {
            "hot_storage": {"cost": 345.67, "percentage": 45, "size_gb": 1500},
            "warm_storage": {"cost": 123.45, "percentage": 35, "size_gb": 2469},
            "cold_storage": {"cost": 67.89, "percentage": 20, "size_gb": 6789}
        }
        
    async def _monitoring_loop(self):
        """Background cost monitoring"""
        while self.monitoring_active:
            metrics = await self.get_real_time_metrics()
            self.cost_history.append(metrics)
            
            # Keep only last 100 entries
            if len(self.cost_history) > 100:
                self.cost_history = self.cost_history[-100:]
                
            await asyncio.sleep(10)
