"""
Metrics Exporters for RAG Monitoring

Export metrics to various formats and systems.
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from prometheus_client import Gauge, Counter, Histogram, CollectorRegistry, generate_latest


class MetricsExporter:
    """
    Base metrics exporter class.
    """
    
    def __init__(self, output_dir: str = "metrics_export"):
        """
        Initialize exporter.
        
        Args:
            output_dir: Directory for exported files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_json(self, metrics: Dict[str, Any], filename: str = None) -> Path:
        """
        Export metrics to JSON.
        
        Args:
            metrics: Metrics dictionary
            filename: Optional filename
            
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        return output_path
    
    def export_csv(self, metrics: List[Dict[str, Any]], filename: str = None) -> Path:
        """
        Export metrics to CSV.
        
        Args:
            metrics: List of metric records
            filename: Optional filename
            
        Returns:
            Path to exported file
        """
        if not metrics:
            return None
        
        if filename is None:
            filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        output_path = self.output_dir / filename
        
        # Get all unique keys
        keys = set()
        for m in metrics:
            keys.update(m.keys())
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            writer.writerows(metrics)
        
        return output_path
    
    def export_markdown(self, metrics: Dict[str, Any], filename: str = None) -> Path:
        """
        Export metrics report to Markdown.
        
        Args:
            metrics: Metrics dictionary
            filename: Optional filename
            
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        output_path = self.output_dir / filename
        
        report = self._generate_markdown_report(metrics)
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        return output_path
    
    def _generate_markdown_report(self, metrics: Dict[str, Any]) -> str:
        """Generate Markdown report from metrics."""
        report = f"""# RAG Metrics Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Research Quality Metrics

"""
        
        if 'research_quality' in metrics:
            rq = metrics['research_quality']
            rm = rq.get('research_metrics', {})
            
            report += f"""
- **Recall Rate**: {rm.get('avg_recall', 0):.2%}
- **Precision Rate**: {rm.get('avg_precision', 0):.2%}
- **Consistency Rate**: {rm.get('consistency_rate', 0):.2%}
- **Completeness Rate**: {rm.get('avg_completeness', 0):.2%}
- **Quality Assessment**: {rq.get('quality_assessment', 'N/A')}

## Performance Metrics

"""
            pm = rq.get('performance_metrics', {})
            report += f"""
- **Average Response Time**: {pm.get('avg_response_time', 0):.3f}s
- **P95 Response Time**: {pm.get('p95_response_time', 0):.3f}s
- **Queries Per Minute**: {pm.get('queries_per_minute', 0):.1f}
- **Cache Hit Rate**: {pm.get('cache_hit_rate', 0):.2%}
"""
        
        if 'alerts' in metrics and metrics['alerts']:
            report += f"""
## Active Alerts

| Level | Type | Message |
|-------|------|---------|
"""
            for alert in metrics['alerts']:
                report += f"| {alert['level']} | {alert['type']} | {alert['message']} |\n"
        
        return report


