import asyncio
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

class ReportGenerator:
    def __init__(self, cost_engine, config: Dict[str, Any]):
        self.cost_engine = cost_engine
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Adjust path for running from src directory
        reports_path = config.get('reporting', {}).get('output_dir', 'data/reports')
        if not reports_path.startswith('/'):
            reports_path = '../' + reports_path
        self.output_dir = Path(reports_path)
        self.output_dir.mkdir(exist_ok=True)

    async def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """Generate daily cost report for all tenants"""
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_time = date
        end_time = date + timedelta(days=1)
        
        self.logger.info(f"Generating daily report for {date.strftime('%Y-%m-%d')}")
        
        # Calculate costs for all tenants
        all_costs = await self.cost_engine.calculate_costs(start_time, end_time)
        
        # Generate detailed reports per tenant
        tenant_details = {}
        total_cost = 0.0
        
        for tenant_id in all_costs.keys():
            tenant_report = await self.cost_engine.get_tenant_costs(tenant_id, start_time, end_time)
            tenant_details[tenant_id] = tenant_report
            total_cost += tenant_report['total_cost']
        
        report_data = {
            'report_type': 'daily',
            'date': date.strftime('%Y-%m-%d'),
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'summary': {
                'total_cost': total_cost,
                'tenant_count': len(tenant_details),
                'cost_by_tenant': {tid: details['total_cost'] for tid, details in tenant_details.items()}
            },
            'tenant_details': tenant_details,
            'generated_at': datetime.now().isoformat()
        }
        
        # Save report in multiple formats
        await self._save_report(report_data, f"daily_report_{date.strftime('%Y%m%d')}")
        
        return report_data

    async def generate_weekly_report(self, week_start: datetime = None) -> Dict[str, Any]:
        """Generate weekly cost report with trends"""
        if week_start is None:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today - timedelta(days=today.weekday())
        
        end_time = week_start + timedelta(days=7)
        
        self.logger.info(f"Generating weekly report for week starting {week_start.strftime('%Y-%m-%d')}")
        
        # Generate daily reports for the week
        daily_costs = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            if day <= datetime.now():
                day_costs = await self.cost_engine.calculate_costs(
                    day, day + timedelta(days=1)
                )
                daily_costs.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'costs': day_costs
                })
        
        # Calculate weekly totals and trends
        weekly_totals = {}
        for tenant_id in self.cost_engine.tenants.keys():
            weekly_totals[tenant_id] = {
                'total_cost': 0.0,
                'daily_breakdown': {},
                'resource_breakdown': {}
            }
        
        for day_data in daily_costs:
            for tenant_id, costs in day_data['costs'].items():
                weekly_totals[tenant_id]['total_cost'] += costs.get('total', 0.0)
                weekly_totals[tenant_id]['daily_breakdown'][day_data['date']] = costs.get('total', 0.0)
                
                for resource_type, cost in costs.items():
                    if resource_type != 'total':
                        if resource_type not in weekly_totals[tenant_id]['resource_breakdown']:
                            weekly_totals[tenant_id]['resource_breakdown'][resource_type] = 0.0
                        weekly_totals[tenant_id]['resource_breakdown'][resource_type] += cost
        
        report_data = {
            'report_type': 'weekly',
            'week_start': week_start.strftime('%Y-%m-%d'),
            'period': {
                'start': week_start.isoformat(),
                'end': end_time.isoformat()
            },
            'weekly_totals': weekly_totals,
            'daily_breakdown': daily_costs,
            'generated_at': datetime.now().isoformat()
        }
        
        # Generate visualizations
        await self._generate_weekly_charts(report_data)
        
        # Save report
        await self._save_report(report_data, f"weekly_report_{week_start.strftime('%Y%m%d')}")
        
        return report_data

    async def generate_monthly_report(self, month_start: datetime = None) -> Dict[str, Any]:
        """Generate comprehensive monthly report with budget analysis"""
        if month_start is None:
            today = datetime.now()
            month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate end of month
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        
        self.logger.info(f"Generating monthly report for {month_start.strftime('%Y-%m')}")
        
        # Calculate monthly costs
        monthly_costs = await self.cost_engine.calculate_costs(month_start, month_end)
        
        # Generate detailed tenant analysis
        tenant_analysis = {}
        budget_alerts = []
        
        for tenant_id in monthly_costs.keys():
            tenant_report = await self.cost_engine.get_tenant_costs(tenant_id, month_start, month_end)
            tenant_analysis[tenant_id] = tenant_report
            
            # Check budget alerts
            if tenant_report['budget']['over_threshold']:
                budget_alerts.append({
                    'tenant_id': tenant_id,
                    'current_cost': tenant_report['total_cost'],
                    'budget': tenant_report['budget']['monthly_budget'],
                    'utilization': tenant_report['budget']['utilization'],
                    'threshold': tenant_report['budget']['alert_threshold']
                })
        
        # Calculate optimization recommendations
        optimizations = await self._generate_optimization_recommendations(tenant_analysis)
        
        report_data = {
            'report_type': 'monthly',
            'month': month_start.strftime('%Y-%m'),
            'period': {
                'start': month_start.isoformat(),
                'end': month_end.isoformat()
            },
            'tenant_analysis': tenant_analysis,
            'budget_alerts': budget_alerts,
            'optimization_recommendations': optimizations,
            'generated_at': datetime.now().isoformat()
        }
        
        # Generate comprehensive charts
        await self._generate_monthly_charts(report_data)
        
        # Save report
        await self._save_report(report_data, f"monthly_report_{month_start.strftime('%Y%m')}")
        
        return report_data

    async def _generate_optimization_recommendations(self, tenant_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        for tenant_id, analysis in tenant_analysis.items():
            cost_breakdown = analysis['cost_breakdown']
            total_cost = analysis['total_cost']
            
            # High storage cost recommendation
            storage_cost = cost_breakdown.get('storage', 0.0)
            if storage_cost > total_cost * 0.4:  # Storage > 40% of total
                recommendations.append({
                    'tenant_id': tenant_id,
                    'type': 'storage_optimization',
                    'priority': 'high',
                    'description': f'Storage costs ({storage_cost:.2f}) are {storage_cost/total_cost*100:.1f}% of total budget',
                    'suggestion': 'Consider implementing log retention policies and archiving old data',
                    'potential_savings': storage_cost * 0.3  # 30% potential savings
                })
            
            # High query cost recommendation
            query_cost = cost_breakdown.get('queries', 0.0)
            if query_cost > total_cost * 0.3:  # Queries > 30% of total
                recommendations.append({
                    'tenant_id': tenant_id,
                    'type': 'query_optimization',
                    'priority': 'medium',
                    'description': f'Query costs ({query_cost:.2f}) are {query_cost/total_cost*100:.1f}% of total budget',
                    'suggestion': 'Implement query result caching and optimize expensive queries',
                    'potential_savings': query_cost * 0.25  # 25% potential savings
                })
            
            # Budget utilization warning
            utilization = analysis['budget']['utilization']
            if utilization > 0.8:  # Using > 80% of budget
                recommendations.append({
                    'tenant_id': tenant_id,
                    'type': 'budget_alert',
                    'priority': 'high' if utilization > 0.9 else 'medium',
                    'description': f'Budget utilization is {utilization*100:.1f}%',
                    'suggestion': 'Review usage patterns and consider budget increase or optimization',
                    'potential_savings': 0.0
                })
        
        return recommendations

    async def _generate_weekly_charts(self, report_data: Dict[str, Any]):
        """Generate weekly visualization charts"""
        try:
            # Create subplot with secondary y-axis
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=['Daily Costs by Tenant', 'Resource Breakdown', 'Weekly Totals', 'Cost Trends'],
                specs=[[{"secondary_y": False}, {"type": "pie"}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Daily costs chart
            daily_data = report_data['daily_breakdown']
            for tenant_id in report_data['weekly_totals'].keys():
                dates = []
                costs = []
                for day in daily_data:
                    dates.append(day['date'])
                    costs.append(day['costs'].get(tenant_id, {}).get('total', 0.0))
                
                fig.add_trace(
                    go.Scatter(x=dates, y=costs, name=f'{tenant_id} Daily',
                              mode='lines+markers'),
                    row=1, col=1
                )
            
            # Save chart
            chart_path = self.output_dir / f"weekly_charts_{report_data['week_start'].replace('-', '')}.html"
            fig.write_html(str(chart_path))
            
        except Exception as e:
            self.logger.error(f"Error generating weekly charts: {e}")

    async def _generate_monthly_charts(self, report_data: Dict[str, Any]):
        """Generate monthly visualization charts"""
        try:
            # Create comprehensive monthly dashboard
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=['Monthly Costs by Tenant', 'Resource Distribution', 
                               'Budget Utilization', 'Cost Trends', 'Top Expenses', 'Optimization Impact'],
                specs=[[{"secondary_y": False}, {"type": "pie"}],
                       [{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Monthly costs bar chart
            tenants = list(report_data['tenant_analysis'].keys())
            total_costs = [report_data['tenant_analysis'][t]['total_cost'] for t in tenants]
            
            fig.add_trace(
                go.Bar(x=tenants, y=total_costs, name='Monthly Cost'),
                row=1, col=1
            )
            
            # Save chart
            chart_path = self.output_dir / f"monthly_charts_{report_data['month'].replace('-', '')}.html"
            fig.write_html(str(chart_path))
            
        except Exception as e:
            self.logger.error(f"Error generating monthly charts: {e}")

    async def _save_report(self, report_data: Dict[str, Any], filename: str):
        """Save report in multiple formats"""
        # JSON format
        json_path = self.output_dir / f"{filename}.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # CSV format for summary data
        csv_path = self.output_dir / f"{filename}_summary.csv"
        if 'tenant_analysis' in report_data:
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Tenant', 'Total Cost', 'Budget', 'Utilization', 'Over Threshold'])
                
                for tenant_id, analysis in report_data['tenant_analysis'].items():
                    writer.writerow([
                        tenant_id,
                        analysis['total_cost'],
                        analysis['budget']['monthly_budget'],
                        f"{analysis['budget']['utilization']*100:.1f}%",
                        analysis['budget']['over_threshold']
                    ])
        
        self.logger.info(f"Report saved: {filename}")

    async def get_realtime_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time data for dashboard"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'tenants': {}
        }
        
        for tenant_id in self.cost_engine.tenants.keys():
            # Get real-time usage
            usage_data = await self.cost_engine.get_realtime_usage(tenant_id)
            
            # Calculate estimated costs for current day
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            daily_costs = await self.cost_engine.calculate_costs(today, tomorrow)
            
            dashboard_data['tenants'][tenant_id] = {
                'realtime_usage': usage_data,
                'daily_cost': daily_costs.get(tenant_id, {}),
                'budget_info': self.cost_engine.tenants[tenant_id]
            }
        
        return dashboard_data
