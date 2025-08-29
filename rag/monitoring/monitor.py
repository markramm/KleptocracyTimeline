"""
Research-Quality Performance Monitoring

Track and analyze RAG system performance with focus on research metrics.
"""

import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
import threading
import logging


logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""
    query_id: str
    query_text: str
    timestamp: datetime
    response_time: float
    results_count: int
    recall_score: float = 0.0
    precision_score: float = 0.0
    consistency_hash: str = ""
    completeness_score: float = 0.0
    cache_hit: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """Aggregated system metrics."""
    total_queries: int = 0
    avg_response_time: float = 0.0
    avg_recall_rate: float = 0.0
    avg_precision_rate: float = 0.0
    consistency_rate: float = 0.0
    completeness_rate: float = 0.0
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0
    queries_per_minute: float = 0.0


class RAGResearchMonitor:
    """
    Research-quality monitoring system for RAG operations.
    Focuses on recall, consistency, and completeness over speed.
    """
    
    def __init__(self, window_size_minutes: int = 60, 
                 persist_metrics: bool = True,
                 metrics_file: str = "rag_metrics.json"):
        """
        Initialize monitor.
        
        Args:
            window_size_minutes: Rolling window for metrics
            persist_metrics: Whether to persist metrics to disk
            metrics_file: File to persist metrics
        """
        self.window_size = timedelta(minutes=window_size_minutes)
        self.persist_metrics = persist_metrics
        self.metrics_file = metrics_file
        
        # Metrics storage
        self.metrics = defaultdict(lambda: deque(maxlen=10000))
        self.query_history = deque(maxlen=10000)
        self.consistency_cache = {}  # For tracking result consistency
        
        # Thresholds for research quality
        self.thresholds = {
            'response_time': 5.0,        # 5s acceptable for research
            'recall_rate': 0.95,         # 95% recall minimum
            'precision_rate': 0.90,      # 90% precision target
            'consistency_score': 0.99,   # 99% result consistency
            'completeness_rate': 0.98,   # 98% completeness
            'cache_hit_rate': 0.50,      # 50% cache hit target
            'error_rate': 0.01           # 1% error rate maximum
        }
        
        # Alert callbacks
        self.alert_callbacks = []
        
        # Statistics tracking
        self.current_stats = SystemMetrics()
        self._stats_lock = threading.Lock()
        
        # Load existing metrics if available
        if persist_metrics:
            self._load_metrics()
    
    def record_query(self, 
                    query_text: str,
                    response_time: float,
                    results: List[Any],
                    recall_score: float = 0.0,
                    precision_score: float = 0.0,
                    completeness_score: float = 0.0,
                    cache_hit: bool = False,
                    error: Optional[str] = None,
                    metadata: Dict[str, Any] = None) -> QueryMetrics:
        """
        Record metrics for a query execution.
        
        Args:
            query_text: The query that was executed
            response_time: Time taken to execute query
            results: List of results returned
            recall_score: Recall score if available
            precision_score: Precision score if available
            completeness_score: Completeness score if available
            cache_hit: Whether result was from cache
            error: Error message if query failed
            metadata: Additional metadata
            
        Returns:
            QueryMetrics object
        """
        # Generate query ID and consistency hash
        query_id = self._generate_query_id(query_text)
        consistency_hash = self._calculate_consistency_hash(results)
        
        # Create metrics object
        metrics = QueryMetrics(
            query_id=query_id,
            query_text=query_text,
            timestamp=datetime.now(),
            response_time=response_time,
            results_count=len(results) if results else 0,
            recall_score=recall_score,
            precision_score=precision_score,
            consistency_hash=consistency_hash,
            completeness_score=completeness_score,
            cache_hit=cache_hit,
            error=error,
            metadata=metadata or {}
        )
        
        # Store metrics
        with self._stats_lock:
            self.query_history.append(metrics)
            self.metrics['response_times'].append(response_time)
            self.metrics['recall_scores'].append(recall_score)
            self.metrics['precision_scores'].append(precision_score)
            self.metrics['completeness_scores'].append(completeness_score)
            
            # Track consistency
            if query_id in self.consistency_cache:
                prev_hash = self.consistency_cache[query_id]
                if prev_hash != consistency_hash:
                    self.metrics['consistency_violations'].append({
                        'query_id': query_id,
                        'timestamp': datetime.now(),
                        'previous_hash': prev_hash,
                        'current_hash': consistency_hash
                    })
            self.consistency_cache[query_id] = consistency_hash
        
        # Update statistics
        self._update_statistics()
        
        # Check for alerts
        self._check_alerts(metrics)
        
        # Persist if enabled
        if self.persist_metrics:
            self._persist_metrics()
        
        return metrics
    
    def get_research_quality_stats(self) -> Dict[str, Any]:
        """
        Get research-focused quality metrics.
        
        Returns:
            Dictionary with research quality statistics
        """
        with self._stats_lock:
            recent_queries = self._get_recent_queries()
            
            if not recent_queries:
                return {
                    'status': 'no_data',
                    'message': 'No recent queries to analyze'
                }
            
            # Calculate research metrics
            recall_scores = [q.recall_score for q in recent_queries if q.recall_score > 0]
            precision_scores = [q.precision_score for q in recent_queries if q.precision_score > 0]
            completeness_scores = [q.completeness_score for q in recent_queries if q.completeness_score > 0]
            
            # Calculate consistency
            consistency_violations = len([v for v in self.metrics['consistency_violations']
                                        if v['timestamp'] > datetime.now() - self.window_size])
            total_repeat_queries = len([q for q in recent_queries 
                                       if self._count_query_occurrences(q.query_id) > 1])
            consistency_rate = 1.0 - (consistency_violations / total_repeat_queries) if total_repeat_queries > 0 else 1.0
            
            stats = {
                'window_size_minutes': self.window_size.total_seconds() / 60,
                'total_queries': len(recent_queries),
                'research_metrics': {
                    'avg_recall': sum(recall_scores) / len(recall_scores) if recall_scores else 0.0,
                    'min_recall': min(recall_scores) if recall_scores else 0.0,
                    'avg_precision': sum(precision_scores) / len(precision_scores) if precision_scores else 0.0,
                    'avg_completeness': sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0,
                    'consistency_rate': consistency_rate,
                    'consistency_violations': consistency_violations
                },
                'performance_metrics': {
                    'avg_response_time': self.current_stats.avg_response_time,
                    'p95_response_time': self._calculate_percentile(
                        [q.response_time for q in recent_queries], 95
                    ),
                    'queries_per_minute': self.current_stats.queries_per_minute,
                    'cache_hit_rate': self.current_stats.cache_hit_rate
                },
                'quality_assessment': self._assess_quality(recall_scores, consistency_rate, completeness_scores),
                'timestamp': datetime.now().isoformat()
            }
            
            return stats
    
    def check_research_quality_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for research quality issues.
        
        Returns:
            List of active alerts
        """
        alerts = []
        stats = self.get_research_quality_stats()
        
        if stats.get('status') == 'no_data':
            return alerts
        
        research_metrics = stats.get('research_metrics', {})
        
        # Check recall (critical for research)
        if research_metrics.get('avg_recall', 0) < self.thresholds['recall_rate']:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'low_recall',
                'message': f"Recall rate {research_metrics['avg_recall']:.2%} below threshold {self.thresholds['recall_rate']:.2%}",
                'value': research_metrics['avg_recall'],
                'threshold': self.thresholds['recall_rate']
            })
        
        # Check consistency (critical for reproducibility)
        if research_metrics.get('consistency_rate', 0) < self.thresholds['consistency_score']:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'inconsistent_results',
                'message': f"Consistency rate {research_metrics['consistency_rate']:.2%} below threshold",
                'value': research_metrics['consistency_rate'],
                'threshold': self.thresholds['consistency_score'],
                'violations': research_metrics.get('consistency_violations', 0)
            })
        
        # Check completeness
        if research_metrics.get('avg_completeness', 0) < self.thresholds['completeness_rate']:
            alerts.append({
                'level': 'WARNING',
                'type': 'incomplete_coverage',
                'message': f"Completeness {research_metrics['avg_completeness']:.2%} below target",
                'value': research_metrics['avg_completeness'],
                'threshold': self.thresholds['completeness_rate']
            })
        
        # Check precision
        if research_metrics.get('avg_precision', 0) < self.thresholds['precision_rate']:
            alerts.append({
                'level': 'WARNING',
                'type': 'low_precision',
                'message': f"Precision {research_metrics['avg_precision']:.2%} below target",
                'value': research_metrics['avg_precision'],
                'threshold': self.thresholds['precision_rate']
            })
        
        # Check error rate
        if self.current_stats.error_rate > self.thresholds['error_rate']:
            alerts.append({
                'level': 'ERROR',
                'type': 'high_error_rate',
                'message': f"Error rate {self.current_stats.error_rate:.2%} exceeds threshold",
                'value': self.current_stats.error_rate,
                'threshold': self.thresholds['error_rate']
            })
        
        return alerts
    
    def track_result_reproducibility(self, query_text: str, results: List[Any]) -> float:
        """
        Track whether identical queries return identical results.
        
        Args:
            query_text: Query text
            results: Query results
            
        Returns:
            Reproducibility score (1.0 = perfect reproducibility)
        """
        query_id = self._generate_query_id(query_text)
        current_hash = self._calculate_consistency_hash(results)
        
        with self._stats_lock:
            if query_id not in self.consistency_cache:
                self.consistency_cache[query_id] = current_hash
                return 1.0
            
            previous_hash = self.consistency_cache[query_id]
            if previous_hash == current_hash:
                return 1.0
            else:
                # Track violation
                self.metrics['consistency_violations'].append({
                    'query_id': query_id,
                    'timestamp': datetime.now(),
                    'query_text': query_text
                })
                return 0.0
    
    def analyze_coverage_gaps(self) -> Dict[str, Any]:
        """
        Identify potential gaps in event coverage.
        
        Returns:
            Analysis of coverage gaps
        """
        with self._stats_lock:
            recent_queries = self._get_recent_queries()
            
            # Analyze query patterns
            query_topics = defaultdict(int)
            low_result_queries = []
            failed_queries = []
            
            for query in recent_queries:
                # Track topics (simplified - could use NLP)
                for word in query.query_text.lower().split():
                    if len(word) > 4:  # Simple filtering
                        query_topics[word] += 1
                
                # Track queries with few results
                if query.results_count < 3:
                    low_result_queries.append({
                        'query': query.query_text,
                        'results': query.results_count,
                        'timestamp': query.timestamp
                    })
                
                # Track failed queries
                if query.error:
                    failed_queries.append({
                        'query': query.query_text,
                        'error': query.error,
                        'timestamp': query.timestamp
                    })
            
            # Identify potential gaps
            gaps = {
                'underserved_topics': [topic for topic, count in query_topics.items() 
                                      if count == 1],  # Topics queried only once
                'low_result_queries': low_result_queries[:10],
                'failed_queries': failed_queries[:10],
                'coverage_score': 1.0 - (len(low_result_queries) / len(recent_queries))
                                 if recent_queries else 0.0,
                'recommendations': []
            }
            
            # Generate recommendations
            if len(low_result_queries) > len(recent_queries) * 0.2:
                gaps['recommendations'].append(
                    "High proportion of queries returning few results - consider expanding index"
                )
            
            if failed_queries:
                gaps['recommendations'].append(
                    f"{len(failed_queries)} queries failed - investigate error patterns"
                )
            
            return gaps
    
    def register_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Register callback for alerts.
        
        Args:
            callback: Function to call when alert triggered
        """
        self.alert_callbacks.append(callback)
    
    def set_threshold(self, metric: str, value: float):
        """
        Update threshold for a metric.
        
        Args:
            metric: Metric name
            value: New threshold value
        """
        if metric in self.thresholds:
            self.thresholds[metric] = value
            logger.info(f"Updated threshold for {metric} to {value}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary.
        
        Returns:
            Complete metrics summary
        """
        return {
            'current_stats': asdict(self.current_stats),
            'research_quality': self.get_research_quality_stats(),
            'alerts': self.check_research_quality_alerts(),
            'coverage_gaps': self.analyze_coverage_gaps(),
            'thresholds': self.thresholds.copy()
        }
    
    def _generate_query_id(self, query_text: str) -> str:
        """Generate unique ID for query."""
        return hashlib.md5(query_text.encode()).hexdigest()
    
    def _calculate_consistency_hash(self, results: List[Any]) -> str:
        """Calculate hash for result consistency checking."""
        if not results:
            return ""
        
        # Extract IDs or create string representation
        result_ids = []
        for r in results:
            if hasattr(r, 'id'):
                result_ids.append(r.id)
            elif isinstance(r, dict) and 'id' in r:
                result_ids.append(r['id'])
            else:
                result_ids.append(str(r))
        
        # Sort for consistency
        result_ids.sort()
        return hashlib.sha256(json.dumps(result_ids).encode()).hexdigest()
    
    def _get_recent_queries(self) -> List[QueryMetrics]:
        """Get queries within the time window."""
        cutoff = datetime.now() - self.window_size
        return [q for q in self.query_history if q.timestamp > cutoff]
    
    def _count_query_occurrences(self, query_id: str) -> int:
        """Count how many times a query has been executed."""
        return sum(1 for q in self.query_history if q.query_id == query_id)
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _assess_quality(self, recall_scores: List[float], 
                       consistency_rate: float,
                       completeness_scores: List[float]) -> str:
        """Assess overall research quality."""
        if not recall_scores:
            return "INSUFFICIENT_DATA"
        
        avg_recall = sum(recall_scores) / len(recall_scores)
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        
        if (avg_recall >= self.thresholds['recall_rate'] and
            consistency_rate >= self.thresholds['consistency_score'] and
            avg_completeness >= self.thresholds['completeness_rate']):
            return "EXCELLENT"
        elif (avg_recall >= self.thresholds['recall_rate'] * 0.95 and
              consistency_rate >= self.thresholds['consistency_score'] * 0.95):
            return "GOOD"
        elif (avg_recall >= self.thresholds['recall_rate'] * 0.9):
            return "ACCEPTABLE"
        else:
            return "NEEDS_IMPROVEMENT"
    
    def _update_statistics(self):
        """Update aggregated statistics."""
        recent_queries = self._get_recent_queries()
        
        if not recent_queries:
            return
        
        # Calculate aggregates
        self.current_stats.total_queries = len(recent_queries)
        self.current_stats.avg_response_time = sum(q.response_time for q in recent_queries) / len(recent_queries)
        
        recall_scores = [q.recall_score for q in recent_queries if q.recall_score > 0]
        self.current_stats.avg_recall_rate = sum(recall_scores) / len(recall_scores) if recall_scores else 0
        
        precision_scores = [q.precision_score for q in recent_queries if q.precision_score > 0]
        self.current_stats.avg_precision_rate = sum(precision_scores) / len(precision_scores) if precision_scores else 0
        
        completeness_scores = [q.completeness_score for q in recent_queries if q.completeness_score > 0]
        self.current_stats.completeness_rate = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        
        cache_hits = sum(1 for q in recent_queries if q.cache_hit)
        self.current_stats.cache_hit_rate = cache_hits / len(recent_queries)
        
        errors = sum(1 for q in recent_queries if q.error)
        self.current_stats.error_rate = errors / len(recent_queries)
        
        # Calculate QPM
        time_span = (recent_queries[-1].timestamp - recent_queries[0].timestamp).total_seconds() / 60
        self.current_stats.queries_per_minute = len(recent_queries) / time_span if time_span > 0 else 0
    
    def _check_alerts(self, metrics: QueryMetrics):
        """Check if metrics trigger any alerts."""
        alerts = []
        
        # Check response time
        if metrics.response_time > self.thresholds['response_time']:
            alerts.append({
                'type': 'slow_query',
                'query_id': metrics.query_id,
                'response_time': metrics.response_time,
                'threshold': self.thresholds['response_time']
            })
        
        # Check recall
        if metrics.recall_score > 0 and metrics.recall_score < self.thresholds['recall_rate']:
            alerts.append({
                'type': 'low_recall',
                'query_id': metrics.query_id,
                'recall_score': metrics.recall_score,
                'threshold': self.thresholds['recall_rate']
            })
        
        # Trigger callbacks
        for alert in alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
    
    def _persist_metrics(self):
        """Save metrics to disk."""
        try:
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'current_stats': asdict(self.current_stats),
                'recent_queries': [
                    {
                        'query_id': q.query_id,
                        'timestamp': q.timestamp.isoformat(),
                        'response_time': q.response_time,
                        'recall_score': q.recall_score,
                        'precision_score': q.precision_score,
                        'completeness_score': q.completeness_score
                    }
                    for q in self._get_recent_queries()[-100:]  # Last 100 queries
                ]
            }
            
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error persisting metrics: {e}")
    
    def _load_metrics(self):
        """Load metrics from disk."""
        try:
            if Path(self.metrics_file).exists():
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    # Could restore historical data here
                    logger.info(f"Loaded metrics from {self.metrics_file}")
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")


class RAGQueryTracker:
    """
    Context manager for tracking individual query performance.
    
    Usage:
        with RAGQueryTracker(monitor, query_text) as tracker:
            results = rag.search(query_text)
            tracker.set_results(results)
    """
    
    def __init__(self, monitor: RAGResearchMonitor, query_text: str, **kwargs):
        """
        Initialize tracker.
        
        Args:
            monitor: Monitor instance
            query_text: Query being tracked
            **kwargs: Additional metadata
        """
        self.monitor = monitor
        self.query_text = query_text
        self.metadata = kwargs
        self.start_time = None
        self.results = None
        self.error = None
    
    def __enter__(self):
        """Start tracking."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete tracking and record metrics."""
        response_time = time.time() - self.start_time
        
        # Handle errors
        if exc_type is not None:
            self.error = str(exc_val)
        
        # Record metrics
        self.monitor.record_query(
            query_text=self.query_text,
            response_time=response_time,
            results=self.results or [],
            cache_hit=self.metadata.get('cache_hit', False),
            error=self.error,
            metadata=self.metadata
        )
        
        # Don't suppress exceptions
        return False
    
    def set_results(self, results: List[Any]):
        """Set query results."""
        self.results = results
    
    def set_scores(self, recall: float = 0, precision: float = 0, completeness: float = 0):
        """Set quality scores."""
        self.metadata['recall_score'] = recall
        self.metadata['precision_score'] = precision
        self.metadata['completeness_score'] = completeness


if __name__ == '__main__':
    # Example usage
    monitor = RAGResearchMonitor()
    
    # Set research-focused thresholds
    monitor.set_threshold('recall_rate', 0.95)
    monitor.set_threshold('consistency_score', 0.99)
    
    # Register alert handler
    def handle_alert(alert):
        print(f"ALERT: {alert}")
    
    monitor.register_alert_callback(handle_alert)
    
    # Track a query
    with RAGQueryTracker(monitor, "test query") as tracker:
        # Simulate search
        time.sleep(0.1)
        tracker.set_results([{'id': '1'}, {'id': '2'}])
        tracker.set_scores(recall=0.92, precision=0.88, completeness=0.95)
    
    # Get statistics
    stats = monitor.get_research_quality_stats()
    print(json.dumps(stats, indent=2))
    
    # Check for alerts
    alerts = monitor.check_research_quality_alerts()
    for alert in alerts:
        print(f"Alert: {alert['level']} - {alert['message']}")