"""Test Log Discovery Engine"""
import pytest
import tempfile
import os
from pathlib import Path
from src.collector.discovery.log_discovery import LogDiscoveryEngine, LogSource


class TestLogDiscoveryEngine:
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test log files
            (Path(tmpdir) / "syslog").write_text("test syslog content")
            (Path(tmpdir) / "auth.log").write_text("test auth content")
            (Path(tmpdir) / "nginx_access.log").write_text("test nginx content")
            (Path(tmpdir) / "regular.txt").write_text("not a log file")
            yield tmpdir
    
    @pytest.fixture
    def config(self, temp_log_dir):
        """Test configuration"""
        return {
            'log_sources': {
                'system_logs': [
                    {'path': f"{temp_log_dir}/syslog", 'type': 'system', 'parser': 'syslog'}
                ]
            },
            'discovery': {
                'scan_paths': [temp_log_dir],
                'exclude_patterns': ['*.txt']
            }
        }
    
    @pytest.mark.asyncio
    async def test_configured_source_discovery(self, config):
        """Test discovery of configured sources"""
        engine = LogDiscoveryEngine(config)
        await engine.discover_sources()
        
        sources = engine.get_discovered_sources()
        syslog_path = list(config['log_sources']['system_logs'])[0]['path']
        
        assert syslog_path in sources
        assert sources[syslog_path].log_type == 'system'
        assert sources[syslog_path].parser == 'syslog'
    
    @pytest.mark.asyncio  
    async def test_filesystem_discovery(self, config, temp_log_dir):
        """Test filesystem-based discovery"""
        engine = LogDiscoveryEngine(config)
        await engine.discover_sources()
        
        sources = engine.get_discovered_sources()
        
        # Should find auth.log and nginx_access.log
        auth_log_path = f"{temp_log_dir}/auth.log"
        nginx_log_path = f"{temp_log_dir}/nginx_access.log"
        regular_file_path = f"{temp_log_dir}/regular.txt"
        
        assert auth_log_path in sources
        assert nginx_log_path in sources
        assert regular_file_path not in sources  # Should be excluded
    
    def test_log_type_inference(self, config):
        """Test log type inference"""
        engine = LogDiscoveryEngine(config)
        
        assert engine._infer_log_type("/var/log/auth.log") == "auth"
        assert engine._infer_log_type("/var/log/nginx/access.log") == "webserver"
        assert engine._infer_log_type("/var/log/mysql/error.log") == "database"
        assert engine._infer_log_type("/var/log/application.log") == "application"
    
    @pytest.mark.asyncio
    async def test_stats_generation(self, config):
        """Test statistics generation"""
        engine = LogDiscoveryEngine(config)
        await engine.discover_sources()
        
        stats = engine.get_stats()
        
        assert 'total_sources' in stats
        assert 'types' in stats
        assert 'total_size_bytes' in stats
        assert stats['total_sources'] > 0
