"""
Evaluation Report Generation

Generates comprehensive evaluation reports in multiple formats (JSON, Markdown, HTML).
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64


class EvaluationReportGenerator:
    """
    Generate research-grade evaluation reports for RAG system.
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory for saving reports
        """
        self.output_dir = Path(output_dir or 'evaluation_reports')
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_report(self, evaluation_results: Dict[str, Any],
                       format: str = 'all') -> Dict[str, Path]:
        """
        Generate evaluation report in specified format(s).
        
        Args:
            evaluation_results: Evaluation results dictionary
            format: Output format ('json', 'markdown', 'html', 'all')
            
        Returns:
            Dictionary mapping format to file path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_files = {}
        
        if format in ['json', 'all']:
            json_path = self._generate_json_report(evaluation_results, timestamp)
            output_files['json'] = json_path
        
        if format in ['markdown', 'all']:
            md_path = self._generate_markdown_report(evaluation_results, timestamp)
            output_files['markdown'] = md_path
        
        if format in ['html', 'all']:
            html_path = self._generate_html_report(evaluation_results, timestamp)
            output_files['html'] = html_path
        
        return output_files
    
    def _generate_json_report(self, results: Dict[str, Any], timestamp: str) -> Path:
        """Generate JSON report."""
        output_path = self.output_dir / f"evaluation_{timestamp}.json"
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return output_path
    
    def _generate_markdown_report(self, results: Dict[str, Any], timestamp: str) -> Path:
        """Generate detailed Markdown report."""
        output_path = self.output_dir / f"evaluation_{timestamp}.md"
        
        report = f"""# RAG System Evaluation Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**System**: Kleptocracy Timeline RAG  
**Evaluation Type**: Research-Grade Comprehensive  

---

## 📊 Executive Summary

{self._generate_executive_summary(results)}

---

## 🎯 Performance Metrics

### Retrieval Quality (Critical for Research)

{self._generate_retrieval_metrics_section(results)}

### Consistency & Reproducibility

{self._generate_consistency_section(results)}

### Completeness & Coverage

{self._generate_completeness_section(results)}

### Research Scenarios

{self._generate_research_scenarios_section(results)}

---

## 📈 Performance Trends

{self._generate_performance_trends_section(results)}

---

## 🔍 Detailed Query Analysis

{self._generate_query_analysis_section(results)}

---

## ⚠️ Issues & Recommendations

{self._generate_recommendations_section(results)}

---

## 📋 Test Configuration

{self._generate_configuration_section(results)}

---

## 🏆 Final Assessment

{self._generate_final_assessment(results)}

---

*Report generated automatically by RAG Evaluation Framework v1.0*
"""
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        return output_path
    
    def _generate_html_report(self, results: Dict[str, Any], timestamp: str) -> Path:
        """Generate HTML report with visualizations."""
        output_path = self.output_dir / f"evaluation_{timestamp}.html"
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG Evaluation Report - {timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .progress-bar {{
            background: #e0e0e0;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
        }}
        .progress-fill {{
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%;
            transition: width 0.3s;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        .status-good {{ background: #4caf50; color: white; }}
        .status-warning {{ background: #ff9800; color: white; }}
        .status-error {{ background: #f44336; color: white; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f5f5f5;
            font-weight: 600;
        }}
        .chart-container {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 RAG System Evaluation Report</h1>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Kleptocracy Timeline - Research-Grade Evaluation</p>
    </div>

    {self._generate_html_summary_cards(results)}
    
    {self._generate_html_metrics_section(results)}
    
    {self._generate_html_query_table(results)}
    
    {self._generate_html_recommendations(results)}

    <div class="metric-card">
        <h2>📋 Evaluation Configuration</h2>
        <pre>{json.dumps(results.get('evaluation_config', {}), indent=2)}</pre>
    </div>
</body>
</html>"""
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        return output_path
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> str:
        """Generate executive summary section."""
        metrics = results.get('aggregate_metrics', {})
        consistency = results.get('consistency_tests', {})
        completeness = results.get('completeness_tests', {})
        
        grade = self._calculate_grade(results)
        
        summary = f"""
### Overall Grade: **{grade}**

The RAG system has been evaluated across multiple dimensions critical for research quality:

- **Retrieval Performance**: The system achieves {metrics.get('avg_recall@10', 0):.1%} recall@10 and {metrics.get('avg_precision@5', 0):.1%} precision@5
- **Consistency**: {consistency.get('overall_consistency', 0):.1%} result consistency across multiple runs
- **Completeness**: {completeness.get('average_completeness', 0):.1%} coverage completeness for comprehensive queries
- **Response Time**: Average query time of {metrics.get('avg_search_time', 0):.2f} seconds

"""
        
        # Add status indicators
        if metrics.get('avg_recall@10', 0) >= 0.95:
            summary += "✅ **Recall Target Met**: System successfully finds >95% of relevant events\n"
        else:
            summary += "⚠️ **Recall Below Target**: System missing relevant events (target: >95%)\n"
        
        if consistency.get('overall_consistency', 0) >= 0.99:
            summary += "✅ **Consistency Excellent**: Results are highly reproducible\n"
        else:
            summary += "⚠️ **Consistency Issues**: Results vary between runs (target: >99%)\n"
        
        return summary
    
    def _generate_retrieval_metrics_section(self, results: Dict[str, Any]) -> str:
        """Generate retrieval metrics section."""
        metrics = results.get('aggregate_metrics', {})
        
        section = """
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
"""
        
        # Define targets and check status
        metric_targets = [
            ('Precision@5', 'avg_precision@5', 0.90),
            ('Recall@10', 'avg_recall@10', 0.95),
            ('F1@10', 'avg_f1@10', 0.85),
            ('NDCG@10', 'avg_ndcg@10', 0.80),
            ('MRR', 'avg_mrr', 0.75)
        ]
        
        for name, key, target in metric_targets:
            value = metrics.get(key, 0)
            status = "✅" if value >= target else "⚠️"
            section += f"| {name} | {value:.3f} | >{target:.2f} | {status} |\n"
        
        return section
    
    def _generate_consistency_section(self, results: Dict[str, Any]) -> str:
        """Generate consistency section."""
        consistency = results.get('consistency_tests', {})
        
        return f"""
Research requires reproducible results. The system was tested for consistency by running identical queries multiple times:

- **Overall Consistency Score**: {consistency.get('overall_consistency', 0):.3f} (Target: >0.99)
- **Perfect Match Rate**: {consistency.get('perfect_consistency_rate', 0):.1%} of queries return identical results
- **Test Configuration**: {consistency.get('evaluation_config', {}).get('num_runs', 0)} runs per query

{"✅ Results are highly reproducible" if consistency.get('overall_consistency', 0) >= 0.99 else "⚠️ Consistency improvements needed for research reliability"}
"""
    
    def _generate_completeness_section(self, results: Dict[str, Any]) -> str:
        """Generate completeness section."""
        completeness = results.get('completeness_tests', {})
        
        return f"""
For comprehensive research, the system must find all relevant events:

- **Average Completeness**: {completeness.get('average_completeness', 0):.3f} (Target: >0.98)
- **Result Diversity**: {completeness.get('average_diversity', 0):.3f}
- **Queries Tested**: {completeness.get('evaluation_config', {}).get('num_queries', 0)}

Individual query completeness varies. Critical events coverage is essential for research integrity.
"""
    
    def _generate_research_scenarios_section(self, results: Dict[str, Any]) -> str:
        """Generate research scenarios section."""
        scenarios = results.get('research_scenarios', {})
        
        section = "### Timeline Analysis\n"
        timeline = scenarios.get('timeline_analysis', {})
        if timeline:
            section += f"""
- Query: "{timeline.get('query', 'N/A')}"
- Results: {timeline.get('num_results', 0)} events found
- Temporal Ordering: {"✅ Correct" if timeline.get('temporally_ordered') else "❌ Incorrect"}
- Date Range: {timeline.get('date_range', {}).get('start', 'N/A')} to {timeline.get('date_range', {}).get('end', 'N/A')}
"""
        
        section += "\n### Actor Network Analysis\n"
        network = scenarios.get('actor_network', {})
        if network:
            section += f"""
- Query: "{network.get('query', 'N/A')}"
- Unique Actors Found: {network.get('unique_actors', 0)}
- Connection Density: {network.get('connection_density', 0):.2f}
"""
        
        section += "\n### Pattern Detection\n"
        pattern = scenarios.get('pattern_detection', {})
        if pattern:
            section += f"""
- Pattern Type: {pattern.get('pattern_type', 'N/A')}
- Total Events: {pattern.get('total_events', 0)}
- Top Actors: {', '.join(pattern.get('top_actors', [])) if pattern.get('top_actors') else 'None'}
"""
        
        return section
    
    def _generate_performance_trends_section(self, results: Dict[str, Any]) -> str:
        """Generate performance trends section."""
        metrics = results.get('aggregate_metrics', {})
        
        section = f"""
### Query Performance Distribution

- **Mean Response Time**: {metrics.get('avg_search_time', 0):.3f}s
- **Target**: <5.0s for research workflows
- **Status**: {"✅ Acceptable" if metrics.get('avg_search_time', 0) < 5.0 else "⚠️ Optimization needed"}

### Metric Stability

Examining standard deviations to assess result consistency:

- Precision@10 StdDev: {metrics.get('std_precision@10', 0):.3f}
- Recall@10 StdDev: {metrics.get('std_recall@10', 0):.3f}

{"✅ Low variance indicates stable performance" if metrics.get('std_recall@10', 0) < 0.1 else "⚠️ High variance suggests inconsistent performance"}
"""
        
        return section
    
    def _generate_query_analysis_section(self, results: Dict[str, Any]) -> str:
        """Generate detailed query analysis."""
        queries = results.get('queries', {})
        
        if not queries:
            return "No detailed query results available."
        
        section = "Top performing queries:\n\n"
        
        # Sort by F1@10 score
        sorted_queries = sorted(
            queries.items(),
            key=lambda x: x[1].get('metrics', {}).get('f1@10', 0),
            reverse=True
        )[:5]
        
        for query_id, data in sorted_queries:
            metrics = data.get('metrics', {})
            section += f"""
#### {query_id}
- **Query**: {metrics.get('query_text', 'N/A')}
- **Precision@5**: {metrics.get('precision@5', 0):.3f}
- **Recall@10**: {metrics.get('recall@10', 0):.3f}
- **Response Time**: {metrics.get('search_time', 0):.3f}s
"""
        
        return section
    
    def _generate_recommendations_section(self, results: Dict[str, Any]) -> str:
        """Generate recommendations based on evaluation results."""
        metrics = results.get('aggregate_metrics', {})
        consistency = results.get('consistency_tests', {})
        completeness = results.get('completeness_tests', {})
        
        recommendations = []
        
        # Check recall
        if metrics.get('avg_recall@10', 0) < 0.95:
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Low Recall',
                'impact': 'Missing relevant events in research',
                'solution': 'Implement query expansion and hybrid retrieval'
            })
        
        # Check consistency
        if consistency.get('overall_consistency', 0) < 0.99:
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Inconsistent Results',
                'impact': 'Research reproducibility compromised',
                'solution': 'Implement deterministic ranking and result caching'
            })
        
        # Check completeness
        if completeness.get('average_completeness', 0) < 0.98:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': 'Incomplete Coverage',
                'impact': 'Potential gaps in analysis',
                'solution': 'Enhance semantic chunking and metadata indexing'
            })
        
        # Check performance
        if metrics.get('avg_search_time', 0) > 5.0:
            recommendations.append({
                'priority': 'LOW',
                'issue': 'Slow Response Time',
                'impact': 'Reduced research efficiency',
                'solution': 'Implement caching and query optimization'
            })
        
        if not recommendations:
            return "✅ System performing well. No critical issues identified."
        
        section = ""
        for rec in sorted(recommendations, key=lambda x: ['HIGH', 'MEDIUM', 'LOW'].index(x['priority'])):
            section += f"""
### {rec['priority']} Priority: {rec['issue']}
- **Impact**: {rec['impact']}
- **Recommended Solution**: {rec['solution']}
"""
        
        return section
    
    def _generate_configuration_section(self, results: Dict[str, Any]) -> str:
        """Generate configuration section."""
        return f"""
```json
{json.dumps(results.get('evaluation_config', {}), indent=2)}
```

### Test Coverage
- Total Queries Evaluated: {len(results.get('queries', {}))}
- Query Types: Entity retrieval, temporal, pattern analysis, research scenarios
- Metrics Calculated: Precision, Recall, F1, NDCG, MRR, Consistency, Completeness
"""
    
    def _generate_final_assessment(self, results: Dict[str, Any]) -> str:
        """Generate final assessment."""
        grade = self._calculate_grade(results)
        
        assessment = f"""
### System Grade: **{grade}**

"""
        
        if grade.startswith('A'):
            assessment += """
🏆 **Excellent Performance**: The system meets research-grade quality standards.
- Ready for production research use
- Suitable for academic and professional analysis
- High confidence in results
"""
        elif grade.startswith('B'):
            assessment += """
📊 **Good Performance**: The system performs well but has room for improvement.
- Suitable for most research tasks
- Some enhancements recommended for critical analysis
- Monitor performance regularly
"""
        else:
            assessment += """
⚠️ **Needs Improvement**: The system requires enhancements for research use.
- Address high-priority issues before production use
- Implement recommended optimizations
- Re-evaluate after improvements
"""
        
        return assessment
    
    def _calculate_grade(self, results: Dict[str, Any]) -> str:
        """Calculate overall grade."""
        metrics = results.get('aggregate_metrics', {})
        consistency = results.get('consistency_tests', {})
        completeness = results.get('completeness_tests', {})
        
        # Weighted scoring
        recall_score = metrics.get('avg_recall@10', 0) * 35
        precision_score = metrics.get('avg_precision@5', 0) * 25
        consistency_score = consistency.get('overall_consistency', 0) * 20
        completeness_score = completeness.get('average_completeness', 0) * 20
        
        total_score = recall_score + precision_score + consistency_score + completeness_score
        
        if total_score >= 95:
            return f"A+ ({total_score:.0f}/100)"
        elif total_score >= 90:
            return f"A ({total_score:.0f}/100)"
        elif total_score >= 85:
            return f"A- ({total_score:.0f}/100)"
        elif total_score >= 80:
            return f"B+ ({total_score:.0f}/100)"
        elif total_score >= 75:
            return f"B ({total_score:.0f}/100)"
        elif total_score >= 70:
            return f"B- ({total_score:.0f}/100)"
        else:
            return f"C ({total_score:.0f}/100)"
    
    def _generate_html_summary_cards(self, results: Dict[str, Any]) -> str:
        """Generate HTML summary cards."""
        metrics = results.get('aggregate_metrics', {})
        consistency = results.get('consistency_tests', {})
        
        return f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Overall Grade</div>
            <div class="metric-value">{self._calculate_grade(results)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Recall@10</div>
            <div class="metric-value">{metrics.get('avg_recall@10', 0):.1%}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {metrics.get('avg_recall@10', 0)*100}%"></div>
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Consistency</div>
            <div class="metric-value">{consistency.get('overall_consistency', 0):.1%}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {consistency.get('overall_consistency', 0)*100}%"></div>
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg Response Time</div>
            <div class="metric-value">{metrics.get('avg_search_time', 0):.2f}s</div>
        </div>
    </div>
"""
    
    def _generate_html_metrics_section(self, results: Dict[str, Any]) -> str:
        """Generate HTML metrics table."""
        metrics = results.get('aggregate_metrics', {})
        
        rows = ""
        for k in [5, 10, 20]:
            if f'avg_precision@{k}' in metrics:
                status_p = 'status-good' if metrics[f'avg_precision@{k}'] >= 0.8 else 'status-warning'
                status_r = 'status-good' if metrics[f'avg_recall@{k}'] >= 0.9 else 'status-warning'
                
                rows += f"""
        <tr>
            <td>@{k}</td>
            <td><span class="status-badge {status_p}">{metrics[f'avg_precision@{k}']:.3f}</span></td>
            <td><span class="status-badge {status_r}">{metrics[f'avg_recall@{k}']:.3f}</span></td>
            <td>{metrics.get(f'avg_f1@{k}', 0):.3f}</td>
            <td>{metrics.get(f'avg_ndcg@{k}', 0):.3f}</td>
        </tr>
"""
        
        return f"""
    <div class="metric-card">
        <h2>📊 Detailed Metrics</h2>
        <table>
            <thead>
                <tr>
                    <th>k</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1</th>
                    <th>NDCG</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
"""
    
    def _generate_html_query_table(self, results: Dict[str, Any]) -> str:
        """Generate HTML query results table."""
        queries = results.get('queries', {})
        
        if not queries:
            return ""
        
        rows = ""
        for query_id, data in list(queries.items())[:10]:
            metrics = data.get('metrics', {})
            rows += f"""
        <tr>
            <td>{query_id}</td>
            <td>{metrics.get('query_text', 'N/A')[:50]}...</td>
            <td>{metrics.get('precision@5', 0):.3f}</td>
            <td>{metrics.get('recall@10', 0):.3f}</td>
            <td>{metrics.get('search_time', 0):.3f}s</td>
        </tr>
"""
        
        return f"""
    <div class="metric-card">
        <h2>🔍 Query Performance</h2>
        <table>
            <thead>
                <tr>
                    <th>Query ID</th>
                    <th>Query Text</th>
                    <th>Precision@5</th>
                    <th>Recall@10</th>
                    <th>Time</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
"""
    
    def _generate_html_recommendations(self, results: Dict[str, Any]) -> str:
        """Generate HTML recommendations."""
        recommendations_text = self._generate_recommendations_section(results)
        
        if "No critical issues" in recommendations_text:
            badge = '<span class="status-badge status-good">All Systems Operational</span>'
        else:
            badge = '<span class="status-badge status-warning">Improvements Recommended</span>'
        
        return f"""
    <div class="metric-card">
        <h2>⚠️ Recommendations {badge}</h2>
        <div style="white-space: pre-line">{recommendations_text}</div>
    </div>
"""


if __name__ == '__main__':
    # Example usage
    generator = EvaluationReportGenerator()
    
    # Sample results
    sample_results = {
        'timestamp': datetime.now().isoformat(),
        'aggregate_metrics': {
            'avg_precision@5': 0.85,
            'avg_recall@10': 0.92,
            'avg_f1@10': 0.88,
            'avg_ndcg@10': 0.87,
            'avg_mrr': 0.83,
            'avg_search_time': 0.45
        },
        'consistency_tests': {
            'overall_consistency': 0.98,
            'perfect_consistency_rate': 0.85
        },
        'completeness_tests': {
            'average_completeness': 0.95,
            'average_diversity': 0.72
        }
    }
    
    # Generate reports
    output_files = generator.generate_report(sample_results, format='all')
    
    print("Generated reports:")
    for format, path in output_files.items():
        print(f"  - {format}: {path}")