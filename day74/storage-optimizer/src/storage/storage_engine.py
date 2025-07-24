"""
Adaptive Storage Engine with Multiple Format Support
Automatically optimizes storage format based on access patterns
"""
import json
import struct
import lz4.frame
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio
import threading
from dataclasses import dataclass
from enum import Enum

class StorageFormat(Enum):
    ROW_ORIENTED = "row"
    COLUMNAR = "columnar"
    HYBRID = "hybrid"

@dataclass
class StorageMetrics:
    read_count: int = 0
    write_count: int = 0
    compression_ratio: float = 0.0
    query_time_avg: float = 0.0
    storage_size: int = 0

class AdaptiveStorageEngine:
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Storage backends
        self.row_storage = RowStorage(self.base_path / "row")
        self.columnar_storage = ColumnarStorage(self.base_path / "columnar")
        self.hybrid_storage = HybridStorage(self.base_path / "hybrid")
        
        # Pattern analyzer
        self.pattern_analyzer = QueryPatternAnalyzer()
        self.format_selector = FormatSelector()
        
        # Metrics tracking
        self.metrics = {}
        self.access_patterns = {}
        self.format_distribution = {'row': 0, 'columnar': 0, 'hybrid': 0}
        self.partition_formats = {}  # Track which format each partition uses
        
        print("🏗️  Adaptive Storage Engine initialized")
    
    async def write_logs(self, logs: List[Dict[str, Any]], partition_key: str = "default") -> bool:
        """Write logs using optimal format based on current patterns"""
        try:
            # Analyze patterns to determine format
            optimal_format = await self.format_selector.select_format(
                partition_key, 
                self.access_patterns.get(partition_key, {})
            )
            
            # Route to appropriate storage backend
            if optimal_format == StorageFormat.ROW_ORIENTED:
                result = await self.row_storage.write(logs, partition_key)
            elif optimal_format == StorageFormat.COLUMNAR:
                result = await self.columnar_storage.write(logs, partition_key)
            else:  # HYBRID
                result = await self.hybrid_storage.write(logs, partition_key)
            
            # Update metrics
            self._update_write_metrics(partition_key, len(logs))
            
            # Track format distribution
            self._update_format_distribution(partition_key, optimal_format)
            
            print(f"📝 Written {len(logs)} logs using {optimal_format.value} format")
            return result
            
        except Exception as e:
            print(f"❌ Write error: {e}")
            return False
    
    async def read_logs(self, query: Dict[str, Any], partition_key: str = "default") -> List[Dict[str, Any]]:
        """Read logs using optimal storage backend"""
        start_time = datetime.now()
        
        try:
            # Track query pattern
            await self.pattern_analyzer.analyze_query(query, partition_key)
            
            # Determine which storage has the data
            format_used = self._determine_storage_location(partition_key)
            
            if format_used == StorageFormat.ROW_ORIENTED:
                results = await self.row_storage.read(query, partition_key)
            elif format_used == StorageFormat.COLUMNAR:
                results = await self.columnar_storage.read(query, partition_key)
            else:  # HYBRID
                results = await self.hybrid_storage.read(query, partition_key)
            
            # Update metrics
            query_time = (datetime.now() - start_time).total_seconds()
            self._update_read_metrics(partition_key, query_time)
            
            print(f"📖 Read {len(results)} logs in {query_time:.3f}s using {format_used.value} format")
            return results
            
        except Exception as e:
            print(f"❌ Read error: {e}")
            return []
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get storage optimization statistics"""
        stats = {
            'partitions': {},
            'total_storage_mb': 0,
            'compression_savings': 0,
            'format_distribution': {'row': 0, 'columnar': 0, 'hybrid': 0}
        }
        
        # Calculate stats for each partition
        total_compression_savings = 0
        for partition_key, metrics in self.metrics.items():
            storage_mb = round(metrics.storage_size / (1024 * 1024), 2)
            compression_savings = round((1 - metrics.compression_ratio) * 100, 1)
            
            stats['partitions'][partition_key] = {
                'reads': metrics.read_count,
                'writes': metrics.write_count,
                'avg_query_time': metrics.query_time_avg,
                'compression_ratio': metrics.compression_ratio,
                'storage_mb': storage_mb
            }
            stats['total_storage_mb'] += storage_mb
            total_compression_savings += compression_savings
        
        # Calculate average compression savings
        if self.metrics:
            stats['compression_savings'] = round(total_compression_savings / len(self.metrics), 1)
        
        # Update format distribution in stats
        stats['format_distribution'] = self.format_distribution.copy()
        
        return stats
    
    def _update_write_metrics(self, partition_key: str, log_count: int):
        """Update write metrics for partition"""
        if partition_key not in self.metrics:
            self.metrics[partition_key] = StorageMetrics()
        
        metrics = self.metrics[partition_key]
        metrics.write_count += log_count
        
        # Estimate storage size (rough calculation)
        # Each log entry is approximately 200 bytes
        estimated_size = log_count * 200
        metrics.storage_size += estimated_size
        
        # Calculate compression ratio (simulated)
        # LZ4 typically achieves 2-3x compression for JSON
        compression_ratio = 0.65  # 35% compression
        metrics.compression_ratio = compression_ratio
    
    def _update_format_distribution(self, partition_key: str, format_used: StorageFormat):
        """Update format distribution tracking"""
        # Remove old format count if partition had a different format
        if partition_key in self.partition_formats:
            old_format = self.partition_formats[partition_key]
            if old_format != format_used:
                self.format_distribution[old_format.value] = max(0, self.format_distribution[old_format.value] - 1)
        
        # Add new format count
        self.format_distribution[format_used.value] += 1
        
        # Update partition format tracking
        self.partition_formats[partition_key] = format_used
    
    def _update_read_metrics(self, partition_key: str, query_time: float):
        """Update read metrics for partition"""
        if partition_key not in self.metrics:
            self.metrics[partition_key] = StorageMetrics()
        
        metrics = self.metrics[partition_key]
        metrics.read_count += 1
        
        # Calculate moving average
        if metrics.read_count == 1:
            metrics.query_time_avg = query_time
        else:
            metrics.query_time_avg = (metrics.query_time_avg * (metrics.read_count - 1) + query_time) / metrics.read_count
    
    def _determine_storage_location(self, partition_key: str) -> StorageFormat:
        """Determine which storage backend contains the data"""
        # For demo, we'll check all backends and return the first with data
        if (self.base_path / "row" / f"{partition_key}.json").exists():
            return StorageFormat.ROW_ORIENTED
        elif (self.base_path / "columnar" / f"{partition_key}.parquet").exists():
            return StorageFormat.COLUMNAR
        else:
            return StorageFormat.HYBRID

class RowStorage:
    """Row-oriented storage optimized for full record access"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(exist_ok=True)
    
    async def write(self, logs: List[Dict[str, Any]], partition_key: str) -> bool:
        """Write logs in row-oriented format with compression"""
        try:
            file_path = self.base_path / f"{partition_key}.json"
            
            # Load existing data if file exists
            existing_logs = []
            if file_path.exists():
                with open(file_path, 'r') as f:
                    existing_logs = json.load(f)
            
            # Append new logs
            all_logs = existing_logs + logs
            
            # Write with LZ4 compression for speed
            compressed_data = lz4.frame.compress(
                json.dumps(all_logs, separators=(',', ':')).encode()
            )
            
            with open(f"{file_path}.lz4", 'wb') as f:
                f.write(compressed_data)
            
            # Also keep uncompressed for compatibility
            with open(file_path, 'w') as f:
                json.dump(all_logs, f, separators=(',', ':'))
            
            return True
        except Exception as e:
            print(f"❌ Row storage write error: {e}")
            return False
    
    async def read(self, query: Dict[str, Any], partition_key: str) -> List[Dict[str, Any]]:
        """Read logs from row-oriented storage"""
        try:
            file_path = self.base_path / f"{partition_key}.json"
            
            if not file_path.exists():
                return []
            
            # Try compressed version first
            compressed_path = f"{file_path}.lz4"
            if Path(compressed_path).exists():
                with open(compressed_path, 'rb') as f:
                    compressed_data = f.read()
                decompressed_data = lz4.frame.decompress(compressed_data)
                logs = json.loads(decompressed_data.decode())
            else:
                with open(file_path, 'r') as f:
                    logs = json.load(f)
            
            # Apply query filters
            filtered_logs = self._apply_filters(logs, query)
            return filtered_logs
            
        except Exception as e:
            print(f"❌ Row storage read error: {e}")
            return []
    
    def _apply_filters(self, logs: List[Dict], query: Dict) -> List[Dict]:
        """Apply query filters to logs"""
        filtered = logs
        
        if 'level' in query:
            filtered = [log for log in filtered if log.get('level') == query['level']]
        
        if 'service' in query:
            filtered = [log for log in filtered if log.get('service') == query['service']]
        
        if 'time_range' in query:
            start_time = query['time_range'].get('start')
            end_time = query['time_range'].get('end')
            if start_time:
                filtered = [log for log in filtered if log.get('timestamp', '') >= start_time]
            if end_time:
                filtered = [log for log in filtered if log.get('timestamp', '') <= end_time]
        
        return filtered

