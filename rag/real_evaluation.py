#!/usr/bin/env python3
"""
Real Evaluation Framework for RAG System

This creates labeled test data and measures actual retrieval performance.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import sys

# Import our real RAG system
from real_rag_system import RealRAGSystem, Event


class RealEvaluator:
    """Evaluates RAG system with real metrics on real data."""
    
    def __init__(self, rag_system: RealRAGSystem):
        """Initialize evaluator with RAG system."""
        self.rag = rag_system
        self.test_queries = []
        self.create_test_dataset()
    
    def create_test_dataset(self):
        """
        Create labeled test queries based on actual events in the data.
        
        This is REAL ground truth labeling based on the actual timeline data.
        """
        print("Creating labeled test dataset...")
        
        # Build an index of events by topic for ground truth
        topic_index = defaultdict(list)
        
        for event in self.rag.events:
            # Index by key topics
            if 'schedule_f' in str(event.tags).lower() or 'schedule f' in event.title.lower():
                topic_index['schedule_f'].append(event.id)
            
            if 'fox' in event.title.lower() or 'ailes' in event.title.lower():
                topic_index['fox_news'].append(event.id)
            
            if 'cryptocurrency' in str(event.tags).lower() or 'crypto' in event.title.lower():
                topic_index['crypto'].append(event.id)
            
            if 'regulatory' in str(event.tags).lower() or 'regulation' in event.title.lower():
                topic_index['regulation'].append(event.id)
            
            if 'democracy' in str(event.tags).lower() or 'democratic' in event.title.lower():
                topic_index['democracy'].append(event.id)
            
            if 'media' in str(event.tags).lower() or 'news' in event.title.lower():
                topic_index['media'].append(event.id)
            
            if 'trump' in event.title.lower() or 'trump' in str(event.actors).lower():
                topic_index['trump'].append(event.id)
            
            if 'corruption' in str(event.tags).lower() or 'corrupt' in event.summary.lower():
                topic_index['corruption'].append(event.id)
        
        # Create test queries with known relevant documents
        self.test_queries = [
            {
                'query': 'Roger Ailes Fox News creation',
                'relevant_ids': topic_index['fox_news'][:5],  # Top fox news events
                'topic': 'media'
            },
            {
                'query': 'Schedule F federal workforce',
                'relevant_ids': topic_index['schedule_f'],
                'topic': 'civil_service'
            },
            {
                'query': 'cryptocurrency market manipulation',
                'relevant_ids': topic_index['crypto'],
                'topic': 'crypto'
            },
            {
                'query': 'regulatory capture deregulation',
                'relevant_ids': topic_index['regulation'][:10],
                'topic': 'regulation'
            },
            {
                'query': 'threats to democracy',
                'relevant_ids': topic_index['democracy'][:10],
                'topic': 'democracy'
            },
            {
                'query': 'media control propaganda',
                'relevant_ids': topic_index['media'][:10],
                'topic': 'media'
            },
            {
                'query': 'Trump executive orders',
                'relevant_ids': [eid for eid in topic_index['trump'] 
                                if 'executive' in eid.lower() or 'order' in eid.lower()][:10],
                'topic': 'executive_power'
            },
            {
                'query': 'corruption investigation journalism',
                'relevant_ids': topic_index['corruption'][:10],
                'topic': 'corruption'
            }
        ]
        
        # Add some specific known-item searches
        specific_queries = [
            {
                'query': 'Lewis Powell memo 1971',
                'relevant_ids': ['1971-08-23--powell-memo'],
                'topic': 'historical'
            },
            {
                'query': 'January 6 Capitol attack',
                'relevant_ids': [eid for eid in [e.id for e in self.rag.events] 
                                if 'january-6' in eid or 'capitol' in eid.lower()],
                'topic': 'insurrection'
            }
        ]
        
        self.test_queries.extend(specific_queries)
        
        # Filter out queries with no relevant documents
        self.test_queries = [q for q in self.test_queries if len(q['relevant_ids']) > 0]
        
        print(f"Created {len(self.test_queries)} test queries with labeled relevance")
        for q in self.test_queries:
            print(f"  - '{q['query']}': {len(q['relevant_ids'])} relevant docs")
    
    def evaluate_retrieval(self, k_values: List[int] = [1, 3, 5, 10]) -> Dict[str, Any]:
        """
        Run evaluation and calculate real metrics.
        
        Metrics calculated:
        - Precision@K: What percentage of retrieved docs are relevant?
        - Recall@K: What percentage of relevant docs were retrieved?
        - MRR: Mean Reciprocal Rank of first relevant result
        - MAP: Mean Average Precision
        - NDCG: Normalized Discounted Cumulative Gain
        """
        print(f"\nEvaluating on {len(self.test_queries)} queries...")
        
        metrics = defaultdict(list)
        detailed_results = []
        
        for i, test_case in enumerate(self.test_queries):
            query = test_case['query']
            relevant_ids = set(test_case['relevant_ids'])
            
            print(f"\n[{i+1}/{len(self.test_queries)}] Query: '{query}'")
            print(f"  Ground truth: {len(relevant_ids)} relevant docs")
            
            # Run actual retrieval
            start_time = time.time()
            results = self.rag.search(query, top_k=max(k_values))
            retrieval_time = time.time() - start_time
            
            retrieved_ids = [r['event']['id'] for r in results]
            
            # Calculate metrics for different K values
            query_metrics = {'query': query, 'topic': test_case['topic']}
            
            for k in k_values:
                retrieved_k = retrieved_ids[:k]
                relevant_retrieved = [rid for rid in retrieved_k if rid in relevant_ids]
                
                # Precision@K
                precision_k = len(relevant_retrieved) / k if k > 0 else 0
                metrics[f'precision@{k}'].append(precision_k)
                query_metrics[f'precision@{k}'] = precision_k
                
                # Recall@K
                recall_k = len(relevant_retrieved) / len(relevant_ids) if len(relevant_ids) > 0 else 0
                metrics[f'recall@{k}'].append(recall_k)
                query_metrics[f'recall@{k}'] = recall_k
                
                # F1@K
                f1_k = 2 * (precision_k * recall_k) / (precision_k + recall_k) if (precision_k + recall_k) > 0 else 0
                metrics[f'f1@{k}'].append(f1_k)
                query_metrics[f'f1@{k}'] = f1_k
            
            # Mean Reciprocal Rank (MRR)
            mrr = 0
            for rank, rid in enumerate(retrieved_ids, 1):
                if rid in relevant_ids:
                    mrr = 1 / rank
                    break
            metrics['mrr'].append(mrr)
            query_metrics['mrr'] = mrr
            
            # Average Precision
            ap = self._calculate_average_precision(retrieved_ids, relevant_ids)
            metrics['map'].append(ap)
            query_metrics['ap'] = ap
            
            # NDCG
            ndcg = self._calculate_ndcg(results, relevant_ids)
            metrics['ndcg'].append(ndcg)
            query_metrics['ndcg'] = ndcg
            
            # Response time
            metrics['response_time'].append(retrieval_time)
            query_metrics['response_time'] = retrieval_time
            
            detailed_results.append(query_metrics)
            
            # Print immediate results
            print(f"  Results: P@5={query_metrics['precision@5']:.2f}, "
                  f"R@5={query_metrics['recall@5']:.2f}, "
                  f"MRR={mrr:.2f}, Time={retrieval_time:.3f}s")
        
        # Calculate aggregate metrics
        aggregate_metrics = {}
        for metric_name, values in metrics.items():
            if len(values) > 0:
                aggregate_metrics[metric_name] = {
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'values': values
                }
        
        return {
            'aggregate': aggregate_metrics,
            'detailed': detailed_results,
            'num_queries': len(self.test_queries),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _calculate_average_precision(self, retrieved_ids: List[str], relevant_ids: set) -> float:
        """Calculate Average Precision for a single query."""
        if len(relevant_ids) == 0:
            return 0
        
        precisions = []
        relevant_found = 0
        
        for i, rid in enumerate(retrieved_ids, 1):
            if rid in relevant_ids:
                relevant_found += 1
                precisions.append(relevant_found / i)
        
        if len(precisions) == 0:
            return 0
        
        return sum(precisions) / len(relevant_ids)
    
    def _calculate_ndcg(self, results: List[Dict], relevant_ids: set, k: int = 10) -> float:
        """Calculate Normalized Discounted Cumulative Gain."""
        # Use relevance scores as gains
        dcg = 0
        for i, result in enumerate(results[:k]):
            if result['event']['id'] in relevant_ids:
                # Use the actual relevance score from the system
                gain = result['relevance_score']
                discount = 1 / (i + 2)  # i+2 because log2(1) = 0
                dcg += gain * discount
        
        # Calculate ideal DCG (all relevant docs at top with perfect scores)
        ideal_gains = sorted([1.0] * min(len(relevant_ids), k), reverse=True)
        idcg = sum(gain / (i + 2) for i, gain in enumerate(ideal_gains))
        
        if idcg == 0:
            return 0
        
        return dcg / idcg
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable evaluation report."""
        lines = []
        lines.append("="*60)
        lines.append("RAG SYSTEM EVALUATION REPORT")
        lines.append("="*60)
        lines.append(f"Timestamp: {results['timestamp']}")
        lines.append(f"Queries Evaluated: {results['num_queries']}")
        lines.append("")
        
        lines.append("AGGREGATE METRICS")
        lines.append("-"*40)
        
        # Key metrics to highlight
        agg = results['aggregate']
        
        # Precision and Recall
        for k in [1, 3, 5, 10]:
            if f'precision@{k}' in agg:
                p = agg[f'precision@{k}']['mean']
                r = agg[f'recall@{k}']['mean']
                f1 = agg[f'f1@{k}']['mean']
                lines.append(f"@{k:2d}: P={p:.3f}, R={r:.3f}, F1={f1:.3f}")
        
        lines.append("")
        
        # Other metrics
        if 'mrr' in agg:
            lines.append(f"MRR (Mean Reciprocal Rank): {agg['mrr']['mean']:.3f}")
        if 'map' in agg:
            lines.append(f"MAP (Mean Average Precision): {agg['map']['mean']:.3f}")
        if 'ndcg' in agg:
            lines.append(f"NDCG (Normalized DCG): {agg['ndcg']['mean']:.3f}")
        if 'response_time' in agg:
            lines.append(f"Avg Response Time: {agg['response_time']['mean']:.3f}s")
        
        lines.append("")
        lines.append("PERFORMANCE BY TOPIC")
        lines.append("-"*40)
        
        # Group results by topic
        topic_metrics = defaultdict(list)
        for detail in results['detailed']:
            topic = detail['topic']
            topic_metrics[topic].append(detail)
        
        for topic, queries in topic_metrics.items():
            avg_p5 = sum(q['precision@5'] for q in queries) / len(queries)
            avg_r5 = sum(q['recall@5'] for q in queries) / len(queries)
            lines.append(f"{topic:15s}: P@5={avg_p5:.3f}, R@5={avg_r5:.3f} ({len(queries)} queries)")
        
        lines.append("")
        lines.append("SYSTEM QUALITY ASSESSMENT")
        lines.append("-"*40)
        
        # Calculate overall quality score
        quality_score = (
            agg['precision@5']['mean'] * 0.25 +
            agg['recall@10']['mean'] * 0.25 +
            agg['mrr']['mean'] * 0.25 +
            agg['map']['mean'] * 0.25
        )
        
        lines.append(f"Quality Score: {quality_score:.3f}")
        
        if quality_score >= 0.8:
            grade = "A (Excellent)"
        elif quality_score >= 0.7:
            grade = "B (Good)"
        elif quality_score >= 0.6:
            grade = "C (Adequate)"
        else:
            grade = "D (Needs Improvement)"
        
        lines.append(f"Grade: {grade}")
        
        return "\n".join(lines)