class PrometheusExporter:
    """
    Export metrics to Prometheus format.
    """
    
    def __init__(self, registry: CollectorRegistry = None):
        """
        Initialize Prometheus exporter.
        
        Args:
            registry: Prometheus registry (creates new if None)
        """
        self.registry = registry or CollectorRegistry()
        
        # Define metrics
        self.metrics = {
            # Gauges for current values
            'recall_rate': Gauge('rag_recall_rate', 'Current recall rate', registry=self.registry),
            'precision_rate': Gauge('rag_precision_rate', 'Current precision rate', registry=self.registry),
            'consistency_rate': Gauge('rag_consistency_rate', 'Result consistency rate', registry=self.registry),
            'completeness_rate': Gauge('rag_completeness_rate', 'Coverage completeness rate', registry=self.registry),
            'avg_response_time': Gauge('rag_avg_response_time_seconds', 'Average response time', registry=self.registry),
            'queries_per_minute': Gauge('rag_queries_per_minute', 'Queries per minute', registry=self.registry),
            'cache_hit_rate': Gauge('rag_cache_hit_rate', 'Cache hit rate', registry=self.registry),
            
            # Counters for cumulative values
            'total_queries': Counter('rag_queries_total', 'Total queries processed', registry=self.registry),
            'total_errors': Counter('rag_errors_total', 'Total errors', registry=self.registry),
            'consistency_violations': Counter('rag_consistency_violations_total', 'Total consistency violations', registry=self.registry),
            
            # Histograms for distributions
            'response_time_histogram': Histogram('rag_response_time_seconds', 
                                                'Response time distribution',
                                                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
                                                registry=self.registry),
            'results_count_histogram': Histogram('rag_results_count',
                                                'Number of results per query',
                                                buckets=[0, 1, 5, 10, 20, 50, 100],
                                                registry=self.registry)
        }
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """
        Update Prometheus metrics from monitoring data.
        
        Args:
            metrics: Current metrics from monitor
        """
        # Update research quality gauges
        if 'research_quality' in metrics:
            rq = metrics['research_quality']
            rm = rq.get('research_metrics', {})
            
            if 'avg_recall' in rm:
                self.metrics['recall_rate'].set(rm['avg_recall'])
            if 'avg_precision' in rm:
                self.metrics['precision_rate'].set(rm['avg_precision'])
            if 'consistency_rate' in rm:
                self.metrics['consistency_rate'].set(rm['consistency_rate'])
            if 'avg_completeness' in rm:
                self.metrics['completeness_rate'].set(rm['avg_completeness'])
            
            # Update performance gauges
            pm = rq.get('performance_metrics', {})
            if 'avg_response_time' in pm:
                self.metrics['avg_response_time'].set(pm['avg_response_time'])
            if 'queries_per_minute' in pm:
                self.metrics['queries_per_minute'].set(pm['queries_per_minute'])
            if 'cache_hit_rate' in pm:
                self.metrics['cache_hit_rate'].set(pm['cache_hit_rate'])
        
        # Update counters from current stats
        if 'current_stats' in metrics:
            stats = metrics['current_stats']
            if 'total_queries' in stats:
                # Counters can only increase, so we track the delta
                # In production, you'd need to store the previous value
                pass
    
    def record_query(self, response_time: float, results_count: int, 
                    error: bool = False):
        """
        Record individual query metrics.
        
        Args:
            response_time: Query response time
            results_count: Number of results returned
            error: Whether query resulted in error
        """
        self.metrics['total_queries'].inc()
        self.metrics['response_time_histogram'].observe(response_time)
        self.metrics['results_count_histogram'].observe(results_count)
        
        if error:
            self.metrics['total_errors'].inc()
    
    def record_consistency_violation(self):
        """Record a consistency violation."""
        self.metrics['consistency_violations'].inc()
    
    def get_metrics(self) -> bytes:
        """
        Get metrics in Prometheus format.
        
        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest(self.registry)
    
    def write_metrics(self, filepath: str):
        """
        Write metrics to file.
        
        Args:
            filepath: Path to write metrics
        """
        with open(filepath, 'wb') as f:
            f.write(self.get_metrics())


class TimeSeriesExporter:
    """
    Export metrics as time series for analysis.
    """
    
    def __init__(self, window_minutes: int = 60):
        """
        Initialize time series exporter.
        
        Args:
            window_minutes: Time window for aggregation
        """
        self.window_minutes = window_minutes
        self.time_series = []
    
    def add_datapoint(self, timestamp: datetime, metrics: Dict[str, Any]):
        """
        Add datapoint to time series.
        
        Args:
            timestamp: Timestamp for datapoint
            metrics: Metrics at this timestamp
        """
        datapoint = {
            'timestamp': timestamp.isoformat(),
            **self._flatten_metrics(metrics)
        }
        self.time_series.append(datapoint)
        
        # Limit size
        if len(self.time_series) > 10000:
            self.time_series = self.time_series[-5000:]
    
    def _flatten_metrics(self, metrics: Dict[str, Any], prefix: str = '') -> Dict[str, Any]:
        """Flatten nested metrics dictionary."""
        result = {}
        
        for key, value in metrics.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten_metrics(value, f"{full_key}."))
            elif isinstance(value, (int, float, str, bool)):
                result[full_key] = value
        
        return result
    
    def export_to_csv(self, filepath: str):
        """
        Export time series to CSV.
        
        Args:
            filepath: Path to CSV file
        """
        if not self.time_series:
            return
        
        keys = set()
        for point in self.time_series:
            keys.update(point.keys())
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            writer.writerows(self.time_series)
    
    def get_aggregates(self, metric_name: str) -> Dict[str, float]:
        """
        Get aggregated statistics for a metric.
        
        Args:
            metric_name: Name of metric to aggregate
            
        Returns:
            Statistics dictionary
        """
        values = [p.get(metric_name) for p in self.time_series 
                 if metric_name in p and p[metric_name] is not None]
        
        if not values:
            return {}
        
        import numpy as np
        
        return {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'median': np.median(values),
            'p95': np.percentile(values, 95),
            'p99': np.percentile(values, 99)
        }


if __name__ == '__main__':
    # Example usage
    exporter = MetricsExporter()
    prometheus = PrometheusExporter()
    
    # Sample metrics
    sample_metrics = {
        'research_quality': {
            'research_metrics': {
                'avg_recall': 0.92,
                'avg_precision': 0.88,
                'consistency_rate': 0.98,
                'avg_completeness': 0.95
            },
            'performance_metrics': {
                'avg_response_time': 0.45,
                'queries_per_minute': 12.5,
                'cache_hit_rate': 0.65
            },
            'quality_assessment': 'GOOD'
        },
        'alerts': []
    }
    
    # Export to various formats
    json_path = exporter.export_json(sample_metrics)
    print(f"Exported JSON to: {json_path}")
    
    md_path = exporter.export_markdown(sample_metrics)
    print(f"Exported Markdown to: {md_path}")
    
    # Update Prometheus metrics
    prometheus.update_metrics(sample_metrics)
    prometheus.record_query(0.35, 15)
    
    # Get Prometheus format
    prom_metrics = prometheus.get_metrics()
    print(f"\nPrometheus metrics ({len(prom_metrics)} bytes)")