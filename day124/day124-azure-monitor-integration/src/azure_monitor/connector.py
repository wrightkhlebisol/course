import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, asdict

import aiohttp
import structlog
from azure.identity.aio import ClientSecretCredential
from azure.monitor.query.aio import LogsQueryClient
from azure.core.exceptions import ServiceRequestError

from config.azure_config import AzureMonitorConfig

logger = structlog.get_logger()

@dataclass
class AzureLogEntry:
    """Standardized Azure log entry"""
    timestamp: str
    workspace_id: str
    table_name: str
    subscription_id: str
    resource_group: Optional[str]
    resource_name: Optional[str]
    level: str
    message: str
    raw_data: Dict
    source: str = "azure_monitor"

class AzureMonitorConnector:
    """Azure Monitor integration connector"""
    
    def __init__(self, config: AzureMonitorConfig):
        self.config = config
        self.credential = ClientSecretCredential(
            tenant_id=config.tenant_id,
            client_id=config.client_id,
            client_secret=config.client_secret
        )
        self.client = LogsQueryClient(self.credential)
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)
        self.last_query_time = {}
        self.connection_healthy = False
        
    async def connect(self) -> bool:
        """Test Azure Monitor connection"""
        try:
            logger.info("Connecting to Azure Monitor...")
            # In demo mode, skip real connection test
            if self.config.client_id == "demo-client-id":
                self.connection_healthy = True
                logger.info("✅ Azure Monitor connection successful (demo mode)")
                return True
            # Test authentication by listing workspaces
            await self._test_connection()
            self.connection_healthy = True
            logger.info("✅ Azure Monitor connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Azure Monitor connection failed: {e}")
            return False
            
    async def _test_connection(self):
        """Test connection with a simple query"""
        if self.config.workspace_ids and self.config.workspace_ids[0] != 'demo-workspace':
            test_query = "Heartbeat | take 1"
            try:
                response = await self.client.query_workspace(
                    workspace_id=self.config.workspace_ids[0],
                    query=test_query,
                    timespan=timedelta(hours=1)
                )
            except ServiceRequestError:
                # Expected in demo mode
                pass
    
    async def discover_workspaces(self) -> List[Dict]:
        """Discover available Log Analytics workspaces"""
        logger.info("🔍 Discovering Azure workspaces...")
        
        # In demo mode, return mock workspaces
        if self.config.client_id == "demo-client-id":
            return [
                {
                    "id": "demo-workspace-1",
                    "name": "Production-Workspace",
                    "subscription_id": "demo-subscription-1",
                    "resource_group": "monitoring-rg",
                    "location": "East US"
                },
                {
                    "id": "demo-workspace-2", 
                    "name": "Staging-Workspace",
                    "subscription_id": "demo-subscription-2",
                    "resource_group": "staging-rg",
                    "location": "West US 2"
                }
            ]
        
        # Real workspace discovery would use Azure Management SDK
        workspaces = []
        for workspace_id in self.config.workspace_ids:
            workspaces.append({
                "id": workspace_id,
                "name": f"Workspace-{workspace_id[:8]}",
                "subscription_id": self.config.subscription_ids[0],
                "resource_group": "unknown",
                "location": "unknown"
            })
        
        logger.info(f"📊 Discovered {len(workspaces)} workspaces")
        return workspaces
    
    async def query_logs(self, workspace_id: str, hours_back: int = 1) -> AsyncGenerator[AzureLogEntry, None]:
        """Query logs from Azure Monitor workspace"""
        await self.rate_limiter.acquire()
        
        # KQL queries for different log types
        queries = [
            # Application logs
            """
            AppTraces
            | where TimeGenerated > ago(1h)
            | project TimeGenerated, SeverityLevel, Message, Properties
            | take 50
            """,
            # Security events  
            """
            SecurityEvent
            | where TimeGenerated > ago(1h) 
            | project TimeGenerated, Level, Activity, Computer
            | take 50
            """,
            # Performance counters
            """
            Perf
            | where TimeGenerated > ago(1h)
            | where CounterName == "% Processor Time"
            | project TimeGenerated, Computer, CounterValue, InstanceName
            | take 50
            """
        ]
        
        for query in queries:
            try:
                if self.config.client_id == "demo-client-id":
                    # Generate demo data
                    async for entry in self._generate_demo_logs(workspace_id):
                        yield entry
                else:
                    # Real Azure Monitor query
                    response = await self.client.query_workspace(
                        workspace_id=workspace_id,
                        query=query,
                        timespan=timedelta(hours=hours_back)
                    )
                    
                    for row in response.tables[0].rows:
                        yield self._convert_to_log_entry(row, workspace_id, query)
                        
            except Exception as e:
                logger.error(f"Query failed for workspace {workspace_id}: {e}")
                continue
    
    async def _generate_demo_logs(self, workspace_id: str) -> AsyncGenerator[AzureLogEntry, None]:
        """Generate demo log entries for testing"""
        import random
        
        log_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        tables = ['AppTraces', 'SecurityEvent', 'Perf']
        messages = [
            'Application started successfully',
            'User authentication completed',
            'Database connection established',
            'API request processed',
            'Cache miss occurred',
            'Memory usage threshold exceeded',
            'Security scan completed',
            'Backup operation finished'
        ]
        
        for i in range(20):
            yield AzureLogEntry(
                timestamp=datetime.now().isoformat(),
                workspace_id=workspace_id,
                table_name=random.choice(tables),
                subscription_id=f"demo-subscription-{random.randint(1,2)}",
                resource_group=f"rg-{random.choice(['prod', 'staging', 'dev'])}",
                resource_name=f"vm-{random.randint(100,999)}",
                level=random.choice(log_levels),
                message=random.choice(messages),
                raw_data={
                    "Computer": f"vm-{random.randint(100,999)}",
                    "ProcessId": random.randint(1000, 9999),
                    "ThreadId": random.randint(100, 999),
                    "Category": "Application"
                }
            )
            await asyncio.sleep(0.1)  # Simulate processing delay
    
    def _convert_to_log_entry(self, row: List, workspace_id: str, query_type: str) -> AzureLogEntry:
        """Convert Azure Monitor row to standardized log entry"""
        return AzureLogEntry(
            timestamp=row[0] if row else datetime.now().isoformat(),
            workspace_id=workspace_id,
            table_name=self._extract_table_from_query(query_type),
            subscription_id=self.config.subscription_ids[0],
            resource_group="unknown",
            resource_name="unknown",
            level=str(row[1]) if len(row) > 1 else "INFO",
            message=str(row[2]) if len(row) > 2 else "No message",
            raw_data={"raw_row": row}
        )
    
    def _extract_table_from_query(self, query: str) -> str:
        """Extract table name from KQL query"""
        lines = query.strip().split('\n')
        return lines[0].strip() if lines else "Unknown"
    
    async def get_health_status(self) -> Dict:
        """Get connector health status"""
        return {
            "healthy": self.connection_healthy,
            "last_connection_test": datetime.now().isoformat(),
            "workspaces_configured": len(self.config.workspace_ids),
            "rate_limit_status": self.rate_limiter.get_status()
        }
    
    async def close(self):
        """Close connections"""
        if self.client:
            await self.client.close()
        if self.credential:
            await self.credential.close()


class RateLimiter:
    """Token bucket rate limiter for Azure API calls"""
    
    def __init__(self, rate_per_minute: int):
        self.rate = rate_per_minute
        self.tokens = rate_per_minute
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token for API call"""
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + time_passed * self.rate / 60)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            else:
                # Wait until next token is available
                wait_time = (1 - self.tokens) * 60 / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
    
    def get_status(self) -> Dict:
        """Get rate limiter status"""
        return {
            "tokens_available": int(self.tokens),
            "rate_per_minute": self.rate,
            "last_update": self.last_update
        }
