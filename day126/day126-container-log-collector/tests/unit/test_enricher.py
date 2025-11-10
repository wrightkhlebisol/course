import pytest
import sys
sys.path.insert(0, 'src')

from enrichment.metadata_enricher import MetadataEnricher

def test_detect_severity():
    enricher = MetadataEnricher()
    
    assert enricher._detect_severity("This is an error message") == "ERROR"
    assert enricher._detect_severity("Warning: disk space low") == "WARN"
    assert enricher._detect_severity("Info: service started") == "INFO"
    assert enricher._detect_severity("Debug trace information") == "DEBUG"

def test_enrich_log():
    enricher = MetadataEnricher()
    log_entry = {
        'timestamp': '2025-05-16T10:00:00Z',
        'message': 'Error processing request',
        'source': 'docker'
    }
    
    enriched = enricher.enrich(log_entry)
    
    assert enriched['level'] == 'ERROR'
    assert 'processed_at' in enriched
    assert enriched['enriched'] == True
    assert 'size_bytes' in enriched

print("✅ Enricher tests passed")
