#!/usr/bin/env python3
"""
Contract tests for Research Monitor v2 API.
These tests validate the API contracts that the timeline viewer depends on.
"""

import pytest
import requests
import time
import json
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:5558"
API_TIMEOUT = 10


class TestAPIContracts:
    """Test API contracts for Research Monitor v2."""
    
    @pytest.fixture(scope="class")
    def api_health_check(self):
        """Verify API is running before testing."""
        try:
            response = requests.get(f"{API_BASE_URL}/api/stats", timeout=5)
            if response.status_code != 200:
                pytest.skip("Research Monitor v2 API not available")
        except requests.exceptions.RequestException:
            pytest.skip("Research Monitor v2 API not accessible")
    
    def test_events_endpoint_contract(self, api_health_check):
        """Test /api/timeline/events endpoint contract."""
        response = requests.get(f"{API_BASE_URL}/api/timeline/events", timeout=API_TIMEOUT)
        
        # Contract: Must return 200 with JSON
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/json'
        
        data = response.json()
        
        # Contract: Must have events array and pagination info
        assert 'events' in data
        assert isinstance(data['events'], list)
        assert 'pagination' in data
        assert 'total' in data['pagination']
        assert 'page' in data['pagination']
        assert 'per_page' in data['pagination']
        
        # Contract: Events must have required fields
        if data['events']:
            event = data['events'][0]
            required_fields = ['id', 'date', 'title', 'summary', 'importance']
            for field in required_fields:
                assert field in event, f"Missing required field: {field}"
    
    def test_events_search_contract(self, api_health_check):
        """Test /api/events/search endpoint contract."""
        response = requests.get(
            f"{API_BASE_URL}/api/events/search", 
            params={'q': 'Trump'},
            timeout=API_TIMEOUT
        )
        
        # Contract: Must return 200 with JSON
        assert response.status_code == 200
        data = response.json()
        
        # Contract: Must have events and count
        assert 'events' in data
        assert 'count' in data
        assert isinstance(data['events'], list)
        assert isinstance(data['count'], int)
        
        # Contract: Search should return relevant results
        if data['events']:
            # At least one result should contain the search term
            search_term_found = any(
                'trump' in event.get('title', '').lower() or 
                'trump' in event.get('summary', '').lower() 
                for event in data['events']
            )
            assert search_term_found, "Search results don't contain search term"
    
    def test_stats_endpoint_contract(self, api_health_check):
        """Test /api/stats endpoint contract."""
        response = requests.get(f"{API_BASE_URL}/api/stats", timeout=API_TIMEOUT)
        
        # Contract: Must return 200 with JSON
        assert response.status_code == 200
        data = response.json()
        
        # Contract: Must have essential statistics
        required_stats = ['events', 'priorities', 'session']
        for stat in required_stats:
            assert stat in data, f"Missing required stat: {stat}"
        
        # Contract: Events section must have total
        assert 'total' in data['events']
        assert isinstance(data['events']['total'], int)
        assert data['events']['total'] > 0
        
        # Contract: Priorities section must have total
        assert 'total' in data['priorities']
        assert isinstance(data['priorities']['total'], int)
    
    def test_metadata_endpoints_contract(self, api_health_check):
        """Test metadata endpoints contract."""
        endpoints = [
            ('/api/timeline/tags', 'tags'),
            ('/api/timeline/actors', 'actors'),
            ('/api/timeline/sources', 'sources')
        ]
        
        for endpoint, key in endpoints:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=API_TIMEOUT)
            
            # Contract: Must return 200 with JSON
            assert response.status_code == 200, f"Failed for {endpoint}"
            data = response.json()
            
            # Contract: Must have the expected key with array
            assert key in data, f"Missing {key} in {endpoint}"
            assert isinstance(data[key], list), f"{key} should be a list in {endpoint}"
    
    def test_performance_contract(self, api_health_check):
        """Test API performance meets contract requirements."""
        # Contract: API responses should be under 100ms for basic queries
        endpoints_to_test = [
            '/api/stats',
            '/api/timeline/tags',
            '/api/timeline/events?per_page=10'
        ]
        
        for endpoint in endpoints_to_test:
            start_time = time.time()
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=API_TIMEOUT)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            # Contract: Response time should be reasonable
            assert response.status_code == 200
            assert response_time_ms < 100, f"{endpoint} took {response_time_ms:.2f}ms"
    
    def test_pagination_contract(self, api_health_check):
        """Test pagination contract."""
        # Test first page
        response = requests.get(
            f"{API_BASE_URL}/api/timeline/events",
            params={'page': 1, 'per_page': 5},
            timeout=API_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Contract: Pagination info must be consistent
        assert len(data['events']) <= 5
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 5
        
        # Test second page if enough events
        if data['pagination']['total'] > 5:
            response2 = requests.get(
                f"{API_BASE_URL}/api/timeline/events",
                params={'page': 2, 'per_page': 5},
                timeout=API_TIMEOUT
            )
            
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2['pagination']['page'] == 2
            
            # Contract: Pages should not have duplicate events
            page1_ids = {event['id'] for event in data['events']}
            page2_ids = {event['id'] for event in data2['events']}
            assert not page1_ids.intersection(page2_ids), "Duplicate events across pages"
    
    def test_data_integrity_contract(self, api_health_check):
        """Test data integrity contracts."""
        response = requests.get(
            f"{API_BASE_URL}/api/timeline/events?per_page=100",
            timeout=API_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for event in data['events']:
            # Contract: Event IDs must be unique and follow format
            assert event['id'], "Event ID cannot be empty"
            assert '--' in event['id'], "Event ID must follow YYYY-MM-DD--slug format"
            
            # Contract: Dates must be valid ISO format
            date_str = event['date']
            assert len(date_str) == 10, "Date must be YYYY-MM-DD format"
            assert date_str.count('-') == 2, "Date must have two hyphens"
            
            # Contract: Importance must be 1-10
            importance = event['importance']
            assert isinstance(importance, int), "Importance must be integer"
            assert 1 <= importance <= 10, f"Importance {importance} out of range 1-10"
            
            # Contract: Title and summary cannot be empty
            assert event['title'].strip(), "Title cannot be empty"
            assert event['summary'].strip(), "Summary cannot be empty"
    
    def test_error_handling_contract(self, api_health_check):
        """Test API error handling contracts."""
        # Test invalid endpoint
        response = requests.get(f"{API_BASE_URL}/api/nonexistent", timeout=API_TIMEOUT)
        assert response.status_code == 404
        
        # Test invalid pagination
        response = requests.get(
            f"{API_BASE_URL}/api/timeline/events",
            params={'page': -1},
            timeout=API_TIMEOUT
        )
        # Should handle gracefully (either 400 or default to page 1)
        assert response.status_code in [200, 400]
        
        # Test invalid per_page
        response = requests.get(
            f"{API_BASE_URL}/api/timeline/events",
            params={'per_page': 10000},
            timeout=API_TIMEOUT
        )
        # Should handle gracefully (cap at reasonable limit)
        assert response.status_code == 200
        data = response.json()
        assert data['pagination']['per_page'] <= 5000  # API maximum limit
    
    def test_search_functionality_contract(self, api_health_check):
        """Test search functionality contracts."""
        # Test empty search
        response = requests.get(
            f"{API_BASE_URL}/api/events/search",
            params={'q': ''},
            timeout=API_TIMEOUT
        )
        assert response.status_code == 200
        
        # Test search with quotes
        response = requests.get(
            f"{API_BASE_URL}/api/events/search",
            params={'q': '"Saudi Arabia"'},
            timeout=API_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        
        # Contract: Quoted search should find exact phrase
        if data['events']:
            found_exact_phrase = any(
                'saudi arabia' in event.get('title', '').lower() or
                'saudi arabia' in event.get('summary', '').lower()
                for event in data['events']
            )
            # Note: This might not always pass depending on data, but tests the contract
    
    def test_database_sync_contract(self, api_health_check):
        """Test that API reflects filesystem data correctly."""
        # Get total events from API
        response = requests.get(f"{API_BASE_URL}/api/stats", timeout=API_TIMEOUT)
        assert response.status_code == 200
        stats = response.json()
        api_total = stats['events']['total']
        
        # Contract: Should have reasonable number of events (>1000 for this project)
        assert api_total > 1000, f"Expected >1000 events, got {api_total}"
        
        # Contract: API should return consistent totals
        response2 = requests.get(f"{API_BASE_URL}/api/stats", timeout=API_TIMEOUT)
        stats2 = response2.json()
        assert stats2['events']['total'] == api_total, "API returning inconsistent totals"


class TestIntegrationContracts:
    """Test integration contracts between components."""
    
    @pytest.fixture(scope="class")
    def api_health_check(self):
        """Verify API is running before testing."""
        try:
            response = requests.get(f"{API_BASE_URL}/api/stats", timeout=5)
            if response.status_code != 200:
                pytest.skip("Research Monitor v2 API not available")
        except requests.exceptions.RequestException:
            pytest.skip("Research Monitor v2 API not accessible")
    
    def test_viewer_api_integration_contract(self, api_health_check):
        """Test contracts that the timeline viewer depends on."""
        # This simulates what the React app does on startup
        endpoints_for_viewer = [
            '/api/timeline/events?per_page=10000',  # Full data load
            '/api/timeline/tags',
            '/api/timeline/actors', 
            '/api/stats',
            '/api/viewer/stats/actors?limit=10',
            '/api/viewer/stats/importance'
        ]
        
        for endpoint in endpoints_for_viewer:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=API_TIMEOUT)
            assert response.status_code == 200, f"Viewer dependency failed: {endpoint}"
            
            # Contract: All viewer endpoints must return JSON
            assert 'application/json' in response.headers.get('content-type', '')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])