from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, List
import time
import builtins

logger = structlog.get_logger()

class LogAnalyzer:
    """Analyzes logs using Spark SQL and DataFrames"""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.results = {}
    
    def read_logs_from_json(self, path: str) -> DataFrame:
        """Read logs from JSON files"""
        logger.info("Reading logs from JSON", path=path)
        
        schema = StructType([
            StructField("timestamp", StringType(), True),
            StructField("level", StringType(), True),
            StructField("service", StringType(), True),
            StructField("message", StringType(), True),
            StructField("response_time", IntegerType(), True),
            StructField("status_code", IntegerType(), True),
            StructField("user_id", StringType(), True),
            StructField("endpoint", StringType(), True),
            StructField("metadata", MapType(StringType(), StringType()), True)
        ])
        
        df = self.spark.read \
            .schema(schema) \
            .json(path)
        
        # Convert timestamp string to timestamp type
        df = df.withColumn("timestamp", to_timestamp(col("timestamp")))
        
        logger.info("Logs loaded", count=df.count())
        return df
    
    def analyze_error_rates(self, df: DataFrame) -> DataFrame:
        """Calculate error rates by service and time"""
        logger.info("Analyzing error rates")
        
        # Add hour column for grouping
        df_with_hour = df.withColumn("hour", date_trunc("hour", "timestamp"))
        
        # Calculate error rates per service per hour
        error_analysis = df_with_hour.groupBy("service", "hour").agg(
            count("*").alias("total_requests"),
            sum(when(col("level") == "ERROR", 1).otherwise(0)).alias("error_count"),
            sum(when(col("level") == "WARN", 1).otherwise(0)).alias("warn_count"),
            avg("response_time").alias("avg_response_time"),
            max("response_time").alias("max_response_time")
        )
        
        # Calculate error rate percentage
        error_analysis = error_analysis.withColumn(
            "error_rate",
            (col("error_count") / col("total_requests") * lit(100))
        )
        
        error_analysis = error_analysis.orderBy(desc("error_rate"))
        
        self.results['error_rates'] = error_analysis
        return error_analysis
    
    def analyze_performance_metrics(self, df: DataFrame) -> DataFrame:
        """Analyze performance metrics by endpoint"""
        logger.info("Analyzing performance metrics")
        
        perf_metrics = df.filter(col("endpoint").isNotNull()).groupBy("endpoint", "service").agg(
            count("*").alias("request_count"),
            avg("response_time").alias("avg_response_time"),
            expr("percentile_approx(response_time, 0.50)").alias("p50_response_time"),
            expr("percentile_approx(response_time, 0.95)").alias("p95_response_time"),
            expr("percentile_approx(response_time, 0.99)").alias("p99_response_time"),
            max("response_time").alias("max_response_time")
        ).orderBy(desc("request_count"))
        
        self.results['performance_metrics'] = perf_metrics
        return perf_metrics
    
    def detect_anomalies(self, df: DataFrame, threshold_multiplier: float = 3.0) -> DataFrame:
        """Detect anomalies in response times using statistical methods"""
        logger.info("Detecting anomalies", threshold_multiplier=threshold_multiplier)
        
        # Calculate statistics by service
        stats = df.groupBy("service").agg(
            avg("response_time").alias("avg_rt"),
            stddev("response_time").alias("stddev_rt")
        )
        
        # Join stats back to original data
        df_with_stats = df.join(stats, "service")
        
        # Flag anomalies (response time > mean + 3*stddev)
        anomalies = df_with_stats.withColumn(
            "is_anomaly",
            when(
                col("response_time") > (col("avg_rt") + lit(threshold_multiplier) * col("stddev_rt")),
                lit(True)
            ).otherwise(lit(False))
        ).filter(col("is_anomaly") == True)
        
        self.results['anomalies'] = anomalies
        logger.info("Anomalies detected", count=anomalies.count())
        return anomalies
    
    def correlation_analysis(self, df: DataFrame) -> Dict[str, float]:
        """Analyze correlation between error rates and response times"""
        logger.info("Performing correlation analysis")
        
        # Aggregate by service and hour
        hourly_metrics = df.withColumn("hour", date_trunc("hour", "timestamp")) \
            .groupBy("service", "hour").agg(
                avg("response_time").alias("avg_response_time"),
                (sum(when(col("level") == "ERROR", 1).otherwise(0)) / count("*")).alias("error_rate")
            )
        
        # Calculate correlation (handle None case)
        correlation = hourly_metrics.stat.corr("avg_response_time", "error_rate")
        correlation = correlation if correlation is not None else 0.0
        
        result = {
            "correlation_coefficient": builtins.round(correlation, 4),
            "interpretation": self._interpret_correlation(correlation)
        }
        
        logger.info("Correlation analysis complete", **result)
        return result
    
    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation coefficient"""
        abs_corr = builtins.abs(corr)
        if abs_corr >= 0.7:
            return "Strong correlation"
        elif abs_corr >= 0.4:
            return "Moderate correlation"
        elif abs_corr >= 0.2:
            return "Weak correlation"
        else:
            return "Very weak or no correlation"
    
    def top_users_by_requests(self, df: DataFrame, limit: int = 10) -> DataFrame:
        """Find top users by request count"""
        logger.info("Finding top users", limit=limit)
        
        top_users = df.filter(col("user_id").isNotNull()).groupBy("user_id").agg(
            count("*").alias("request_count"),
            sum(when(col("level") == "ERROR", 1).otherwise(0)).alias("error_count"),
            avg("response_time").alias("avg_response_time")
        ).orderBy(desc("request_count")).limit(limit)
        
        self.results['top_users'] = top_users
        return top_users
    
    def save_results(self, output_path: str, format: str = "parquet"):
        """Save all analysis results"""
        logger.info("Saving results", output_path=output_path, format=format)
        
        for name, df in self.results.items():
            if df is not None:
                result_path = f"{output_path}/{name}"
                
                if format == "parquet":
                    df.write.mode("overwrite").parquet(result_path)
                elif format == "json":
                    df.write.mode("overwrite").json(result_path)
                elif format == "csv":
                    df.write.mode("overwrite").option("header", True).csv(result_path)
                
                logger.info("Result saved", name=name, path=result_path)
    
    def run_full_analysis(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """Run complete log analysis pipeline"""
        start_time = time.time()
        logger.info("Starting full analysis pipeline")
        
        # Load data
        df = self.read_logs_from_json(input_path)
        total_records = df.count()
        
        # Run analyses
        error_rates = self.analyze_error_rates(df)
        perf_metrics = self.analyze_performance_metrics(df)
        anomalies = self.detect_anomalies(df)
        correlation = self.correlation_analysis(df)
        top_users = self.top_users_by_requests(df)
        
        # Save results
        self.save_results(output_path)
        
        duration = time.time() - start_time
        
        summary = {
            "total_records_processed": total_records,
            "duration_seconds": builtins.round(duration, 2),
            "records_per_second": builtins.round(total_records / duration, 2),
            "analyses_completed": len(self.results),
            "correlation": correlation,
            "anomaly_count": anomalies.count()
        }
        
        logger.info("Full analysis complete", **summary)
        return summary
