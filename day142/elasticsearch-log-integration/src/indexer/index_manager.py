from datetime import datetime, timedelta
from typing import Dict, List
from elasticsearch import AsyncElasticsearch
import structlog

logger = structlog.get_logger()

class IndexManager:
    """Manages Elasticsearch index lifecycle"""
    
    def __init__(self, es_client: AsyncElasticsearch, config: Dict):
        self.es = es_client
        self.index_prefix = config.get('index_prefix', 'logs')
        self.retention_days = config.get('retention_days', 30)
        
    async def create_index_template(self):
        """Create index template for log indices"""
        template = {
            "index_patterns": [f"{self.index_prefix}-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "5s",
                    "index.mapping.total_fields.limit": 2000
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "message": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}
                        },
                        "level": {"type": "keyword"},
                        "service": {"type": "keyword"},
                        "component": {"type": "keyword"},
                        "response_time_ms": {"type": "integer"},
                        "status_code": {"type": "integer"},
                        "tags": {"type": "keyword"},
                        "indexed_at": {"type": "date"}
                    }
                }
            }
        }
        
        try:
            await self.es.indices.put_index_template(
                name=f"{self.index_prefix}_template",
                body=template
            )
            logger.info("index_template_created", prefix=self.index_prefix)
            return True
        except Exception as e:
            logger.error("template_creation_failed", error=str(e))
            return False
    
    async def ensure_today_index(self) -> str:
        """Ensure today's index exists"""
        index_name = f"{self.index_prefix}-{datetime.now().strftime('%Y.%m.%d')}"
        
        try:
            exists = await self.es.indices.exists(index=index_name)
            if not exists:
                await self.es.indices.create(index=index_name)
                logger.info("index_created", index=index_name)
            return index_name
        except Exception as e:
            logger.error("index_ensure_failed", error=str(e), index=index_name)
            return index_name
    
    async def cleanup_old_indices(self) -> int:
        """Delete indices older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0
        
        try:
            # Get all indices matching prefix
            indices = await self.es.indices.get(index=f"{self.index_prefix}-*")
            
            for index_name in indices:
                try:
                    # Extract date from index name
                    date_str = index_name.split('-', 1)[1]
                    index_date = datetime.strptime(date_str, '%Y.%m.%d')
                    
                    if index_date < cutoff_date:
                        await self.es.indices.delete(index=index_name)
                        logger.info("index_deleted", index=index_name)
                        deleted_count += 1
                except (ValueError, IndexError) as e:
                    logger.warning("index_date_parse_failed", index=index_name, error=str(e))
                    
            return deleted_count
            
        except Exception as e:
            logger.error("cleanup_failed", error=str(e))
            return deleted_count
    
    async def get_index_stats(self) -> List[Dict]:
        """Get statistics for all log indices"""
        try:
            stats = await self.es.indices.stats(index=f"{self.index_prefix}-*")
            
            indices_info = []
            for index_name, index_stats in stats['indices'].items():
                indices_info.append({
                    'name': index_name,
                    'docs': index_stats['primaries']['docs']['count'],
                    'size': index_stats['primaries']['store']['size_in_bytes'],
                    'size_mb': round(index_stats['primaries']['store']['size_in_bytes'] / 1024 / 1024, 2)
                })
                
            return sorted(indices_info, key=lambda x: x['name'], reverse=True)
            
        except Exception as e:
            logger.error("stats_failed", error=str(e))
            return []
