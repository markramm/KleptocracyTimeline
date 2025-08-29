"""
Research-Grade RAG Evaluator

Comprehensive evaluation engine for the Kleptocracy Timeline RAG system,
focusing on research quality metrics including recall, consistency, and completeness.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import time
import hashlib
from datetime import datetime
from collections import defaultdict
import numpy as np

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# from simple_rag import TimelineRAG  # Commented out - not needed for ground truth building
from evaluation.metrics import (
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_ndcg_at_k,
    calculate_mrr,
    calculate_f1_at_k,
    calculate_consistency_score,
    calculate_completeness_score,
    calculate_diversity_score,
    calculate_temporal_coverage,
    calculate_result_hash
)
from evaluation.test_queries import TEST_QUERIES, load_test_queries
from evaluation.ground_truth import GroundTruthManager


class RAGEvaluator:
    """
    Research-grade evaluation engine for RAG system.
    """
    
    def __init__(self, rag_system: TimelineRAG = None, 
                 ground_truth_manager: GroundTruthManager = None,
                 output_dir: str = None):
        """
        Initialize evaluator.
        
        Args:
            rag_system: RAG system to evaluate (will create if None)
            ground_truth_manager: Ground truth manager (will create if None)
            output_dir: Directory for evaluation outputs
        """
        # Initialize RAG system
        if rag_system is None:
            print("Initializing RAG system for evaluation...")
            self.rag = TimelineRAG(
                timeline_dir="../timeline_data/events",
                use_local_embeddings=True
            )
        else:
            self.rag = rag_system
        
        # Initialize ground truth manager
        if ground_truth_manager is None:
            self.ground_truth = GroundTruthManager(
                events_dir="../timeline_data/events"
            )
        else:
            self.ground_truth = ground_truth_manager
        
        # Setup output directory
        self.output_dir = Path(output_dir or 'evaluation_results')
        self.output_dir.mkdir(exist_ok=True)
        
        # Load test queries
        self.test_queries = load_test_queries()
        
        # Results storage
        self.evaluation_results = {
            'timestamp': datetime.now().isoformat(),
            'queries': {},
            'aggregate_metrics': {},
            'consistency_tests': {},
            'completeness_tests': {},
            'research_scenarios': {}
        }
    
    def evaluate_retrieval(self, queries: List[Dict[str, Any]] = None,
                          k_values: List[int] = None) -> Dict[str, Any]:
        """
        Evaluate retrieval quality with precision@k, recall@k, NDCG@k.
        
        Args:
            queries: Test queries to evaluate (default: all)
            k_values: List of k values for metrics (default: [5, 10, 20])
            
        Returns:
            Dictionary with retrieval metrics
        """
        if queries is None:
            queries = self.test_queries
        
        if k_values is None:
            k_values = [5, 10, 20]
        
        print(f"Evaluating retrieval quality on {len(queries)} queries...")
        
        all_metrics = []
        query_results = {}
        
        for i, query in enumerate(queries):
            query_id = query.get('id', f'query_{i}')
            query_text = query['query']
            
            # Get ground truth
            relevant_ids = self.ground_truth.get_relevant_events(query_id)
            if not relevant_ids and 'expected_event_ids' in query:
                relevant_ids = query['expected_event_ids']
            
            if not relevant_ids:
                print(f"  Skipping {query_id}: No ground truth available")
                continue
            
            # Perform search
            start_time = time.time()
            search_results = self.rag.search(query_text, n_results=max(k_values))
            search_time = time.time() - start_time
            
            # Extract retrieved IDs
            retrieved_ids = [r['event']['id'] for r in search_results]
            
            # Calculate metrics for each k
            metrics = {
                'query_id': query_id,
                'query_text': query_text,
                'search_time': search_time,
                'total_retrieved': len(retrieved_ids),
                'total_relevant': len(relevant_ids)
            }
            
            for k in k_values:
                metrics[f'precision@{k}'] = calculate_precision_at_k(retrieved_ids, relevant_ids, k)
                metrics[f'recall@{k}'] = calculate_recall_at_k(retrieved_ids, relevant_ids, k)
                metrics[f'f1@{k}'] = calculate_f1_at_k(retrieved_ids, relevant_ids, k)
                metrics[f'ndcg@{k}'] = calculate_ndcg_at_k(retrieved_ids, relevant_ids, k)
            
            metrics['mrr'] = calculate_mrr(retrieved_ids, relevant_ids)
            
            # Store detailed results
            query_results[query_id] = {
                'metrics': metrics,
                'retrieved_ids': retrieved_ids[:20],  # Top 20 for analysis
                'relevant_ids': relevant_ids,
                'missing_ids': list(set(relevant_ids) - set(retrieved_ids))
            }
            
            all_metrics.append(metrics)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(queries)} queries...")
        
        # Calculate aggregate metrics
        if all_metrics:
            aggregate = self._aggregate_metrics(all_metrics, k_values)
        else:
            aggregate = {}
        
        results = {
            'individual_queries': query_results,
            'aggregate_metrics': aggregate,
            'evaluation_config': {
                'k_values': k_values,
                'num_queries': len(queries),
                'num_evaluated': len(all_metrics)
            }
        }
        
        # Store in main results
        self.evaluation_results['queries'] = query_results
        self.evaluation_results['aggregate_metrics'] = aggregate
        
        return results
    
    def evaluate_consistency(self, queries: List[Dict[str, Any]] = None,
                           num_runs: int = 5) -> Dict[str, Any]:
        """
        Test result reproducibility and determinism.
        
        Args:
            queries: Test queries (default: sample of 10)
            num_runs: Number of times to run each query
            
        Returns:
            Consistency metrics
        """
        if queries is None:
            # Sample 10 queries for consistency testing
            queries = self.test_queries[:10]
        
        print(f"Evaluating consistency across {num_runs} runs for {len(queries)} queries...")
        
        consistency_results = {}
        
        for query in queries:
            query_id = query.get('id', 'unknown')
            query_text = query['query']
            
            # Run query multiple times
            runs_results = []
            runs_hashes = []
            
            for run in range(num_runs):
                results = self.rag.search(query_text, n_results=10)
                result_ids = [r['event']['id'] for r in results]
                runs_results.append(result_ids)
                runs_hashes.append(calculate_result_hash(result_ids))
            
            # Calculate consistency
            consistency = calculate_consistency_score(runs_results)
            hash_consistency = len(set(runs_hashes)) == 1  # All hashes identical
            
            consistency_results[query_id] = {
                'consistency_score': consistency,
                'hash_consistent': hash_consistency,
                'unique_results': len(set(runs_hashes)),
                'num_runs': num_runs
            }
        
        # Overall consistency
        avg_consistency = np.mean([r['consistency_score'] for r in consistency_results.values()])
        perfect_consistency_rate = sum(1 for r in consistency_results.values() 
                                      if r['hash_consistent']) / len(consistency_results)
        
        results = {
            'individual_queries': consistency_results,
            'overall_consistency': avg_consistency,
            'perfect_consistency_rate': perfect_consistency_rate,
            'evaluation_config': {
                'num_queries': len(queries),
                'num_runs': num_runs
            }
        }
        
        self.evaluation_results['consistency_tests'] = results
        return results
    
    def evaluate_research_scenarios(self) -> Dict[str, Any]:
        """
        Evaluate complex research patterns: timeline analysis, actor networks, etc.
        
        Returns:
            Research scenario evaluation results
        """
        print("Evaluating research-specific scenarios...")
        
        scenarios = {
            'timeline_analysis': self._evaluate_timeline_scenario(),
            'actor_network': self._evaluate_actor_network_scenario(),
            'pattern_detection': self._evaluate_pattern_detection_scenario(),
            'gap_analysis': self._evaluate_gap_analysis_scenario(),
            'comparative_analysis': self._evaluate_comparative_scenario()
        }
        
        self.evaluation_results['research_scenarios'] = scenarios
        return scenarios
    
    def evaluate_completeness(self, sample_size: int = 20) -> Dict[str, Any]:
        """
        Test comprehensive coverage - are we missing relevant events?
        
        Args:
            sample_size: Number of queries to test
            
        Returns:
            Completeness metrics
        """
        print(f"Evaluating completeness on {sample_size} queries...")
        
        # Select queries focused on completeness
        completeness_queries = [q for q in self.test_queries 
                               if q.get('type') in ['research_comprehensive', 'pattern_analysis']]
        
        if not completeness_queries:
            completeness_queries = self.test_queries[:sample_size]
        else:
            completeness_queries = completeness_queries[:sample_size]
        
        completeness_results = {}
        
        for query in completeness_queries:
            query_id = query.get('id', 'unknown')
            query_text = query['query']
            
            # Get extensive results
            results = self.rag.search(query_text, n_results=50)
            retrieved_ids = [r['event']['id'] for r in results]
            
            # Get ground truth
            relevant_ids = self.ground_truth.get_relevant_events(query_id)
            if not relevant_ids and 'expected_event_ids' in query:
                relevant_ids = query['expected_event_ids']
            
            # Get critical events
            critical_ids = self.ground_truth.get_critical_events()
            
            # Calculate completeness
            if relevant_ids:
                completeness = calculate_completeness_score(
                    retrieved_ids,
                    relevant_ids,
                    critical_ids
                )
            else:
                completeness = {'overall_completeness': 0.0, 'note': 'No ground truth'}
            
            # Analyze coverage
            retrieved_events = [r['event'] for r in results[:20]]
            temporal_coverage = calculate_temporal_coverage(retrieved_events)
            diversity = calculate_diversity_score(retrieved_events)
            
            completeness_results[query_id] = {
                'completeness_metrics': completeness,
                'temporal_coverage': temporal_coverage,
                'diversity_score': diversity,
                'total_retrieved': len(retrieved_ids),
                'total_relevant': len(relevant_ids) if relevant_ids else 'unknown'
            }
        
        # Aggregate completeness
        avg_completeness = np.mean([
            r['completeness_metrics'].get('overall_completeness', 0)
            for r in completeness_results.values()
            if isinstance(r['completeness_metrics'], dict)
        ])
        
        avg_diversity = np.mean([
            r['diversity_score'] for r in completeness_results.values()
        ])
        
        results = {
            'individual_queries': completeness_results,
            'average_completeness': avg_completeness,
            'average_diversity': avg_diversity,
            'evaluation_config': {
                'num_queries': len(completeness_queries)
            }
        }
        
        self.evaluation_results['completeness_tests'] = results
        return results
    
    def run_comprehensive_evaluation(self, save_report: bool = True) -> Dict[str, Any]:
        """
        Run all evaluations with research-grade rigor.
        
        Args:
            save_report: Whether to save report to file
            
        Returns:
            Comprehensive evaluation results
        """
        print("\n" + "="*60)
        print("COMPREHENSIVE RAG EVALUATION")
        print("="*60)
        
        # 1. Retrieval Quality
        print("\n1. Evaluating Retrieval Quality...")
        retrieval_results = self.evaluate_retrieval()
        
        # 2. Consistency
        print("\n2. Evaluating Consistency...")
        consistency_results = self.evaluate_consistency()
        
        # 3. Completeness
        print("\n3. Evaluating Completeness...")
        completeness_results = self.evaluate_completeness()
        
        # 4. Research Scenarios
        print("\n4. Evaluating Research Scenarios...")
        research_results = self.evaluate_research_scenarios()
        
        # Generate summary
        summary = self._generate_summary()
        
        # Save results if requested
        if save_report:
            self._save_evaluation_report()
        
        print("\n" + "="*60)
        print("EVALUATION COMPLETE")
        print("="*60)
        print(summary)
        
        return self.evaluation_results
    
    def _evaluate_timeline_scenario(self) -> Dict[str, Any]:
        """Evaluate timeline reconstruction capabilities."""
        query = "Show timeline of Schedule F implementation and federal workforce changes"
        results = self.rag.search(query, n_results=20)
        
        # Check temporal ordering
        dates = [r['event'].get('date', '') for r in results]
        is_ordered = dates == sorted(dates)
        
        # Check coverage
        events = [r['event'] for r in results]
        temporal_coverage = calculate_temporal_coverage(events)
        
        return {
            'query': query,
            'num_results': len(results),
            'temporally_ordered': is_ordered,
            'temporal_coverage': temporal_coverage,
            'date_range': {'start': min(dates) if dates else None,
                          'end': max(dates) if dates else None}
        }
    
    def _evaluate_actor_network_scenario(self) -> Dict[str, Any]:
        """Evaluate actor relationship mapping."""
        query = "Show all connections between Trump and his business associates"
        results = self.rag.search(query, n_results=30)
        
        # Extract actor networks
        actor_connections = defaultdict(set)
        for r in results:
            actors = r['event'].get('actors', [])
            if isinstance(actors, str):
                actors = [actors]
            for actor in actors:
                actor_connections[actor].update(actors)
        
        return {
            'query': query,
            'num_results': len(results),
            'unique_actors': len(actor_connections),
            'connection_density': sum(len(v) for v in actor_connections.values()) / len(actor_connections)
            if actor_connections else 0
        }
    
    def _evaluate_pattern_detection_scenario(self) -> Dict[str, Any]:
        """Evaluate pattern detection capabilities."""
        patterns = self.rag.find_patterns(tag='regulatory-capture')
        
        return {
            'pattern_type': 'regulatory-capture',
            'total_events': patterns['total_events'],
            'date_range': patterns['date_range'],
            'top_actors': list(patterns['top_actors'].keys())[:5] if patterns['top_actors'] else [],
            'events_by_month': len(patterns.get('events_by_month', {}))
        }
    
    def _evaluate_gap_analysis_scenario(self) -> Dict[str, Any]:
        """Evaluate coverage gap detection."""
        # Look for potential gaps
        all_events = list(self.rag.events)
        dates = sorted([e.get('date', '') for e in all_events if e.get('date')])
        
        # Find largest gaps
        gaps = []
        for i in range(1, len(dates)):
            if dates[i][:7] != dates[i-1][:7]:  # Different months
                gaps.append((dates[i-1], dates[i]))
        
        return {
            'total_events': len(all_events),
            'date_coverage': {'start': dates[0] if dates else None,
                            'end': dates[-1] if dates else None},
            'identified_gaps': len(gaps),
            'largest_gaps': gaps[:5] if gaps else []
        }
    
    def _evaluate_comparative_scenario(self) -> Dict[str, Any]:
        """Evaluate comparative analysis capabilities."""
        query1 = "cryptocurrency and Trump"
        query2 = "judicial appointments"
        
        results1 = self.rag.search(query1, n_results=10)
        results2 = self.rag.search(query2, n_results=10)
        
        ids1 = set(r['event']['id'] for r in results1)
        ids2 = set(r['event']['id'] for r in results2)
        
        return {
            'queries': [query1, query2],
            'results_count': [len(results1), len(results2)],
            'overlap': len(ids1.intersection(ids2)),
            'unique_to_first': len(ids1 - ids2),
            'unique_to_second': len(ids2 - ids1)
        }
    
    def _aggregate_metrics(self, metrics_list: List[Dict], k_values: List[int]) -> Dict:
        """Aggregate individual metrics into summary statistics."""
        aggregate = {
            'avg_search_time': np.mean([m['search_time'] for m in metrics_list]),
            'avg_mrr': np.mean([m['mrr'] for m in metrics_list])
        }
        
        for k in k_values:
            precision_values = [m[f'precision@{k}'] for m in metrics_list]
            recall_values = [m[f'recall@{k}'] for m in metrics_list]
            f1_values = [m[f'f1@{k}'] for m in metrics_list]
            ndcg_values = [m[f'ndcg@{k}'] for m in metrics_list]
            
            aggregate[f'avg_precision@{k}'] = np.mean(precision_values)
            aggregate[f'avg_recall@{k}'] = np.mean(recall_values)
            aggregate[f'avg_f1@{k}'] = np.mean(f1_values)
            aggregate[f'avg_ndcg@{k}'] = np.mean(ndcg_values)
            
            aggregate[f'std_precision@{k}'] = np.std(precision_values)
            aggregate[f'std_recall@{k}'] = np.std(recall_values)
        
        return aggregate
    
    def _generate_summary(self) -> str:
        """Generate human-readable evaluation summary."""
        metrics = self.evaluation_results.get('aggregate_metrics', {})
        consistency = self.evaluation_results.get('consistency_tests', {})
        completeness = self.evaluation_results.get('completeness_tests', {})
        
        summary = f"""
