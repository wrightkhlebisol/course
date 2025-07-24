"""
Query Pattern Analyzer for Storage Format Optimization
"""
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json

class AccessPatternAnalyzer:
    def __init__(self):
        self.patterns = defaultdict(dict)
        self.field_statistics = defaultdict(lambda: defaultdict(int))
        self.query_performance = defaultdict(list)
        self.format_recommendations = {}
    
    def record_query(self, partition_key: str, query: Dict[str, Any], 
                    execution_time: float, result_count: int):
        """Record query execution for pattern analysis"""
        timestamp = datetime.now()
        
        query_record = {
            'timestamp': timestamp.isoformat(),
            'query': query,
            'execution_time': execution_time,
            'result_count': result_count,
            'query_type': self._classify_query_type(query)
        }
        
        # Store query performance
        if partition_key not in self.query_performance:
            self.query_performance[partition_key] = []
        
        self.query_performance[partition_key].append(query_record)
        
        # Update field access statistics
        self._update_field_stats(partition_key, query)
        
        # Clean old records (keep last 24 hours)
        self._cleanup_old_records(partition_key)
    
    def _classify_query_type(self, query: Dict[str, Any]) -> str:
        """Classify query type for optimization decisions"""
        columns = query.get('columns', [])
        has_aggregation = 'aggregation' in query
        has_full_scan = not query.get('filters', {})
        
        if has_aggregation and len(columns) <= 3:
            return 'analytical'
        elif not columns or len(columns) > 10:
            return 'full_record'
        elif has_full_scan:
            return 'scan_heavy'
        else:
            return 'mixed'
    
    def _update_field_stats(self, partition_key: str, query: Dict[str, Any]):
        """Update field access frequency statistics"""
        columns = query.get('columns', [])
        for column in columns:
            self.field_statistics[partition_key][column] += 1
    
    def _cleanup_old_records(self, partition_key: str):
        """Remove records older than 24 hours"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        if partition_key in self.query_performance:
            self.query_performance[partition_key] = [
                record for record in self.query_performance[partition_key]
                if datetime.fromisoformat(record['timestamp']) > cutoff_time
            ]
    
    def get_recommendations(self, partition_key: str) -> Dict[str, Any]:
        """Get storage format recommendations based on patterns"""
        if partition_key not in self.query_performance:
            return {'recommended_format': 'row_oriented', 'confidence': 'low'}
        
        records = self.query_performance[partition_key]
        
        if not records:
            return {'recommended_format': 'row_oriented', 'confidence': 'low'}
        
        # Analyze query types
        query_type_counts = defaultdict(int)
        total_queries = len(records)
        avg_execution_time = sum(r['execution_time'] for r in records) / total_queries
        
        for record in records:
            query_type_counts[record['query_type']] += 1
        
        # Calculate ratios
        analytical_ratio = query_type_counts['analytical'] / total_queries
        full_record_ratio = query_type_counts['full_record'] / total_queries
        
        # Make recommendation
        if analytical_ratio > 0.6:
            recommendation = 'columnar'
            confidence = 'high' if analytical_ratio > 0.8 else 'medium'
        elif full_record_ratio > 0.6:
            recommendation = 'row_oriented'
            confidence = 'high' if full_record_ratio > 0.8 else 'medium'
        else:
            recommendation = 'hybrid'
            confidence = 'medium'
        
        return {
            'recommended_format': recommendation,
            'confidence': confidence,
            'analytical_ratio': analytical_ratio,
            'full_record_ratio': full_record_ratio,
            'avg_execution_time': avg_execution_time,
            'total_queries': total_queries,
            'field_access_frequency': dict(self.field_statistics[partition_key])
        }
    
    def get_optimization_insights(self) -> Dict[str, Any]:
        """Get insights for storage optimization"""
        insights = {
            'partitions_analyzed': len(self.query_performance),
            'total_queries': sum(len(records) for records in self.query_performance.values()),
            'recommendations': {}
        }
        
        for partition_key in self.query_performance:
            insights['recommendations'][partition_key] = self.get_recommendations(partition_key)
        
        return insights
