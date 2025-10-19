#!/usr/bin/env python3
"""
Tests for ResearchAPI.

Comprehensive test coverage for the research_api.py module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

from research_api import ResearchAPI, ResearchAPIError


class TestResearchAPIInit(unittest.TestCase):
    """Test ResearchAPI initialization"""

    def test_init_with_default_url(self):
        """Test API initializes with default URL from env"""
        with patch.dict('os.environ', {}, clear=True):
            api = ResearchAPI()
            self.assertEqual(api.base_url, 'http://localhost:5558')

    def test_init_with_env_url(self):
        """Test API uses RESEARCH_MONITOR_URL env var"""
        with patch.dict('os.environ', {'RESEARCH_MONITOR_URL': 'http://custom:9999'}):
            api = ResearchAPI()
            self.assertEqual(api.base_url, 'http://custom:9999')

    def test_init_with_custom_url(self):
        """Test API initializes with custom URL parameter"""
        api = ResearchAPI(base_url='http://test:8080')
        self.assertEqual(api.base_url, 'http://test:8080')

    def test_init_with_default_api_key(self):
        """Test API uses default api_key"""
        with patch.dict('os.environ', {}, clear=True):
            api = ResearchAPI()
            self.assertEqual(api.api_key, 'test')

    def test_init_with_env_api_key(self):
        """Test API uses RESEARCH_MONITOR_API_KEY env var"""
        with patch.dict('os.environ', {'RESEARCH_MONITOR_API_KEY': 'custom-key'}):
            api = ResearchAPI()
            self.assertEqual(api.api_key, 'custom-key')

    def test_init_with_custom_api_key(self):
        """Test API initializes with custom api_key parameter"""
        api = ResearchAPI(api_key='my-key')
        self.assertEqual(api.api_key, 'my-key')

    def test_init_sets_headers(self):
        """Test that session headers are configured"""
        api = ResearchAPI(api_key='test-key')
        self.assertEqual(api.session.headers['Content-Type'], 'application/json')
        self.assertEqual(api.session.headers['X-API-Key'], 'test-key')


class TestResearchAPIMakeRequest(unittest.TestCase):
    """Test ResearchAPI._make_request() method"""

    def setUp(self):
        """Set up test API"""
        self.api = ResearchAPI(base_url='http://localhost:5558', api_key='test')

    @patch('research_api.requests.Session.get')
    def test_make_request_get(self, mock_get):
        """Test GET request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_get.return_value = mock_response

        result = self.api._make_request('GET', 'test', {'param': 'value'})

        self.assertEqual(result, {'status': 'success'})
        mock_get.assert_called_once()

    @patch('research_api.requests.Session.post')
    def test_make_request_post(self, mock_post):
        """Test POST request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'created': True}
        mock_post.return_value = mock_response

        result = self.api._make_request('POST', 'create', {'data': 'value'})

        self.assertEqual(result, {'created': True})
        mock_post.assert_called_once()

    @patch('research_api.requests.Session.put')
    def test_make_request_put(self, mock_put):
        """Test PUT request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'updated': True}
        mock_put.return_value = mock_response

        result = self.api._make_request('PUT', 'update', {'data': 'value'})

        self.assertEqual(result, {'updated': True})
        mock_put.assert_called_once()

    @patch('research_api.requests.Session.get')
    def test_make_request_error(self, mock_get):
        """Test request handles error response"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = 'Not found'
        mock_get.return_value = mock_response

        with self.assertRaises(ResearchAPIError) as cm:
            self.api._make_request('GET', 'test')

        self.assertIn('API Error 404', str(cm.exception))

    @patch('research_api.requests.Session.get')
    def test_make_request_network_error(self, mock_get):
        """Test request handles network errors"""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError('Network error')

        with self.assertRaises(ResearchAPIError) as cm:
            self.api._make_request('GET', 'test')

        self.assertIn('Request failed', str(cm.exception))

    @patch('research_api.requests.Session.get')
    def test_make_request_json_decode_error(self, mock_get):
        """Test request handles invalid JSON response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError('test', 'test', 0)
        mock_response.text = 'Invalid JSON'
        mock_get.return_value = mock_response

        with self.assertRaises(ResearchAPIError) as cm:
            self.api._make_request('GET', 'test')

        self.assertIn('Invalid JSON response', str(cm.exception))

    def test_make_request_unsupported_method(self):
        """Test request rejects unsupported HTTP methods"""
        with self.assertRaises(ResearchAPIError) as cm:
            self.api._make_request('DELETE', 'test')

        self.assertIn('Unsupported HTTP method', str(cm.exception))