EVALUATION SUMMARY
==================

Retrieval Quality (Primary Metrics):
  • Recall@10: {metrics.get('avg_recall@10', 0):.3f} (Target: >0.95)
  • Precision@5: {metrics.get('avg_precision@5', 0):.3f} (Target: >0.90)
  • F1@10: {metrics.get('avg_f1@10', 0):.3f}
  • NDCG@10: {metrics.get('avg_ndcg@10', 0):.3f}
  • MRR: {metrics.get('avg_mrr', 0):.3f}

Consistency (Research Reproducibility):
  • Overall Consistency: {consistency.get('overall_consistency', 0):.3f} (Target: >0.99)
  • Perfect Consistency Rate: {consistency.get('perfect_consistency_rate', 0):.2%}

Completeness (Coverage Quality):
  • Average Completeness: {completeness.get('average_completeness', 0):.3f} (Target: >0.98)
  • Average Diversity: {completeness.get('average_diversity', 0):.3f}

Performance:
  • Average Search Time: {metrics.get('avg_search_time', 0):.3f}s (Target: <5.0s)

Grade Assessment:
  • Current Grade: {self._calculate_grade()}
  • Target Grade: A+ (95/100)
"""
        return summary
    
    def _calculate_grade(self) -> str:
        """Calculate overall system grade based on metrics."""
        metrics = self.evaluation_results.get('aggregate_metrics', {})
        consistency = self.evaluation_results.get('consistency_tests', {})
        completeness = self.evaluation_results.get('completeness_tests', {})
        
        # Weighted scoring
        recall_score = metrics.get('avg_recall@10', 0) * 35  # 35% weight
        precision_score = metrics.get('avg_precision@5', 0) * 25  # 25% weight
        consistency_score = consistency.get('overall_consistency', 0) * 20  # 20% weight
        completeness_score = completeness.get('average_completeness', 0) * 20  # 20% weight
        
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
    
    def _save_evaluation_report(self):
        """Save evaluation report to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON report
        json_path = self.output_dir / f"evaluation_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(self.evaluation_results, f, indent=2, default=str)
        
        # Save markdown summary
        md_path = self.output_dir / f"evaluation_{timestamp}.md"
        with open(md_path, 'w') as f:
            f.write(self._generate_markdown_report())
        
        print(f"\nReports saved to:")
        print(f"  - {json_path}")
        print(f"  - {md_path}")
    
    def _generate_markdown_report(self) -> str:
        """Generate detailed markdown report."""
        report = f"""# RAG Evaluation Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

{self._generate_summary()}

## Detailed Results

### 1. Retrieval Quality

"""
        
        # Add query-by-query results
        for query_id, result in list(self.evaluation_results.get('queries', {}).items())[:10]:
            metrics = result['metrics']
            report += f"""
#### Query: {query_id}
- **Text**: {metrics['query_text']}
- **Precision@5**: {metrics.get('precision@5', 0):.3f}
- **Recall@10**: {metrics.get('recall@10', 0):.3f}
- **MRR**: {metrics.get('mrr', 0):.3f}
- **Search Time**: {metrics.get('search_time', 0):.3f}s
"""
        
        return report


if __name__ == '__main__':
    # Run comprehensive evaluation
    evaluator = RAGEvaluator()
    results = evaluator.run_comprehensive_evaluation()
    
    # Print final grade
    print(f"\nFinal System Grade: {evaluator._calculate_grade()}")