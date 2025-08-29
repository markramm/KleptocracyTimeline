#!/usr/bin/env python3
"""
Compare Basic and Enhanced RAG Systems

Evaluates both systems on the same ground truth dataset to measure improvements.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any
import sys
import numpy as np
from collections import defaultdict

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from real_rag_system import RealRAGSystem
from enhanced_rag_system import EnhancedRAGSystem
from evaluation.metrics import (
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_f1_at_k,
    calculate_ndcg_at_k,
    calculate_mrr
)


class SystemComparator:
    """Compares performance of different RAG systems."""
    
    def __init__(self):
        """Initialize comparator."""
        # Load ground truth
        self.ground_truth = self.load_ground_truth()
        
        # Initialize systems
        print("Initializing Basic RAG System...")
        self.basic_rag = RealRAGSystem(data_path="../timeline_data/timeline_complete.json")
        
        print("\nInitializing Enhanced RAG System...")
        self.enhanced_rag = EnhancedRAGSystem(data_path="../timeline_data/timeline_complete.json")
        
        # Results storage
        self.basic_results = []
        self.enhanced_results = []
    
    def load_ground_truth(self) -> Dict:
        """Load ground truth data."""
        gt_path = Path("ground_truth.json")
        if not gt_path.exists():
            raise FileNotFoundError("Ground truth file not found.")
        
        with open(gt_path, 'r') as f:
            return json.load(f)
    
    def evaluate_system(self, system, system_name: str, query_limit: int = None) -> List[Dict]:
        """
        Evaluate a single system.
        
        Args:
            system: RAG system to evaluate
            system_name: Name of the system
            query_limit: Optional limit on number of queries to test
            
        Returns:
            List of evaluation results
        """
        print(f"\n{'='*60}")
        print(f"Evaluating {system_name}")
        print('='*60)
        
        results = []
        query_annotations = self.ground_truth['query_annotations']
        
        # Limit queries if specified
        if query_limit:
            query_items = list(query_annotations.items())[:query_limit]
        else:
            query_items = list(query_annotations.items())
        
        for i, (query_id, query_data) in enumerate(query_items, 1):
            query_text = query_data['query_text']
            relevant_ids = set(query_data['relevant_events'])
            
            if not relevant_ids:
                continue
            
            print(f"\n[{i}/{len(query_items)}] {query_id}")
            
            # Get search results
            start_time = time.time()
            search_results = system.search(query_text, top_k=20)
            search_time = time.time() - start_time
            
            # Extract retrieved IDs
            retrieved_ids = []
            for result in search_results:
                event_id = None
                if isinstance(result, dict):
                    if 'event' in result and isinstance(result['event'], dict):
                        event_id = result['event'].get('id')
                    else:
                        event_id = result.get('id') or result.get('event_id')
                elif hasattr(result, 'id'):
                    event_id = result.id
                
                if event_id:
                    retrieved_ids.append(event_id)
            
            # Calculate metrics
            metrics = {}
            for k in [1, 3, 5, 10, 20]:
                if k <= len(retrieved_ids):
                    metrics[f'P@{k}'] = calculate_precision_at_k(retrieved_ids, list(relevant_ids), k)
                    metrics[f'R@{k}'] = calculate_recall_at_k(retrieved_ids, list(relevant_ids), k)
                    metrics[f'F1@{k}'] = calculate_f1_at_k(retrieved_ids, list(relevant_ids), k)
            
            # Calculate MRR
            metrics['MRR'] = calculate_mrr(retrieved_ids, list(relevant_ids))
            
            # Store result
            result = {
                'query_id': query_id,
                'query_text': query_text,
                'relevant_count': len(relevant_ids),
                'retrieved_count': len(retrieved_ids),
                'search_time': search_time,
                'metrics': metrics,
                'query_type': query_data.get('metadata', {}).get('type', 'unknown')
            }
            results.append(result)
            
            # Print progress
            print(f"  P@5: {metrics.get('P@5', 0):.3f}, R@5: {metrics.get('R@5', 0):.3f}, "
                  f"Time: {search_time:.3f}s")
        
        return results
    
    def calculate_aggregate_metrics(self, results: List[Dict]) -> Dict:
        """Calculate aggregate metrics for a system."""
        if not results:
            return {}
        
        all_metrics = defaultdict(list)
        
        for result in results:
            for metric, value in result['metrics'].items():
                all_metrics[metric].append(value)
        
        aggregate = {}
        for metric, values in all_metrics.items():
            aggregate[f'avg_{metric}'] = np.mean(values)
            aggregate[f'std_{metric}'] = np.std(values)
        
        # Calculate quality score
        key_metrics = ['avg_P@5', 'avg_R@5', 'avg_F1@5', 'avg_MRR']
        quality_scores = [aggregate.get(m, 0) for m in key_metrics]
        aggregate['quality_score'] = np.mean(quality_scores)
        
        # Average search time
        avg_time = np.mean([r['search_time'] for r in results])
        aggregate['avg_search_time'] = avg_time
        
        return aggregate
    
    def compare_systems(self, query_limit: int = None):
        """Run comparison between systems."""
        # Evaluate basic system
        self.basic_results = self.evaluate_system(
            self.basic_rag, 
            "Basic RAG System",
            query_limit
        )
        basic_aggregate = self.calculate_aggregate_metrics(self.basic_results)
        
        # Evaluate enhanced system
        self.enhanced_results = self.evaluate_system(
            self.enhanced_rag,
            "Enhanced RAG System",
            query_limit
        )
        enhanced_aggregate = self.calculate_aggregate_metrics(self.enhanced_results)
        
        # Generate comparison report
        self.generate_comparison_report(basic_aggregate, enhanced_aggregate)
    
    def generate_comparison_report(self, basic_metrics: Dict, enhanced_metrics: Dict):
        """Generate comparison report."""
        print("\n" + "="*60)
        print("SYSTEM COMPARISON REPORT")
        print("="*60)
        
        # Key metrics comparison
        print("\nKEY METRICS COMPARISON")
        print("-"*40)
        print(f"{'Metric':<20} {'Basic':>10} {'Enhanced':>10} {'Improvement':>12}")
        print("-"*40)
        
        metrics_to_compare = [
            ('Precision@5', 'avg_P@5'),
            ('Recall@5', 'avg_R@5'),
            ('F1@5', 'avg_F1@5'),
            ('MRR', 'avg_MRR'),
            ('Quality Score', 'quality_score'),
            ('Avg Search Time', 'avg_search_time')
        ]
        
        improvements = {}
        for display_name, metric_key in metrics_to_compare:
            basic_val = basic_metrics.get(metric_key, 0)
            enhanced_val = enhanced_metrics.get(metric_key, 0)
            
            if metric_key == 'avg_search_time':
                # For time, lower is better
                if basic_val > 0:
                    improvement = -((enhanced_val - basic_val) / basic_val * 100)
                else:
                    improvement = 0
                print(f"{display_name:<20} {basic_val:>10.3f}s {enhanced_val:>10.3f}s "
                      f"{improvement:>+11.1f}%")
            else:
                # For other metrics, higher is better
                if basic_val > 0:
                    improvement = (enhanced_val - basic_val) / basic_val * 100
                else:
                    improvement = enhanced_val * 100
                print(f"{display_name:<20} {basic_val:>10.3f} {enhanced_val:>10.3f} "
                      f"{improvement:>+11.1f}%")
            
            improvements[display_name] = improvement
        
        # Performance by query type
        print("\n\nPERFORMANCE BY QUERY TYPE (P@5)")
        print("-"*40)
        
        basic_by_type = self.analyze_by_type(self.basic_results)
        enhanced_by_type = self.analyze_by_type(self.enhanced_results)
        
        print(f"{'Query Type':<25} {'Basic':>10} {'Enhanced':>10} {'Change':>10}")
        print("-"*40)
        
        all_types = set(basic_by_type.keys()) | set(enhanced_by_type.keys())
        for qtype in sorted(all_types):
            basic_p5 = basic_by_type.get(qtype, {}).get('P@5', 0)
            enhanced_p5 = enhanced_by_type.get(qtype, {}).get('P@5', 0)
            change = enhanced_p5 - basic_p5
            print(f"{qtype:<25} {basic_p5:>10.3f} {enhanced_p5:>10.3f} {change:>+10.3f}")
        
        # Overall assessment
        print("\n\nOVERALL ASSESSMENT")
        print("-"*40)
        
        avg_improvement = np.mean([v for k, v in improvements.items() if k != 'Avg Search Time'])
        
        if avg_improvement > 20:
            assessment = "SIGNIFICANT IMPROVEMENT"
            grade = "A"
        elif avg_improvement > 10:
            assessment = "MODERATE IMPROVEMENT"
            grade = "B"
        elif avg_improvement > 0:
            assessment = "SLIGHT IMPROVEMENT"
            grade = "C"
        else:
            assessment = "NO IMPROVEMENT"
            grade = "D"
        
        print(f"Average Improvement: {avg_improvement:+.1f}%")
        print(f"Assessment: {assessment}")
        print(f"Grade: {grade}")
        
        # Key improvements
        print("\n\nKEY IMPROVEMENTS")
        print("-"*40)
        
        if improvements['Recall@5'] > 10:
            print("✓ Significant recall improvement from query expansion")
        if improvements['Precision@5'] > 10:
            print("✓ Better precision from re-ranking and boosting")
        if improvements['MRR'] > 10:
            print("✓ Improved first result quality")
        if improvements.get('Avg Search Time', 0) < -10:
            print("✓ Faster search performance")
        
        # Save detailed report
        report = {
            'basic_metrics': basic_metrics,
            'enhanced_metrics': enhanced_metrics,
            'improvements': improvements,
            'basic_results': self.basic_results,
            'enhanced_results': self.enhanced_results
        }
        
        with open("system_comparison_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("\n✓ Detailed report saved to system_comparison_report.json")
    
    def analyze_by_type(self, results: List[Dict]) -> Dict:
        """Analyze performance by query type."""
        type_metrics = defaultdict(lambda: defaultdict(list))
        
        for result in results:
            qtype = result['query_type']
            for metric, value in result['metrics'].items():
                type_metrics[qtype][metric].append(value)
        
        # Calculate averages
        type_avg = {}
        for qtype, metrics in type_metrics.items():
            type_avg[qtype] = {}
            for metric, values in metrics.items():
                type_avg[qtype][metric] = np.mean(values)
        
        return type_avg


def main():
    """Main execution."""
    comparator = SystemComparator()
    
    # Run comparison on subset for speed (use None for all queries)
    comparator.compare_systems(query_limit=15)


if __name__ == '__main__':
    main()