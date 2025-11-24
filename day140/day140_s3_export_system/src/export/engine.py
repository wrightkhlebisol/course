"""Core export engine for processing and uploading log data."""
import gzip
import zstandard as zstd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import json
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.storage.client import StorageClient, ProgressCallback
from src.export.partitioner import DataPartitioner

logger = structlog.get_logger()


class ExportEngine:
    """Handles log data export to cloud storage."""
    
    def __init__(self, config: Dict[str, Any], storage_client: StorageClient):
        self.config = config
        self.storage_client = storage_client
        self.partitioner = DataPartitioner(config.get('partitioning', {}))
        
        # Database connection
        db_url = config.get('database', {}).get('url', 'sqlite:///data/logs.db')
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Metadata tracking
        metadata_url = config.get('database', {}).get('metadata_url', 'sqlite:///data/metadata.db')
        self.metadata_engine = create_engine(metadata_url)
        self._init_metadata_table()
        
        # Export settings
        self.batch_size = config.get('export', {}).get('batch_size', 10000)
        self.export_format = config.get('export', {}).get('format', 'parquet')
        self.compression = config.get('export', {}).get('compression', 'gzip')
        
        # Retry configuration
        retry_config = config.get('retry', {})
        self.max_attempts = retry_config.get('max_attempts', 3)
        self.backoff_multiplier = retry_config.get('backoff_multiplier', 2)
        self.initial_delay = retry_config.get('initial_delay', 1)
    
    def _init_metadata_table(self):
        """Initialize export metadata tracking table."""
        with self.metadata_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS export_metadata (
                    export_id TEXT PRIMARY KEY,
                    export_time TIMESTAMP,
                    s3_key TEXT,
                    record_count INTEGER,
                    file_size INTEGER,
                    start_timestamp TIMESTAMP,
                    end_timestamp TIMESTAMP,
                    status TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    
    def get_last_export_time(self) -> Optional[datetime]:
        """Get timestamp of last successful export."""
        with self.metadata_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT MAX(end_timestamp) as last_export
                FROM export_metadata
                WHERE status = 'completed'
            """))
            row = result.fetchone()
            if row and row[0]:
                last_export = row[0]
                # Handle both datetime objects and strings
                if isinstance(last_export, str):
                    try:
                        return datetime.fromisoformat(last_export.replace(' ', 'T'))
                    except:
                        return datetime.fromisoformat(last_export)
                return last_export
            return None
    
    def export_logs(self, start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Export logs for given time range."""
        export_time = datetime.utcnow()
        
        # Determine time range
        if not start_time:
            last_export = self.get_last_export_time()
            if last_export:
                # Ensure it's a datetime object
                if isinstance(last_export, str):
                    try:
                        start_time = datetime.fromisoformat(last_export.replace(' ', 'T'))
                    except:
                        start_time = datetime.fromisoformat(last_export)
                else:
                    start_time = last_export
            else:
                start_time = export_time - timedelta(days=1)
        if not end_time:
            end_time = export_time
        
        # Ensure both are datetime objects
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace(' ', 'T'))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace(' ', 'T'))
        
        logger.info(f"Starting export from {start_time} to {end_time}")
        
        try:
            # Fetch logs from database
            logs = self._fetch_logs(start_time, end_time)
            
            if not logs:
                logger.info("No logs to export")
                return {'status': 'success', 'records_exported': 0}
            
            # Group logs by partition
            partitioned_logs = self._partition_logs(logs, export_time)
            
            # Export each partition
            total_exported = 0
            export_results = []
            
            for partition_key, partition_logs in partitioned_logs.items():
                result = self._export_partition(
                    partition_logs,
                    partition_key,
                    export_time,
                    start_time,
                    end_time
                )
                export_results.append(result)
                total_exported += result['record_count']
            
            logger.info(f"Export completed: {total_exported} records exported")
            
            return {
                'status': 'success',
                'records_exported': total_exported,
                'partitions': len(export_results),
                'export_details': export_results
            }
            
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _fetch_logs(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Fetch logs from database for export."""
        with self.Session() as session:
            query = text("""
                SELECT id, timestamp, service, level, message, metadata
                FROM logs
                WHERE timestamp >= :start_time AND timestamp < :end_time
                ORDER BY timestamp
                LIMIT :limit
            """)
            
            result = session.execute(
                query,
                {'start_time': start_time, 'end_time': end_time, 'limit': self.batch_size * 10}
            )
            
            logs = []
            for row in result:
                logs.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'service': row[2],
                    'level': row[3],
                    'message': row[4],
                    'metadata': json.loads(row[5]) if row[5] else {}
                })
            
            return logs
    
    def _partition_logs(self, logs: List[Dict[str, Any]], 
                       export_time: datetime) -> Dict[str, List[Dict[str, Any]]]:
        """Group logs by partition key."""
        partitions = {}
        
        for log in logs:
            partition_key = self.partitioner.generate_partition_key(log, export_time)
            if partition_key not in partitions:
                partitions[partition_key] = []
            partitions[partition_key].append(log)
        
        return partitions
    
    def _export_partition(self, logs: List[Dict[str, Any]], partition_key: str,
                         export_time: datetime, start_time: datetime,
                         end_time: datetime) -> Dict[str, Any]:
        """Export a single partition to S3."""
        # Generate filename
        filename = self.partitioner.generate_filename(
            export_time, self.export_format, self.compression
        )
        s3_key = f'{partition_key}/{filename}'
        
        # Create temporary file
        temp_dir = Path('data/exports')
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / filename
        
        try:
            # Convert to desired format and compress
            file_size = self._write_export_file(logs, temp_file)
            
            # Upload to S3
            success = self.storage_client.upload_file(
                str(temp_file),
                s3_key,
                metadata={
                    'record_count': str(len(logs)),
                    'export_time': export_time.isoformat(),
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                }
            )
            
            if success:
                # Record metadata
                self._record_export_metadata(
                    s3_key, len(logs), file_size,
                    start_time, end_time, 'completed', None
                )
            
            return {
                's3_key': s3_key,
                'record_count': len(logs),
                'file_size': file_size,
                'status': 'completed' if success else 'failed'
            }
            
        finally:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()
    
    def _write_export_file(self, logs: List[Dict[str, Any]], 
                          output_path: Path) -> int:
        """Write logs to file in specified format with compression."""
        if self.export_format == 'parquet':
            return self._write_parquet(logs, output_path)
        elif self.export_format == 'json':
            return self._write_json(logs, output_path)
        else:
            raise ValueError(f"Unsupported export format: {self.export_format}")
    
    def _write_parquet(self, logs: List[Dict[str, Any]], output_path: Path) -> int:
        """Write logs as Parquet file."""
        df = pd.DataFrame(logs)
        
        # Convert to Arrow table
        table = pa.Table.from_pandas(df)
        
        # Determine compression
        compression_type = 'gzip' if self.compression == 'gzip' else 'zstd' if self.compression == 'zstd' else None
        
        # Write Parquet
        pq.write_table(table, str(output_path), compression=compression_type)
        
        return output_path.stat().st_size
    
    def _write_json(self, logs: List[Dict[str, Any]], output_path: Path) -> int:
        """Write logs as JSON file with optional compression."""
        if self.compression == 'gzip':
            with gzip.open(str(output_path), 'wt', encoding='utf-8') as f:
                for log in logs:
                    json.dump(log, f)
                    f.write('\n')
        elif self.compression == 'zstd':
            cctx = zstd.ZstdCompressor()
            with open(str(output_path), 'wb') as f:
                with cctx.stream_writer(f) as compressor:
                    for log in logs:
                        line = json.dumps(log) + '\n'
                        compressor.write(line.encode('utf-8'))
        else:
            with open(str(output_path), 'w', encoding='utf-8') as f:
                for log in logs:
                    json.dump(log, f)
                    f.write('\n')
        
        return output_path.stat().st_size
    
    def _record_export_metadata(self, s3_key: str, record_count: int,
                                file_size: int, start_time: datetime,
                                end_time: datetime, status: str,
                                error_message: Optional[str]):
        """Record export metadata to tracking table."""
        export_id = f"{s3_key}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        with self.metadata_engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO export_metadata 
                (export_id, export_time, s3_key, record_count, file_size,
                 start_timestamp, end_timestamp, status, error_message)
                VALUES (:export_id, :export_time, :s3_key, :record_count, :file_size,
                        :start_time, :end_time, :status, :error_message)
            """), {
                'export_id': export_id,
                'export_time': datetime.utcnow(),
                's3_key': s3_key,
                'record_count': record_count,
                'file_size': file_size,
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'error_message': error_message
            })
            conn.commit()