class TestResearchAPIPriorityManagement(unittest.TestCase):
    """Test priority management methods"""

    def setUp(self):
        """Set up test API"""
        self.api = ResearchAPI(base_url='http://localhost:5558')

    @patch.object(ResearchAPI, '_make_request')
    def test_reserve_priority(self, mock_request):
        """Test reserve_priority"""
        mock_request.return_value = {
            'id': 'RP-123',
            'title': 'Research topic',
            'status': 'reserved'
        }

        result = self.api.reserve_priority('agent-1')

        self.assertEqual(result['id'], 'RP-123')
        self.assertEqual(result['status'], 'reserved')
        mock_request.assert_called_once_with('POST', 'priorities/next', {'agent_id': 'agent-1'})

    @patch.object(ResearchAPI, '_make_request')
    def test_get_next_priority_info(self, mock_request):
        """Test get_next_priority_info"""
        mock_request.return_value = {'id': 'RP-124', 'title': 'Next topic'}

        result = self.api.get_next_priority_info()

        self.assertEqual(result['id'], 'RP-124')
        mock_request.assert_called_once_with('GET', 'priorities/next')

    @patch.object(ResearchAPI, '_make_request')
    def test_get_next_priority_info_no_priorities(self, mock_request):
        """Test get_next_priority_info handles no priorities gracefully"""
        mock_request.side_effect = ResearchAPIError('No priorities')

        result = self.api.get_next_priority_info()

        self.assertEqual(result, {})

    @patch.object(ResearchAPI, '_make_request')
    def test_confirm_work_started(self, mock_request):
        """Test confirm_work_started"""
        mock_request.return_value = {'status': 'in_progress'}

        result = self.api.confirm_work_started('RP-123')

        self.assertEqual(result['status'], 'in_progress')
        mock_request.assert_called_once_with('PUT', 'priorities/RP-123/start')

    @patch.object(ResearchAPI, '_make_request')
    def test_update_priority_status(self, mock_request):
        """Test update_priority_status"""
        mock_request.return_value = {'status': 'success'}

        result = self.api.update_priority_status(
            'RP-123',
            'completed',
            actual_events=3,
            notes='Done'
        )

        self.assertEqual(result['status'], 'success')
        # Verify data payload
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][1], 'priorities/RP-123/status')
        self.assertEqual(call_args[0][2]['status'], 'completed')
        self.assertEqual(call_args[0][2]['actual_events'], 3)

    @patch.object(ResearchAPI, '_make_request')
    def test_complete_priority(self, mock_request):
        """Test complete_priority convenience method"""
        mock_request.return_value = {'status': 'success'}

        result = self.api.complete_priority('RP-123', events_created=5, notes='Completed')

        self.assertEqual(result['status'], 'success')
        # Verify it calls update_priority_status with correct params
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][2]['status'], 'completed')
        self.assertEqual(call_args[0][2]['actual_events'], 5)


class TestResearchAPIEventSubmission(unittest.TestCase):
    """Test event submission methods"""

    def setUp(self):
        """Set up test API"""
        self.api = ResearchAPI(base_url='http://localhost:5558')

    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_submit_events_delegates_to_batch(self, mock_batch):
        """Test submit_events uses batch endpoint"""
        events = [{'id': 'test', 'title': 'Test'}]
        mock_batch.return_value = {'status': 'success'}

        result = self.api.submit_events(events, 'RP-123')

        self.assertEqual(result['status'], 'success')
        mock_batch.assert_called_once_with(events, 'RP-123')

    @patch.object(ResearchAPI, '_make_request')
    def test_submit_events_batch(self, mock_request):
        """Test submit_events_batch"""
        events = [{'date': '2025-01-15', 'title': 'Test Event'}]
        mock_request.return_value = {
            'successful_events': 1,
            'failed_events': 0,
            'results': [{'status': 'success'}]
        }

        result = self.api.submit_events_batch(events, 'RP-123', auto_fix=False)

        self.assertEqual(result['successful_events'], 1)
        mock_request.assert_called_once_with('POST', 'events/batch', {
            'events': events,
            'priority_id': 'RP-123'
        })

    @patch.object(ResearchAPI, '_make_request')
    def test_submit_events_legacy(self, mock_request):
        """Test submit_events_legacy"""
        events = [{'title': 'Test'}]
        mock_request.return_value = {'status': 'success'}

        result = self.api.submit_events_legacy(events, 'RP-123')

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['events_submitted'], 1)