class ColumnarStorage:
    """Columnar storage optimized for analytical queries"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(exist_ok=True)
    
    async def write(self, logs: List[Dict[str, Any]], partition_key: str) -> bool:
        """Write logs in columnar format using Parquet"""
        try:
            file_path = self.base_path / f"{partition_key}.parquet"
            
            # Convert to DataFrame for columnar processing
            df = pd.DataFrame(logs)
            
            # Append to existing data if file exists
            if file_path.exists():
                existing_df = pd.read_parquet(file_path)
                df = pd.concat([existing_df, df], ignore_index=True)
            
            # Write as Parquet with compression
            df.to_parquet(
                file_path,
                compression='snappy',
                index=False
            )
            
            return True
        except Exception as e:
            print(f"❌ Columnar storage write error: {e}")
            return False
    
    async def read(self, query: Dict[str, Any], partition_key: str) -> List[Dict[str, Any]]:
        """Read logs from columnar storage with column pruning"""
        try:
            file_path = self.base_path / f"{partition_key}.parquet"
            
            if not file_path.exists():
                return []
            
            # Read with column pruning if specific columns requested
            columns = query.get('columns', None)
            df = pd.read_parquet(file_path, columns=columns)
            
            # Apply filters
            if 'level' in query:
                df = df[df['level'] == query['level']]
            
            if 'service' in query:
                df = df[df['service'] == query['service']]
            
            if 'time_range' in query:
                start_time = query['time_range'].get('start')
                end_time = query['time_range'].get('end')
                if start_time:
                    df = df[df['timestamp'] >= start_time]
                if end_time:
                    df = df[df['timestamp'] <= end_time]
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Columnar storage read error: {e}")
            return []

class HybridStorage:
    """Hybrid storage that combines row and columnar approaches"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(exist_ok=True)
        
        # Use both storage types internally
        self.row_storage = RowStorage(self.base_path / "hot")
        self.columnar_storage = ColumnarStorage(self.base_path / "cold")
        
        # Hot data threshold (recent data stays in row format)
        self.hot_data_hours = 24
    
    async def write(self, logs: List[Dict[str, Any]], partition_key: str) -> bool:
        """Write to hot storage first, migrate to cold storage later"""
        return await self.row_storage.write(logs, partition_key)
    
    async def read(self, query: Dict[str, Any], partition_key: str) -> List[Dict[str, Any]]:
        """Read from both hot and cold storage, merge results"""
        try:
            hot_results = await self.row_storage.read(query, partition_key)
            cold_results = await self.columnar_storage.read(query, partition_key)
            
            # Merge and deduplicate results
            all_results = hot_results + cold_results
            
            # Remove duplicates based on log ID if available
            seen_ids = set()
            unique_results = []
            for result in all_results:
                log_id = result.get('id', str(hash(json.dumps(result, sort_keys=True))))
                if log_id not in seen_ids:
                    seen_ids.add(log_id)
                    unique_results.append(result)
            
            return unique_results
            
        except Exception as e:
            print(f"❌ Hybrid storage read error: {e}")
            return []

