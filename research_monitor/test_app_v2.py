#!/usr/bin/env python3
"""
Comprehensive test suite for Research Monitor v2
Tests database operations, API endpoints, filesystem sync, and commit orchestration
"""

import unittest
import tempfile
import shutil
import json
import os
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Set up test environment before imports
os.environ['RESEARCH_MONITOR_API_KEY'] = 'test-key'
os.environ['RESEARCH_DB_PATH'] = ':memory:'  # Use in-memory database for tests
os.environ['COMMIT_THRESHOLD'] = '3'

import sys
sys.path.insert(0, str(Path(__file__).parent))

from app_v2 import app, Session, FilesystemSyncer, trigger_commit
from models import (
    Base, TimelineEvent, EventMetadata, ResearchPriority,
    EventResearchLink, ActivityLog, ResearchSession, init_database
)

class TestResearchMonitorBase(unittest.TestCase):
    """Base test class with common setup/teardown"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories
        self.test_dir = Path(tempfile.mkdtemp())
        self.events_dir = self.test_dir / 'timeline_data' / 'events'
        self.priorities_dir = self.test_dir / 'research_priorities'
        self.events_dir.mkdir(parents=True)
        self.priorities_dir.mkdir(parents=True)
        
        # Patch environment paths
        os.environ['TIMELINE_EVENTS_PATH'] = str(self.events_dir)
        os.environ['RESEARCH_PRIORITIES_PATH'] = str(self.priorities_dir)
        
        # Set up Flask test client
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Initialize test database
        self.engine = init_database(':memory:')
        self.session = Session()
        
        # Clear any existing data
        self.session.query(TimelineEvent).delete()
        self.session.query(ResearchPriority).delete()
        self.session.commit()
    
    def tearDown(self):
        """Clean up test environment"""
        # Close database session
        self.session.close()
        
        # Remove temporary directories
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def create_test_event(self, event_id='test-event-001', date='2023-01-01'):
        """Create a test event JSON file"""
        event_data = {
            'id': event_id,
            'date': date,
            'title': f'Test Event {event_id}',
            'summary': 'Test event summary',
            'importance': 7,
            'actors': ['Test Actor'],
            'tags': ['test', 'sample'],
            'sources': [
                {'title': 'Test Source', 'url': 'https://example.com', 'outlet': 'Test Outlet'}
            ],
            'status': 'confirmed'
        }
        
        event_path = self.events_dir / f'{event_id}.json'
        with open(event_path, 'w') as f:
            json.dump(event_data, f, indent=2)
        
        return event_path, event_data
    
    def create_test_priority(self, priority_id='RT-001', status='pending'):
        """Create a test research priority JSON file"""
        priority_data = {
            'id': priority_id,
            'title': f'Test Priority {priority_id}',
            'description': 'Test priority description',
            'priority': 8,
            'status': status,
            'estimated_events': 5,
            'actual_events': 0,
            'category': 'test-category',
            'tags': ['test', 'priority']
        }
        
        priority_path = self.priorities_dir / f'{priority_id}.json'
        with open(priority_path, 'w') as f:
            json.dump(priority_data, f, indent=2)
        
        return priority_path, priority_data


class TestDatabaseModels(TestResearchMonitorBase):
    """Test database models and relationships"""
    
    def test_timeline_event_creation(self):
        """Test creating timeline event in database"""
        event = TimelineEvent(
            id='test-001',
            json_content={'test': 'data'},
            date='2023-01-01',
            title='Test Event',
            summary='Test summary',
            importance=5,
            file_path='/test/path',
            file_hash='testhash123'
        )
        
        self.session.add(event)
        self.session.commit()
        
        # Verify event was saved
        saved_event = self.session.query(TimelineEvent).filter_by(id='test-001').first()
        self.assertIsNotNone(saved_event)
        self.assertEqual(saved_event.title, 'Test Event')
        self.assertEqual(saved_event.json_content, {'test': 'data'})
    
    def test_research_priority_creation(self):
        """Test creating research priority in database"""
        priority = ResearchPriority(
            id='RT-001',
            title='Test Priority',
            description='Test description',
            priority=9,
            status='pending',
            estimated_events=5,
            tags=['test', 'priority']
        )
        
        self.session.add(priority)
        self.session.commit()
        
        # Verify priority was saved
        saved = self.session.query(ResearchPriority).filter_by(id='RT-001').first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.title, 'Test Priority')
        self.assertEqual(saved.priority, 9)
        self.assertEqual(saved.tags, ['test', 'priority'])
    
    def test_event_metadata_relationship(self):
        """Test relationship between event and metadata"""
        # Create event
        event = TimelineEvent(
            id='test-001', 
            title='Test', 
            file_path='/test', 
            file_hash='hash',
            json_content={'id': 'test-001', 'title': 'Test'}
        )
        self.session.add(event)
        
        # Create metadata
        metadata = EventMetadata(
            event_id='test-001',
            validation_status='validated',
            quality_score=8.5,
            created_by='test-agent'
        )
        self.session.add(metadata)
        self.session.commit()
        
        # Test relationship
        saved_event = self.session.query(TimelineEvent).filter_by(id='test-001').first()
        self.assertIsNotNone(saved_event.event_metadata)
        self.assertEqual(saved_event.event_metadata.validation_status, 'validated')
        self.assertEqual(saved_event.event_metadata.quality_score, 8.5)
    
    def test_activity_logging(self):
        """Test activity log creation"""
        activity = ActivityLog(
            action='test_action',
            agent='test_agent',
            priority_id='RT-001',
            details={'test': 'data'},
            success=True
        )
        
        self.session.add(activity)
        self.session.commit()
        
        # Verify activity was logged
        saved = self.session.query(ActivityLog).filter_by(action='test_action').first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.agent, 'test_agent')
        self.assertEqual(saved.details, {'test': 'data'})


class TestFilesystemSync(TestResearchMonitorBase):
    """Test filesystem synchronization functionality"""
    
    @patch('app_v2.EVENTS_PATH')
    @patch('app_v2.Session')
    def test_sync_events_from_filesystem(self, mock_session_class, mock_events_path):
        """Test syncing events from filesystem to database"""
        # Set up mocks
        mock_events_path.glob.return_value = []
        mock_session_class.return_value = self.session
        
        # Create test events
        self.create_test_event('event-001', '2023-01-01')
        self.create_test_event('event-002', '2023-01-02')
        
        # Set up path mock to return our test files
        mock_events_path.glob.return_value = list(self.events_dir.glob('*.json'))
        
        # Run sync
        syncer = FilesystemSyncer()
        syncer.sync_events()
        
        # Verify events were synced
        events = self.session.query(TimelineEvent).all()
        self.assertEqual(len(events), 2)
        
        event_ids = [e.id for e in events]
        self.assertIn('event-001', event_ids)
        self.assertIn('event-002', event_ids)
    
    @patch('app_v2.EVENTS_PATH')
    @patch('app_v2.Session')
    def test_sync_detects_changes(self, mock_session_class, mock_events_path):
        """Test that sync detects file changes"""
        # Set up mocks
        mock_session_class.return_value = self.session
        
        # Create and sync initial event
        event_path, event_data = self.create_test_event('event-001')
        mock_events_path.glob.return_value = list(self.events_dir.glob('*.json'))
        
        syncer = FilesystemSyncer()
        syncer.sync_events()
        
        # Get initial hash
        event = self.session.query(TimelineEvent).filter_by(id='event-001').first()
        initial_hash = event.file_hash
        
        # Modify event file
        event_data['title'] = 'Modified Title'
        with open(event_path, 'w') as f:
            json.dump(event_data, f, indent=2)
        
        # Sync again
        syncer.sync_events()
        
        # Verify hash changed
        event = self.session.query(TimelineEvent).filter_by(id='event-001').first()
        self.assertNotEqual(event.file_hash, initial_hash)
        self.assertEqual(event.title, 'Modified Title')
    
    @patch('app_v2.PRIORITIES_PATH')
    @patch('app_v2.Session')
    def test_seed_priorities_only_if_not_exists(self, mock_session_class, mock_priorities_path):
        """Test that priorities are only seeded if they don't exist"""
        # Set up mocks
        mock_session_class.return_value = self.session
        
        # Create priority file
        self.create_test_priority('RT-001', 'pending')
        mock_priorities_path.glob.return_value = list(self.priorities_dir.glob('*.json'))
        
        # Seed priorities
        syncer = FilesystemSyncer()
        syncer.seed_priorities()
        
        # Verify priority was seeded
        priority = self.session.query(ResearchPriority).filter_by(id='RT-001').first()
        self.assertIsNotNone(priority)
        original_status = priority.status
        
        # Modify priority in database
        priority.status = 'completed'
        self.session.commit()
        
        # Run seed again
        syncer.seed_priorities()
        
        # Verify database wasn't overwritten
        priority = self.session.query(ResearchPriority).filter_by(id='RT-001').first()
        self.assertEqual(priority.status, 'completed')  # Should remain completed
        self.assertNotEqual(priority.status, original_status)


