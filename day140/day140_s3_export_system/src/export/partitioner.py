"""Data partitioning logic for organized S3 exports."""
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger()


class DataPartitioner:
    """Handles data partitioning strategies for S3 exports."""
    
    def __init__(self, config: Dict[str, Any]):
        self.scheme = config.get('scheme', 'date_service_level')
        self.date_format = config.get('date_format', 'year=%Y/month=%m/day=%d')
        self.include_service = config.get('include_service', True)
        self.include_level = config.get('include_level', True)
    
    def generate_partition_key(self, log_entry: Dict[str, Any], 
                               export_time: Optional[datetime] = None) -> str:
        """Generate S3 key based on partitioning scheme."""
        export_time = export_time or datetime.utcnow()
        
        # Base path with date partition
        date_path = export_time.strftime(self.date_format)
        path_parts = ['logs', date_path]
        
        # Add service partition
        if self.include_service and 'service' in log_entry:
            service = log_entry['service']
            path_parts.append(f'service={service}')
        
        # Add level partition
        if self.include_level and 'level' in log_entry:
            level = log_entry['level']
            path_parts.append(f'level={level}')
        
        return '/'.join(path_parts)
    
    def generate_filename(self, export_time: datetime, 
                         export_format: str = 'parquet',
                         compression: str = 'gzip') -> str:
        """Generate filename for export file."""
        timestamp = export_time.strftime('%Y%m%d_%H%M%S')
        
        # Extension based on format and compression
        ext = self._get_extension(export_format, compression)
        
        return f'export_{timestamp}.{ext}'
    
    def _get_extension(self, format: str, compression: str) -> str:
        """Determine file extension based on format and compression."""
        extensions = {
            ('parquet', 'gzip'): 'parquet.gz',
            ('parquet', 'zstd'): 'parquet.zst',
            ('parquet', 'none'): 'parquet',
            ('json', 'gzip'): 'json.gz',
            ('json', 'zstd'): 'json.zst',
            ('json', 'none'): 'json',
            ('csv', 'gzip'): 'csv.gz',
            ('csv', 'none'): 'csv'
        }
        return extensions.get((format, compression), f'{format}.{compression}')
    
    def parse_partition_from_key(self, s3_key: str) -> Dict[str, Any]:
        """Extract partition information from S3 key."""
        parts = s3_key.split('/')
        partition_info = {}
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                partition_info[key] = value
        
        return partition_info
    
    def generate_full_s3_key(self, log_entry: Dict[str, Any],
                             export_time: datetime,
                             export_format: str = 'parquet',
                             compression: str = 'gzip') -> str:
        """Generate complete S3 key including filename."""
        partition_key = self.generate_partition_key(log_entry, export_time)
        filename = self.generate_filename(export_time, export_format, compression)
        
        return f'{partition_key}/{filename}'
