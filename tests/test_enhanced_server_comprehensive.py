#!/usr/bin/env python3
"""
Comprehensive tests for the enhanced timeline server.
"""

import pytest
import json
import tempfile
import shutil
import yaml
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.enhanced_server import app, load_timeline_events, load_posts, load_book_chapters


class TestEnhancedServer:
    
    @pytest.fixture
    def client(self):
        """Create test client with temporary data."""
        app.config['TESTING'] = True
        
        # Create temporary directories for test data
        self.test_dir = Path(tempfile.mkdtemp())
        self.timeline_dir = self.test_dir / "timeline_data" / "events"
        self.posts_dir = self.test_dir / "posts"
        self.book_dir = self.test_dir / "book_vision"
        
        self.timeline_dir.mkdir(parents=True)
        self.posts_dir.mkdir(parents=True)
        self.book_dir.mkdir(parents=True)
        
        # Create test timeline events
        self._create_test_events()
        self._create_test_posts()
        self._create_test_book_chapters()
        
        # Patch the directories in the app
        import api.enhanced_server as server
        server.TIMELINE_DIR = self.test_dir / "timeline_data"
        server.POSTS_DIR = self.posts_dir
        server.BOOK_DIR = self.book_dir
        
        # Clear cache
        server._cache = {
            'events': None,
            'posts': None,
            'book_chapters': None,
            'events_by_id': {},
            'last_load': 0
        }
        
        with app.test_client() as client:
            yield client
        
        # Cleanup
        shutil.rmtree(self.test_dir)
    
    def _create_test_events(self):
        """Create test timeline events."""
        events = [
            {
                'id': '2025-01-01--test-event-1',
                'date': '2025-01-01',
                'title': 'Test Event 1',
                'summary': 'This is a test event for validation',
                'status': 'confirmed',
                'tags': ['test', 'validation'],
                'actors': ['Test Actor'],
                'sources': [
                    {
                        'title': 'Test Source',
                        'url': 'https://example.com/test',
                        'outlet': 'Test Outlet',
                        'date': '2025-01-01'
                    }
                ],
                'monitoring_status': 'active',
                'followup_schedule': 'weekly',
                'search_keywords': ['test event', 'validation'],
                'trigger_events': ['test trigger'],
                'fallout_indicators': ['test indicator']
            },
            {
                'id': '2025-01-02--test-event-2',
                'date': '2025-01-02',
                'title': 'Test Event 2',
                'summary': 'Second test event',
                'status': 'pending',
                'tags': ['test'],
                'actors': ['Test Actor 2'],
                'sources': [
                    {
                        'title': 'Test Source 2',
                        'url': 'https://example.com/test2',
                        'outlet': 'Test Outlet 2',
                        'date': '2025-01-02'
                    }
                ]
            }
        ]
        
        for event in events:
            event_file = self.timeline_dir / f"{event['id']}.yaml"
            with open(event_file, 'w') as f:
                yaml.dump(event, f, default_flow_style=False)
    
    def _create_test_posts(self):
        """Create test posts."""
        post_content = """---
title: Test Post
date: 2025-01-01
series: tech_frame
tags: [test, analysis]
---

# Test Post Content

This is a test post for validation.
"""
        
        post_file = self.posts_dir / "test-post.md"
        with open(post_file, 'w') as f:
            f.write(post_content)
    
    def _create_test_book_chapters(self):
        """Create test book chapters."""
        chapter_content = """---
title: Test Chapter
chapter: 1
order: 1
---

# Test Chapter

This is a test chapter.
"""
        
        chapter_file = self.book_dir / "test-chapter.md"
        with open(chapter_file, 'w') as f:
            f.write(chapter_content)
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_api_events_endpoint(self, client):
        """Test the events API endpoint."""
        response = client.get('/api/events')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'events' in data
        assert len(data['events']) == 2
        
        # Check first event
        event1 = data['events'][0]
        assert event1['id'] == '2025-01-01--test-event-1'
        assert event1['title'] == 'Test Event 1'
        assert event1['monitoring_status'] == 'active'
        assert 'search_keywords' in event1
    
    def test_api_events_filtering(self, client):
        """Test events API with filtering."""
        # Test tag filtering
        response = client.get('/api/events?tag=validation')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['events']) == 1
        assert data['events'][0]['id'] == '2025-01-01--test-event-1'
        
        # Test status filtering
        response = client.get('/api/events?status=pending')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['events']) == 1
        assert data['events'][0]['id'] == '2025-01-02--test-event-2'
    
    def test_api_monitoring_endpoint(self, client):
        """Test the monitoring events endpoint."""
        response = client.get('/api/monitoring')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'monitoring_events' in data
        assert len(data['monitoring_events']) == 1
        
        event = data['monitoring_events'][0]
        assert event['id'] == '2025-01-01--test-event-1'
        assert event['monitoring_status'] == 'active'
        assert event['followup_schedule'] == 'weekly'
    
    def test_api_posts_endpoint(self, client):
        """Test the posts API endpoint."""
        response = client.get('/api/posts')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'posts' in data
        assert len(data['posts']) >= 1
        
        # Check that post has required fields
        post = data['posts'][0]
        assert 'title' in post
        assert 'content' in post
        assert 'metadata' in post
    
    def test_api_stats_endpoint(self, client):
        """Test the stats API endpoint."""
        response = client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'total_events' in data
        assert 'events_by_status' in data
        assert 'events_by_year' in data
        assert 'monitoring_summary' in data
        
        assert data['total_events'] == 2
        assert data['events_by_status']['confirmed'] == 1
        assert data['events_by_status']['pending'] == 1
    
    def test_load_timeline_events(self):
        """Test the timeline events loading function."""
        # Create temporary test data
        test_dir = Path(tempfile.mkdtemp())
        events_dir = test_dir / "events"
        events_dir.mkdir(parents=True)
        
        # Create test event
        test_event = {
            'id': 'test-event',
            'date': '2025-01-01',
            'title': 'Test',
            'summary': 'Test event',
            'status': 'confirmed',
            'sources': [{'title': 'Test', 'url': 'https://example.com'}]
        }
        
        with open(events_dir / "test-event.yaml", 'w') as f:
            yaml.dump(test_event, f)
        
        # Test loading
        events, events_by_id = load_timeline_events(test_dir)
        
        assert len(events) == 1
        assert events[0]['id'] == 'test-event'
        assert 'test-event' in events_by_id
        
        # Cleanup
        shutil.rmtree(test_dir)
    
    def test_invalid_yaml_handling(self):
        """Test handling of invalid YAML files."""
        test_dir = Path(tempfile.mkdtemp())
        events_dir = test_dir / "events"
        events_dir.mkdir(parents=True)
        
        # Create invalid YAML file
        with open(events_dir / "invalid.yaml", 'w') as f:
            f.write("invalid: yaml: content: [")
        
        # Should handle gracefully
        events, events_by_id = load_timeline_events(test_dir)
        assert len(events) == 0
        
        # Cleanup
        shutil.rmtree(test_dir)
    
    def test_search_functionality(self, client):
        """Test search functionality."""
        response = client.get('/api/events?search=Test Event 1')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should find the event with "Test Event 1" in title
        assert len(data['events']) >= 1
        found_event = next((e for e in data['events'] if e['title'] == 'Test Event 1'), None)
        assert found_event is not None
    
    def test_date_range_filtering(self, client):
        """Test date range filtering."""
        response = client.get('/api/events?start_date=2025-01-01&end_date=2025-01-01')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should only return events from 2025-01-01
        assert len(data['events']) == 1
        assert data['events'][0]['date'] == '2025-01-01'
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get('/api/events')
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_error_handling(self, client):
        """Test error handling for invalid requests."""
        # Test invalid date format
        response = client.get('/api/events?start_date=invalid-date')
        # Should not crash, may return 400 or handle gracefully
        assert response.status_code in [200, 400]
        
        # Test invalid endpoint
        response = client.get('/api/nonexistent')
        assert response.status_code == 404


if __name__ == '__main__':
    pytest.main([__file__, '-v'])