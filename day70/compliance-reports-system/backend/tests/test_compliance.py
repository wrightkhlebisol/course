import pytest
import asyncio
from datetime import datetime, timedelta
import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.compliance_service import ComplianceReportGenerator

@pytest.fixture
def report_generator():
    return ComplianceReportGenerator(storage_path="./test_exports")

@pytest.mark.asyncio
async def test_sox_report_generation(report_generator):
    """Test SOX compliance report generation"""
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    report_data = await report_generator.generate_sox_report(start_date, end_date)
    
    assert report_data['framework'] == 'SOX'
    assert 'summary' in report_data
    assert 'findings' in report_data
    assert 'data' in report_data
    assert len(report_data['data']['financial_transactions']) > 0

@pytest.mark.asyncio
async def test_hipaa_report_generation(report_generator):
    """Test HIPAA compliance report generation"""
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    report_data = await report_generator.generate_hipaa_report(start_date, end_date)
    
    assert report_data['framework'] == 'HIPAA'
    assert 'summary' in report_data
    assert 'findings' in report_data
    assert 'data' in report_data
    assert len(report_data['data']['patient_data_access']) > 0

@pytest.mark.asyncio
async def test_pdf_export(report_generator):
    """Test PDF export functionality"""
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    report_data = await report_generator.generate_sox_report(start_date, end_date)
    filepath = await report_generator.export_to_pdf(report_data, "test_report")
    
    assert os.path.exists(filepath)
    assert filepath.endswith('.pdf')
    
    # Cleanup
    if os.path.exists(filepath):
        os.remove(filepath)

@pytest.mark.asyncio
async def test_csv_export(report_generator):
    """Test CSV export functionality"""
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    report_data = await report_generator.generate_sox_report(start_date, end_date)
    filepath = await report_generator.export_to_csv(report_data, "test_report")
    
    assert os.path.exists(filepath)
    assert filepath.endswith('.csv')
    
    # Cleanup
    if os.path.exists(filepath):
        os.remove(filepath)

def test_signature_generation(report_generator):
    """Test cryptographic signature generation"""
    test_data = {
        "framework": "TEST",
        "period": "2024-01-01 to 2024-01-31",
        "summary": {"total_events": 100}
    }
    
    signature1 = report_generator.generate_signature(test_data)
    signature2 = report_generator.generate_signature(test_data)
    
    # Same data should produce same signature
    assert signature1 == signature2
    assert len(signature1) == 64  # SHA256 hex length
    
    # Different data should produce different signature
    test_data['summary']['total_events'] = 200
    signature3 = report_generator.generate_signature(test_data)
    assert signature1 != signature3

if __name__ == "__main__":
    pytest.main([__file__])
