import asyncio
import asyncpg
import pymongo
import mysql.connector.pooling
try:
    import pyodbc
except ImportError:
    pyodbc = None  # Optional dependency
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import yaml

class DatabaseConnectionManager:
    def __init__(self, config_path: str = "config/database_config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.pools = {}
        self.logger = logging.getLogger(__name__)
        
    async def initialize_pools(self):
        """Initialize connection pools for all database types"""
        try:
            # PostgreSQL async pool
            pg_config = self.config['databases']['postgresql']
            self.pools['postgresql'] = await asyncpg.create_pool(
                host=pg_config['host'],
                port=pg_config['port'],
                user=pg_config['username'],
                password=pg_config['password'],
                database=pg_config['database'],
                min_size=5,
                max_size=pg_config['connection_pool_size']
            )
            
            # MongoDB connection
            mongo_config = self.config['databases']['mongodb']
            mongo_uri = f"mongodb://{mongo_config['username']}:{mongo_config['password']}@{mongo_config['host']}:{mongo_config['port']}/{mongo_config['database']}"
            self.pools['mongodb'] = pymongo.MongoClient(mongo_uri, maxPoolSize=mongo_config['connection_pool_size'])
            
            # MySQL connection pool
            mysql_config = self.config['databases']['mysql']
            self.pools['mysql'] = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="audit_pool",
                pool_size=mysql_config['connection_pool_size'],
                host=mysql_config['host'],
                port=mysql_config['port'],
                user=mysql_config['username'],
                password=mysql_config['password'],
                database=mysql_config['database']
            )
            
            self.logger.info("All database connection pools initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize connection pools: {e}")
            return False
    
    def get_connection(self, db_type: str):
        """Get connection from appropriate pool"""
        return self.pools.get(db_type)
    
    async def close_pools(self):
        """Close all connection pools"""
        for db_type, pool in self.pools.items():
            try:
                if db_type == 'postgresql':
                    await pool.close()
                elif db_type == 'mongodb':
                    pool.close()
                elif db_type == 'mysql':
                    # MySQL connection pool doesn't have explicit close
                    pass
                self.logger.info(f"Closed {db_type} connection pool")
            except Exception as e:
                self.logger.error(f"Error closing {db_type} pool: {e}")
