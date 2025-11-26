from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import structlog
from typing import Dict, Any, Optional
import yaml
import os
from datetime import datetime

logger = structlog.get_logger()

class SparkManager:
    """Manages Spark session and job execution"""
    
    def __init__(self, config_path: str = "config/spark_config.yaml"):
        self.config = self._load_config(config_path)
        self.spark: Optional[SparkSession] = None
        self.job_history = []
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load Spark configuration"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def initialize_spark(self) -> SparkSession:
        """Initialize Spark session with configuration"""
        logger.info("Initializing Spark session")
        
        spark_config = self.config['spark']
        
        self.spark = SparkSession.builder \
            .appName(spark_config['app_name']) \
            .master(spark_config['master']) \
            .config("spark.executor.memory", spark_config['executor_memory']) \
            .config("spark.driver.memory", spark_config['driver_memory']) \
            .config("spark.executor.cores", spark_config['executor_cores']) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.es.nodes", self.config['elasticsearch']['host']) \
            .config("spark.es.port", str(self.config['elasticsearch']['port'])) \
            .config("spark.driver.host", "localhost") \
            .config("spark.driver.bindAddress", "0.0.0.0") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel(spark_config['log_level'])
        
        logger.info("Spark session initialized", 
                   app_name=spark_config['app_name'],
                   master=spark_config['master'])
        
        return self.spark
    
    def get_or_create_spark(self) -> SparkSession:
        """Get existing or create new Spark session"""
        if self.spark is None:
            return self.initialize_spark()
        return self.spark
    
    def stop_spark(self):
        """Stop Spark session"""
        if self.spark:
            logger.info("Stopping Spark session")
            self.spark.stop()
            self.spark = None
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get Spark cluster information"""
        if not self.spark:
            return {"status": "not_initialized"}
        
        sc = self.spark.sparkContext
        ui_url = sc.uiWebUrl
        
        # Replace internal IP addresses with localhost for browser accessibility
        if ui_url:
            import re
            # Replace IP addresses (like 10.255.255.254) with localhost
            ui_url = re.sub(r'http://[\d\.]+:(\d+)', r'http://localhost:\1', ui_url)
            # Also handle cases where it might already have localhost
            ui_url = ui_url.replace('127.0.0.1', 'localhost')
            # Replace any other internal IPs
            ui_url = re.sub(r'http://(?!localhost|127\.0\.0\.1)[\d\.]+:(\d+)', r'http://localhost:\1', ui_url)
        
        return {
            "status": "running",
            "app_name": sc.appName,
            "app_id": sc.applicationId,
            "master": sc.master,
            "version": sc.version,
            "default_parallelism": sc.defaultParallelism,
            "ui_web_url": ui_url
        }
    
    def record_job_execution(self, job_name: str, status: str, 
                            records_processed: int, duration: float, 
                            details: Dict = None):
        """Record job execution for monitoring"""
        execution_record = {
            "job_name": job_name,
            "status": status,
            "records_processed": records_processed,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.job_history.append(execution_record)
        logger.info("Job execution recorded", **execution_record)
    
    def get_job_history(self, limit: int = 10) -> list:
        """Get recent job execution history"""
        return self.job_history[-limit:]