class TestResearchAPIValidation(unittest.TestCase):
    """Test validation methods"""

    def setUp(self):
        """Set up test API"""
        self.api = ResearchAPI(base_url='http://localhost:5558')

    @patch.object(ResearchAPI, '_make_request')
    def test_validate_event(self, mock_request):
        """Test validate_event"""
        mock_request.return_value = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        event = {'date': '2025-01-15', 'title': 'Test'}
        result = self.api.validate_event(event, auto_fix=False)

        self.assertTrue(result['valid'])
        mock_request.assert_called_once_with('POST', 'events/validate', event)

    @patch.object(ResearchAPI, '_make_request')
    def test_search_events(self, mock_request):
        """Test search_events"""
        mock_request.return_value = {
            'events': [{'id': '1'}, {'id': '2'}]
        }

        result = self.api.search_events('test query', limit=10)

        self.assertEqual(len(result), 2)
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][2]['q'], 'test query')
        self.assertEqual(call_args[0][2]['limit'], 10)


class TestResearchAPISystemInfo(unittest.TestCase):
    """Test system information methods"""

    def setUp(self):
        """Set up test API"""
        self.api = ResearchAPI(base_url='http://localhost:5558')

    @patch.object(ResearchAPI, '_make_request')
    def test_get_stats(self, mock_request):
        """Test get_stats"""
        mock_request.return_value = {
            'events': {'total': 1500},
            'priorities': {'pending': 10}
        }

        result = self.api.get_stats()

        self.assertEqual(result['events']['total'], 1500)
        mock_request.assert_called_once_with('GET', 'stats')

    @patch.object(ResearchAPI, '_make_request')
    def test_get_commit_status(self, mock_request):
        """Test get_commit_status"""
        mock_request.return_value = {
            'commit_needed': True,
            'events_staged': 12
        }

        result = self.api.get_commit_status()

        self.assertTrue(result['commit_needed'])
        mock_request.assert_called_once_with('GET', 'commit/status')

    @patch.object(ResearchAPI, '_make_request')
    def test_reset_commit_counter(self, mock_request):
        """Test reset_commit_counter"""
        mock_request.return_value = {'status': 'success'}

        result = self.api.reset_commit_counter()

        self.assertEqual(result['status'], 'success')
        mock_request.assert_called_once_with('POST', 'commit/reset')

    @patch.object(ResearchAPI, '_make_request')
    def test_health_check(self, mock_request):
        """Test health_check"""
        mock_request.return_value = {
            'status': 'healthy',
            'database': 'connected'
        }

        result = self.api.health_check()

        self.assertEqual(result['status'], 'healthy')
        mock_request.assert_called_once_with('GET', 'server/health')

    @patch.object(ResearchAPI, '_make_request')
    def test_shutdown_server(self, mock_request):
        """Test shutdown_server"""
        mock_request.return_value = {'status': 'shutting down'}

        result = self.api.shutdown_server()

        self.assertEqual(result['status'], 'shutting down')
        mock_request.assert_called_once_with('POST', 'server/shutdown')


