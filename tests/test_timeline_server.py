#!/usr/bin/env python3
"""
Test suite for timeline server
Tests API endpoints, data loading, and server functionality
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
import sys
import yaml
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from timeline_server import app, load_timeline_events, extract_all_tags, extract_all_actors

class TestTimelineServer(unittest.TestCase):
    """Test cases for timeline server"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
        # Create a temporary directory for test data
        cls.test_dir = tempfile.mkdtemp()
        cls.test_timeline_dir = Path(cls.test_dir) / 'timeline_data'
        cls.test_timeline_dir.mkdir()
        
        # Create sample test events
        cls.create_test_events()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        shutil.rmtree(cls.test_dir)
    
    @classmethod
    def create_test_events(cls):
        """Create sample YAML events for testing"""
        test_events = [
            {
                'id': '2024-01-01_test-event-one',
                'date': '2024-01-01',
                'title': 'Test Event One',
                'summary': 'This is the first test event',
                'tags': ['test', 'sample'],
                'status': 'confirmed',
                'sources': [
                    {
                        'title': 'Test Source',
                        'url': 'https://example.com/test',
                        'outlet': 'Test News'
                    }
                ],
                'actors': ['Test Actor 1', 'Test Actor 2']
            },
            {
                'id': '2024-02-15_test-event-two',
                'date': '2024-02-15',
                'title': 'Test Event Two',
                'summary': 'This is the second test event',
                'tags': ['test', 'democracy'],
                'status': 'confirmed',
                'sources': [
                    {
                        'title': 'Another Source',
                        'url': 'https://example.org/test',
                        'outlet': 'Test Org'
                    }
                ],
                'actors': ['Test Actor 2', 'Test Actor 3']
            },
            {
                'id': '2023-12-31_test-event-three',
                'date': '2023-12-31',
                'title': 'Test Event Three',
                'summary': 'This is the third test event',
                'tags': ['sample', 'validation'],
                'status': 'unconfirmed',
                'sources': []
            }
        ]
        
        for event in test_events:
            file_path = cls.test_timeline_dir / f"{event['id']}.yaml"
            with open(file_path, 'w') as f:
                yaml.dump(event, f)
    
    def test_server_health(self):
        """Test server is running"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_get_all_events(self):
        """Test GET /api/events endpoint"""
        response = self.client.get('/api/events')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('events', data)
        self.assertIn('total', data)
        self.assertIsInstance(data['events'], list)
    
    def test_get_single_event(self):
        """Test GET /api/events/<id> endpoint"""
        # First get all events to find a valid ID
        response = self.client.get('/api/events')
        data = json.loads(response.data)
        
        if data['events']:
            event_id = data['events'][0]['id']
            response = self.client.get(f'/api/events/{event_id}')
            self.assertEqual(response.status_code, 200)
            
            event_data = json.loads(response.data)
            self.assertEqual(event_data['id'], event_id)
    
    def test_get_nonexistent_event(self):
        """Test GET /api/events/<id> with invalid ID"""
        response = self.client.get('/api/events/nonexistent-id')
        self.assertEqual(response.status_code, 404)
    
    def test_get_tags(self):
        """Test GET /api/tags endpoint"""
        response = self.client.get('/api/tags')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('tags', data)
        self.assertIsInstance(data['tags'], list)
    
    def test_get_actors(self):
        """Test GET /api/actors endpoint"""
        response = self.client.get('/api/actors')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('actors', data)
        self.assertIsInstance(data['actors'], list)
    
    def test_get_stats(self):
        """Test GET /api/stats endpoint"""
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('total_events', data)
        self.assertIn('date_range', data)
        self.assertIn('total_tags', data)
        self.assertIn('total_actors', data)
        self.assertIn('events_by_year', data)
        self.assertIn('events_by_status', data)
    
    def test_search_events(self):
        """Test GET /api/events/search endpoint"""
        response = self.client.get('/api/events/search?q=test')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('events', data)
        self.assertIn('total', data)
        self.assertIn('query', data)
    
    def test_filter_by_tag(self):
        """Test GET /api/events?tag=<tag> endpoint"""
        response = self.client.get('/api/events?tag=test')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('events', data)
        # All returned events should have the 'test' tag
        for event in data['events']:
            if 'tags' in event:
                self.assertIn('test', event.get('tags', []))
    
    def test_filter_by_year(self):
        """Test GET /api/events?year=<year> endpoint"""
        response = self.client.get('/api/events?year=2024')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('events', data)
        # All returned events should be from 2024
        for event in data['events']:
            if 'date' in event:
                self.assertTrue(str(event['date']).startswith('2024'))
    
    def test_filter_by_status(self):
        """Test GET /api/events?status=<status> endpoint"""
        response = self.client.get('/api/events?status=confirmed')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('events', data)
        # All returned events should have confirmed status
        for event in data['events']:
            if 'status' in event:
                self.assertEqual(event['status'], 'confirmed')
    
    def test_pagination(self):
        """Test pagination parameters"""
        response = self.client.get('/api/events?limit=10&offset=0')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('events', data)
        self.assertIn('total', data)
        self.assertIn('limit', data)
        self.assertIn('offset', data)
        
        # Check limit is respected
        if data['total'] > 10:
            self.assertLessEqual(len(data['events']), 10)
    
    def test_sort_order(self):
        """Test sort order of events"""
        response = self.client.get('/api/events?sort=asc')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        events = data['events']
        
        # Check events are sorted ascending by date
        if len(events) > 1:
            for i in range(len(events) - 1):
                date1 = events[i].get('date', '')
                date2 = events[i + 1].get('date', '')
                self.assertLessEqual(date1, date2)
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = self.client.get('/api/events')
        self.assertIn('Access-Control-Allow-Origin', response.headers)
    
    def test_content_type(self):
        """Test response content type"""
        response = self.client.get('/api/events')
        self.assertEqual(response.content_type, 'application/json')
    
    def test_date_range_filter(self):
        """Test filtering by date range"""
        response = self.client.get('/api/events?start_date=2024-01-01&end_date=2024-12-31')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        # All events should be within 2024
        for event in data['events']:
            date_str = str(event.get('date', ''))
            if date_str:
                self.assertTrue(date_str >= '2024-01-01')
                self.assertTrue(date_str <= '2024-12-31')
    
    def test_multiple_filters(self):
        """Test combining multiple filters"""
        response = self.client.get('/api/events?year=2024&status=confirmed&tag=test')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        # Events should match all filters
        for event in data['events']:
            self.assertTrue(str(event.get('date', '')).startswith('2024'))
            self.assertEqual(event.get('status'), 'confirmed')
            self.assertIn('test', event.get('tags', []))
    
    def test_invalid_parameters(self):
        """Test handling of invalid parameters"""
        # Invalid year
        response = self.client.get('/api/events?year=invalid')
        self.assertEqual(response.status_code, 400)
        
        # Invalid limit
        response = self.client.get('/api/events?limit=-1')
        self.assertEqual(response.status_code, 400)
        
        # Invalid offset
        response = self.client.get('/api/events?offset=abc')
        self.assertEqual(response.status_code, 400)

class TestDataLoading(unittest.TestCase):
    """Test data loading functions"""
    
    def test_load_timeline_events(self):
        """Test loading events from YAML files"""
        events = load_timeline_events()
        self.assertIsInstance(events, list)
        
        # Check event structure
        for event in events:
            self.assertIsInstance(event, dict)
            # Should have required fields
            self.assertIn('id', event)
            self.assertIn('date', event)
            self.assertIn('title', event)
    
    def test_extract_all_tags(self):
        """Test tag extraction"""
        sample_events = [
            {'tags': ['tag1', 'tag2']},
            {'tags': ['tag2', 'tag3']},
            {'tags': ['tag1', 'tag4']}
        ]
        
        tags = extract_all_tags(sample_events)
        self.assertEqual(set(tags), {'tag1', 'tag2', 'tag3', 'tag4'})
        # Should be sorted
        self.assertEqual(tags, sorted(tags))
    
    def test_extract_all_actors(self):
        """Test actor extraction"""
        sample_events = [
            {'actors': ['Actor 1', 'Actor 2']},
            {'actors': ['Actor 2', 'Actor 3']},
            {}  # No actors field
        ]
        
        actors = extract_all_actors(sample_events)
        self.assertEqual(set(actors), {'Actor 1', 'Actor 2', 'Actor 3'})
        # Should be sorted
        self.assertEqual(actors, sorted(actors))

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestTimelineServer))
    suite.addTests(loader.loadTestsFromTestCase(TestDataLoading))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())