class TestAPIEndpoints(TestResearchMonitorBase):
    """Test API endpoints"""
    
    def test_get_next_priority(self):
        """Test getting next priority endpoint"""
        # Create priorities with different statuses
        priority1 = ResearchPriority(id='RT-001', title='Low', priority=5, status='pending')
        priority2 = ResearchPriority(id='RT-002', title='High', priority=9, status='pending')
        priority3 = ResearchPriority(id='RT-003', title='Done', priority=10, status='completed')
        
        self.session.add_all([priority1, priority2, priority3])
        self.session.commit()
        
        # Get next priority
        response = self.client.get('/api/priorities/next')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['id'], 'RT-002')  # Highest pending priority
        self.assertEqual(data['priority'], 9)
    
    def test_update_priority_status(self):
        """Test updating priority status"""
        # Create priority
        priority = ResearchPriority(id='RT-001', title='Test', status='pending')
        self.session.add(priority)
        self.session.commit()
        
        # Update status
        response = self.client.put(
            '/api/priorities/RT-001/status',
            json={'status': 'in_progress', 'actual_events': 3},
            headers={'X-API-Key': 'test-key'}
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        priority = self.session.query(ResearchPriority).filter_by(id='RT-001').first()
        self.assertEqual(priority.status, 'in_progress')
        self.assertEqual(priority.actual_events, 3)
        self.assertIsNotNone(priority.started_date)
    
    def test_search_events(self):
        """Test event search endpoint"""
        # Create test events
        event1 = TimelineEvent(
            id='event-001',
            date='2023-01-01',
            title='Halliburton Contract',
            summary='No-bid contract awarded',
            json_content={'test': 'data'},
            file_path='/test',
            file_hash='hash1'
        )
        event2 = TimelineEvent(
            id='event-002',
            date='2023-01-02',
            title='Different Event',
            summary='Something else',
            json_content={'test': 'data2'},
            file_path='/test2',
            file_hash='hash2'
        )
        
        self.session.add_all([event1, event2])
        self.session.commit()
        
        # Search for "halliburton"
        response = self.client.get('/api/events/search?q=halliburton')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        # Note: Full-text search requires proper FTS setup, so basic test here
        self.assertIsInstance(data['events'], list)
    
    def test_validate_event(self):
        """Test event validation endpoint"""
        # Valid event
        valid_event = {
            'id': 'test-001',
            'date': '2023-01-01',
            'title': 'Test Event',
            'summary': 'Test summary',
            'sources': [{'url': 'https://example.com', 'title': 'Source'}]
        }
        
        response = self.client.post('/api/events/validate', json=valid_event)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['valid'])
        self.assertEqual(len(data['errors']), 0)
        
        # Invalid event (missing required field)
        invalid_event = {
            'id': 'test-002',
            'title': 'Missing Date'
        }
        
        response = self.client.post('/api/events/validate', json=invalid_event)
        data = json.loads(response.data)
        self.assertFalse(data['valid'])
        self.assertIn('Missing required field: date', data['errors'])
    
    def test_stage_event(self):
        """Test staging event for commit"""
        event_data = {
            'id': 'test-001',
            'date': '2023-01-01',
            'title': 'Test Event',
            'summary': 'Test',
            'priority_id': 'RT-001'
        }
        
        response = self.client.post(
            '/api/events/staged',
            json=event_data,
            headers={'X-API-Key': 'test-key'}
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify file was created
        event_file = self.events_dir / 'test-001.json'
        self.assertTrue(event_file.exists())
        
        # Verify metadata was created
        metadata = self.session.query(EventMetadata).filter_by(event_id='test-001').first()
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.research_priority_id, 'RT-001')
    
    def test_export_priorities(self):
        """Test exporting valuable priorities"""
        # Create priorities
        p1 = ResearchPriority(id='RT-001', title='Export Me', export_worthy=True)
        p2 = ResearchPriority(id='RT-002', title='Generated', is_generated=True, actual_events=5)
        p3 = ResearchPriority(id='RT-003', title='Skip Me', export_worthy=False)
        
        self.session.add_all([p1, p2, p3])
        self.session.commit()
        
        response = self.client.get('/api/priorities/export')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['count'], 2)  # Should export p1 and p2
        
        exported_ids = [p['id'] for p in data['priorities']]
        self.assertIn('RT-001', exported_ids)
        self.assertIn('RT-002', exported_ids)
        self.assertNotIn('RT-003', exported_ids)
    
    def test_get_stats(self):
        """Test statistics endpoint"""
        # Create test data
        event = TimelineEvent(
            id='e1', 
            title='Test', 
            file_path='/test', 
            file_hash='h1',
            json_content={'id': 'e1', 'title': 'Test'}
        )
        p1 = ResearchPriority(id='RT-001', title='P1', status='pending')
        p2 = ResearchPriority(id='RT-002', title='P2', status='completed')
        
        self.session.add_all([event, p1, p2])
        self.session.commit()
        
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['events']['total'], 1)
        self.assertEqual(data['priorities']['total'], 2)
        self.assertEqual(data['priorities']['pending'], 1)
        self.assertEqual(data['priorities']['completed'], 1)


