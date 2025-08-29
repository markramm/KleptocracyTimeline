#!/usr/bin/env python3
"""
Run baseline evaluation of the RAG system.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def main():
    """Run comprehensive evaluation."""
    
    print("\n" + "="*60)
    print("RAG SYSTEM BASELINE EVALUATION")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60)
    
    try:
        # Import RAG components
        from rag.simple_rag import TimelineRAG
        from rag.evaluation.evaluator import RAGEvaluator
        from rag.evaluation.ground_truth import GroundTruthManager
        from rag.evaluation.test_queries import TEST_QUERIES, get_priority_queries
        from rag.evaluation.reports import EvaluationReportGenerator
        
        # Initialize RAG system
        print("\n1. Initializing RAG system...")
        rag = TimelineRAG(
            timeline_dir="timeline_data/events",
            use_local_embeddings=True
        )
        print(f"   ✓ Loaded {len(rag.events)} events")
        
        # Initialize ground truth manager
        print("\n2. Setting up ground truth...")
        ground_truth = GroundTruthManager(
            events_dir="timeline_data/events"
        )
        
        # Import test queries into ground truth
        ground_truth.import_from_test_queries(TEST_QUERIES)
        print(f"   ✓ Imported {len(TEST_QUERIES)} test queries")
        
        # Auto-annotate some queries based on tags/actors
        print("\n3. Auto-annotating ground truth...")
        ground_truth.auto_annotate_by_tags(
            'auto_democracy',
            'Find all events threatening democracy',
            required_tags=['democracy']
        )
        ground_truth.auto_annotate_by_tags(
            'auto_cryptocurrency', 
            'Find all cryptocurrency events',
            required_tags=['cryptocurrency']
        )
        ground_truth.auto_annotate_by_date_range(
            'auto_jan_2025',
            'Events in January 2025',
            '2025-01-01',
            '2025-01-31'
        )
        print("   ✓ Added auto-annotations")
        
        # Initialize evaluator
        print("\n4. Initializing evaluator...")
        evaluator = RAGEvaluator(
            rag_system=rag,
            ground_truth_manager=ground_truth,
            output_dir="evaluation_results"
        )
        
        # Get high-priority queries for focused evaluation
        priority_queries = get_priority_queries('high')
        print(f"   ✓ Selected {len(priority_queries)} high-priority queries")
        
        # Run evaluation components
        print("\n5. Running evaluation components...")
        print("-"*40)
        
        # Retrieval evaluation (using subset for speed)
        print("\n5.1 Evaluating retrieval quality...")
        retrieval_results = evaluator.evaluate_retrieval(
            queries=priority_queries[:20],  # Use subset for faster evaluation
            k_values=[5, 10, 20]
        )
        
        # Consistency evaluation
        print("\n5.2 Evaluating consistency...")
        consistency_results = evaluator.evaluate_consistency(
            queries=priority_queries[:10],
            num_runs=3
        )
        
        # Completeness evaluation
        print("\n5.3 Evaluating completeness...")
        completeness_results = evaluator.evaluate_completeness(
            sample_size=10
        )
        
        # Research scenarios
        print("\n5.4 Evaluating research scenarios...")
        research_results = evaluator.evaluate_research_scenarios()
        
        # Generate report
        print("\n6. Generating evaluation report...")
        report_generator = EvaluationReportGenerator(
            output_dir="evaluation_results"
        )
        
        # Combine all results
        full_results = {
            'timestamp': datetime.now().isoformat(),
            'aggregate_metrics': retrieval_results.get('aggregate_metrics', {}),
            'queries': retrieval_results.get('individual_queries', {}),
            'consistency_tests': consistency_results,
            'completeness_tests': completeness_results,
            'research_scenarios': research_results,
            'evaluation_config': {
                'total_events': len(rag.events),
                'queries_evaluated': len(priority_queries[:20]),
                'k_values': [5, 10, 20]
            }
        }
        
        # Generate reports
        output_files = report_generator.generate_report(full_results, format='all')
        
        print("   ✓ Reports generated:")
        for format_type, filepath in output_files.items():
            print(f"     - {format_type}: {filepath}")
        
        # Print summary
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        
        metrics = full_results.get('aggregate_metrics', {})
        consistency = full_results.get('consistency_tests', {})
        completeness = full_results.get('completeness_tests', {})
        
        print("\n📊 Retrieval Metrics:")
        print(f"  • Precision@5: {metrics.get('avg_precision@5', 0):.3f} (Target: >0.90)")
        print(f"  • Recall@10: {metrics.get('avg_recall@10', 0):.3f} (Target: >0.95)")
        print(f"  • F1@10: {metrics.get('avg_f1@10', 0):.3f}")
        print(f"  • NDCG@10: {metrics.get('avg_ndcg@10', 0):.3f}")
        print(f"  • MRR: {metrics.get('avg_mrr', 0):.3f}")
        
        print("\n🔄 Consistency:")
        print(f"  • Overall: {consistency.get('overall_consistency', 0):.3f} (Target: >0.99)")
        print(f"  • Perfect Match Rate: {consistency.get('perfect_consistency_rate', 0):.2%}")
        
        print("\n📈 Completeness:")
        print(f"  • Average: {completeness.get('average_completeness', 0):.3f} (Target: >0.98)")
        print(f"  • Diversity: {completeness.get('average_diversity', 0):.3f}")
        
        print("\n⚡ Performance:")
        print(f"  • Avg Response Time: {metrics.get('avg_search_time', 0):.3f}s (Target: <5.0s)")
        
        # Calculate grade
        recall_score = metrics.get('avg_recall@10', 0) * 35
        precision_score = metrics.get('avg_precision@5', 0) * 25
        consistency_score = consistency.get('overall_consistency', 0) * 20
        completeness_score = completeness.get('average_completeness', 0) * 20
        
        total_score = recall_score + precision_score + consistency_score + completeness_score
        
        if total_score >= 95:
            grade = f"A+ ({total_score:.0f}/100)"
        elif total_score >= 90:
            grade = f"A ({total_score:.0f}/100)"
        elif total_score >= 85:
            grade = f"A- ({total_score:.0f}/100)"
        elif total_score >= 80:
            grade = f"B+ ({total_score:.0f}/100)"
        elif total_score >= 75:
            grade = f"B ({total_score:.0f}/100)"
        elif total_score >= 70:
            grade = f"B- ({total_score:.0f}/100)"
        else:
            grade = f"C ({total_score:.0f}/100)"
        
        print(f"\n🎯 Overall Grade: {grade}")
        print(f"   Target Grade: A+ (95/100)")
        
        # Research scenarios summary
        scenarios = full_results.get('research_scenarios', {})
        if scenarios:
            print("\n🔬 Research Scenarios:")
            
            if 'timeline_analysis' in scenarios:
                timeline = scenarios['timeline_analysis']
                print(f"  • Timeline Analysis: {timeline.get('num_results', 0)} events")
                print(f"    Temporal Ordering: {'✓' if timeline.get('temporally_ordered') else '✗'}")
            
            if 'pattern_detection' in scenarios:
                pattern = scenarios['pattern_detection']
                print(f"  • Pattern Detection: {pattern.get('total_events', 0)} events found")
            
            if 'gap_analysis' in scenarios:
                gaps = scenarios['gap_analysis']
                print(f"  • Coverage Gaps: {gaps.get('identified_gaps', 0)} gaps identified")
        
        print("\n" + "="*60)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Save summary to JSON
        summary_path = Path("evaluation_results") / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w') as f:
            json.dump({
                'grade': grade,
                'total_score': total_score,
                'metrics': {
                    'precision@5': metrics.get('avg_precision@5', 0),
                    'recall@10': metrics.get('avg_recall@10', 0),
                    'consistency': consistency.get('overall_consistency', 0),
                    'completeness': completeness.get('average_completeness', 0),
                    'response_time': metrics.get('avg_search_time', 0)
                },
                'targets': {
                    'precision@5': 0.90,
                    'recall@10': 0.95,
                    'consistency': 0.99,
                    'completeness': 0.98,
                    'response_time': 5.0
                }
            }, f, indent=2)
        
        print(f"\n📄 Summary saved to: {summary_path}")
        
        return 0
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nPlease ensure all dependencies are installed:")
        print("  pip install sentence-transformers chromadb pyyaml numpy")
        return 1
    
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())