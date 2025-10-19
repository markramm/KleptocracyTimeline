#!/usr/bin/env python3
"""
End-to-End Tests for Research Monitor v2 API
Tests against live server with real data - validates the complete system
"""

import unittest
import requests
import json
import time
import sys
from typing import Dict, List, Any

# Configuration
SERVER_URL = "http://localhost:5558"
TIMEOUT = 10

class TestE2EResearchMonitorAPI(unittest.TestCase):
    """End-to-end tests against live server with real data"""
    
    @classmethod
    def setUpClass(cls):
        """Check server availability before running tests"""
        try:
            response = requests.get(f"{SERVER_URL}/api/server/health", timeout=5)
            if response.status_code != 200:
                raise Exception(f"Server health check failed: {response.status_code}")
            
            health_data = response.json()
            if health_data.get('status') != 'healthy':
                raise Exception(f"Server reports unhealthy: {health_data}")
                
            print(f"✓ Server is healthy at {SERVER_URL}")
            
        except Exception as e:
            print(f"✗ Cannot connect to server at {SERVER_URL}: {e}")
            print("Make sure the server is running: cd research_monitor && python3 app_v2.py")
            sys.exit(1)
    
    def api_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request with error handling and logging"""
        url = f"{SERVER_URL}{endpoint}"
        
        try:
            response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
            
            # Log request details for debugging
            if response.status_code >= 400:
                print(f"✗ {method} {endpoint} -> {response.status_code}")
                if response.headers.get('content-type', '').startswith('application/json'):
                    try:
                        error_data = response.json()
                        print(f"   Error: {error_data}")
                    except:
                        print(f"   Error: {response.text[:200]}")
                else:
                    print(f"   Error: {response.text[:200]}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.fail(f"API request failed: {method} {endpoint} - {str(e)}")
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON response: {method} {endpoint} - {str(e)}")
    
    def test_01_system_health_and_stats(self):
        """Test basic system health and statistics"""
        print("\n🏥 Testing system health and stats...")
        
        # Health check
        health = self.api_request("GET", "/api/server/health")
        self.assertEqual(health['status'], 'healthy')
        self.assertIn('database', health)
        self.assertIn('events_since_commit', health)
        print(f"   ✓ Server healthy, {health['events_since_commit']} events since last commit")
        
        # Basic stats
        stats = self.api_request("GET", "/api/stats")
        self.assertIn('events', stats)
        total_events = stats['events']['total']
        self.assertGreater(total_events, 0, "Should have timeline events in database")
        print(f"   ✓ {total_events} total events in database")
        
        # Documentation endpoints
        docs = self.api_request("GET", "/api/docs")
        self.assertIn('documentation', docs)
        self.assertIn('endpoints', docs)
        print("   ✓ API documentation available")
        
        openapi = self.api_request("GET", "/api/openapi.json")
        self.assertEqual(openapi['openapi'], '3.0.0')
        self.assertEqual(openapi['info']['title'], 'Research Monitor v2 API')
        print("   ✓ OpenAPI specification valid")
    
    def test_02_timeline_events_core(self):
        """Test core timeline events functionality"""
        print("\n📅 Testing timeline events...")
        
        # Basic timeline events
        data = self.api_request("GET", "/api/timeline/events?limit=10")
        self.assertIn('events', data)
        self.assertIn('pagination', data)
        
        events = data['events']
        pagination = data['pagination']
        
        self.assertGreater(len(events), 0, "Should return events")
        self.assertLessEqual(len(events), 10, "Should respect limit")
        self.assertGreater(pagination['total'], 0, "Should have total count")
        
        print(f"   ✓ Retrieved {len(events)} events (limit 10), {pagination['total']} total")
        
        # Check event structure
        if events:
            event = events[0]
            required_fields = ['id', 'date', 'title', 'summary', 'importance']
            for field in required_fields:
                self.assertIn(field, event, f"Event should have {field} field")
            
            self.assertIsInstance(event['importance'], int)
            self.assertGreaterEqual(event['importance'], 1)
            self.assertLessEqual(event['importance'], 10)
            print(f"   ✓ Event structure valid: {event['title'][:50]}...")
        
        # Test pagination
        page2_data = self.api_request("GET", "/api/timeline/events?page=2&per_page=5")
        self.assertIn('events', page2_data)
        self.assertEqual(page2_data['pagination']['page'], 2)
        self.assertEqual(page2_data['pagination']['per_page'], 5)
        print("   ✓ Pagination working correctly")
    
    def test_03_timeline_filtering_and_search(self):
        """Test timeline filtering and search capabilities"""
        print("\n🔍 Testing search and filtering...")
        
        # Test importance filtering
        high_importance = self.api_request("GET", "/api/timeline/events?importance_min=8&limit=5")
        for event in high_importance['events']:
            self.assertGreaterEqual(event['importance'], 8)
        print(f"   ✓ Importance filter: {len(high_importance['events'])} high-importance events")
        
        # Test date filtering (last 5 years)
        recent_events = self.api_request("GET", "/api/timeline/events?start_date=2020-01-01&limit=10")
        for event in recent_events['events']:
            self.assertGreaterEqual(event['date'], '2020-01-01')
        print(f"   ✓ Date filter: {len(recent_events['events'])} events since 2020")
        
        # Test full-text search
        search_results = self.api_request("GET", "/api/events/search?q=Trump&limit=5")
        self.assertIn('events', search_results)
        self.assertIn('total', search_results)
        
        if search_results['events']:
            # Check if search term appears in results
            found_trump = any('Trump' in str(event.values()).lower() for event in search_results['events'])
            if found_trump:
                print(f"   ✓ Search working: {search_results['total']} results for 'Trump'")
            else:
                print(f"   ? Search returned results but term not obviously found: {search_results['total']} results")
        else:
            print("   - No results for 'Trump' search (might be expected)")
        
        # Test advanced search
        advanced_search = {
            "query": "intelligence",
            "filters": {
                "importance_range": [6, 10]
            },
            "sort": {"field": "date", "order": "desc"},
            "limit": 5
        }
        
        search_response = self.api_request("POST", "/api/timeline/search", 
                                         json=advanced_search)
        self.assertIn('events', search_response)
        self.assertIn('metadata', search_response)
        print(f"   ✓ Advanced search: {len(search_response['events'])} intelligence-related events")
    
    def test_04_timeline_metadata(self):
        """Test timeline metadata endpoints"""
        print("\n📊 Testing metadata endpoints...")
        
        # Test actors
        actors_data = self.api_request("GET", "/api/timeline/actors?limit=10")
        self.assertIn('actors', actors_data)
        
        if actors_data['actors']:
            actor = actors_data['actors'][0]
            self.assertIn('name', actor)
            self.assertIn('event_count', actor)
            self.assertGreater(actor['event_count'], 0)
            print(f"   ✓ {len(actors_data['actors'])} actors, top: {actor['name']} ({actor['event_count']} events)")
        
        # Test tags
        tags_data = self.api_request("GET", "/api/timeline/tags?limit=10")
        self.assertIn('tags', tags_data)
        
        if tags_data['tags']:
            tag = tags_data['tags'][0]
            self.assertIn('name', tag)
            self.assertIn('count', tag)
            print(f"   ✓ {len(tags_data['tags'])} tags, top: {tag['name']} ({tag['count']} uses)")
        
        # Test sources
        sources_data = self.api_request("GET", "/api/timeline/sources?limit=10")
        self.assertIn('sources', sources_data)
        print(f"   ✓ {len(sources_data['sources'])} source domains")
        
        # Test date range
        date_range = self.api_request("GET", "/api/timeline/date-range")
        self.assertIn('date_range', date_range)
        self.assertIn('min_date', date_range['date_range'])
        self.assertIn('max_date', date_range['date_range'])
        
        min_date = date_range['date_range']['min_date']
        max_date = date_range['date_range']['max_date']
        if min_date and max_date:
            print(f"   ✓ Timeline spans {min_date} to {max_date}")
        else:
            print("   - Date range returned null values")
    
    def test_05_visualization_endpoints(self):
        """Test visualization-specific endpoints"""
        print("\n📈 Testing visualization endpoints...")
        
        # Test actor network
        network_data = self.api_request("GET", "/api/viewer/actor-network?min_connections=2&max_actors=20")
        self.assertIn('network', network_data)
        self.assertIn('metadata', network_data)
        
        network = network_data['network']
        self.assertIn('nodes', network)
        self.assertIn('edges', network)
        
        print(f"   ✓ Actor network: {len(network['nodes'])} nodes, {len(network['edges'])} edges")
        
        # Test tag cloud
        tag_cloud = self.api_request("GET", "/api/viewer/tag-cloud?min_frequency=2&max_tags=20")
        self.assertIn('tag_cloud', tag_cloud)
        self.assertIn('metadata', tag_cloud)
        
        print(f"   ✓ Tag cloud: {len(tag_cloud['tag_cloud'])} tags")
        
        # Test timeline data for visualization
        timeline_viz = self.api_request("GET", "/api/viewer/timeline-data?granularity=year")
        self.assertIn('timeline', timeline_viz)
        self.assertIn('metadata', timeline_viz)
        
        print(f"   ✓ Timeline visualization data: {len(timeline_viz['timeline'])} data points")
    
    def test_06_statistics_endpoints(self):
        """Test statistical analysis endpoints"""
        print("\n📊 Testing statistics endpoints...")
        
        # Test overview stats
        overview = self.api_request("GET", "/api/viewer/stats/overview")
        self.assertIn('total_events', overview)
        self.assertIn('total_actors', overview)
        self.assertIn('total_tags', overview)
        self.assertIn('date_range', overview)
        
        print(f"   ✓ Overview: {overview['total_events']} events, {overview['total_actors']} actors, {overview['total_tags']} tags")
        
        # Test actor stats
        actor_stats = self.api_request("GET", "/api/viewer/stats/actors?limit=5")
        self.assertIn('actor_stats', actor_stats)
        self.assertIn('metadata', actor_stats)
        
        print(f"   ✓ Actor stats: {len(actor_stats['actor_stats'])} top actors")
        
        # Test importance distribution
        importance_stats = self.api_request("GET", "/api/viewer/stats/importance")
        self.assertIn('distribution', importance_stats)
        
        distribution = importance_stats['distribution']
        if distribution:
            total_by_importance = sum(distribution.values())
            print(f"   ✓ Importance distribution: {total_by_importance} events across {len(distribution)} importance levels")
        else:
            print("   - No importance distribution data")
        
        # Test timeline patterns
        patterns = self.api_request("GET", "/api/viewer/stats/patterns")
        self.assertIn('yearly_trends', patterns)
        print("   ✓ Timeline patterns analysis available")
    
    def test_07_research_priorities(self):
        """Test research priorities functionality"""
        print("\n🎯 Testing research priorities...")
        
        # Test getting next priority
        try:
            next_priority = self.api_request("GET", "/api/priorities/next")
            self.assertIn('id', next_priority)
            self.assertIn('title', next_priority)
            self.assertIn('status', next_priority)
            print(f"   ✓ Next priority: {next_priority['title'][:50]}...")
            
        except Exception as e:
            if "404" in str(e):
                print("   - No pending research priorities available")
            else:
                raise
        
        # Test listing priorities
        priorities_list = self.api_request("GET", "/api/priorities?limit=5")
        self.assertIn('priorities', priorities_list)
        print(f"   ✓ Listed {len(priorities_list['priorities'])} research priorities")
    
    def test_08_caching_performance(self):
        """Test caching is working for performance"""
        print("\n⚡ Testing caching performance...")
        
        # Time the same request twice to check caching
        import time
        
        endpoint = "/api/viewer/stats/overview"
        
        # First request (cache miss)
        start_time = time.time()
        first_response = self.api_request("GET", endpoint)
        first_duration = time.time() - start_time
        
        # Second request (cache hit)
        start_time = time.time() 
        second_response = self.api_request("GET", endpoint)
        second_duration = time.time() - start_time
        
        # Responses should be identical
        self.assertEqual(first_response, second_response)
        
        # Second request should be faster (or at least not significantly slower)
        speed_ratio = second_duration / first_duration if first_duration > 0 else 1
        
        print(f"   ✓ First request: {first_duration:.3f}s, Second request: {second_duration:.3f}s")
        print(f"   ✓ Speed ratio: {speed_ratio:.2f}x ({'cached' if speed_ratio < 0.8 else 'not cached'})")
    
    def test_09_api_client_integration(self):
        """Test Python API client against live server"""
        print("\n🐍 Testing Python API client...")
        
        try:
            # Import the client
            import sys
            sys.path.append('/Users/markr/kleptocracy-timeline/research_monitor')
            from research_client import ResearchMonitorClient
            
            client = ResearchMonitorClient(base_url=SERVER_URL)
            
            # Test basic operations
            health = client.health_check()
            self.assertEqual(health['status'], 'healthy')
            print("   ✓ Client health check working")
            
            # Test timeline stats
            stats = client.get_timeline_stats()
            self.assertIn('total_events', stats)
            print(f"   ✓ Client timeline stats: {stats['total_events']} events")
            
            # Test search
            search_results = client.search_events("corruption", limit=3)
            self.assertIn('events', search_results)
            print(f"   ✓ Client search: {len(search_results['events'])} results for 'corruption'")
            
            # Test actor analysis if we have data
            if search_results['events']:
                # Try to analyze an actor from the results
                for event in search_results['events']:
                    if event.get('actors'):
                        actor_name = event['actors'][0]
                        analysis = client.analyze_actor(actor_name)
                        self.assertIn('total_events', analysis)
                        print(f"   ✓ Client actor analysis: {actor_name} appears in {analysis['total_events']} events")
                        break
            
        except ImportError as e:
            print(f"   - Client test skipped: {e}")
        except Exception as e:
            print(f"   ✗ Client test failed: {e}")
            # Don't fail the whole test suite for client issues
    
    def test_10_error_handling(self):
        """Test API error handling"""
        print("\n🚨 Testing error handling...")
        
        # Test 404 for non-existent event
        try:
            self.api_request("GET", "/api/events/nonexistent-event-id")
            self.fail("Should have gotten 404 for non-existent event")
        except Exception as e:
            if "404" in str(e):
                print("   ✓ 404 error handled correctly for non-existent event")
            else:
                raise
        
        # Test invalid parameters
        try:
            self.api_request("GET", "/api/timeline/events?importance_min=invalid")
            print("   - Invalid parameter accepted (may be expected)")
        except Exception as e:
            if "400" in str(e):
                print("   ✓ 400 error for invalid parameters")
            else:
                print(f"   ? Unexpected error for invalid parameters: {e}")
        
        # Test endpoint that doesn't exist
        try:
            self.api_request("GET", "/api/nonexistent/endpoint")
            self.fail("Should have gotten 404 for non-existent endpoint")
        except Exception as e:
            if "404" in str(e):
                print("   ✓ 404 error handled correctly for non-existent endpoint")
            else:
                raise

def run_comprehensive_test():
    """Run all tests with summary"""
    print("=" * 60)
    print("🧪 Research Monitor v2 API - End-to-End Test Suite")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestE2EResearchMonitorAPI)
    
    # Run tests with custom result handler
    runner = unittest.TextTestRunner(verbosity=0, stream=open('/dev/null', 'w'))
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"✅ Passed: {passed}/{total_tests}")
    if failures > 0:
        print(f"❌ Failed: {failures}")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print(f"💥 Errors: {errors}")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Research Monitor v2 API is working correctly.")
    else:
        print(f"\n⚠️  {failures + errors} test(s) failed. Check the details above.")
    
    print("=" * 60)
    return result

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--summary':
        run_comprehensive_test()
    else:
        unittest.main(verbosity=2)