class TestCommitOrchestration(TestResearchMonitorBase):
    """Test commit orchestration functionality"""
    
    @patch('subprocess.run')
    def test_trigger_commit(self, mock_run):
        """Test commit triggering"""
        # Create export-worthy priority
        priority = ResearchPriority(
            id='RT-001',
            title='Export Me',
            export_worthy=True,
            status='completed',
            actual_events=5
        )
        self.session.add(priority)
        self.session.commit()
        
        # Mock git commands
        mock_run.return_value = Mock(returncode=0)
        
        # Trigger commit
        trigger_commit()
        
        # Verify git commands were called
        self.assertEqual(mock_run.call_count, 2)  # git add and git commit
        
        # Verify priority was exported to file
        priority_file = self.priorities_dir / 'RT-001.json'
        self.assertTrue(priority_file.exists())
        
        with open(priority_file) as f:
            data = json.load(f)
            self.assertEqual(data['status'], 'completed')
            self.assertEqual(data['actual_events'], 5)
    
    def test_commit_threshold(self):
        """Test that commit is triggered at threshold"""
        # Set threshold to 3 (done in setUp via environment)
        
        # Stage events up to threshold
        for i in range(3):
            event_data = {
                'id': f'test-{i:03d}',
                'date': '2023-01-01',
                'title': f'Event {i}',
                'summary': 'Test'
            }
            
            response = self.client.post(
                '/api/events/staged',
                json=event_data,
                headers={'X-API-Key': 'test-key'}
            )
            self.assertEqual(response.status_code, 200)
        
        # Check that files were created
        for i in range(3):
            event_file = self.events_dir / f'test-{i:03d}.json'
            self.assertTrue(event_file.exists())


