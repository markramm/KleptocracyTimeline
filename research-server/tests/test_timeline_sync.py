#!/usr/bin/env python3
"""
Tests for TimelineSyncService.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import tempfile
import shutil
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

from services.timeline_sync import TimelineSyncService
from services.git_service import GitService


class TestTimelineSyncService(unittest.TestCase):
    """Test TimelineSyncService operations"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.workspace = self.temp_dir / 'workspace'
        self.workspace.mkdir()

        # Create mock GitService
        self.git_service = Mock(spec=GitService)
        self.git_service.workspace = self.workspace

        # Create events directory
        self.events_dir = self.workspace / 'timeline' / 'data' / 'events'
        self.events_dir.mkdir(parents=True)

        self.sync_service = TimelineSyncService(self.git_service, self.events_dir)

    def tearDown(self):
        """Clean up temp directory"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_init_sets_correct_paths(self):
        """Test that initialization sets correct paths"""
        self.assertEqual(self.sync_service.git, self.git_service)
        self.assertEqual(self.sync_service.events_dir, self.events_dir)

    def test_import_from_repo_success_with_changes(self):
        """Test importing events when pull has changes"""
        # Mock successful pull with changes
        self.git_service.pull_latest.return_value = {
            'success': True,
            'new_commits': 2,
            'files_changed': [
                'timeline/data/events/2025-01-01--test-event.json',
                'README.md'
            ]
        }

        # Create test event file
        event_file = self.events_dir / '2025-01-01--test-event.json'
        test_event = {
            'id': '2025-01-01--test-event',
            'date': '2025-01-01',
            'title': 'Test Event',
            'summary': 'Test summary'
        }
        with open(event_file, 'w') as f:
            json.dump(test_event, f)

        result = self.sync_service.import_from_repo()

        self.assertTrue(result['pulled'])
        self.assertEqual(result['new_commits'], 2)
        self.assertEqual(len(result['files_changed']), 2)
        self.assertEqual(len(result['events']), 1)
        self.assertEqual(result['events'][0]['id'], '2025-01-01--test-event')

    def test_import_from_repo_pull_failure(self):
        """Test import when pull fails"""
        self.git_service.pull_latest.return_value = {
            'success': False,
            'error': 'Network error'
        }

        result = self.sync_service.import_from_repo()

        self.assertFalse(result['pulled'])
        self.assertGreater(len(result['errors']), 0)
        self.assertIn('Network error', result['errors'][0])

    def test_import_from_repo_no_changes(self):
        """Test import when no changes pulled"""
        self.git_service.pull_latest.return_value = {
            'success': True,
            'new_commits': 0,
            'files_changed': []
        }

        result = self.sync_service.import_from_repo()

        self.assertTrue(result['pulled'])
        self.assertEqual(result['new_commits'], 0)
        self.assertEqual(len(result['events']), 0)

    def test_load_event_file_success(self):
        """Test loading a valid event file"""
        event_file = self.events_dir / 'test-event.json'
        test_event = {
            'id': 'test-event',
            'date': '2025-01-01',
            'title': 'Test'
        }

        with open(event_file, 'w') as f:
            json.dump(test_event, f)

        loaded = self.sync_service._load_event_file(event_file)

        self.assertEqual(loaded['id'], 'test-event')
        self.assertEqual(loaded['date'], '2025-01-01')

    def test_prepare_export_files(self):
        """Test preparing events for export"""
        events = [
            {
                'id': '2025-01-01--event1',
                'date': '2025-01-01',
                'title': 'Event 1',
                'summary': 'Summary 1'
            },
            {
                'id': '2025-01-02--event2',
                'date': '2025-01-02',
                'title': 'Event 2',
                'summary': 'Summary 2'
            }
        ]

        files = self.sync_service.prepare_export_files(events)

        self.assertEqual(len(files), 2)

        # Check files were written
        event1_file = self.events_dir / '2025-01-01--event1.json'
        event2_file = self.events_dir / '2025-01-02--event2.json'

        self.assertTrue(event1_file.exists())
        self.assertTrue(event2_file.exists())

        # Verify content
        with open(event1_file) as f:
            data = json.load(f)
            self.assertEqual(data['id'], '2025-01-01--event1')

    def test_prepare_export_files_skips_events_without_id(self):
        """Test that events without ID are skipped"""
        events = [
            {
                'date': '2025-01-01',
                'title': 'Event without ID'
            }
        ]

        files = self.sync_service.prepare_export_files(events)

        self.assertEqual(len(files), 0)

    def test_get_sync_status(self):
        """Test getting sync status"""
        self.git_service.get_status.return_value = {
            'exists': True,
            'current_branch': 'main'
        }

        # Create some test events
        for i in range(3):
            event_file = self.events_dir / f'event{i}.json'
            with open(event_file, 'w') as f:
                json.dump({'id': f'event{i}'}, f)

        status = self.sync_service.get_sync_status()

        self.assertEqual(status['events_in_workspace'], 3)
        self.assertIn('git_status', status)
        self.assertIn('last_check', status)

    def test_list_workspace_events(self):
        """Test listing workspace events"""
        # Create test events
        event_ids = ['2025-01-01--event1', '2025-01-02--event2', '2025-01-03--event3']

        for event_id in event_ids:
            event_file = self.events_dir / f'{event_id}.json'
            with open(event_file, 'w') as f:
                json.dump({'id': event_id}, f)

        events = self.sync_service.list_workspace_events()

        self.assertEqual(len(events), 3)
        self.assertIn('2025-01-01--event1', events)
        self.assertIn('2025-01-02--event2', events)
        self.assertIn('2025-01-03--event3', events)

    def test_list_workspace_events_empty(self):
        """Test listing events when directory is empty"""
        events = self.sync_service.list_workspace_events()
        self.assertEqual(len(events), 0)

    def test_get_workspace_event_success(self):
        """Test getting a single event by ID"""
        event_id = '2025-01-01--test-event'
        event_data = {
            'id': event_id,
            'date': '2025-01-01',
            'title': 'Test Event'
        }

        event_file = self.events_dir / f'{event_id}.json'
        with open(event_file, 'w') as f:
            json.dump(event_data, f)

        retrieved = self.sync_service.get_workspace_event(event_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['id'], event_id)
        self.assertEqual(retrieved['title'], 'Test Event')

    def test_get_workspace_event_not_found(self):
        """Test getting non-existent event"""
        result = self.sync_service.get_workspace_event('nonexistent')
        self.assertIsNone(result)

    def test_validate_workspace_events_all_valid(self):
        """Test validating workspace with all valid events"""
        # Create valid events
        for i in range(3):
            event = {
                'id': f'event{i}',
                'date': '2025-01-01',
                'title': f'Event {i}',
                'summary': f'Summary {i}'
            }
            event_file = self.events_dir / f'event{i}.json'
            with open(event_file, 'w') as f:
                json.dump(event, f)

        result = self.sync_service.validate_workspace_events()

        self.assertEqual(result['valid'], 3)
        self.assertEqual(result['invalid'], 0)
        self.assertEqual(result['total'], 3)

    def test_validate_workspace_events_with_invalid(self):
        """Test validation with invalid events"""
        # Create valid event
        valid_event = {
            'id': 'valid',
            'date': '2025-01-01',
            'title': 'Valid',
            'summary': 'Valid summary'
        }
        with open(self.events_dir / 'valid.json', 'w') as f:
            json.dump(valid_event, f)

        # Create invalid event (missing required fields)
        invalid_event = {
            'id': 'invalid'
            # Missing date, title, summary
        }
        with open(self.events_dir / 'invalid.json', 'w') as f:
            json.dump(invalid_event, f)

        # Create malformed JSON
        with open(self.events_dir / 'malformed.json', 'w') as f:
            f.write('{ invalid json ')

        result = self.sync_service.validate_workspace_events()

        self.assertEqual(result['valid'], 1)
        self.assertEqual(result['invalid'], 2)
        self.assertEqual(result['total'], 3)
        self.assertGreater(len(result['errors']), 0)

    def test_validate_event_basic(self):
        """Test basic event validation"""
        valid_event = {
            'id': 'test',
            'date': '2025-01-01',
            'title': 'Test',
            'summary': 'Test summary'
        }

        invalid_event = {
            'id': 'test',
            'date': '2025-01-01'
            # Missing title and summary
        }

        self.assertTrue(self.sync_service._validate_event_basic(valid_event))
        self.assertFalse(self.sync_service._validate_event_basic(invalid_event))


if __name__ == '__main__':
    unittest.main()
