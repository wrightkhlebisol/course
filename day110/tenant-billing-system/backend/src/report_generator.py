import json
from datetime import datetime, date, timedelta
from typing import Dict, List
from models import UsageReport
from billing_engine import BillingEngine
from usage_collector import UsageCollector

class ReportGenerator:
    def __init__(self, db_path: str = "usage.db"):
        self.billing_engine = BillingEngine(db_path)
        self.usage_collector = UsageCollector(db_path)
        
    def generate_usage_report(self, tenant_id: str, period_start: date, 
                            period_end: date) -> UsageReport:
        """Generate comprehensive usage report for a tenant"""
        
        # Get billing calculation
        billing = self.billing_engine.calculate_billing(tenant_id, period_start, period_end)
        
        # Get usage data
        usage_data = self.usage_collector.get_usage_for_period(
            tenant_id,
            datetime.combine(period_start, datetime.min.time()),
            datetime.combine(period_end, datetime.max.time())
        )
        
        # Calculate usage summary
        usage_summary = {
            'total_bytes_ingested': billing.total_bytes,
            'total_storage_used': billing.total_storage,
            'total_queries': billing.total_queries,
            'total_compute_seconds': billing.total_compute,
            'total_bandwidth_gb': billing.total_bandwidth,
            'average_daily_ingestion': billing.total_bytes / max((period_end - period_start).days, 1),
            'data_points_collected': len(usage_data)
        }
        
        # Cost breakdown
        cost_breakdown = {
            'ingestion_cost': billing.ingestion_cost,
            'storage_cost': billing.storage_cost,
            'query_cost': billing.query_cost,
            'compute_cost': billing.compute_cost,
            'bandwidth_cost': billing.bandwidth_cost,
            'total_cost': billing.total_cost,
            'tier': billing.tier.value,
            'cost_per_gb': billing.total_cost / (billing.total_bytes / (1024**3)) if billing.total_bytes > 0 else 0
        }
        
        # Daily usage breakdown
        daily_usage = []
        current_date = period_start
        while current_date <= period_end:
            daily_data = self.usage_collector.get_usage_for_period(
                tenant_id,
                datetime.combine(current_date, datetime.min.time()),
                datetime.combine(current_date, datetime.max.time())
            )
            
            daily_bytes = sum(row['bytes_ingested'] for row in daily_data)
            daily_queries = sum(row['queries_processed'] for row in daily_data)
            
            daily_usage.append({
                'date': current_date.isoformat(),
                'bytes_ingested': daily_bytes,
                'queries_processed': daily_queries,
                'data_points': len(daily_data)
            })
            
            current_date += timedelta(days=1)
            
        # Top services analysis (simulated for demo)
        top_services = [
            {'service': 'web-api', 'bytes': int(billing.total_bytes * 0.4), 'cost': billing.total_cost * 0.4},
            {'service': 'database', 'bytes': int(billing.total_bytes * 0.3), 'cost': billing.total_cost * 0.3},
            {'service': 'auth-service', 'bytes': int(billing.total_bytes * 0.2), 'cost': billing.total_cost * 0.2},
            {'service': 'monitoring', 'bytes': int(billing.total_bytes * 0.1), 'cost': billing.total_cost * 0.1}
        ]
        
        return UsageReport(
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            usage_summary=usage_summary,
            cost_breakdown=cost_breakdown,
            daily_usage=daily_usage,
            top_services=top_services
        )
        
    def export_report_json(self, report: UsageReport) -> str:
        """Export report as JSON string"""
        return json.dumps(report.dict(), indent=2, default=str)
        
    def export_report_csv(self, report: UsageReport) -> str:
        """Export daily usage as CSV string"""
        csv_lines = ["Date,Bytes Ingested,Queries Processed,Data Points"]
        
        for daily in report.daily_usage:
            csv_lines.append(
                f"{daily['date']},{daily['bytes_ingested']},"
                f"{daily['queries_processed']},{daily['data_points']}"
            )
            
        return "\n".join(csv_lines)
        
    def generate_executive_summary(self, tenant_id: str, month: int, year: int) -> Dict:
        """Generate executive summary with key insights"""
        summary = self.billing_engine.get_monthly_billing_summary(tenant_id, month, year)
        billing = summary['billing_summary']
        
        # Calculate key metrics
        total_cost = billing['total_cost']
        total_gb = billing['total_bytes'] / (1024**3)
        cost_per_gb = total_cost / total_gb if total_gb > 0 else 0
        
        # Usage efficiency score (lower cost per GB is better)
        if cost_per_gb < 0.30:
            efficiency_score = "Excellent"
        elif cost_per_gb < 0.50:
            efficiency_score = "Good"
        elif cost_per_gb < 0.80:
            efficiency_score = "Fair"
        else:
            efficiency_score = "Needs Optimization"
            
        insights = []
        if billing['ingestion_cost'] > total_cost * 0.6:
            insights.append("High ingestion costs - consider data filtering")
        if billing['storage_cost'] > total_cost * 0.3:
            insights.append("High storage costs - review retention policies")
        if summary['cost_trend'] == "increasing":
            insights.append("Costs are trending upward - monitor usage closely")
            
        return {
            'tenant_id': tenant_id,
            'period': f"{year}-{month:02d}",
            'total_cost': total_cost,
            'total_gb_processed': round(total_gb, 2),
            'cost_per_gb': round(cost_per_gb, 4),
            'efficiency_score': efficiency_score,
            'cost_trend': summary['cost_trend'],
            'insights': insights,
            'tier': billing['tier'],
            'generated_at': datetime.now().isoformat()
        }