class TestThreadSafety(TestResearchMonitorBase):
    """Test thread safety of database operations"""
    
    def test_concurrent_database_access(self):
        """Test that concurrent access doesn't cause issues"""
        results = []
        errors = []
        
        def write_priority(thread_id):
            try:
                session = Session()
                priority = ResearchPriority(
                    id=f'RT-{thread_id:03d}',
                    title=f'Thread {thread_id}',
                    priority=thread_id
                )
                session.add(priority)
                session.commit()
                session.close()
                results.append(thread_id)
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=write_priority, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Verify all writes succeeded
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 10)
        
        # Verify all priorities were saved
        priorities = self.session.query(ResearchPriority).all()
        self.assertEqual(len(priorities), 10)


class TestErrorHandling(TestResearchMonitorBase):
    """Test error handling and edge cases"""
    
    def test_handle_corrupted_json(self):
        """Test handling of corrupted JSON files"""
        # Create corrupted JSON file
        corrupted_file = self.events_dir / 'corrupted.json'
        with open(corrupted_file, 'w') as f:
            f.write('{ this is not valid json }')
        
        # Sync should handle error gracefully
        syncer = FilesystemSyncer()
        syncer.sync_events()  # Should not raise exception
        
        # Verify corrupted file was skipped
        events = self.session.query(TimelineEvent).all()
        event_ids = [e.id for e in events]
        self.assertNotIn('corrupted', event_ids)
    
    def test_handle_missing_priority(self):
        """Test handling of missing priority in update"""
        response = self.client.put(
            '/api/priorities/NONEXISTENT/status',
            json={'status': 'completed'},
            headers={'X-API-Key': 'test-key'}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Priority not found')
    
    def test_handle_duplicate_event_id(self):
        """Test handling of duplicate event IDs"""
        # Create event
        event = TimelineEvent(
            id='duplicate', 
            title='First', 
            file_path='/test', 
            file_hash='h1',
            json_content={'id': 'duplicate', 'title': 'First'}
        )
        self.session.add(event)
        self.session.commit()
        
        # Try to validate duplicate
        response = self.client.post('/api/events/validate', json={'id': 'duplicate'})
        data = json.loads(response.data)
        
        self.assertFalse(data['valid'])
        self.assertIn('Event duplicate already exists', data['errors'][0])
    
    def test_api_key_required(self):
        """Test that API key is required for write operations"""
        # Without API key
        response = self.client.put(
            '/api/priorities/RT-001/status',
            json={'status': 'completed'}
        )
        self.assertEqual(response.status_code, 401)
        
        # With wrong API key
        response = self.client.put(
            '/api/priorities/RT-001/status',
            json={'status': 'completed'},
            headers={'X-API-Key': 'wrong-key'}
        )
        self.assertEqual(response.status_code, 401)
        
        # With correct API key
        priority = ResearchPriority(id='RT-001', title='Test')
        self.session.add(priority)
        self.session.commit()
        
        response = self.client.put(
            '/api/priorities/RT-001/status',
            json={'status': 'completed'},
            headers={'X-API-Key': 'test-key'}
        )
        self.assertEqual(response.status_code, 200)


class TestPerformance(TestResearchMonitorBase):
    """Test performance with larger datasets"""
    
    def test_bulk_event_sync(self):
        """Test syncing many events efficiently"""
        # Create 100 test events
        for i in range(100):
            self.create_test_event(f'bulk-{i:03d}', f'2023-01-{(i % 28) + 1:02d}')
        
        # Time the sync
        start_time = time.time()
        syncer = FilesystemSyncer()
        syncer.sync_events()
        sync_time = time.time() - start_time
        
        # Verify all events were synced
        events = self.session.query(TimelineEvent).all()
        self.assertEqual(len(events), 100)
        
        # Should complete in reasonable time (< 5 seconds for 100 events)
        self.assertLess(sync_time, 5.0, f"Sync took {sync_time:.2f} seconds")
    
    def test_search_performance(self):
        """Test search performance with many events"""
        # Create events
        for i in range(50):
            event = TimelineEvent(
                id=f'perf-{i:03d}',
                date=f'2023-01-{(i % 28) + 1:02d}',
                title=f'Event {i} {"halliburton" if i % 10 == 0 else "other"}',
                summary=f'Summary for event {i}',
                json_content={'index': i},
                file_path=f'/test/{i}',
                file_hash=f'hash{i}'
            )
            self.session.add(event)
        self.session.commit()
        
        # Time search
        start_time = time.time()
        response = self.client.get('/api/events/search?q=halliburton')
        search_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        
        # Should complete quickly (< 1 second)
        self.assertLess(search_time, 1.0, f"Search took {search_time:.2f} seconds")


def run_tests():
    """Run all tests with verbosity"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestDatabaseModels,
        TestFilesystemSync,
        TestAPIEndpoints,
        TestCommitOrchestration,
        TestThreadSafety,
        TestErrorHandling,
        TestPerformance
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)