class TestResearchAPIConvenienceMethods(unittest.TestCase):
    """Test convenience methods"""

    def setUp(self):
        """Set up test API"""
        self.api = ResearchAPI(base_url='http://localhost:5558')

    def test_create_simple_event(self):
        """Test create_simple_event"""
        event = self.api.create_simple_event(
            date='2025-01-15',
            title='Test Event',
            summary='Test summary',
            actors=['Actor1'],
            sources=['http://example.com'],
            importance=8,
            tags=['tag1']
        )

        self.assertEqual(event['date'], '2025-01-15')
        self.assertEqual(event['title'], 'Test Event')
        self.assertEqual(event['importance'], 8)
        self.assertEqual(event['status'], 'confirmed')
        self.assertIn('Actor1', event['actors'])

    def test_create_simple_event_minimal(self):
        """Test create_simple_event with minimal params"""
        event = self.api.create_simple_event(
            date='2025-01-15',
            title='Minimal Event',
            summary='Summary'
        )

        self.assertEqual(event['date'], '2025-01-15')
        self.assertEqual(event['importance'], 5)  # default
        self.assertNotIn('actors', event)
        self.assertNotIn('sources', event)

    @patch.object(ResearchAPI, 'reserve_priority')
    @patch.object(ResearchAPI, 'confirm_work_started')
    def test_research_workflow(self, mock_confirm, mock_reserve):
        """Test research_workflow"""
        mock_reserve.return_value = {
            'id': 'RP-123',
            'title': 'Research topic'
        }
        mock_confirm.return_value = {'status': 'in_progress'}

        result = self.api.research_workflow('agent-1')

        self.assertEqual(result['agent_id'], 'agent-1')
        self.assertEqual(result['priority_id'], 'RP-123')
        self.assertTrue(result['workflow_ready'])
        mock_reserve.assert_called_once_with('agent-1')
        mock_confirm.assert_called_once_with('RP-123')

    @patch.object(ResearchAPI, 'reserve_priority')
    def test_research_workflow_error(self, mock_reserve):
        """Test research_workflow handles errors"""
        mock_reserve.side_effect = ResearchAPIError('No priorities')

        result = self.api.research_workflow('agent-1')

        self.assertFalse(result['success'])
        self.assertIn('No priorities', result['error'])


class TestResearchAPIAutoFixFeatures(unittest.TestCase):
    """Test auto_fix parameter and error handling"""

    def setUp(self):
        """Set up test API"""
        self.api = ResearchAPI(base_url='http://localhost:5558')

    @patch('builtins.__import__', side_effect=ImportError)
    @patch.object(ResearchAPI, '_make_request')
    def test_submit_events_batch_auto_fix_import_error(self, mock_request, mock_import):
        """Test submit_events_batch handles missing enhanced validator"""
        events = [{'date': '2025-01-15', 'title': 'Test'}]
        mock_request.return_value = {'successful_events': 1, 'failed_events': 0}

        result = self.api.submit_events_batch(events, 'RP-123', auto_fix=True)

        self.assertEqual(result['successful_events'], 1)
        # Verify it continues without auto_fix when enhanced validator unavailable
        mock_request.assert_called_once()

    @patch('builtins.__import__', side_effect=ImportError)
    @patch.object(ResearchAPI, '_make_request')
    def test_validate_event_auto_fix_import_error(self, mock_request, mock_import):
        """Test validate_event handles missing enhanced validator"""
        event = {'date': '2025-01-15', 'title': 'Test'}
        mock_request.return_value = {'valid': True, 'errors': []}

        result = self.api.validate_event(event, auto_fix=True)

        self.assertTrue(result['valid'])
        # Verify it falls back to API validation
        mock_request.assert_called_once_with('POST', 'events/validate', event)

    @patch('builtins.__import__', side_effect=ImportError)
    @patch.object(ResearchAPI, 'validate_event')
    def test_validate_events_batch_fallback(self, mock_validate, mock_import):
        """Test validate_events_batch falls back to individual validation"""
        events = [
            {'date': '2025-01-15', 'title': 'Event 1'},
            {'date': '2025-01-16', 'title': 'Event 2'}
        ]
        mock_validate.side_effect = [
            {'valid': True, 'errors': []},
            {'valid': False, 'errors': ['Missing field: actors']}
        ]

        result = self.api.validate_events_batch(events, auto_fix=True)

        self.assertEqual(result['summary']['total_events'], 2)
        self.assertEqual(result['summary']['valid_events'], 1)
        self.assertEqual(result['summary']['total_errors'], 1)
        self.assertEqual(len(result['results']), 2)


