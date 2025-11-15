import json
import time
import asyncio
from typing import Dict, List, Any
import redis.asyncio as redis
import structlog
from .context import TraceContext

logger = structlog.get_logger()

class TraceCollector:
    """Collects and stores trace data for visualization"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self.traces: Dict[str, List[Dict]] = {}
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Trace collector initialized", redis_url=self.redis_url)
        except Exception as e:
            logger.error("Failed to initialize trace collector", error=str(e))
            # Fallback to in-memory storage
            self.redis_client = None
    
    async def record_span(self, context: TraceContext, operation: str, duration_ms: float, status: str = "success", metadata: Dict = None):
        """Record a span in the trace"""
        span_data = {
            "trace_id": context.trace_id,
            "span_id": context.span_id,
            "parent_span_id": context.parent_span_id,
            "service_name": context.service_name,
            "operation": operation,
            "start_time": context.start_time,
            "duration_ms": duration_ms,
            "status": status,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        
        try:
            if self.redis_client:
                # Store in Redis with TTL
                await self.redis_client.lpush(f"trace:{context.trace_id}", json.dumps(span_data))
                await self.redis_client.expire(f"trace:{context.trace_id}", 3600)  # 1 hour TTL
            else:
                # Fallback to in-memory storage
                if context.trace_id not in self.traces:
                    self.traces[context.trace_id] = []
                self.traces[context.trace_id].append(span_data)
                
            logger.info("Span recorded", trace_id=context.trace_id, operation=operation, duration_ms=duration_ms)
        except Exception as e:
            logger.error("Failed to record span", error=str(e))
    
    async def get_trace(self, trace_id: str) -> List[Dict]:
        """Retrieve complete trace by ID"""
        try:
            if self.redis_client:
                spans_json = await self.redis_client.lrange(f"trace:{trace_id}", 0, -1)
                return [json.loads(span) for span in spans_json]
            else:
                return self.traces.get(trace_id, [])
        except Exception as e:
            logger.error("Failed to retrieve trace", trace_id=trace_id, error=str(e))
            return []
    
    async def get_recent_traces(self, limit: int = 50) -> List[Dict]:
        """Get recent trace summaries"""
        try:
            if self.redis_client:
                keys = await self.redis_client.keys("trace:*")
                recent_traces = []
                
                for key in keys[:limit]:
                    trace_id = key.decode().split(":")[1]
                    spans = await self.get_trace(trace_id)
                    if spans:
                        # Create trace summary
                        total_duration = sum(span.get("duration_ms", 0) for span in spans)
                        error_count = sum(1 for span in spans if span.get("status") == "error")
                        
                        recent_traces.append({
                            "trace_id": trace_id,
                            "span_count": len(spans),
                            "total_duration_ms": total_duration,
                            "error_count": error_count,
                            "services": list(set(span.get("service_name") for span in spans)),
                            "start_time": min(span.get("start_time", 0) for span in spans) if spans else 0
                        })
                
                return sorted(recent_traces, key=lambda x: x["start_time"], reverse=True)
            else:
                # In-memory fallback
                recent_traces = []
                for trace_id, spans in list(self.traces.items())[-limit:]:
                    if spans:
                        total_duration = sum(span.get("duration_ms", 0) for span in spans)
                        error_count = sum(1 for span in spans if span.get("status") == "error")
                        
                        recent_traces.append({
                            "trace_id": trace_id,
                            "span_count": len(spans),
                            "total_duration_ms": total_duration,
                            "error_count": error_count,
                            "services": list(set(span.get("service_name") for span in spans)),
                            "start_time": min(span.get("start_time", 0) for span in spans) if spans else 0
                        })
                
                return sorted(recent_traces, key=lambda x: x["start_time"], reverse=True)
        except Exception as e:
            logger.error("Failed to get recent traces", error=str(e))
            return []

# Global trace collector instance
trace_collector = None

async def get_trace_collector():
    """Get or create trace collector instance"""
    global trace_collector
    if trace_collector is None:
        from config.config import config
        trace_collector = TraceCollector(config.redis_url)
        await trace_collector.initialize()
    return trace_collector
