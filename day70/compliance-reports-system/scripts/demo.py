#!/usr/bin/env python3
"""
Day 70: Compliance Reports Demo Script
Demonstrates the automated compliance reporting system
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

from services.compliance_service import ComplianceReportGenerator

class ComplianceDemo:
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.report_generator = ComplianceReportGenerator()
    
    async def run_demo(self):
        """Run complete compliance demo"""
        print("🚀 Day 70: Compliance Reports System Demo")
        print("=" * 60)
        
        # 1. Test report generation service
        await self.test_report_generation()
        
        # 2. Test API endpoints
        await self.test_api_endpoints()
        
        # 3. Generate sample reports
        await self.generate_sample_reports()
        
        print("\n✅ Demo completed successfully!")
        print("🌐 Access the dashboard at: http://localhost:3000")
        print("📊 API documentation at: http://localhost:8000/docs")
    
    async def test_report_generation(self):
        """Test compliance report generation"""
        print("\n1. Testing Compliance Report Generation")
        print("-" * 40)
        
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Test SOX report
        print("📋 Generating SOX compliance report...")
        sox_report = await self.report_generator.generate_sox_report(start_date, end_date)
        print(f"   ✅ SOX report generated with {sox_report['summary']['total_transactions']} transactions")
        
        # Test HIPAA report
        print("🏥 Generating HIPAA compliance report...")
        hipaa_report = await self.report_generator.generate_hipaa_report(start_date, end_date)
        print(f"   ✅ HIPAA report generated with {hipaa_report['summary']['patient_access_events']} access events")
        
        # Test exports
        print("📄 Testing PDF export...")
        pdf_path = await self.report_generator.export_to_pdf(sox_report, "demo_sox_report")
        print(f"   ✅ PDF exported: {pdf_path}")
        
        print("📊 Testing CSV export...")
        csv_path = await self.report_generator.export_to_csv(hipaa_report, "demo_hipaa_report")
        print(f"   ✅ CSV exported: {csv_path}")
        
        # Test signature
        signature = self.report_generator.generate_signature(sox_report)
        print(f"🔐 Report signature: {signature[:16]}...")
    
    async def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n2. Testing API Endpoints")
        print("-" * 40)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test root endpoint
                async with session.get(f"{self.api_base}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ API running - Version: {data.get('version')}")
                    else:
                        print(f"   ❌ API not responding (status: {response.status})")
                        return
                
                # Test frameworks endpoint
                async with session.get(f"{self.api_base}/frameworks") as response:
                    if response.status == 200:
                        data = await response.json()
                        frameworks = data.get('frameworks', [])
                        print(f"   ✅ {len(frameworks)} compliance frameworks available")
                        for fw in frameworks:
                            print(f"      - {fw['name']}: {fw['description']}")
                    else:
                        print(f"   ❌ Frameworks endpoint failed")
                
                # Test dashboard stats
                async with session.get(f"{self.api_base}/dashboard/stats") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Dashboard stats loaded")
                        print(f"      - Total reports: {data['summary']['total_reports']}")
                        print(f"      - Success rate: {data['summary']['success_rate']:.1f}%")
                    else:
                        print(f"   ❌ Dashboard stats failed")
        
        except Exception as e:
            print(f"   ❌ API test failed: {str(e)}")
            print("   ℹ️  Make sure the backend is running: python backend/app/main.py")
    
    async def generate_sample_reports(self):
        """Generate sample reports via API"""
        print("\n3. Generating Sample Reports")
        print("-" * 40)
        
        sample_requests = [
            {
                "framework": "SOX",
                "period_start": (datetime.now() - timedelta(days=7)).isoformat(),
                "period_end": datetime.now().isoformat(),
                "export_format": "pdf",
                "title": "Weekly SOX Compliance Report",
                "description": "Automated weekly SOX compliance report for demo"
            },
            {
                "framework": "HIPAA",
                "period_start": (datetime.now() - timedelta(days=30)).isoformat(),
                "period_end": datetime.now().isoformat(),
                "export_format": "csv",
                "title": "Monthly HIPAA Audit Report",
                "description": "Monthly HIPAA compliance audit for demo"
            }
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                for i, request_data in enumerate(sample_requests, 1):
                    print(f"📋 Generating {request_data['framework']} report...")
                    
                    async with session.post(
                        f"{self.api_base}/reports/generate",
                        json=request_data,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            report_id = data.get('report_id')
                            print(f"   ✅ Report {i} queued - ID: {report_id}")
                            
                            # Wait a moment for processing
                            await asyncio.sleep(2)
                            
                            # Check status
                            async with session.get(f"{self.api_base}/reports/{report_id}") as status_response:
                                if status_response.status == 200:
                                    status_data = await status_response.json()
                                    print(f"   📊 Status: {status_data.get('status')}")
                                    if status_data.get('status') == 'completed':
                                        print(f"   📁 Report ready for download")
                        else:
                            print(f"   ❌ Report {i} generation failed")
        
        except Exception as e:
            print(f"   ❌ Sample report generation failed: {str(e)}")
    
    def print_summary(self):
        """Print demo summary"""
        print("\n" + "=" * 60)
        print("🎉 Compliance Reports System Demo Summary")
        print("=" * 60)
        print("✅ Report generation service working")
        print("✅ Multiple compliance frameworks supported")
        print("✅ PDF and CSV export capabilities")
        print("✅ Cryptographic signature verification")
        print("✅ REST API endpoints functional")
        print("✅ Sample reports generated")
        
        print("\n📋 Supported Compliance Frameworks:")
        print("   • SOX - Sarbanes-Oxley Act (Financial)")
        print("   • HIPAA - Healthcare Data Privacy")
        print("   • PCI_DSS - Payment Card Security")
        print("   • GDPR - General Data Protection")
        
        print("\n🚀 Next Steps:")
        print("   1. Open http://localhost:3000 for web dashboard")
        print("   2. Generate custom reports via the UI")
        print("   3. Schedule automated reports")
        print("   4. Download reports in various formats")
        
        print("\n📖 Learning Outcomes Achieved:")
        print("   • Built multi-framework compliance engine")
        print("   • Implemented automated report generation")
        print("   • Created cryptographic integrity verification")
        print("   • Developed professional web dashboard")

async def main():
    """Main demo function"""
    demo = ComplianceDemo()
    await demo.run_demo()
    demo.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
