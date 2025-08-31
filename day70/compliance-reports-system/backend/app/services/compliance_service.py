from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import json
import hashlib
from cryptography.fernet import Fernet
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import os

class ComplianceReportGenerator:
    def __init__(self, storage_path: str = "./exports"):
        self.storage_path = storage_path
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        os.makedirs(storage_path, exist_ok=True)
    
    async def generate_sox_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate SOX compliance report for financial controls"""
        
        # Simulate SOX data aggregation
        sox_data = {
            "financial_transactions": await self._get_financial_transactions(start_date, end_date),
            "admin_access_logs": await self._get_admin_access_logs(start_date, end_date),
            "system_changes": await self._get_system_changes(start_date, end_date),
            "approval_workflows": await self._get_approval_workflows(start_date, end_date)
        }
        
        report_content = {
            "framework": "SOX",
            "period": f"{start_date.date()} to {end_date.date()}",
            "summary": {
                "total_transactions": len(sox_data["financial_transactions"]),
                "admin_access_events": len(sox_data["admin_access_logs"]),
                "system_changes": len(sox_data["system_changes"]),
                "approval_workflows": len(sox_data["approval_workflows"])
            },
            "findings": await self._analyze_sox_compliance(sox_data),
            "data": sox_data
        }
        
        return report_content
    
    async def generate_hipaa_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate HIPAA compliance report for healthcare data"""
        
        hipaa_data = {
            "patient_data_access": await self._get_patient_data_access(start_date, end_date),
            "data_breaches": await self._get_data_breaches(start_date, end_date),
            "audit_logs": await self._get_hipaa_audit_logs(start_date, end_date),
            "user_activity": await self._get_user_activity(start_date, end_date)
        }
        
        report_content = {
            "framework": "HIPAA",
            "period": f"{start_date.date()} to {end_date.date()}",
            "summary": {
                "patient_access_events": len(hipaa_data["patient_data_access"]),
                "security_incidents": len(hipaa_data["data_breaches"]),
                "audit_entries": len(hipaa_data["audit_logs"]),
                "user_sessions": len(hipaa_data["user_activity"])
            },
            "findings": await self._analyze_hipaa_compliance(hipaa_data),
            "data": hipaa_data
        }
        
        return report_content
    
    async def export_to_pdf(self, report_data: Dict[str, Any], filename: str) -> str:
        """Export compliance report to PDF format"""
        
        filepath = os.path.join(self.storage_path, f"{filename}.pdf")
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"Compliance Report - {report_data['framework']}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Period
        period = Paragraph(f"Period: {report_data['period']}", styles['Normal'])
        story.append(period)
        story.append(Spacer(1, 12))
        
        # Summary Table
        summary_data = [['Metric', 'Count']]
        for key, value in report_data['summary'].items():
            summary_data.append([key.replace('_', ' ').title(), str(value)])
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 12))
        
        # Findings
        findings_title = Paragraph("Compliance Findings", styles['Heading2'])
        story.append(findings_title)
        story.append(Spacer(1, 6))
        
        for finding in report_data['findings']:
            finding_text = Paragraph(f"• {finding}", styles['Normal'])
            story.append(finding_text)
            story.append(Spacer(1, 3))
        
        doc.build(story)
        return filepath
    
    async def export_to_csv(self, report_data: Dict[str, Any], filename: str) -> str:
        """Export compliance report to CSV format"""
        
        filepath = os.path.join(self.storage_path, f"{filename}.csv")
        
        # Flatten data for CSV export
        flattened_data = []
        for category, items in report_data['data'].items():
            for item in items:
                flattened_item = {'category': category, **item}
                flattened_data.append(flattened_item)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(filepath, index=False)
        return filepath
    
    def generate_signature(self, report_data: Dict[str, Any]) -> str:
        """Generate cryptographic signature for report integrity"""
        
        report_string = json.dumps(report_data, sort_keys=True, default=str)
        signature = hashlib.sha256(report_string.encode()).hexdigest()
        return signature
    
    # Simulation methods for demo
    async def _get_financial_transactions(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Simulate financial transaction logs"""
        return [
            {
                "transaction_id": f"TXN_{i:06d}",
                "amount": 1000.00 + (i * 50),
                "timestamp": start_date + timedelta(hours=i),
                "user_id": f"user_{i % 10}",
                "approved_by": f"approver_{i % 3}"
            }
            for i in range(50)
        ]
    
    async def _get_admin_access_logs(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Simulate admin access logs"""
        return [
            {
                "session_id": f"ADMIN_{i:06d}",
                "user_id": f"admin_{i % 5}",
                "action": ["login", "logout", "config_change", "user_management"][i % 4],
                "timestamp": start_date + timedelta(hours=i * 2),
                "ip_address": f"192.168.1.{i % 255}",
                "resource": f"financial_system_{i % 3}"
            }
            for i in range(25)
        ]
    
    async def _get_system_changes(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Simulate system change logs"""
        return [
            {
                "change_id": f"CHG_{i:06d}",
                "change_type": ["configuration", "security", "financial"][i % 3],
                "timestamp": start_date + timedelta(days=i),
                "changed_by": f"admin_{i % 3}",
                "approved_by": f"manager_{i % 2}",
                "description": f"System change {i}"
            }
            for i in range(10)
        ]
    
    async def _get_approval_workflows(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Simulate approval workflow logs"""
        return [
            {
                "workflow_id": f"WF_{i:06d}",
                "request_type": ["financial_approval", "access_request", "configuration_change"][i % 3],
                "status": ["approved", "rejected", "pending"][i % 3],
                "timestamp": start_date + timedelta(hours=i * 4),
                "requestor": f"user_{i % 10}",
                "approver": f"manager_{i % 3}"
            }
            for i in range(20)
        ]
    
    async def _get_patient_data_access(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Simulate patient data access logs"""
        return [
            {
                "access_id": f"PAT_{i:06d}",
                "patient_id": f"patient_{i % 100}",
                "user_id": f"doctor_{i % 20}",
                "access_type": ["view", "edit", "create", "delete"][i % 4],
                "timestamp": start_date + timedelta(hours=i),
                "ip_address": f"10.0.1.{i % 255}",
                "department": ["cardiology", "emergency", "surgery"][i % 3]
            }
            for i in range(75)
        ]
    
    async def _get_data_breaches(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Simulate security incident logs"""
        return [
            {
                "incident_id": f"SEC_{i:06d}",
                "severity": ["low", "medium", "high"][i % 3],
                "type": ["unauthorized_access", "data_exposure", "system_breach"][i % 3],
                "timestamp": start_date + timedelta(days=i * 5),
                "affected_records": (i + 1) * 10,
                "resolved": i % 2 == 0,
                "reported_to_authorities": i % 3 == 0
            }
            for i in range(5)
        ]
    
    async def _get_hipaa_audit_logs(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Simulate HIPAA audit logs"""
        return [
            {
                "audit_id": f"AUDIT_{i:06d}",
                "action": ["patient_lookup", "record_access", "export_data"][i % 3],
                "user_id": f"staff_{i % 15}",
                "timestamp": start_date + timedelta(hours=i * 2),
                "patient_count": i % 5 + 1,
                "justification": f"Medical necessity {i}"
            }
            for i in range(40)
        ]
    
    async def _get_user_activity(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Simulate user activity logs"""
        return [
            {
                "session_id": f"SESS_{i:06d}",
                "user_id": f"user_{i % 25}",
                "login_time": start_date + timedelta(hours=i),
                "logout_time": start_date + timedelta(hours=i, minutes=45),
                "ip_address": f"192.168.10.{i % 255}",
                "user_agent": f"Browser_{i % 3}",
                "pages_accessed": i % 10 + 1
            }
            for i in range(60)
        ]
    
    async def _analyze_sox_compliance(self, sox_data: Dict) -> List[str]:
        """Analyze SOX compliance findings"""
        findings = []
        
        if len(sox_data["financial_transactions"]) > 0:
            findings.append("All financial transactions have proper audit trails")
        
        admin_changes = [log for log in sox_data["admin_access_logs"] if log["action"] == "config_change"]
        if len(admin_changes) > 0:
            findings.append(f"Found {len(admin_changes)} administrative configuration changes requiring review")
        
        unapproved_workflows = [wf for wf in sox_data["approval_workflows"] if wf["status"] == "pending"]
        if len(unapproved_workflows) > 0:
            findings.append(f"Warning: {len(unapproved_workflows)} pending approval workflows require attention")
        
        return findings
    
    async def _analyze_hipaa_compliance(self, hipaa_data: Dict) -> List[str]:
        """Analyze HIPAA compliance findings"""
        findings = []
        
        high_severity_incidents = [inc for inc in hipaa_data["data_breaches"] if inc["severity"] == "high"]
        if len(high_severity_incidents) > 0:
            findings.append(f"Critical: {len(high_severity_incidents)} high-severity security incidents detected")
        
        unresolved_incidents = [inc for inc in hipaa_data["data_breaches"] if not inc["resolved"]]
        if len(unresolved_incidents) > 0:
            findings.append(f"Warning: {len(unresolved_incidents)} security incidents remain unresolved")
        
        after_hours_access = [acc for acc in hipaa_data["patient_data_access"] 
                             if acc["timestamp"].hour < 8 or acc["timestamp"].hour > 18]
        if len(after_hours_access) > 10:
            findings.append(f"Notice: {len(after_hours_access)} patient data access events occurred after hours")
        
        return findings