class TestResearchAPIFixAndRetry(unittest.TestCase):
    """Test fix_and_retry_events method"""

    def setUp(self):
        """Set up test API"""
        self.api = ResearchAPI(base_url='http://localhost:5558')

    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_fix_missing_actors(self, mock_submit):
        """Test automatic fixing of missing actors field"""
        failed_results = [{
            'status': 'failed',
            'index': 0,
            'errors': ['Missing required field: actors']
        }]
        events = [{'date': '2025-01-15', 'title': 'Test Event'}]
        mock_submit.return_value = {'successful_events': 1}

        result = self.api.fix_and_retry_events(failed_results, events, 'RP-123')

        # Verify actors were added
        fixed_call = mock_submit.call_args[0][0]
        self.assertEqual(fixed_call[0]['actors'], ['Unknown Actor'])
        self.assertEqual(result['successful_events'], 1)

    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_fix_missing_sources(self, mock_submit):
        """Test automatic fixing of missing sources field"""
        failed_results = [{
            'status': 'failed',
            'index': 0,
            'errors': ['Missing required field: sources']
        }]
        events = [{'date': '2025-01-15', 'title': 'Test Event'}]
        mock_submit.return_value = {'successful_events': 1}

        result = self.api.fix_and_retry_events(failed_results, events, 'RP-123')

        # Verify sources were added
        fixed_call = mock_submit.call_args[0][0]
        self.assertIn('sources', fixed_call[0])
        self.assertEqual(len(fixed_call[0]['sources']), 1)
        self.assertEqual(fixed_call[0]['sources'][0]['title'], 'Source needed')

    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_fix_missing_tags(self, mock_submit):
        """Test automatic fixing of missing tags field"""
        failed_results = [{
            'status': 'failed',
            'index': 0,
            'errors': ['Missing required field: tags']
        }]
        events = [{'date': '2025-01-15', 'title': 'Test Event'}]
        mock_submit.return_value = {'successful_events': 1}

        result = self.api.fix_and_retry_events(failed_results, events, 'RP-123')

        # Verify tags were added
        fixed_call = mock_submit.call_args[0][0]
        self.assertEqual(fixed_call[0]['tags'], ['needs_tags'])

    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_fix_missing_importance(self, mock_submit):
        """Test automatic fixing of missing importance field"""
        failed_results = [{
            'status': 'failed',
            'index': 0,
            'errors': ['Missing required field: importance']
        }]
        events = [{'date': '2025-01-15', 'title': 'Test Event'}]
        mock_submit.return_value = {'successful_events': 1}

        result = self.api.fix_and_retry_events(failed_results, events, 'RP-123')

        # Verify importance was added
        fixed_call = mock_submit.call_args[0][0]
        self.assertEqual(fixed_call[0]['importance'], 5)

    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_fix_invalid_date_format(self, mock_submit):
        """Test automatic fixing of date format (MM/DD/YYYY to YYYY-MM-DD)"""
        failed_results = [{
            'status': 'failed',
            'index': 0,
            'errors': ['Date must be YYYY-MM-DD format']
        }]
        events = [{'date': '1/15/2025', 'title': 'Test Event'}]
        mock_submit.return_value = {'successful_events': 1}

        result = self.api.fix_and_retry_events(failed_results, events, 'RP-123')

        # Verify date was fixed
        fixed_call = mock_submit.call_args[0][0]
        self.assertEqual(fixed_call[0]['date'], '2025-01-15')

    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_fix_multiple_fields(self, mock_submit):
        """Test fixing multiple fields in single event"""
        failed_results = [{
            'status': 'failed',
            'index': 0,
            'errors': [
                'Missing required field: actors',
                'Missing required field: tags',
                'Missing required field: importance'
            ]
        }]
        events = [{'date': '2025-01-15', 'title': 'Test Event'}]
        mock_submit.return_value = {'successful_events': 1}

        result = self.api.fix_and_retry_events(failed_results, events, 'RP-123')

        # Verify all fields were fixed
        fixed_call = mock_submit.call_args[0][0]
        self.assertEqual(fixed_call[0]['actors'], ['Unknown Actor'])
        self.assertEqual(fixed_call[0]['tags'], ['needs_tags'])
        self.assertEqual(fixed_call[0]['importance'], 5)

    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_no_fixes_applied_still_retries(self, mock_submit):
        """Test when no automatic fixes match but event is still retried"""
        failed_results = [{
            'status': 'failed',
            'index': 0,
            'errors': ['Unknown error type']
        }]
        events = [{'date': '2025-01-15', 'title': 'Test Event'}]
        mock_submit.return_value = {'successful_events': 0, 'failed_events': 1}

        result = self.api.fix_and_retry_events(failed_results, events, 'RP-123')

        # Event is still resubmitted even if no fixes were applied
        mock_submit.assert_called_once()
        self.assertEqual(result['failed_events'], 1)

    def test_no_failed_events_in_results(self):
        """Test when failed_results list is empty"""
        failed_results = []
        events = [{'date': '2025-01-15', 'title': 'Test Event'}]

        result = self.api.fix_and_retry_events(failed_results, events, 'RP-123')

        # No events to fix, returns no_fixes_applied
        self.assertEqual(result['status'], 'no_fixes_applied')
        self.assertIn('No automatic fixes', result['message'])


