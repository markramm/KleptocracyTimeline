#!/usr/bin/env python3
"""
Tests for research_cli.py - CLI wrapper and command handling.

Tests focus on CLI-specific functionality:
- ResearchCLIWrapper class
- _make_request() success/error handling
- JSON output formatting
- Sample command methods
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

# Import the CLI wrapper
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from research_cli import ResearchCLIWrapper


class TestResearchCLIWrapperInit(unittest.TestCase):
    """Test ResearchCLIWrapper initialization"""

    def test_init_with_default_url(self):
        """Test wrapper initializes with default URL"""
        wrapper = ResearchCLIWrapper()
        self.assertIsNotNone(wrapper.client)
        self.assertEqual(wrapper.api_key, "test-key")

    def test_init_with_custom_url(self):
        """Test wrapper initializes with custom URL"""
        wrapper = ResearchCLIWrapper(base_url="http://custom:9999")
        self.assertIsNotNone(wrapper.client)
        # Verify client was initialized with custom URL
        self.assertEqual(wrapper.client.base_url, "http://custom:9999")


class TestResearchCLIWrapperMakeRequest(unittest.TestCase):
    """Test ResearchCLIWrapper._make_request() method"""

    def setUp(self):
        """Set up test wrapper"""
        self.wrapper = ResearchCLIWrapper()

    def test_make_request_success(self):
        """Test _make_request returns structured success response"""
        mock_func = Mock(return_value={'result': 'data'})

        result = self.wrapper._make_request(mock_func, 'arg1', kwarg1='value1')

        self.assertTrue(result['success'])
        self.assertEqual(result['status_code'], 200)
        self.assertIn('timestamp', result)
        self.assertEqual(result['data'], {'result': 'data'})
        mock_func.assert_called_once_with('arg1', kwarg1='value1')

    def test_make_request_error(self):
        """Test _make_request handles exceptions and returns error response"""
        mock_func = Mock(side_effect=Exception("API Error"))

        result = self.wrapper._make_request(mock_func)

        self.assertFalse(result['success'])
        self.assertEqual(result['status_code'], 500)
        self.assertIn('timestamp', result)
        # Error is nested in a dict with 'message' and 'details'
        self.assertIn('error', result)
        self.assertIn('message', result['error'])
        self.assertIn('API Error', result['error']['message'])

    def test_make_request_includes_timestamp(self):
        """Test _make_request includes ISO timestamp"""
        mock_func = Mock(return_value={'data': 'test'})

        result = self.wrapper._make_request(mock_func)

        self.assertIn('timestamp', result)
        # Verify timestamp is ISO format with Z suffix
        self.assertTrue(result['timestamp'].endswith('Z'))
        # Verify it can be parsed as datetime
        datetime.fromisoformat(result['timestamp'].rstrip('Z'))


class TestResearchCLIWrapperSearchMethods(unittest.TestCase):
    """Test search-related wrapper methods"""

    def setUp(self):
        """Set up test wrapper"""
        self.wrapper = ResearchCLIWrapper()

    @patch('research_cli.TimelineResearchClient.search')
    def test_search_events(self, mock_search):
        """Test search_events wrapper method"""
        # TimelineResearchClient.search() returns a list directly
        mock_search.return_value = [{'id': '1', 'title': 'Test'}]

        result = self.wrapper.search_events(query='test', limit=10)

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], [{'id': '1', 'title': 'Test'}])
        # Wrapper calls search() with positional query arg and limit kwarg
        mock_search.assert_called_once_with('test', limit=10)

    @patch('research_cli.TimelineResearchClient.search')
    def test_search_events_error(self, mock_search):
        """Test search_events handles errors"""
        mock_search.side_effect = Exception("Search failed")

        result = self.wrapper.search_events(query='test')

        self.assertFalse(result['success'])
        # Error is nested in error dict
        self.assertIn('error', result)
        self.assertIn('Search failed', result['error']['message'])

    @patch('research_cli.TimelineResearchClient.get_actors')
    def test_list_actors(self, mock_get_actors):
        """Test list_actors wrapper method"""
        mock_get_actors.return_value = ['Trump', 'Musk', 'Thiel']

        result = self.wrapper.list_actors()

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], ['Trump', 'Musk', 'Thiel'])

    @patch('research_cli.TimelineResearchClient.get_tags')
    def test_list_tags(self, mock_get_tags):
        """Test list_tags wrapper method"""
        mock_get_tags.return_value = ['corruption', 'surveillance']

        result = self.wrapper.list_tags()

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], ['corruption', 'surveillance'])


class TestResearchCLIWrapperPriorityMethods(unittest.TestCase):
    """Test priority management wrapper methods"""

    def setUp(self):
        """Set up test wrapper"""
        self.wrapper = ResearchCLIWrapper()

    @patch('research_cli.TimelineResearchClient.get_next_priority')
    def test_get_next_priority(self, mock_get_priority):
        """Test get_next_priority wrapper method"""
        mock_get_priority.return_value = {
            'id': 'RP-123',
            'title': 'Research topic'
        }

        result = self.wrapper.get_next_priority()

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['id'], 'RP-123')

    @patch('research_cli.TimelineResearchClient.update_priority')
    def test_update_priority(self, mock_update):
        """Test update_priority wrapper method"""
        mock_update.return_value = {'status': 'success'}

        result = self.wrapper.update_priority(
            priority_id='RP-123',
            status='completed',
            notes='Done',
            actual_events=3
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['status'], 'success')
        # Wrapper passes all args positionally to client.update_priority()
        mock_update.assert_called_once_with('RP-123', 'completed', 'Done', 3)


class TestResearchCLIWrapperEventMethods(unittest.TestCase):
    """Test event management wrapper methods"""

    def setUp(self):
        """Set up test wrapper"""
        self.wrapper = ResearchCLIWrapper()

    @patch('research_cli.TimelineResearchClient.create_event')
    def test_create_event(self, mock_create):
        """Test create_event wrapper method"""
        mock_create.return_value = {'status': 'success', 'event_id': 'test-123'}
        event_data = {
            'date': '2025-01-15',
            'title': 'Test Event',
            'summary': 'Summary'
        }

        result = self.wrapper.create_event(event_data)

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['event_id'], 'test-123')
        # Wrapper only passes event_data, no save_yaml parameter
        mock_create.assert_called_once_with(event_data)

    @patch('research_cli.TimelineResearchClient.validate_event')
    def test_validate_event(self, mock_validate):
        """Test validate_event wrapper method"""
        mock_validate.return_value = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        event_data = {'date': '2025-01-15', 'title': 'Test'}

        result = self.wrapper.validate_event(event_data)

        self.assertTrue(result['success'])
        self.assertTrue(result['data']['valid'])


class TestResearchCLIWrapperStatsMethods(unittest.TestCase):
    """Test statistics and status wrapper methods"""

    def setUp(self):
        """Set up test wrapper"""
        self.wrapper = ResearchCLIWrapper()

    @patch('research_cli.TimelineResearchClient.get_stats')
    def test_get_stats(self, mock_get_stats):
        """Test get_stats wrapper method"""
        mock_get_stats.return_value = {
            'events': {'total': 1500},
            'priorities': {'pending': 10}
        }

        result = self.wrapper.get_stats()

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['events']['total'], 1500)

    @patch('research_cli.TimelineResearchClient.get_commit_status')
    def test_check_commit_status(self, mock_commit_status):
        """Test check_commit_status wrapper method"""
        mock_commit_status.return_value = {
            'commit_needed': True,
            'events_staged': 12
        }

        result = self.wrapper.check_commit_status()

        self.assertTrue(result['success'])
        self.assertTrue(result['data']['commit_needed'])


class TestResearchCLIWrapperQAMethods(unittest.TestCase):
    """Test QA system wrapper methods"""

    def setUp(self):
        """Set up test wrapper"""
        self.wrapper = ResearchCLIWrapper()

    @patch('research_cli.TimelineResearchClient.get_qa_queue')
    def test_get_qa_queue(self, mock_qa_queue):
        """Test get_qa_queue wrapper method"""
        mock_qa_queue.return_value = {
            'events': [{'id': '1'}],
            'total': 1
        }

        result = self.wrapper.get_qa_queue(limit=10, offset=0)

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['total'], 1)

    @patch('research_cli.TimelineResearchClient.get_qa_stats')
    def test_get_qa_stats(self, mock_qa_stats):
        """Test get_qa_stats wrapper method"""
        mock_qa_stats.return_value = {
            'total_events': 1500,
            'validated': 800
        }

        result = self.wrapper.get_qa_stats()

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['total_events'], 1500)

    @patch('research_cli.TimelineResearchClient.mark_event_validated')
    def test_mark_event_validated(self, mock_validate):
        """Test mark_event_validated wrapper method"""
        mock_validate.return_value = {'status': 'success'}

        result = self.wrapper.mark_event_validated(
            event_id='test-123',
            quality_score=9.0,
            validation_notes='Excellent'
        )

        self.assertTrue(result['success'])

    @patch('research_cli.TimelineResearchClient.mark_event_rejected')
    def test_mark_event_rejected(self, mock_reject):
        """Test mark_event_rejected wrapper method"""
        mock_reject.return_value = {'status': 'success'}

        result = self.wrapper.mark_event_rejected(
            event_id='test-123',
            rejection_reason='insufficient_sources',
            created_by='test-agent'
        )

        self.assertTrue(result['success'])


class TestResearchCLIWrapperResearchMethods(unittest.TestCase):
    """Test research enhancement wrapper methods"""

    def setUp(self):
        """Set up test wrapper"""
        self.wrapper = ResearchCLIWrapper()

    @patch('research_cli.TimelineResearchClient.get_events_missing_sources')
    def test_get_events_missing_sources(self, mock_missing):
        """Test get_events_missing_sources wrapper method"""
        mock_missing.return_value = [{'id': '1', 'sources': []}]

        result = self.wrapper.get_events_missing_sources(min_sources=2, limit=10)

        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 1)

    @patch('research_cli.TimelineResearchClient.get_validation_queue')
    def test_get_validation_queue(self, mock_queue):
        """Test get_validation_queue wrapper method"""
        mock_queue.return_value = [{'id': '1', 'importance': 8}]

        result = self.wrapper.get_validation_queue(limit=20)

        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 1)

    @patch('research_cli.TimelineResearchClient.get_research_candidates')
    def test_get_research_candidates(self, mock_candidates):
        """Test get_research_candidates wrapper method"""
        mock_candidates.return_value = [{'id': '1', 'importance': 9}]

        result = self.wrapper.get_research_candidates(min_importance=8, limit=5)

        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 1)


class TestResearchCLIWrapperValidationRunMethods(unittest.TestCase):
    """Test validation run wrapper methods"""

    def setUp(self):
        """Set up test wrapper"""
        self.wrapper = ResearchCLIWrapper()

    @patch('research_cli.TimelineResearchClient.list_validation_runs')
    def test_list_validation_runs(self, mock_list):
        """Test list_validation_runs wrapper method"""
        mock_list.return_value = {
            'runs': [{'id': 1, 'run_type': 'source_quality'}]
        }

        result = self.wrapper.list_validation_runs(status='active', limit=10)

        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']['runs']), 1)

    @patch('research_cli.TimelineResearchClient.create_validation_run')
    def test_create_validation_run(self, mock_create):
        """Test create_validation_run wrapper method"""
        mock_create.return_value = {'run_id': 1, 'status': 'active'}

        result = self.wrapper.create_validation_run(
            run_type='source_quality',
            target_count=30
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['run_id'], 1)

    @patch('research_cli.TimelineResearchClient.get_next_validation_event')
    def test_get_next_validation_event(self, mock_next):
        """Test get_next_validation_event wrapper method"""
        mock_next.return_value = {
            'run_event_id': 5,
            'event_id': 'test-123'
        }

        result = self.wrapper.get_next_validation_event(run_id=1, validator_id='agent-1')

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['event_id'], 'test-123')


class TestResearchCLIWrapperJSONOutput(unittest.TestCase):
    """Test JSON output formatting"""

    def setUp(self):
        """Set up test wrapper"""
        self.wrapper = ResearchCLIWrapper()

    @patch('research_cli.TimelineResearchClient.search')
    def test_json_output_is_valid(self, mock_search):
        """Test that all responses are valid JSON"""
        mock_search.return_value = [{'id': '1'}]

        result = self.wrapper.search_events(query='test')

        # Verify it can be serialized to JSON
        json_str = json.dumps(result)
        self.assertIsNotNone(json_str)
        # Verify it can be parsed back
        parsed = json.loads(json_str)
        self.assertEqual(parsed, result)

    @patch('research_cli.TimelineResearchClient.search')
    def test_success_response_structure(self, mock_search):
        """Test success response has required fields"""
        mock_search.return_value = [{'id': '1'}]

        result = self.wrapper.search_events(query='test')

        self.assertIn('success', result)
        self.assertIn('status_code', result)
        self.assertIn('timestamp', result)
        self.assertIn('data', result)
        self.assertTrue(result['success'])
        self.assertEqual(result['status_code'], 200)

    @patch('research_cli.TimelineResearchClient.search')
    def test_error_response_structure(self, mock_search):
        """Test error response has required fields"""
        mock_search.side_effect = Exception("Test error")

        result = self.wrapper.search_events(query='test')

        self.assertIn('success', result)
        self.assertIn('status_code', result)
        self.assertIn('timestamp', result)
        self.assertIn('error', result)
        self.assertFalse(result['success'])
        self.assertEqual(result['status_code'], 500)
        # Error should be a dict with message and details
        self.assertIsInstance(result['error'], dict)
        self.assertIn('message', result['error'])
        self.assertIn('details', result['error'])


if __name__ == '__main__':
    unittest.main()
