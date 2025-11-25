import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from elasticsearch import AsyncElasticsearch, helpers
from elasticsearch.exceptions import ConnectionError, TransportError
import structlog

logger = structlog.get_logger()

class LogIndexer:
    """Handles bulk indexing of logs to Elasticsearch"""
    
    def __init__(self, es_client: AsyncElasticsearch, config: Dict[str, Any]):
        self.es = es_client
        self.config = config
        self.batch: List[Dict] = []
        self.index_prefix = config.get('index_prefix', 'logs')
        self.batch_size = config.get('batch_size', 100)
        self.last_flush = datetime.now()
        self.flush_interval = config.get('flush_interval', 2)
        self.stats = {
            'indexed': 0,
            'failed': 0,
            'batches': 0
        }
        
    async def add_log(self, log_entry: Dict[str, Any]) -> bool:
        """Add log to indexing batch"""
        try:
            # Enrich log with indexing metadata
            doc = self._prepare_document(log_entry)
            self.batch.append(doc)
            
            # Check if batch is ready to flush
            if len(self.batch) >= self.batch_size:
                await self.flush_batch()
                
            return True
            
        except Exception as e:
            logger.error("add_log_failed", error=str(e), log=log_entry)
            self.stats['failed'] += 1
            return False
    
    def _prepare_document(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare log document for Elasticsearch indexing"""
        timestamp = log_entry.get('timestamp', datetime.now().isoformat())
        
        # Parse timestamp if string
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                dt = datetime.now()
        else:
            dt = timestamp
            
        # Determine index name (daily indices)
        index_name = f"{self.index_prefix}-{dt.strftime('%Y.%m.%d')}"
        
        # Prepare document
        doc = {
            '_index': index_name,
            '_source': {
                '@timestamp': dt.isoformat(),
                'message': log_entry.get('message', ''),
                'level': log_entry.get('level', 'INFO'),
                'service': log_entry.get('service', 'unknown'),
                'component': log_entry.get('component', ''),
                'metadata': log_entry.get('metadata', {}),
                'tags': log_entry.get('tags', []),
                'indexed_at': datetime.now().isoformat()
            }
        }
        
        # Add custom fields from metadata
        if 'response_time' in log_entry.get('metadata', {}):
            doc['_source']['response_time_ms'] = log_entry['metadata']['response_time']
        
        if 'status_code' in log_entry.get('metadata', {}):
            doc['_source']['status_code'] = log_entry['metadata']['status_code']
            
        return doc
    
    async def flush_batch(self) -> Dict[str, int]:
        """Flush current batch to Elasticsearch"""
        if not self.batch:
            return {'indexed': 0, 'failed': 0}
            
        logger.info("flushing_batch", size=len(self.batch))
        
        try:
            # Bulk index using helpers
            success, failed = await helpers.async_bulk(
                self.es,
                self.batch,
                raise_on_error=False,
                raise_on_exception=False
            )
            
            self.stats['indexed'] += success
            self.stats['failed'] += len(failed) if isinstance(failed, list) else 0
            self.stats['batches'] += 1
            
            logger.info("batch_flushed", 
                       success=success, 
                       failed=len(failed) if isinstance(failed, list) else 0,
                       total_indexed=self.stats['indexed'])
            
            self.batch.clear()
            self.last_flush = datetime.now()
            
            return {'indexed': success, 'failed': len(failed) if isinstance(failed, list) else 0}
            
        except Exception as e:
            logger.error("flush_failed", error=str(e))
            self.stats['failed'] += len(self.batch)
            self.batch.clear()
            return {'indexed': 0, 'failed': len(self.batch)}
    
    async def periodic_flush(self):
        """Background task to flush based on time interval"""
        while True:
            await asyncio.sleep(self.flush_interval)
            
            time_since_flush = (datetime.now() - self.last_flush).total_seconds()
            if self.batch and time_since_flush >= self.flush_interval:
                await self.flush_batch()
    
    def get_stats(self) -> Dict[str, int]:
        """Get indexing statistics"""
        return self.stats.copy()
