import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

logger = logging.getLogger(__name__)

class LogMonitor:
    def __init__(self, storage_dirs: Dict[str, str]):
        self.storage_dirs = storage_dirs
        self.log_types = ['application', 'security', 'system', 'error', 'access']
        self.log_levels = ['debug', 'info', 'warning', 'error', 'critical']
        
    def generate_sample_logs(self, count: int = 100):
        """Generate sample log files in storage directories"""
        for storage_type, dir_path in self.storage_dirs.items():
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # Generate logs based on storage type
            if storage_type == 'hot':
                self._generate_hot_logs(dir_path, count)
            elif storage_type == 'warm':
                self._generate_warm_logs(dir_path, count // 2)
            elif storage_type == 'cold':
                self._generate_cold_logs(dir_path, count // 4)
    
    def _generate_hot_logs(self, dir_path: str, count: int):
        """Generate recent logs for hot storage"""
        for i in range(count):
            log_entry = self._create_log_entry(
                log_type=random.choice(self.log_types),
                level=random.choice(self.log_levels),
                hours_ago=random.randint(0, 24)
            )
            
            filename = f"hot_log_{datetime.now().strftime('%Y%m%d')}_{i}.log"
            filepath = os.path.join(dir_path, filename)
            
            with open(filepath, 'w') as f:
                f.write(json.dumps(log_entry) + '\n')
    
    def _generate_warm_logs(self, dir_path: str, count: int):
        """Generate older logs for warm storage"""
        for i in range(count):
            log_entry = self._create_log_entry(
                log_type=random.choice(self.log_types),
                level=random.choice(self.log_levels),
                hours_ago=random.randint(24, 168)  # 1-7 days ago
            )
            
            filename = f"warm_log_{datetime.now().strftime('%Y%m%d')}_{i}.log"
            filepath = os.path.join(dir_path, filename)
            
            with open(filepath, 'w') as f:
                f.write(json.dumps(log_entry) + '\n')
    
    def _generate_cold_logs(self, dir_path: str, count: int):
        """Generate very old logs for cold storage"""
        for i in range(count):
            log_entry = self._create_log_entry(
                log_type=random.choice(self.log_types),
                level=random.choice(self.log_levels),
                hours_ago=random.randint(168, 8760)  # 7 days to 1 year ago
            )
            
            filename = f"cold_log_{datetime.now().strftime('%Y%m%d')}_{i}.log"
            filepath = os.path.join(dir_path, filename)
            
            with open(filepath, 'w') as f:
                f.write(json.dumps(log_entry) + '\n')
    
    def _create_log_entry(self, log_type: str, level: str, hours_ago: int) -> Dict[str, Any]:
        """Create a single log entry"""
        timestamp = datetime.now() - timedelta(hours=hours_ago)
        
        messages = {
            'application': [
                'User login successful',
                'Database query executed',
                'API request processed',
                'Cache updated',
                'Background job completed'
            ],
            'security': [
                'Authentication attempt',
                'Permission denied',
                'Session expired',
                'Failed login attempt',
                'Security scan completed'
            ],
            'system': [
                'System startup',
                'Memory usage high',
                'Disk space low',
                'Service restarted',
                'Backup completed'
            ],
            'error': [
                'Database connection failed',
                'API timeout',
                'Invalid input data',
                'Service unavailable',
                'Configuration error'
            ],
            'access': [
                'Page accessed',
                'File downloaded',
                'API endpoint called',
                'Resource requested',
                'Search performed'
            ]
        }
        
        return {
            'timestamp': timestamp.isoformat(),
            'type': log_type,
            'level': level,
            'message': random.choice(messages.get(log_type, ['Unknown event'])),
            'user_id': random.randint(1000, 9999) if log_type in ['application', 'access'] else None,
            'ip_address': f"192.168.1.{random.randint(1, 254)}" if log_type in ['access', 'security'] else None,
            'session_id': f"sess_{random.randint(100000, 999999)}" if log_type in ['application', 'access'] else None,
            'duration_ms': random.randint(10, 5000) if log_type in ['application', 'access'] else None,
            'bytes_transferred': random.randint(100, 100000) if log_type == 'access' else None
        }
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get statistics about logs in storage"""
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'by_storage': {},
            'by_type': {},
            'by_level': {},
            'recent_logs': []
        }
        
        for storage_type, dir_path in self.storage_dirs.items():
            if not os.path.exists(dir_path):
                continue
                
            storage_stats = {
                'files': 0,
                'size_mb': 0,
                'types': {},
                'levels': {}
            }
            
            for filename in os.listdir(dir_path):
                if filename.endswith('.log'):
                    filepath = os.path.join(dir_path, filename)
                    file_size = os.path.getsize(filepath)
                    
                    storage_stats['files'] += 1
                    storage_stats['size_mb'] += file_size / (1024 * 1024)
                    stats['total_files'] += 1
                    stats['total_size_mb'] += file_size / (1024 * 1024)
                    
                    # Read a few lines to get log stats
                    try:
                        with open(filepath, 'r') as f:
                            for line_num, line in enumerate(f):
                                if line_num >= 10:  # Only read first 10 lines per file
                                    break
                                try:
                                    log_entry = json.loads(line.strip())
                                    log_type = log_entry.get('type', 'unknown')
                                    log_level = log_entry.get('level', 'unknown')
                                    
                                    # Update storage stats
                                    storage_stats['types'][log_type] = storage_stats['types'].get(log_type, 0) + 1
                                    storage_stats['levels'][log_level] = storage_stats['levels'].get(log_level, 0) + 1
                                    
                                    # Update global stats
                                    stats['by_type'][log_type] = stats['by_type'].get(log_type, 0) + 1
                                    stats['by_level'][log_level] = stats['by_level'].get(log_level, 0) + 1
                                    
                                    # Add to recent logs (last 24 hours)
                                    log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                                    if datetime.now() - log_time < timedelta(hours=24):
                                        stats['recent_logs'].append(log_entry)
                                        
                                except json.JSONDecodeError:
                                    continue
                    except Exception as e:
                        logger.warning(f"Error reading log file {filepath}: {e}")
            
            stats['by_storage'][storage_type] = storage_stats
        
        # Sort recent logs by timestamp
        stats['recent_logs'].sort(key=lambda x: x['timestamp'], reverse=True)
        stats['recent_logs'] = stats['recent_logs'][:50]  # Keep only last 50
        
        return stats
    
    def get_logs_by_criteria(self, storage_type: str = None, log_type: str = None, 
                           level: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs filtered by criteria"""
        logs = []
        
        storage_dirs = self.storage_dirs.items()
        if storage_type:
            storage_dirs = [(storage_type, self.storage_dirs[storage_type])]
        
        for st_type, dir_path in storage_dirs:
            if not os.path.exists(dir_path):
                continue
                
            for filename in os.listdir(dir_path):
                if filename.endswith('.log'):
                    filepath = os.path.join(dir_path, filename)
                    
                    try:
                        with open(filepath, 'r') as f:
                            for line in f:
                                if len(logs) >= limit:
                                    break
                                    
                                try:
                                    log_entry = json.loads(line.strip())
                                    
                                    # Apply filters
                                    if log_type and log_entry.get('type') != log_type:
                                        continue
                                    if level and log_entry.get('level') != level:
                                        continue
                                    
                                    log_entry['storage_type'] = st_type
                                    log_entry['filename'] = filename
                                    logs.append(log_entry)
                                    
                                except json.JSONDecodeError:
                                    continue
                    except Exception as e:
                        logger.warning(f"Error reading log file {filepath}: {e}")
        
        # Sort by timestamp
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return logs[:limit]
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up logs older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_files = 0
        freed_space_mb = 0
        
        for storage_type, dir_path in self.storage_dirs.items():
            if not os.path.exists(dir_path):
                continue
                
            for filename in os.listdir(dir_path):
                if filename.endswith('.log'):
                    filepath = os.path.join(dir_path, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff_date:
                        try:
                            file_size = os.path.getsize(filepath)
                            os.remove(filepath)
                            deleted_files += 1
                            freed_space_mb += file_size / (1024 * 1024)
                            logger.info(f"Deleted old log file: {filepath}")
                        except Exception as e:
                            logger.error(f"Error deleting file {filepath}: {e}")
        
        return {
            'deleted_files': deleted_files,
            'freed_space_mb': freed_space_mb
        } 