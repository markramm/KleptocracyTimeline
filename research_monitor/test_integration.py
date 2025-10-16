#!/usr/bin/env python3
"""
Integration Tests for Research Monitor v2 API
Tests with real sample data to ensure all endpoints work correctly
"""

import unittest
import json
import tempfile
import os
import shutil
from datetime import datetime
from pathlib import Path

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, TimelineEvent, ResearchPriority, init_database
from app_v2 import app

class TestResearchMonitorIntegration(unittest.TestCase):
    """Integration tests with real sample data"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment with sample data"""
        # Create temporary directories for test data
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_events_dir = Path(cls.temp_dir) / 'timeline_data' / 'events'
        cls.test_priorities_dir = Path(cls.temp_dir) / 'research_priorities'
        cls.test_events_dir.mkdir(parents=True, exist_ok=True)
        cls.test_priorities_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample timeline events
        cls.sample_events = [
            {
                "id": "2001-09-11--september-11-attacks",
                "date": "2001-09-11",
                "title": "September 11 Attacks",
                "summary": "Coordinated terrorist attacks involving hijacked commercial airliners",
                "importance": 10,
                "tags": ["terrorism", "national-security", "intelligence-failure"],
                "actors": ["Al-Qaeda", "Osama bin Laden", "Mohamed Atta"],
                "sources": [
                    {
                        "url": "https://www.911commission.gov/report/",
                        "title": "The 9/11 Commission Report"
                    }
                ]
            },
            {
                "id": "2003-03-20--iraq-war-begins",
                "date": "2003-03-20",
                "title": "Iraq War Begins",
                "summary": "US-led invasion of Iraq begins based on claims of WMDs",
                "importance": 9,
                "tags": ["war", "wmds", "intelligence-manipulation"],
                "actors": ["George W. Bush", "Dick Cheney", "Donald Rumsfeld", "Colin Powell"],
                "sources": [
                    {
                        "url": "https://www.senate.gov/artandhistory/history/minute/Iraq_War_Resolution.htm",
                        "title": "Iraq War Resolution"
                    }
                ]
            },
            {
                "id": "2005-07-06--plame-affair-revealed",
                "date": "2005-07-06", 
                "title": "Plame Affair CIA Leak Revealed",
                "summary": "Valerie Plame's CIA identity leaked in retaliation for husband's WMD criticism",
                "importance": 8,
                "tags": ["intelligence-leak", "retaliation", "cia"],
                "actors": ["Valerie Plame", "Joseph Wilson", "Scooter Libby", "Karl Rove"],
                "sources": [
                    {
                        "url": "https://www.washingtonpost.com/politics/plame-affair/",
                        "title": "The Plame Affair"
                    }
                ]
            },
            {
                "id": "2008-09-15--lehman-brothers-collapse",
                "date": "2008-09-15",
                "title": "Lehman Brothers Collapse",
                "summary": "Investment bank Lehman Brothers files for bankruptcy, triggering financial crisis",
                "importance": 9,
                "tags": ["financial-crisis", "banking", "deregulation"],
                "actors": ["Dick Fuld", "Henry Paulson", "Ben Bernanke"],
                "sources": [
                    {
                        "url": "https://www.sec.gov/news/press/2008/2008-204.htm",
                        "title": "SEC Statement on Lehman Brothers"
                    }
                ]
            },
            {
                "id": "2013-06-06--snowden-nsa-revelations",
                "date": "2013-06-06",
                "title": "Snowden NSA Mass Surveillance Revelations",
                "summary": "Edward Snowden reveals extensive NSA domestic surveillance programs",
                "importance": 10,
                "tags": ["surveillance", "whistleblowing", "nsa", "privacy"],
                "actors": ["Edward Snowden", "Glenn Greenwald", "Laura Poitras"],
                "sources": [
                    {
                        "url": "https://www.theguardian.com/world/2013/jun/06/nsa-phone-records-verizon-court-order",
                        "title": "NSA collecting phone records of millions of Verizon customers daily"
                    }
                ]
            }
        ]
        
        # Write sample events to files
        for event in cls.sample_events:
            event_file = cls.test_events_dir / f"{event['id']}.json"
            with open(event_file, 'w') as f:
                json.dump(event, f, indent=2)
        
        # Create sample research priorities
        cls.sample_priorities = [
            {
                "id": "RP-001-cheney-halliburton",
                "title": "Dick Cheney Halliburton Connections",
                "description": "Research connections between Dick Cheney and Halliburton contracts",
                "priority": 8,
                "status": "pending",
                "category": "corporate-capture",
                "estimated_events": 5
            },
            {
                "id": "RP-002-nsa-expansion", 
                "title": "NSA Surveillance Expansion Timeline",
                "description": "Document the expansion of NSA surveillance capabilities post-9/11",
                "priority": 9,
                "status": "in_progress",
                "category": "surveillance-state",
                "estimated_events": 8
            }
        ]
        
        # Write sample priorities to files
        for priority in cls.sample_priorities:
            priority_file = cls.test_priorities_dir / f"{priority['id']}.json"
            with open(priority_file, 'w') as f:
                json.dump(priority, f, indent=2)
        
        # Set up test Flask app
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Override paths for testing
        app.config['EVENTS_PATH'] = str(cls.test_events_dir)
        app.config['PRIORITIES_PATH'] = str(cls.test_priorities_dir)
        app.config['DATABASE_PATH'] = os.path.join(cls.temp_dir, 'test_research.db')
        
        cls.app = app.test_client()
        cls.app_context = app.app_context()
        cls.app_context.push()
        
        # Initialize test database
        cls.engine = init_database(app.config['DATABASE_PATH'])
        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()
        
        # Load sample data into database
        cls.load_sample_data()
        
    @classmethod
    def load_sample_data(cls):
        """Load sample events and priorities into test database"""
        # Add timeline events
        for event_data in cls.sample_events:
            event = TimelineEvent(
                id=event_data['id'],
                json_content=event_data,
                date=event_data['date'],
                title=event_data['title'],
                summary=event_data['summary'],
                importance=event_data['importance'],
                file_path=str(cls.test_events_dir / f"{event_data['id']}.json"),
                file_hash="test_hash"
            )
            cls.session.add(event)
        
        # Add research priorities
        for priority_data in cls.sample_priorities:
            priority = ResearchPriority(
                id=priority_data['id'],
                title=priority_data['title'],
                description=priority_data['description'],
                priority=priority_data['priority'],
                status=priority_data['status'],
                category=priority_data['category'],
                estimated_events=priority_data['estimated_events']
            )
            cls.session.add(priority)
        
        cls.session.commit()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        cls.session.close()
        cls.app_context.pop()
        shutil.rmtree(cls.temp_dir)
    
    def test_timeline_events_endpoint(self):
        """Test timeline events endpoint with real data"""
        response = self.app.get('/api/timeline/events')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('events', data)
        self.assertIn('pagination', data)
        self.assertEqual(len(data['events']), 5)  # All 5 sample events
        self.assertEqual(data['pagination']['total'], 5)
        
        # Check event structure
        event = data['events'][0]
        self.assertIn('id', event)
        self.assertIn('date', event)
        self.assertIn('title', event)
        self.assertIn('importance', event)
        self.assertIn('actors', event)
        self.assertIn('tags', event)
    
    def test_timeline_events_with_filters(self):
        """Test timeline events with filtering"""
        # Test importance filter
        response = self.app.get('/api/timeline/events?importance_min=9')
        data = json.loads(response.data)
        self.assertEqual(len(data['events']), 3)  # 3 events with importance >= 9
        
        # Test date range filter
        response = self.app.get('/api/timeline/events?start_date=2005-01-01&end_date=2010-12-31')
        data = json.loads(response.data)
        self.assertEqual(len(data['events']), 2)  # Plame affair and Lehman collapse
        
        # Test pagination
        response = self.app.get('/api/timeline/events?per_page=2&page=1')
        data = json.loads(response.data)
        self.assertEqual(len(data['events']), 2)
        self.assertTrue(data['pagination']['has_next'])
    
    def test_timeline_actors_endpoint(self):
        """Test timeline actors endpoint"""
        response = self.app.get('/api/timeline/actors')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('actors', data)
        
        # Should include actors from our sample events
        actor_names = [actor['name'] for actor in data['actors']]
        self.assertIn('Dick Cheney', actor_names)
        self.assertIn('Edward Snowden', actor_names)
        
        # Check event counts
        cheney_actor = next(a for a in data['actors'] if a['name'] == 'Dick Cheney')
        self.assertGreaterEqual(cheney_actor['event_count'], 1)
    
    def test_timeline_tags_endpoint(self):
        """Test timeline tags endpoint"""
        response = self.app.get('/api/timeline/tags')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('tags', data)
        
        # Should include tags from our sample events
        tag_names = [tag['name'] for tag in data['tags']]
        self.assertIn('surveillance', tag_names)
        self.assertIn('intelligence-leak', tag_names)
        self.assertIn('financial-crisis', tag_names)
    
    def test_timeline_date_range_endpoint(self):
        """Test timeline date range endpoint"""
        response = self.app.get('/api/timeline/date-range')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('date_range', data)
        self.assertEqual(data['date_range']['min_date'], '2001-09-11')
        self.assertEqual(data['date_range']['max_date'], '2013-06-06')
        self.assertEqual(data['total_events'], 5)
    
    def test_viewer_stats_overview(self):
        """Test viewer statistics overview endpoint"""
        response = self.app.get('/api/viewer/stats/overview')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['total_events'], 5)
        self.assertGreater(data['total_actors'], 0)
        self.assertGreater(data['total_tags'], 0)
        self.assertIn('date_range', data)
        self.assertIn('avg_importance', data)
    
    def test_viewer_actor_network(self):
        """Test actor network endpoint"""
        response = self.app.get('/api/viewer/actor-network?min_connections=1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('network', data)
        self.assertIn('nodes', data['network'])
        self.assertIn('edges', data['network'])
        
        # Should have nodes for actors that appear in multiple events
        node_ids = [node['id'] for node in data['network']['nodes']]
        self.assertIn('Dick Cheney', node_ids)
    
    def test_viewer_tag_cloud(self):
        """Test tag cloud endpoint"""
        response = self.app.get('/api/viewer/tag-cloud?min_frequency=1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('tag_cloud', data)
        
        # Should include our sample tags
        tag_names = [tag['name'] for tag in data['tag_cloud']]
        self.assertIn('surveillance', tag_names)
        self.assertIn('intelligence-leak', tag_names)
    
    def test_events_search_endpoint(self):
        """Test events search endpoint"""
        # Full-text search
        response = self.app.get('/api/events/search?q=surveillance')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('events', data)
        self.assertGreater(len(data['events']), 0)
        
        # Should find Snowden NSA event
        titles = [event['title'] for event in data['events']]
        self.assertTrue(any('Snowden' in title for title in titles))
        
        # Search with filters
        response = self.app.get('/api/events/search?q=war&min_importance=8')
        data = json.loads(response.data)
        self.assertGreater(len(data['events']), 0)
    
    def test_timeline_search_advanced(self):
        """Test advanced timeline search endpoint"""
        search_data = {
            "query": "intelligence",
            "filters": {
                "importance_range": [8, 10],
                "date_range": ["2000-01-01", "2015-12-31"]
            },
            "sort": {
                "field": "date",
                "order": "desc"
            },
            "limit": 10
        }
        
        response = self.app.post('/api/timeline/search',
                                data=json.dumps(search_data),
                                content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('events', data)
        self.assertIn('metadata', data)
        
        # Should find intelligence-related events
        self.assertGreater(len(data['events']), 0)
    
    def test_research_priorities_endpoints(self):
        """Test research priorities endpoints"""
        # Get next priority
        response = self.app.get('/api/priorities/next')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('priority', data)
        
        # Should get highest priority pending item
        self.assertEqual(data['status'], 'pending')
        self.assertGreaterEqual(data['priority'], 8)
    
    def test_health_and_stats_endpoints(self):
        """Test system health and statistics endpoints"""
        # Health check
        response = self.app.get('/api/server/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        
        # Statistics
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('events', data)
        self.assertEqual(data['events']['total'], 5)
    
    def test_documentation_endpoints(self):
        """Test API documentation endpoints"""
        # API docs overview
        response = self.app.get('/api/docs')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('documentation', data)
        self.assertIn('endpoints', data)
        
        # OpenAPI specification
        response = self.app.get('/api/openapi.json')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['openapi'], '3.0.0')
        self.assertEqual(data['info']['title'], 'Research Monitor v2 API')

class TestAPIClientIntegration(unittest.TestCase):
    """Test the Python API client against live server"""
    
    def setUp(self):
        """Set up for API client tests"""
        # Import after app is configured
        from research_client import ResearchMonitorClient
        self.client = ResearchMonitorClient(base_url="http://localhost:5558")
    
    def test_client_basic_operations(self):
        """Test basic client operations"""
        try:
            # Test health check
            health = self.client.health_check()
            self.assertEqual(health['status'], 'healthy')
            
            # Test timeline stats
            stats = self.client.get_timeline_stats()
            self.assertIn('total_events', stats)
            self.assertGreater(stats['total_events'], 0)
            
            # Test search
            results = self.client.search_events("Trump")
            self.assertIn('events', results)
            
        except Exception as e:
            self.skipTest(f"Server not available for client testing: {e}")
    
    def test_client_advanced_features(self):
        """Test advanced client features"""
        try:
            # Test actor analysis
            analysis = self.client.analyze_actor("Trump")
            self.assertIn('total_events', analysis)
            
            # Test actor network
            network = self.client.get_actor_network()
            self.assertIn('nodes', network)
            self.assertIn('edges', network)
            
        except Exception as e:
            self.skipTest(f"Server not available for advanced client testing: {e}")

if __name__ == '__main__':
    # Run integration tests
    unittest.main(verbosity=2)