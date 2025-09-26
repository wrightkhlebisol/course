import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Set
from pathlib import Path
import logging

from restoration.models import ArchiveMetadata, QueryRequest

logger = logging.getLogger(__name__)

class ArchiveLocator:
    def __init__(self, base_path: str, index_path: str):
        self.base_path = Path(base_path)
        self.index_path = Path(index_path)
        self.metadata_cache: Dict[str, ArchiveMetadata] = {}
        self.last_scan = None
        
    async def find_relevant_archives(self, query: QueryRequest) -> List[ArchiveMetadata]:
        """Find archives that contain data for the given time range"""
        await self._ensure_index_loaded()
        
        relevant_archives = []
        
        for file_path, metadata in self.metadata_cache.items():
            if self._archive_overlaps_timerange(metadata, query.start_time, query.end_time):
                # Apply additional filters
                if self._archive_matches_filters(metadata, query.filters):
                    relevant_archives.append(metadata)
        
        # Sort by start time for optimal processing order
        relevant_archives.sort(key=lambda x: x.start_time)
        
        logger.info(f"Found {len(relevant_archives)} relevant archives for query")
        return relevant_archives
    
    async def _ensure_index_loaded(self):
        """Load or refresh the archive index"""
        index_file = self.index_path / "archive_index.json"
        
        if not index_file.exists() or self._index_needs_refresh():
            await self._rebuild_index()
        elif not self.metadata_cache:
            await self._load_index_from_file()
    
    async def _rebuild_index(self):
        """Scan archive directory and rebuild index"""
        logger.info("Rebuilding archive index...")
        self.metadata_cache.clear()
        
        # Scan for archive files
        if self.base_path.exists():
            for file_path in self.base_path.rglob("*.archive"):
                try:
                    metadata = await self._extract_metadata(file_path)
                    if metadata:
                        self.metadata_cache[str(file_path)] = metadata
                except Exception as e:
                    logger.error(f"Failed to extract metadata from {file_path}: {e}")
        
        # Save index to file
        await self._save_index_to_file()
        self.last_scan = datetime.now()
        
        logger.info(f"Index rebuilt with {len(self.metadata_cache)} archives")
    
    async def _load_index_from_file(self):
        """Load index from saved file"""
        index_file = self.index_path / "archive_index.json"
        
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)
                    
                for file_path, metadata_dict in data.get('archives', {}).items():
                    # Convert datetime strings back to datetime objects
                    start_dt = datetime.fromisoformat(metadata_dict['start_time'])
                    end_dt = datetime.fromisoformat(metadata_dict['end_time'])
                    # Ensure timezone-naive datetimes
                    metadata_dict['start_time'] = start_dt.replace(tzinfo=None) if start_dt.tzinfo else start_dt
                    metadata_dict['end_time'] = end_dt.replace(tzinfo=None) if end_dt.tzinfo else end_dt
                    
                    self.metadata_cache[file_path] = ArchiveMetadata(**metadata_dict)
                
                last_scan_dt = datetime.fromisoformat(data.get('last_scan', datetime.now().isoformat()))
                self.last_scan = last_scan_dt.replace(tzinfo=None) if last_scan_dt.tzinfo else last_scan_dt
                
            except Exception as e:
                logger.error(f"Failed to load index from file: {e}")
                await self._rebuild_index()
    
    async def _save_index_to_file(self):
        """Save current index to file"""
        self.index_path.mkdir(parents=True, exist_ok=True)
        index_file = self.index_path / "archive_index.json"
        
        data = {
            'last_scan': datetime.now().isoformat(),
            'archives': {}
        }
        
        for file_path, metadata in self.metadata_cache.items():
            metadata_dict = metadata.model_dump()
            # Convert datetime objects to strings for JSON serialization
            metadata_dict['start_time'] = metadata.start_time.isoformat()
            metadata_dict['end_time'] = metadata.end_time.isoformat()
            data['archives'][file_path] = metadata_dict
        
        with open(index_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _extract_metadata(self, file_path: Path) -> Optional[ArchiveMetadata]:
        """Extract metadata from archive file"""
        if not file_path.exists():
            return None
            
        # For demo purposes, create metadata from filename pattern
        # In production, this would read actual archive headers
        name_parts = file_path.stem.split('_')
        
        if len(name_parts) >= 3:
            try:
                start_str = name_parts[1]
                end_str = name_parts[2]
                
                # Handle format with dashes instead of colons in time part only
                # Replace dashes with colons only in the time portion (after T)
                if 'T' in start_str:
                    date_part, time_part = start_str.split('T')
                    time_part = time_part.replace('-', ':')
                    start_str = f"{date_part}T{time_part}"
                if 'T' in end_str:
                    date_part, time_part = end_str.split('T')
                    time_part = time_part.replace('-', ':')
                    end_str = f"{date_part}T{time_part}"
                    
                start_dt = datetime.fromisoformat(start_str)
                end_dt = datetime.fromisoformat(end_str)
                # Ensure timezone-naive datetimes
                start_time = start_dt.replace(tzinfo=None) if start_dt.tzinfo else start_dt
                end_time = end_dt.replace(tzinfo=None) if end_dt.tzinfo else end_dt
                
                stat = file_path.stat()
                
                # Detect compression type from file
                compression_type = "gzip"  # Default for demo archives
                
                return ArchiveMetadata(
                    file_path=str(file_path),
                    start_time=start_time,
                    end_time=end_time,
                    compression=compression_type,
                    original_size=stat.st_size * 3,  # Estimate
                    compressed_size=stat.st_size,
                    record_count=1000,  # Estimate
                    checksum="demo_checksum",
                    tags={"source": "demo"}
                )
            except:
                pass
        
        return None
    
    def _archive_overlaps_timerange(self, metadata: ArchiveMetadata, 
                                  start_time: datetime, end_time: datetime) -> bool:
        """Check if archive time range overlaps with query time range"""
        return not (metadata.end_time < start_time or metadata.start_time > end_time)
    
    def _archive_matches_filters(self, metadata: ArchiveMetadata, filters: Dict) -> bool:
        """Check if archive matches additional filters"""
        if not filters:
            return True
            
        # Example filter matching - extend based on your needs
        for key, value in filters.items():
            if key in metadata.tags:
                if metadata.tags[key] != value:
                    return False
        
        return True
    
    def _index_needs_refresh(self) -> bool:
        """Check if index needs to be refreshed"""
        if not self.last_scan:
            return True
            
        # Refresh every hour
        return datetime.now() - self.last_scan > timedelta(hours=1)