class TestResearchAPISubmitWithRetry(unittest.TestCase):
    """Test submit_events_with_retry method"""

    def setUp(self):
        """Set up test API"""
        self.api = ResearchAPI(base_url='http://localhost:5558')

    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_success_no_retry_needed(self, mock_submit):
        """Test successful submission with no retries needed"""
        mock_submit.return_value = {
            'successful_events': 2,
            'failed_events': 0,
            'results': []
        }
        events = [
            {'date': '2025-01-15', 'title': 'Event 1'},
            {'date': '2025-01-16', 'title': 'Event 2'}
        ]

        result = self.api.submit_events_with_retry(events, 'RP-123', max_retries=2)

        self.assertEqual(result['successful_events'], 2)
        self.assertEqual(result['failed_events'], 0)
        mock_submit.assert_called_once()

    @patch.object(ResearchAPI, 'fix_and_retry_events')
    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_retry_once_success(self, mock_submit, mock_fix):
        """Test submission with one retry that succeeds"""
        # First submission has 1 failure
        mock_submit.return_value = {
            'successful_events': 1,
            'failed_events': 1,
            'results': [
                {'status': 'success'},
                {'status': 'failed', 'index': 1, 'errors': ['Missing field: actors']}
            ]
        }
        # Retry succeeds
        mock_fix.return_value = {
            'successful_events': 1,
            'failed_events': 0
        }
        events = [
            {'date': '2025-01-15', 'title': 'Event 1'},
            {'date': '2025-01-16', 'title': 'Event 2'}
        ]

        result = self.api.submit_events_with_retry(events, 'RP-123', max_retries=2)

        # Verify retry was attempted
        self.assertEqual(result['retry_attempts'], 1)
        self.assertEqual(result['successful_events'], 2)
        self.assertEqual(result['failed_events'], 0)
        mock_fix.assert_called_once()

    @patch.object(ResearchAPI, 'fix_and_retry_events')
    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_max_retries_exhausted(self, mock_submit, mock_fix):
        """Test submission with max retries exhausted"""
        # All submissions have failures
        mock_submit.return_value = {
            'successful_events': 0,
            'failed_events': 2,
            'results': [
                {'status': 'failed', 'index': 0, 'errors': ['Error 1']},
                {'status': 'failed', 'index': 1, 'errors': ['Error 2']}
            ]
        }
        # Retries also fail
        mock_fix.return_value = {
            'successful_events': 0,
            'failed_events': 2
        }
        events = [
            {'date': '2025-01-15', 'title': 'Event 1'},
            {'date': '2025-01-16', 'title': 'Event 2'}
        ]

        result = self.api.submit_events_with_retry(events, 'RP-123', max_retries=2)

        # Verify max retries were attempted
        self.assertEqual(result['retry_attempts'], 2)
        self.assertEqual(result['successful_events'], 0)
        self.assertEqual(result['failed_events'], 2)
        self.assertEqual(mock_fix.call_count, 2)

    @patch.object(ResearchAPI, 'fix_and_retry_events')
    @patch.object(ResearchAPI, 'submit_events_batch')
    def test_partial_retry_success(self, mock_submit, mock_fix):
        """Test submission with partial success on retry"""
        # First submission has 2 failures
        mock_submit.return_value = {
            'successful_events': 1,
            'failed_events': 2,
            'results': [
                {'status': 'success'},
                {'status': 'failed', 'index': 1, 'errors': ['Error 1']},
                {'status': 'failed', 'index': 2, 'errors': ['Error 2']}
            ]
        }
        # Retry fixes 1 event
        mock_fix.return_value = {
            'successful_events': 1,
            'failed_events': 1
        }
        events = [
            {'date': '2025-01-15', 'title': 'Event 1'},
            {'date': '2025-01-16', 'title': 'Event 2'},
            {'date': '2025-01-17', 'title': 'Event 3'}
        ]

        result = self.api.submit_events_with_retry(events, 'RP-123', max_retries=1)

        # Verify partial success tracking
        self.assertEqual(result['retry_attempts'], 1)
        self.assertEqual(result['successful_events'], 2)  # 1 initial + 1 retry
        self.assertEqual(result['failed_events'], 1)  # 2 - 1
        self.assertIn('retry_result', result)


if __name__ == '__main__':
    unittest.main()