def main():
    """Run real evaluation."""
    print("="*60)
    print("REAL RAG EVALUATION - Measuring Actual Performance")
    print("="*60)
    
    # Initialize RAG system
    print("\nInitializing RAG system...")
    rag = RealRAGSystem('../timeline_data/timeline_complete.json')
    
    # Create evaluator
    evaluator = RealEvaluator(rag)
    
    # Run evaluation
    print("\n" + "="*60)
    print("RUNNING EVALUATION")
    print("="*60)
    
    results = evaluator.evaluate_retrieval(k_values=[1, 3, 5, 10])
    
    # Generate report
    report = evaluator.generate_report(results)
    print("\n" + report)
    
    # Save results
    output_dir = Path("evaluation_results")
    output_dir.mkdir(exist_ok=True)
    
    # Save JSON results
    json_path = output_dir / "real_evaluation_results.json"
    with open(json_path, 'w') as f:
        # Convert values lists to stats only for cleaner JSON
        clean_results = {
            'aggregate': {k: {sk: sv for sk, sv in v.items() if sk != 'values'} 
                         for k, v in results['aggregate'].items()},
            'detailed': results['detailed'],
            'num_queries': results['num_queries'],
            'timestamp': results['timestamp']
        }
        json.dump(clean_results, f, indent=2)
    
    print(f"\nResults saved to: {json_path}")
    
    # Save report
    report_path = output_dir / "real_evaluation_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()