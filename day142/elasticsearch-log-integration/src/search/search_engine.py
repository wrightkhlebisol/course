from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from elasticsearch import AsyncElasticsearch
import structlog

logger = structlog.get_logger()

class SearchEngine:
    """Handles search operations on indexed logs"""
    
    def __init__(self, es_client: AsyncElasticsearch, config: Dict):
        self.es = es_client
        self.index_prefix = config.get('index_prefix', 'logs')
        self.max_results = config.get('max_results', 100)
    
    async def search_logs(self, 
                         query: Optional[str] = None,
                         level: Optional[str] = None,
                         service: Optional[str] = None,
                         time_range_minutes: int = 60,
                         size: int = 50) -> Dict[str, Any]:
        """Search logs with various filters"""
        
        # Build query
        must_clauses = []
        
        # Time range filter
        time_filter = {
            "range": {
                "@timestamp": {
                    "gte": f"now-{time_range_minutes}m",
                    "lte": "now"
                }
            }
        }
        must_clauses.append(time_filter)
        
        # Text search
        if query:
            must_clauses.append({
                "match": {
                    "message": {
                        "query": query,
                        "operator": "and"
                    }
                }
            })
        
        # Level filter
        if level:
            must_clauses.append({"term": {"level": level}})
        
        # Service filter
        if service:
            must_clauses.append({"term": {"service": service}})
        
        # Execute search
        search_body = {
            "query": {
                "bool": {
                    "must": must_clauses
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": min(size, self.max_results)
        }
        
        try:
            result = await self.es.search(
                index=f"{self.index_prefix}-*",
                body=search_body
            )
            
            hits = result['hits']['hits']
            logs = [self._format_hit(hit) for hit in hits]
            
            return {
                'total': result['hits']['total']['value'],
                'logs': logs,
                'took_ms': result['took']
            }
            
        except Exception as e:
            logger.error("search_failed", error=str(e))
            return {'total': 0, 'logs': [], 'took_ms': 0}
    
    async def aggregate_by_level(self, time_range_minutes: int = 60) -> Dict[str, int]:
        """Aggregate log counts by level"""
        agg_body = {
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": f"now-{time_range_minutes}m"
                    }
                }
            },
            "aggs": {
                "levels": {
                    "terms": {
                        "field": "level",
                        "size": 10
                    }
                }
            },
            "size": 0
        }
        
        try:
            result = await self.es.search(
                index=f"{self.index_prefix}-*",
                body=agg_body
            )
            
            buckets = result['aggregations']['levels']['buckets']
            return {bucket['key']: bucket['doc_count'] for bucket in buckets}
            
        except Exception as e:
            logger.error("aggregation_failed", error=str(e))
            return {}
    
    async def aggregate_over_time(self, 
                                  interval: str = "1m",
                                  time_range_minutes: int = 60) -> List[Dict]:
        """Get log volume over time"""
        agg_body = {
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": f"now-{time_range_minutes}m"
                    }
                }
            },
            "aggs": {
                "logs_over_time": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "fixed_interval": interval,
                        "min_doc_count": 0
                    }
                }
            },
            "size": 0
        }
        
        try:
            result = await self.es.search(
                index=f"{self.index_prefix}-*",
                body=agg_body
            )
            
            buckets = result['aggregations']['logs_over_time']['buckets']
            return [
                {
                    'timestamp': bucket['key_as_string'],
                    'count': bucket['doc_count']
                }
                for bucket in buckets
            ]
            
        except Exception as e:
            logger.error("time_aggregation_failed", error=str(e))
            return []
    
    def _format_hit(self, hit: Dict) -> Dict:
        """Format Elasticsearch hit for API response"""
        source = hit['_source']
        return {
            'id': hit['_id'],
            'timestamp': source.get('@timestamp'),
            'level': source.get('level'),
            'service': source.get('service'),
            'message': source.get('message'),
            'metadata': source.get('metadata', {}),
            'score': hit['_score']
        }
