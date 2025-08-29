#!/usr/bin/env python3
"""
Quick baseline evaluation of the RAG system without heavy dependencies.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def simple_search_test(rag, query):
    """Run a simple search test."""
    try:
        results = rag.search(query, n_results=10)
        return len(results), results
    except Exception as e:
        print(f"Error searching: {e}")
        return 0, []

def main():
    """Run simplified evaluation."""
    
    print("\n" + "="*60)
    print("RAG SYSTEM QUICK EVALUATION")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60)
    
    try:
        # Import RAG components
        from rag.simple_rag import TimelineRAG
        
        # Initialize RAG system
        print("\n1. Initializing RAG system...")
        rag = TimelineRAG(
            timeline_dir="timeline_data/events",
            use_local_embeddings=True
        )
        print(f"   ✓ Loaded {len(rag.events)} events")
        print(f"   ✓ Collection has {rag.collection.count()} indexed events")
        
        # Define test queries
        test_queries = [
            {
                'query': 'What events involve cryptocurrency and Trump?',
                'expected_keywords': ['cryptocurrency', 'Trump', 'memecoin'],
            },
            {
                'query': 'What happened with Epstein files in 2025?',
                'expected_keywords': ['Epstein', 'files', '2025'],
            },
            {
                'query': 'Show me events about regulatory capture',
                'expected_keywords': ['regulatory', 'capture'],
            },
            {
                'query': 'What executive orders were signed in January 2025?',
                'expected_keywords': ['executive', 'order', 'January', '2025'],
            },
            {
                'query': 'Events about Schedule F and federal workforce',
                'expected_keywords': ['Schedule F', 'federal', 'workforce'],
            }
        ]
        
        print("\n2. Running test queries...")
        print("-"*40)
        
        total_results = 0
        query_results = []
        
        for i, test in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {test['query']}")
            
            import time
            start_time = time.time()
            num_results, results = simple_search_test(rag, test['query'])
            search_time = time.time() - start_time
            
            print(f"  • Results: {num_results}")
            print(f"  • Time: {search_time:.3f}s")
            
            if results:
                # Show top 3 results
                print("  • Top results:")
                for j, result in enumerate(results[:3], 1):
                    event = result['event']
                    score = result['score']
                    print(f"    {j}. {event.get('title', 'No title')} (score: {score:.3f})")
                    print(f"       Date: {event.get('date', 'Unknown')}")
                
                # Check for expected keywords in results
                found_keywords = []
                for keyword in test['expected_keywords']:
                    for result in results[:5]:
                        event_text = str(result['event'])
                        if keyword.lower() in event_text.lower():
                            found_keywords.append(keyword)
                            break
                
                relevance = len(found_keywords) / len(test['expected_keywords'])
                print(f"  • Keyword relevance: {relevance:.1%} ({len(found_keywords)}/{len(test['expected_keywords'])})")
            
            total_results += num_results
            query_results.append({
                'query': test['query'],
                'num_results': num_results,
                'search_time': search_time,
                'relevance': relevance if results else 0
            })
        
        # Test pattern analysis
        print("\n3. Testing pattern analysis...")
        print("-"*40)
        
        patterns = rag.find_patterns(tag='cryptocurrency')
        print(f"  • Cryptocurrency events: {patterns['total_events']}")
        print(f"  • Date range: {patterns['date_range']['earliest']} to {patterns['date_range']['latest']}")
        print(f"  • Top actors: {list(patterns['top_actors'].keys())[:5] if patterns['top_actors'] else 'None'}")
        
        # Test question answering
        print("\n4. Testing question answering...")
        print("-"*40)
        
        question = "What are the implications of the Trump cryptocurrency launches?"
        answer_result = rag.answer_question(question, max_events=5, use_llm=False)
        print(f"  • Question: {question}")
        print(f"  • Answer: {answer_result['answer'][:200]}...")
        print(f"  • Events used: {len(answer_result['events'])}")
        print(f"  • Sources found: {len(answer_result['sources'])}")
        
        # Calculate basic metrics
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        
        avg_results = sum(q['num_results'] for q in query_results) / len(query_results)
        avg_time = sum(q['search_time'] for q in query_results) / len(query_results)
        avg_relevance = sum(q['relevance'] for q in query_results) / len(query_results)
        
        print(f"\n📊 Basic Metrics:")
        print(f"  • Total events in dataset: {len(rag.events)}")
        print(f"  • Indexed events: {rag.collection.count()}")
        print(f"  • Queries tested: {len(test_queries)}")
        print(f"  • Avg results per query: {avg_results:.1f}")
        print(f"  • Avg search time: {avg_time:.3f}s")
        print(f"  • Avg keyword relevance: {avg_relevance:.1%}")
        
        # Estimate performance
        if avg_time < 0.5:
            time_grade = "Excellent"
        elif avg_time < 1.0:
            time_grade = "Good"
        elif avg_time < 5.0:
            time_grade = "Acceptable"
        else:
            time_grade = "Needs Improvement"
        
        if avg_relevance > 0.8:
            relevance_grade = "Excellent"
        elif avg_relevance > 0.6:
            relevance_grade = "Good"
        elif avg_relevance > 0.4:
            relevance_grade = "Acceptable"
        else:
            relevance_grade = "Needs Improvement"
        
        print(f"\n🎯 Performance Assessment:")
        print(f"  • Response Time: {time_grade}")
        print(f"  • Result Relevance: {relevance_grade}")
        
        # Estimated grade (simplified)
        if avg_relevance > 0.7 and avg_time < 1.0:
            grade = "B+ to A-"
        elif avg_relevance > 0.5 and avg_time < 5.0:
            grade = "B- to B"
        else:
            grade = "C to B-"
        
        print(f"  • Estimated Grade: {grade} (simplified assessment)")
        print(f"  • Note: Full evaluation would include precision, recall, and consistency metrics")
        
        print("\n" + "="*60)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Save results
        results_file = Path("evaluation_results") / f"quick_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_events': len(rag.events),
                'indexed_events': rag.collection.count(),
                'query_results': query_results,
                'metrics': {
                    'avg_results': avg_results,
                    'avg_time': avg_time,
                    'avg_relevance': avg_relevance
                },
                'assessment': {
                    'time_grade': time_grade,
                    'relevance_grade': relevance_grade,
                    'estimated_grade': grade
                }
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")
        
        return 0
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nPlease ensure dependencies are installed:")
        print("  pip install sentence-transformers chromadb pyyaml")
        return 1
    
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())