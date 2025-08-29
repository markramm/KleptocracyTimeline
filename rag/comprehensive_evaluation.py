#!/usr/bin/env python3
"""
Comprehensive RAG Evaluation Script

Evaluates the RAG system against the complete ground truth dataset.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import sys
import numpy as np

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from real_rag_system import RealRAGSystem, Event
from evaluation.metrics import (
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_ndcg_at_k,
    calculate_mrr,
    calculate_f1_at_k
)


class ComprehensiveEvaluator:
    """Comprehensive evaluator for the RAG system."""
    
    def __init__(self):
        """Initialize evaluator."""
        # Load ground truth
        self.ground_truth = self.load_ground_truth()
        
        # Initialize RAG system
        print("Initializing RAG system...")
        self.rag = RealRAGSystem(data_path="../timeline_data/timeline_complete.json")
        
        # Results storage
        self.results = []
        
    def load_ground_truth(self) -> Dict:
        """Load ground truth data."""
        gt_path = Path("ground_truth.json")
        if not gt_path.exists():
            raise FileNotFoundError("Ground truth file not found. Run build_ground_truth.py first.")
        
        with open(gt_path, 'r') as f:
            return json.load(f)
    
    def evaluate_query(self, query_data: Dict) -> Dict:
        """
        Evaluate a single query.
        
        Args:
            query_data: Query annotation from ground truth
            
        Returns:
            Evaluation results for this query
        """
        query_text = query_data['query_text']
        relevant_ids = set(query_data['relevant_events'])
        
        if not relevant_ids:
            # Skip queries with no relevant events
            return None
        
        # Get search results from RAG
        start_time = time.time()
        results = self.rag.search(query_text, top_k=20)
        search_time = time.time() - start_time
        
        # Extract retrieved event IDs
        retrieved_ids = []
        for result in results:
            # Handle different result formats
            event_id = None
            if isinstance(result, dict):
                # Check if it has an 'event' key with nested data
                if 'event' in result and isinstance(result['event'], dict):
                    event_id = result['event'].get('id')
                else:
                    event_id = result.get('id') or result.get('event_id')
            elif hasattr(result, 'id'):
                event_id = result.id
            elif hasattr(result, 'event') and hasattr(result.event, 'id'):
                event_id = result.event.id
            
            if event_id:
                retrieved_ids.append(event_id)
        
        # Calculate metrics at different k values
        metrics = {}
        for k in [1, 3, 5, 10, 20]:
            if k <= len(retrieved_ids):
                # Use the correct signature for metrics
                metrics[f'P@{k}'] = calculate_precision_at_k(retrieved_ids, list(relevant_ids), k)
                metrics[f'R@{k}'] = calculate_recall_at_k(retrieved_ids, list(relevant_ids), k)
                metrics[f'F1@{k}'] = calculate_f1_at_k(retrieved_ids, list(relevant_ids), k)
                
                if k == 10:
                    # Calculate NDCG for k=10
                    metrics['NDCG@10'] = calculate_ndcg_at_k(retrieved_ids, list(relevant_ids), k)
        
        # Calculate MRR
        first_relevant = None
        for i, rid in enumerate(retrieved_ids, 1):
            if rid in relevant_ids:
                first_relevant = i
                break
        
        metrics['MRR'] = 1.0 / first_relevant if first_relevant else 0.0
        
        # Store detailed results
        result = {
            'query_id': query_data['query_id'],
            'query_text': query_text,
            'relevant_count': len(relevant_ids),
            'retrieved_count': len(retrieved_ids),
            'search_time': search_time,
            'metrics': metrics,
            'metadata': query_data.get('metadata', {})
        }
        
        return result
    
    def run_evaluation(self):
        """Run complete evaluation on all queries."""
        print("\n" + "="*60)
        print("COMPREHENSIVE RAG EVALUATION")
        print("="*60)
        
        query_annotations = self.ground_truth['query_annotations']
        total_queries = len(query_annotations)
        
        # Track metrics by category
        category_metrics = defaultdict(lambda: defaultdict(list))
        
        for i, (query_id, query_data) in enumerate(query_annotations.items(), 1):
            print(f"\n[{i}/{total_queries}] Evaluating: {query_id}")
            
            # Evaluate query
            result = self.evaluate_query(query_data)
            
            if result:
                self.results.append(result)
                
                # Categorize results
                query_type = result['metadata'].get('type', 'unknown')
                difficulty = result['metadata'].get('difficulty', 'unknown')
                priority = result['metadata'].get('priority', 'unknown')
                
                category_metrics['type'][query_type].append(result['metrics'])
                category_metrics['difficulty'][difficulty].append(result['metrics'])
                category_metrics['priority'][priority].append(result['metrics'])
                
                # Print query results
                print(f"  Relevant: {result['relevant_count']}, Retrieved: {result['retrieved_count']}")
                print(f"  P@5: {result['metrics'].get('P@5', 0):.3f}, " 
                      f"R@5: {result['metrics'].get('R@5', 0):.3f}, "
                      f"MRR: {result['metrics'].get('MRR', 0):.3f}")
    
    def calculate_aggregate_metrics(self) -> Dict:
        """Calculate aggregate metrics across all queries."""
        if not self.results:
            return {}
        
        # Aggregate metrics
        all_metrics = defaultdict(list)
        
        for result in self.results:
            for metric, value in result['metrics'].items():
                all_metrics[metric].append(value)
        
        # Calculate averages
        aggregate = {}
        for metric, values in all_metrics.items():
            aggregate[f'avg_{metric}'] = np.mean(values)
            aggregate[f'std_{metric}'] = np.std(values)
        
        # Calculate overall quality score
        key_metrics = ['avg_P@5', 'avg_R@5', 'avg_F1@5', 'avg_NDCG@10', 'avg_MRR']
        quality_scores = [aggregate.get(m, 0) for m in key_metrics]
        aggregate['quality_score'] = np.mean(quality_scores)
        
        # Determine grade
        score = aggregate['quality_score']
        if score >= 0.9:
            grade = 'A+ (Excellent)'
        elif score >= 0.8:
            grade = 'A (Very Good)'
        elif score >= 0.7:
            grade = 'B (Good)'
        elif score >= 0.6:
            grade = 'C (Satisfactory)'
        elif score >= 0.5:
            grade = 'D (Needs Improvement)'
        else:
            grade = 'F (Poor)'
        
        aggregate['grade'] = grade
        
        return aggregate
    
    def generate_report(self):
        """Generate comprehensive evaluation report."""
        aggregate = self.calculate_aggregate_metrics()
        
        report = []
        report.append("="*60)
        report.append("COMPREHENSIVE RAG EVALUATION REPORT")
        report.append("="*60)
        report.append(f"Total Queries Evaluated: {len(self.results)}")
        report.append("")
        
        # Key metrics
        report.append("KEY METRICS")
        report.append("-"*40)
        report.append(f"Precision@5: {aggregate.get('avg_P@5', 0):.3f} ± {aggregate.get('std_P@5', 0):.3f}")
        report.append(f"Recall@5: {aggregate.get('avg_R@5', 0):.3f} ± {aggregate.get('std_R@5', 0):.3f}")
        report.append(f"F1@5: {aggregate.get('avg_F1@5', 0):.3f} ± {aggregate.get('std_F1@5', 0):.3f}")
        report.append(f"NDCG@10: {aggregate.get('avg_NDCG@10', 0):.3f} ± {aggregate.get('std_NDCG@10', 0):.3f}")
        report.append(f"MRR: {aggregate.get('avg_MRR', 0):.3f} ± {aggregate.get('std_MRR', 0):.3f}")
        report.append("")
        
        # Performance at different k
        report.append("PERFORMANCE AT DIFFERENT K")
        report.append("-"*40)
        for k in [1, 3, 5, 10]:
            report.append(f"@{k:2}: P={aggregate.get(f'avg_P@{k}', 0):.3f}, "
                         f"R={aggregate.get(f'avg_R@{k}', 0):.3f}, "
                         f"F1={aggregate.get(f'avg_F1@{k}', 0):.3f}")
        report.append("")
        
        # Performance by query type
        report.append("PERFORMANCE BY QUERY TYPE")
        report.append("-"*40)
        
        type_performance = self.analyze_by_category('type')
        for qtype, metrics in sorted(type_performance.items()):
            if metrics and 'P@5' in metrics:
                report.append(f"{qtype:20}: P@5={metrics['P@5']:.3f}, R@5={metrics['R@5']:.3f}")
        report.append("")
        
        # Performance by difficulty
        report.append("PERFORMANCE BY DIFFICULTY")
        report.append("-"*40)
        
        difficulty_performance = self.analyze_by_category('difficulty')
        for diff, metrics in sorted(difficulty_performance.items()):
            if metrics and 'P@5' in metrics:
                report.append(f"{diff:10}: P@5={metrics['P@5']:.3f}, R@5={metrics['R@5']:.3f}")
        report.append("")
        
        # Overall assessment
        report.append("OVERALL ASSESSMENT")
        report.append("-"*40)
        report.append(f"Quality Score: {aggregate['quality_score']:.3f}")
        report.append(f"Grade: {aggregate['grade']}")
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-"*40)
        
        if aggregate.get('avg_P@5', 0) < 0.5:
            report.append("- Low precision: Consider improving ranking/reranking")
        if aggregate.get('avg_R@5', 0) < 0.5:
            report.append("- Low recall: Consider query expansion and hybrid search")
        if aggregate.get('avg_MRR', 0) < 0.5:
            report.append("- Poor first result quality: Focus on relevance scoring")
        
        report_text = "\n".join(report)
        
        # Save report
        with open("comprehensive_evaluation_report.txt", "w") as f:
            f.write(report_text)
        
        # Save detailed results
        with open("comprehensive_evaluation_results.json", "w") as f:
            json.dump({
                'aggregate_metrics': aggregate,
                'detailed_results': self.results,
                'ground_truth_stats': {
                    'total_queries': len(self.ground_truth['query_annotations']),
                    'total_events': self.ground_truth['metadata']['total_events'],
                    'coverage': self.ground_truth['metadata']['coverage_percentage']
                }
            }, f, indent=2)
        
        print(report_text)
        print("\n✓ Report saved to comprehensive_evaluation_report.txt")
        print("✓ Detailed results saved to comprehensive_evaluation_results.json")
    
    def analyze_by_category(self, category: str) -> Dict:
        """Analyze performance by category."""
        category_metrics = defaultdict(lambda: defaultdict(list))
        
        for result in self.results:
            cat_value = result['metadata'].get(category, 'unknown')
            for metric, value in result['metrics'].items():
                category_metrics[cat_value][metric].append(value)
        
        # Calculate averages
        category_avg = {}
        for cat_value, metrics in category_metrics.items():
            category_avg[cat_value] = {}
            for metric, values in metrics.items():
                category_avg[cat_value][metric] = np.mean(values)
        
        return category_avg


def main():
    """Main execution."""
    evaluator = ComprehensiveEvaluator()
    evaluator.run_evaluation()
    evaluator.generate_report()


if __name__ == '__main__':
    main()