"""Log Source Discovery Engine"""
import os
import glob
import time
from pathlib import Path
from typing import List, Dict, Set, Any
import structlog
import fnmatch


class LogSource:
    def __init__(self, path: str, log_type: str, parser: str, size: int = 0):
        self.path = path
        self.log_type = log_type
        self.parser = parser
        self.size = size
        self.last_modified = time.time()
        self.inode = None
        
        if os.path.exists(path):
            stat = os.stat(path)
            self.size = stat.st_size
            self.last_modified = stat.st_mtime
            self.inode = stat.st_ino


class LogDiscoveryEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = structlog.get_logger("discovery")
        self.discovered_sources: Dict[str, LogSource] = {}
        
    async def discover_sources(self) -> None:
        """Discover all available log sources"""
        self.logger.info("Starting log source discovery")
        
        # Discover configured sources
        await self._discover_configured_sources()
        
        # Discover additional sources
        await self._discover_filesystem_sources()
        
        self.logger.info("Discovery complete", 
                        sources_found=len(self.discovered_sources))
    
    async def _discover_configured_sources(self) -> None:
        """Discover explicitly configured log sources"""
        log_sources = self.config.get('log_sources', {})
        
        for category, sources in log_sources.items():
            for source_config in sources:
                path = source_config['path']
                
                # Handle glob patterns
                if '*' in path:
                    for file_path in glob.glob(path):
                        if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
                            source = LogSource(
                                path=file_path,
                                log_type=source_config.get('type', category),
                                parser=source_config.get('parser', 'default')
                            )
                            self.discovered_sources[file_path] = source
                            self.logger.debug("Configured source discovered", 
                                            path=file_path, type=category)
                else:
                    if os.path.isfile(path) and os.access(path, os.R_OK):
                        source = LogSource(
                            path=path,
                            log_type=source_config.get('type', category),
                            parser=source_config.get('parser', 'default')
                        )
                        self.discovered_sources[path] = source
                        self.logger.debug("Configured source discovered", 
                                        path=path, type=category)
    
    async def _discover_filesystem_sources(self) -> None:
        """Discover additional log sources by filesystem scanning"""
        discovery_config = self.config.get('discovery', {})
        scan_paths = discovery_config.get('scan_paths', ['/var/log'])
        exclude_patterns = discovery_config.get('exclude_patterns', [])
        
        for scan_path in scan_paths:
            if not os.path.exists(scan_path):
                continue
                
            for root, dirs, files in os.walk(scan_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Skip if already discovered
                    if file_path in self.discovered_sources:
                        continue
                    
                    # Check exclude patterns
                    if any(fnmatch.fnmatch(file, pattern) for pattern in exclude_patterns):
                        continue
                    
                    # Check if it looks like a log file
                    if self._is_log_file(file_path):
                        source = LogSource(
                            path=file_path,
                            log_type=self._infer_log_type(file_path),
                            parser='auto'
                        )
                        self.discovered_sources[file_path] = source
                        self.logger.debug("Filesystem source discovered", 
                                        path=file_path, type=source.log_type)
    
    def _is_log_file(self, file_path: str) -> bool:
        """Check if file appears to be a log file"""
        if not os.access(file_path, os.R_OK):
            return False
        
        filename = os.path.basename(file_path).lower()
        
        # Check common log file patterns
        log_indicators = ['.log', 'log', 'access', 'error', 'debug', 'audit', 'trace']
        
        return any(indicator in filename for indicator in log_indicators)
    
    def _infer_log_type(self, file_path: str) -> str:
        """Infer log type from file path"""
        path_lower = file_path.lower()
        
        if 'auth' in path_lower:
            return 'auth'
        elif 'kern' in path_lower or 'kernel' in path_lower:
            return 'kernel'
        elif 'daemon' in path_lower:
            return 'daemon'
        elif 'nginx' in path_lower:
            return 'webserver'
        elif 'apache' in path_lower:
            return 'webserver'
        elif 'mysql' in path_lower or 'postgres' in path_lower:
            return 'database'
        else:
            return 'application'
    
    def get_discovered_sources(self) -> Dict[str, LogSource]:
        """Get all discovered log sources"""
        return self.discovered_sources
    
    def get_stats(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        type_counts = {}
        total_size = 0
        
        for source in self.discovered_sources.values():
            type_counts[source.log_type] = type_counts.get(source.log_type, 0) + 1
            total_size += source.size
        
        return {
            'total_sources': len(self.discovered_sources),
            'types': type_counts,
            'total_size_bytes': total_size
        }