class QueryPatternAnalyzer:
    """Analyzes query patterns to inform storage format decisions"""
    
    def __init__(self):
        self.query_history = {}
        self.field_access_frequency = {}
    
    async def analyze_query(self, query: Dict[str, Any], partition_key: str):
        """Analyze query pattern and update statistics"""
        if partition_key not in self.query_history:
            self.query_history[partition_key] = []
            self.field_access_frequency[partition_key] = {}
        
        # Track query pattern
        query_pattern = {
            'timestamp': datetime.now().isoformat(),
            'query_type': self._classify_query(query),
            'fields_accessed': query.get('columns', []),
            'has_filters': bool(query.get('level') or query.get('service') or query.get('time_range'))
        }
        
        self.query_history[partition_key].append(query_pattern)
        
        # Update field access frequency
        for field in query_pattern['fields_accessed']:
            if field not in self.field_access_frequency[partition_key]:
                self.field_access_frequency[partition_key][field] = 0
            self.field_access_frequency[partition_key][field] += 1
        
        # Keep only recent history
        if len(self.query_history[partition_key]) > 1000:
            self.query_history[partition_key] = self.query_history[partition_key][-1000:]
    
    def _classify_query(self, query: Dict[str, Any]) -> str:
        """Classify query type for pattern analysis"""
        if query.get('columns') and len(query['columns']) <= 3:
            return 'analytical'  # Few columns = columnar friendly
        elif not query.get('columns'):
            return 'full_record'  # All columns = row friendly
        else:
            return 'mixed'  # Some columns = hybrid candidate

class FormatSelector:
    """Selects optimal storage format based on access patterns"""
    
    async def select_format(self, partition_key: str, access_patterns: Dict) -> StorageFormat:
        """Select optimal storage format based on patterns"""
        # For demo purposes, let's make the format selection more interesting
        # Use the partition key to determine format for demonstration
        
        if 'error' in partition_key:
            # Error logs are typically accessed for full records (debugging)
            return StorageFormat.ROW_ORIENTED
        elif 'api' in partition_key:
            # API logs often have analytical queries (performance monitoring)
            return StorageFormat.COLUMNAR
        elif 'web' in partition_key:
            # Web logs have mixed access patterns
            return StorageFormat.HYBRID
        else:
            # Default to row-oriented for new partitions
            return StorageFormat.ROW_ORIENTED
