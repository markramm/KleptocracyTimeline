#!/usr/bin/env python3
"""
Test suite for RAG API

Tests API endpoints and functionality.
"""

import requests
import json
import time
from typing import Dict, List, Any


class RAGAPITester:
    """Test client for RAG API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize test client."""
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_status(self) -> bool:
        """Test status endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/status")
            response.raise_for_status()
            
            data = response.json()
            print("✓ Status endpoint working")
            print(f"  - Total events: {data['total_events']}")
            print(f"  - Systems available: {data['systems_available']}")
            print(f"  - Total searches: {data['total_searches']}")
            return True
        except Exception as e:
            print(f"✗ Status endpoint failed: {e}")
            return False
    
    def test_search(self) -> bool:
        """Test search endpoint."""
        test_queries = [
            {
                "query": "cryptocurrency Trump",
                "top_k": 5,
                "system": "advanced"
            },
            {
                "query": "Schedule F implementation",
                "top_k": 10,
                "system": "optimized"
            },
            {
                "query": "events in January 2025",
                "top_k": 5,
                "system": "advanced"
            }
        ]
        
        all_passed = True
        
        for test_query in test_queries:
            try:
                response = self.session.post(
                    f"{self.base_url}/search",
                    json=test_query
                )
                response.raise_for_status()
                
                data = response.json()
                print(f"✓ Search: '{test_query['query'][:30]}...'")
                print(f"  - Results: {data['total_results']}")
                print(f"  - Time: {data['search_time']:.3f}s")
                print(f"  - System: {data['system_used']}")
                
                # Test cache
                response2 = self.session.post(
                    f"{self.base_url}/search",
                    json=test_query
                )
                data2 = response2.json()
                
                if data2.get('metadata', {}).get('cache_hit'):
                    print(f"  - Cache hit confirmed")
                
            except Exception as e:
                print(f"✗ Search failed for '{test_query['query']}': {e}")
                all_passed = False
        
        return all_passed
    
    def test_feedback(self) -> bool:
        """Test feedback endpoint."""
        try:
            feedback = {
                "query": "test query",
                "event_id": "test-event-id",
                "relevant": True,
                "comment": "This was helpful"
            }
            
            response = self.session.post(
                f"{self.base_url}/feedback",
                json=feedback
            )
            response.raise_for_status()
            
            print("✓ Feedback endpoint working")
            return True
        except Exception as e:
            print(f"✗ Feedback endpoint failed: {e}")
            return False
    
    def test_metrics(self) -> bool:
        """Test metrics endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/metrics")
            response.raise_for_status()
            
            data = response.json()
            print("✓ Metrics endpoint working")
            print(f"  - Total searches: {data['total_searches']}")
            print(f"  - Average search time: {data['average_search_time']:.3f}s")
            return True
        except Exception as e:
            print(f"✗ Metrics endpoint failed: {e}")
            return False
    
    def test_event_retrieval(self) -> bool:
        """Test event retrieval endpoint."""
        try:
            # First get an event ID from search
            search_response = self.session.post(
                f"{self.base_url}/search",
                json={"query": "Trump", "top_k": 1}
            )
            search_data = search_response.json()
            
            if search_data['results']:
                event_id = search_data['results'][0]['id']
                
                # Get the event
                response = self.session.get(f"{self.base_url}/events/{event_id}")
                response.raise_for_status()
                
                event_data = response.json()
                print(f"✓ Event retrieval working")
                print(f"  - Event: {event_data['title'][:50]}...")
                return True
            else:
                print("✗ No events found for test")
                return False
                
        except Exception as e:
            print(f"✗ Event retrieval failed: {e}")
            return False
    
    def test_cache_operations(self) -> bool:
        """Test cache operations."""
        try:
            # Clear cache
            response = self.session.post(f"{self.base_url}/cache/clear")
            response.raise_for_status()
            
            print("✓ Cache clear working")
            
            # Verify cache was cleared by checking status
            status = self.session.get(f"{self.base_url}/status").json()
            print(f"  - Cache size after clear: {status['cache_size']}")
            
            return True
        except Exception as e:
            print(f"✗ Cache operations failed: {e}")
            return False
    
    def run_load_test(self, num_requests: int = 50):
        """Run a simple load test."""
        print(f"\nRunning load test with {num_requests} requests...")
        
        queries = [
            "cryptocurrency events",
            "Schedule F",
            "democracy threats",
            "Trump administration",
            "regulatory capture"
        ]
        
        times = []
        errors = 0
        
        for i in range(num_requests):
            query = queries[i % len(queries)]
            
            try:
                start = time.time()
                response = self.session.post(
                    f"{self.base_url}/search",
                    json={"query": query, "top_k": 5},
                    params={"use_cache": False}  # Disable cache for load test
                )
                response.raise_for_status()
                elapsed = time.time() - start
                times.append(elapsed)
                
                if (i + 1) % 10 == 0:
                    print(f"  Completed {i + 1}/{num_requests} requests")
                    
            except Exception as e:
                errors += 1
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"\nLoad test results:")
            print(f"  - Successful: {len(times)}/{num_requests}")
            print(f"  - Errors: {errors}")
            print(f"  - Avg time: {avg_time:.3f}s")
            print(f"  - Min time: {min_time:.3f}s")
            print(f"  - Max time: {max_time:.3f}s")
    
    def run_all_tests(self):
        """Run all tests."""
        print("="*50)
        print("RAG API Test Suite")
        print("="*50)
        
        tests = [
            ("Status", self.test_status),
            ("Search", self.test_search),
            ("Feedback", self.test_feedback),
            ("Metrics", self.test_metrics),
            ("Event Retrieval", self.test_event_retrieval),
            ("Cache Operations", self.test_cache_operations)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\nTesting {test_name}...")
            result = test_func()
            results.append((test_name, result))
            time.sleep(0.5)  # Small delay between tests
        
        # Summary
        print("\n" + "="*50)
        print("Test Summary")
        print("="*50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{test_name:20} {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        # Optional load test
        if passed == total:
            print("\nAll tests passed! Running load test...")
            self.run_load_test(20)


def main():
    """Main test execution."""
    import sys
    
    # Check if API is running
    base_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        response.raise_for_status()
        print(f"API is running at {base_url}")
    except:
        print(f"Error: API is not running at {base_url}")
        print("Please start the API first with: python rag_production_api.py")
        sys.exit(1)
    
    # Run tests
    tester = RAGAPITester(base_url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()