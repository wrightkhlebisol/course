import asyncio
import json
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, AsyncIterator, Optional
from pathlib import Path
import logging

from restoration.models import QueryRequest, QueryResponse, RestorationJob
from archive.locator import ArchiveLocator
from restoration.decompressor import StreamingDecompressor
from cache.manager import SmartCache

logger = logging.getLogger(__name__)

class QueryProcessor:
    def __init__(self, archive_locator: ArchiveLocator, 
                 decompressor: StreamingDecompressor,
                 cache: SmartCache):
        self.archive_locator = archive_locator
        self.decompressor = decompressor
        self.cache = cache
        self.active_jobs: Dict[str, RestorationJob] = {}
    
    async def execute_query(self, query: QueryRequest) -> QueryResponse:
        """Execute query across live and archived data"""
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(query)
        
        # Check cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return QueryResponse(
                **cached_result,
                cache_hit=True,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # Find relevant archives
        archives = await self.archive_locator.find_relevant_archives(query)
        
        # Process query
        if query.stream_results:
            # For streaming queries, create a job
            job_id = str(uuid.uuid4())
            job = RestorationJob(
                job_id=job_id,
                query=query,
                status="processing",
                progress=0.0,
                start_time=datetime.now()
            )
            self.active_jobs[job_id] = job
            
            # Start background processing
            asyncio.create_task(self._process_streaming_query(job, archives))
            
            return QueryResponse(
                records=[],
                total_count=0,
                sources=[a.file_path for a in archives],
                processing_time_ms=int((time.time() - start_time) * 1000),
                page_token=job_id
            )
        else:
            # Process immediately for non-streaming queries
            records = []
            total_count = 0
            
            for archive in archives:
                archive_records = await self._process_archive(archive, query)
                records.extend(archive_records)
                total_count += len(archive_records)
                
                # Apply pagination
                if len(records) >= query.page_size:
                    records = records[:query.page_size]
                    break
            
            response = QueryResponse(
                records=records,
                total_count=total_count,
                sources=[a.file_path for a in archives],
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
            
            # Cache response
            await self.cache.set(cache_key, response.model_dump(), ttl=1800)  # 30 min
            
            return response
    
    async def _process_archive(self, archive, query: QueryRequest) -> List[Dict[str, Any]]:
        """Process single archive file"""
        records = []
        
        try:
            # Stream decompress archive
            async for chunk in self.decompressor.decompress_stream(
                Path(archive.file_path), archive.compression
            ):
                # Parse log entries from chunk
                chunk_records = self._parse_log_chunk(chunk.decode('utf-8', errors='ignore'))
                
                # Apply filters
                filtered_records = [
                    record for record in chunk_records
                    if self._matches_filters(record, query.filters)
                ]
                
                records.extend(filtered_records)
                
                # Limit results to prevent memory issues
                if len(records) >= 10000:
                    break
        
        except Exception as e:
            logger.error(f"Error processing archive {archive.file_path}: {e}")
        
        return records
    
    def _parse_log_chunk(self, chunk: str) -> List[Dict[str, Any]]:
        """Parse log entries from text chunk"""
        records = []
        
        # Split by lines and parse JSON
        for line in chunk.strip().split('\n'):
            if line.strip():
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError:
                    # Skip invalid JSON lines
                    continue
        
        return records
    
    def _matches_filters(self, record: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if record matches query filters"""
        if not filters:
            return True
        
        for key, value in filters.items():
            if key in record:
                if isinstance(value, list):
                    if record[key] not in value:
                        return False
                else:
                    if record[key] != value:
                        return False
            else:
                return False
        
        return True
    
    def _generate_cache_key(self, query: QueryRequest) -> str:
        """Generate unique cache key for query"""
        key_data = {
            'start_time': query.start_time.isoformat(),
            'end_time': query.end_time.isoformat(),
            'filters': query.filters,
            'page_size': query.page_size
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return f"query:{hash(key_str)}"
    
    async def get_job_status(self, job_id: str) -> Optional[RestorationJob]:
        """Get status of streaming job"""
        return self.active_jobs.get(job_id)
    
    async def _process_streaming_query(self, job: RestorationJob, archives):
        """Process query in background for streaming"""
        try:
            job.status = "processing"
            
            # Simulate processing with progress updates
            for i, archive in enumerate(archives):
                await asyncio.sleep(0.1)  # Simulate work
                job.progress = (i + 1) / len(archives)
            
            job.status = "completed"
            job.progress = 1.0
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            logger.error(f"Job {job.job_id} failed: {e}")
