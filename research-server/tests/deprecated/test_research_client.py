#!/usr/bin/env python3
"""
Tests for TimelineResearchClient.

Comprehensive test coverage for the research_client.py module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

from research_client import TimelineResearchClient


class TestTimelineResearchClientInit(unittest.TestCase):
    """Test TimelineResearchClient initialization"""

    def test_init_with_default_url(self):
        """Test client initializes with default URL"""
        with patch('research_client.get_research_monitor_url', return_value='http://localhost:5558'):
            client = TimelineResearchClient()
            self.assertEqual(client.base_url, 'http://localhost:5558')

    def test_init_with_custom_url(self):
        """Test client initializes with custom URL"""
        client = TimelineResearchClient(base_url='http://custom:9999')
        self.assertEqual(client.base_url, 'http://custom:9999')

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from base URL"""
        client = TimelineResearchClient(base_url='http://localhost:5558/')
        self.assertEqual(client.base_url, 'http://localhost:5558')

    def test_init_sets_api_key(self):
        """Test that API key is set in session headers"""
        client = TimelineResearchClient(base_url='http://localhost:5558', api_key='custom-key')
        self.assertEqual(client.session.headers['X-API-Key'], 'custom-key')

    def test_init_sets_default_api_key(self):
        """Test that default API key is used"""
        client = TimelineResearchClient(base_url='http://localhost:5558')
        self.assertEqual(client.session.headers['X-API-Key'], 'test-key')

    def test_init_sets_content_type_header(self):
        """Test that Content-Type header is set"""
        client = TimelineResearchClient(base_url='http://localhost:5558')
        self.assertEqual(client.session.headers['Content-Type'], 'application/json')


class TestTimelineResearchClientRequest(unittest.TestCase):
    """Test TimelineResearchClient._request() method"""

    def setUp(self):
        """Set up test client"""
        self.client = TimelineResearchClient(base_url='http://localhost:5558')

    @patch('research_client.requests.Session.request')
    def test_request_success(self, mock_request):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success', 'data': []}
        mock_request.return_value = mock_response

        result = self.client._request('GET', '/api/test')

        self.assertEqual(result, {'status': 'success', 'data': []})
        mock_request.assert_called_once_with('GET', 'http://localhost:5558/api/test')

    @patch('research_client.requests.Session.request')
    def test_request_with_params(self, mock_request):
        """Test request with query parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'results': []}
        mock_request.return_value = mock_response

        result = self.client._request('GET', '/api/test', params={'q': 'search'})

        mock_request.assert_called_once_with('GET', 'http://localhost:5558/api/test', params={'q': 'search'})

    @patch('research_client.requests.Session.request')
    def test_request_error_with_json(self, mock_request):
        """Test request handles error response with JSON"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'Bad request'}
        mock_request.return_value = mock_response

        with self.assertRaises(Exception) as cm:
            self.client._request('GET', '/api/test')

        self.assertIn('API Error 400', str(cm.exception))
        self.assertIn('Bad request', str(cm.exception))

    @patch('research_client.requests.Session.request')
    def test_request_error_with_message(self, mock_request):
        """Test request handles error response with message field"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'message': 'Not found'}
        mock_request.return_value = mock_response

        with self.assertRaises(Exception) as cm:
            self.client._request('GET', '/api/test')

        self.assertIn('API Error 404', str(cm.exception))
        self.assertIn('Not found', str(cm.exception))

    @patch('research_client.requests.Session.request')
    def test_request_error_with_errors_list(self, mock_request):
        """Test request handles error response with errors list"""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {'errors': ['Field required', 'Invalid format']}
        mock_request.return_value = mock_response

        with self.assertRaises(Exception) as cm:
            self.client._request('GET', '/api/test')

        self.assertIn('API Error 422', str(cm.exception))
        self.assertIn('Field required', str(cm.exception))

    @patch('research_client.requests.Session.request')
    def test_request_error_non_json(self, mock_request):
        """Test request handles error response without JSON"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = json.JSONDecodeError('test', 'test', 0)
        mock_response.text = 'Internal Server Error'
        mock_request.return_value = mock_response

        with self.assertRaises(Exception) as cm:
            self.client._request('GET', '/api/test')

        self.assertIn('HTTP Error 500', str(cm.exception))
        self.assertIn('Internal Server Error', str(cm.exception))


class TestTimelineResearchClientSearch(unittest.TestCase):
    """Test search methods"""

    def setUp(self):
        """Set up test client"""
        self.client = TimelineResearchClient(base_url='http://localhost:5558')

    @patch('research_client.requests.Session.request')
    def test_search(self, mock_request):
        """Test search method returns full response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': [{'id': '1', 'title': 'Test'}],
            'count': 1,
            'page': 1
        }
        mock_request.return_value = mock_response

        result = self.client.search(query='test')

        self.assertEqual(result['count'], 1)
        self.assertEqual(len(result['events']), 1)

    @patch('research_client.requests.Session.request')
    def test_find_connections(self, mock_request):
        """Test search with additional filters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'events': [], 'count': 0}
        mock_request.return_value = mock_response

        self.client.search(query='test', actor='Trump', limit=10)

        # Verify params were passed correctly
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['params']['q'], 'test')
        self.assertEqual(call_args[1]['params']['actor'], 'Trump')
        self.assertEqual(call_args[1]['params']['limit'], 10)

    @patch('research_client.requests.Session.request')
    def test_search_events_returns_list(self, mock_request):
        """Test search_events returns just the events list"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': [{'id': '1'}, {'id': '2'}],
            'count': 2
        }
        mock_request.return_value = mock_response

        result = self.client.search_events(query='test')

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], '1')

    @patch('research_client.requests.Session.request')
    def test_search_events_empty_result(self, mock_request):
        """Test search_events handles empty results"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'events': [], 'count': 0}
        mock_request.return_value = mock_response

        result = self.client.search_events(query='nonexistent')

        self.assertEqual(result, [])


class TestTimelineResearchClientGetters(unittest.TestCase):
    """Test getter methods"""

    def setUp(self):
        """Set up test client"""
        self.client = TimelineResearchClient(base_url='http://localhost:5558')

    @patch('research_client.requests.Session.request')
    def test_get_event_success(self, mock_request):
        """Test get_event returns event"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'test-123', 'title': 'Test Event'}
        mock_request.return_value = mock_response

        result = self.client.get_event('test-123')

        self.assertEqual(result['id'], 'test-123')
        mock_request.assert_called_once_with('GET', 'http://localhost:5558/api/event/test-123')

    @patch('research_client.requests.Session.request')
    def test_get_event_not_found(self, mock_request):
        """Test get_event returns None for 404"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'error': 'Not found'}
        mock_request.return_value = mock_response

        result = self.client.get_event('nonexistent')

        self.assertIsNone(result)

    @patch('research_client.requests.Session.request')
    def test_get_actors(self, mock_request):
        """Test get_actors returns list of actors"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'actors': ['Trump', 'Musk', 'Thiel']}
        mock_request.return_value = mock_response

        result = self.client.get_actors()

        self.assertEqual(len(result), 3)
        self.assertIn('Trump', result)

    @patch('research_client.requests.Session.request')
    def test_get_tags(self, mock_request):
        """Test get_tags returns list of tags"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'tags': ['corruption', 'surveillance']}
        mock_request.return_value = mock_response

        result = self.client.get_tags()

        self.assertEqual(len(result), 2)
        self.assertIn('corruption', result)

    @patch('research_client.requests.Session.request')
    def test_get_stats(self, mock_request):
        """Test get_stats returns statistics"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': {'total': 1500},
            'actors': {'total': 200}
        }
        mock_request.return_value = mock_response

        result = self.client.get_stats()

        self.assertEqual(result['events']['total'], 1500)


class TestTimelineResearchClientEnhancementMethods(unittest.TestCase):
    """Test research enhancement methods"""

    def setUp(self):
        """Set up test client"""
        self.client = TimelineResearchClient(base_url='http://localhost:5558')

    @patch('research_client.requests.Session.request')
    def test_get_events_missing_sources(self, mock_request):
        """Test get_events_missing_sources"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': [{'id': '1', 'sources': []}]
        }
        mock_request.return_value = mock_response

        result = self.client.get_events_missing_sources(min_sources=2, limit=10)

        self.assertEqual(len(result), 1)
        # Verify params
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['params']['min_sources'], 2)
        self.assertEqual(call_args[1]['params']['limit'], 10)

    @patch('research_client.requests.Session.request')
    def test_get_validation_queue(self, mock_request):
        """Test get_validation_queue"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': [{'id': '1', 'importance': 8}]
        }
        mock_request.return_value = mock_response

        result = self.client.get_validation_queue(limit=20)

        self.assertEqual(len(result), 1)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['params']['limit'], 20)

    @patch('research_client.requests.Session.request')
    def test_get_broken_links(self, mock_request):
        """Test get_broken_links"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': [{'id': '1', 'sources': [{'url': 'bad'}]}]
        }
        mock_request.return_value = mock_response

        result = self.client.get_broken_links(limit=15)

        self.assertEqual(len(result), 1)

    @patch('research_client.requests.Session.request')
    def test_get_research_candidates(self, mock_request):
        """Test get_research_candidates"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': [{'id': '1', 'importance': 9}]
        }
        mock_request.return_value = mock_response

        result = self.client.get_research_candidates(min_importance=8, limit=5)

        self.assertEqual(len(result), 1)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['params']['min_importance'], 8)


class TestTimelineResearchClientQAMethods(unittest.TestCase):
    """Test QA system methods"""

    def setUp(self):
        """Set up test client"""
        self.client = TimelineResearchClient(base_url='http://localhost:5558')

    @patch('research_client.requests.Session.request')
    def test_get_qa_queue(self, mock_request):
        """Test get_qa_queue"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': [{'id': '1', 'qa_priority': 8.5}],
            'total': 1
        }
        mock_request.return_value = mock_response

        result = self.client.get_qa_queue(limit=10, offset=0)

        self.assertEqual(result['total'], 1)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['params']['limit'], 10)

    @patch('research_client.requests.Session.request')
    def test_get_qa_stats(self, mock_request):
        """Test get_qa_stats"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'total_events': 1500,
            'validated': 800,
            'pending': 700
        }
        mock_request.return_value = mock_response

        result = self.client.get_qa_stats()

        self.assertEqual(result['total_events'], 1500)
        self.assertEqual(result['validated'], 800)

    @patch('research_client.requests.Session.request')
    def test_mark_event_validated(self, mock_request):
        """Test mark_event_validated"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success', 'validated': True}
        mock_request.return_value = mock_response

        result = self.client.mark_event_validated(
            event_id='test-123',
            quality_score=9.0,
            validation_notes='Excellent sources'
        )

        self.assertEqual(result['status'], 'success')
        # Verify POST was made
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], 'POST')

    @patch('research_client.requests.Session.request')
    def test_mark_event_rejected(self, mock_request):
        """Test mark_event_rejected"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success', 'rejected': True}
        mock_request.return_value = mock_response

        result = self.client.mark_event_rejected(
            event_id='test-123',
            rejection_reason='insufficient_sources',
            created_by='test-agent'
        )

        self.assertEqual(result['status'], 'success')

    @patch('research_client.requests.Session.request')
    def test_calculate_qa_score(self, mock_request):
        """Test calculate_qa_score"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'qa_score': 7.5, 'issues': []}
        mock_request.return_value = mock_response

        event_data = {'id': 'test', 'importance': 8, 'sources': [{'url': 'test'}]}
        result = self.client.calculate_qa_score(event_data)

        self.assertEqual(result['qa_score'], 7.5)


class TestTimelineResearchClientPriorityMethods(unittest.TestCase):
    """Test priority management methods"""

    def setUp(self):
        """Set up test client"""
        self.client = TimelineResearchClient(base_url='http://localhost:5558')

    @patch('research_client.requests.Session.request')
    def test_get_next_priority(self, mock_request):
        """Test get_next_priority"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'RP-123',
            'title': 'Research Trump crypto',
            'priority': 'high'
        }
        mock_request.return_value = mock_response

        result = self.client.get_next_priority()

        self.assertEqual(result['id'], 'RP-123')
        self.assertEqual(result['title'], 'Research Trump crypto')

    @patch('research_client.requests.Session.request')
    def test_update_priority(self, mock_request):
        """Test update_priority"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success', 'updated': True}
        mock_request.return_value = mock_response

        result = self.client.update_priority(
            priority_id='RP-123',
            status='completed',
            notes='Research completed',
            actual_events=3
        )

        self.assertEqual(result['status'], 'success')
        # Verify PUT request was made
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], 'PUT')


class TestTimelineResearchClientEventMethods(unittest.TestCase):
    """Test event creation and update methods"""

    def setUp(self):
        """Set up test client"""
        self.client = TimelineResearchClient(base_url='http://localhost:5558')

    @patch('research_client.requests.Session.request')
    def test_create_event(self, mock_request):
        """Test create_event"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success', 'event_id': 'test-123'}
        mock_request.return_value = mock_response

        event_data = {
            'id': 'test-123',
            'date': '2025-01-15',
            'title': 'Test Event',
            'summary': 'Test summary'
        }
        result = self.client.create_event(event_data)

        self.assertEqual(result['status'], 'success')
        # Verify POST request
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], 'POST')

    @patch('research_client.requests.Session.request')
    def test_update_event(self, mock_request):
        """Test update_event"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success', 'updated': True}
        mock_request.return_value = mock_response

        event_data = {'title': 'Updated Title'}
        result = self.client.update_event('test-123', event_data)

        self.assertEqual(result['status'], 'success')
        # Verify PUT request
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], 'PUT')

    @patch('research_client.requests.Session.request')
    def test_validate_event(self, mock_request):
        """Test validate_event"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        mock_request.return_value = mock_response

        event_data = {'date': '2025-01-15', 'title': 'Test'}
        result = self.client.validate_event(event_data)

        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)


class TestTimelineResearchClientCommitMethods(unittest.TestCase):
    """Test commit status methods"""

    def setUp(self):
        """Set up test client"""
        self.client = TimelineResearchClient(base_url='http://localhost:5558')

    @patch('research_client.requests.Session.request')
    def test_get_commit_status(self, mock_request):
        """Test get_commit_status"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'commit_needed': True,
            'events_staged': 12
        }
        mock_request.return_value = mock_response

        result = self.client.get_commit_status()

        self.assertTrue(result['commit_needed'])
        self.assertEqual(result['events_staged'], 12)

    @patch('research_client.requests.Session.request')
    def test_reset_commit_counter(self, mock_request):
        """Test reset_commit_counter"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success', 'counter_reset': True}
        mock_request.return_value = mock_response

        result = self.client.reset_commit_counter()

        self.assertEqual(result['status'], 'success')


class TestTimelineResearchClientResearchNotes(unittest.TestCase):
    """Test research notes methods"""

    def setUp(self):
        """Set up test client"""
        self.client = TimelineResearchClient(base_url='http://localhost:5558')

    @patch('research_client.requests.Session.request')
    def test_add_research_note(self, mock_request):
        """Test add_research_note"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success', 'note_id': 'note-1'}
        mock_request.return_value = mock_response

        result = self.client.add_research_note(
            query='Trump crypto',
            results='Found 5 events',
            priority=7
        )

        self.assertEqual(result['status'], 'success')

    @patch('research_client.requests.Session.request')
    def test_get_research_notes(self, mock_request):
        """Test get_research_notes"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'notes': [{'id': 'note-1', 'query': 'test'}]
        }
        mock_request.return_value = mock_response

        result = self.client.get_research_notes(status='pending', limit=20)

        self.assertEqual(len(result), 1)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['params']['limit'], 20)


class TestTimelineResearchClientAdvancedSearch(unittest.TestCase):
    """Test advanced search and filter methods"""

    def setUp(self):
        """Set up test client"""
        with patch('research_client.get_research_monitor_url', return_value='http://localhost:5558'):
            self.client = TimelineResearchClient()

    @patch.object(TimelineResearchClient, 'search_events')
    def test_find_connections_actor_only(self, mock_search):
        """Test find_connections with actor filter"""
        mock_search.return_value = [{'id': '1', 'actors': ['Trump']}]

        result = self.client.find_connections(actor='Trump')

        self.assertEqual(len(result), 1)
        mock_search.assert_called_once_with(actor='Trump')

    @patch.object(TimelineResearchClient, 'search_events')
    def test_find_connections_tag_only(self, mock_search):
        """Test find_connections with tag filter"""
        mock_search.return_value = [{'id': '1', 'tags': ['corruption']}]

        result = self.client.find_connections(tag='corruption')

        self.assertEqual(len(result), 1)
        mock_search.assert_called_once_with(tag='corruption')

    @patch.object(TimelineResearchClient, 'search_events')
    def test_find_connections_date_range(self, mock_search):
        """Test find_connections with date range"""
        mock_search.return_value = [{'id': '1', 'date': '2025-01-15'}]

        result = self.client.find_connections(date_range=('2025-01-01', '2025-12-31'))

        self.assertEqual(len(result), 1)
        mock_search.assert_called_once_with(start_date='2025-01-01', end_date='2025-12-31')

    @patch.object(TimelineResearchClient, 'search_events')
    def test_find_connections_combined(self, mock_search):
        """Test find_connections with multiple filters"""
        mock_search.return_value = [{'id': '1'}]

        result = self.client.find_connections(
            actor='Trump',
            tag='corruption',
            date_range=('2020-01-01', '2025-12-31')
        )

        self.assertEqual(len(result), 1)
        mock_search.assert_called_once_with(
            actor='Trump',
            tag='corruption',
            start_date='2020-01-01',
            end_date='2025-12-31'
        )

    @patch.object(TimelineResearchClient, 'search_events')
    def test_find_connections_no_filters(self, mock_search):
        """Test find_connections with no filters"""
        mock_search.return_value = [{'id': '1'}, {'id': '2'}]

        result = self.client.find_connections()

        self.assertEqual(len(result), 2)
        mock_search.assert_called_once_with()

    @patch.object(TimelineResearchClient, 'search_events')
    def test_analyze_actor_with_events(self, mock_search):
        """Test analyze_actor with events found"""
        mock_search.return_value = [
            {
                'id': '1',
                'date': '2020-01-15',
                'actors': ['Trump', 'Musk'],
                'tags': ['corruption', 'tech'],
                'importance': 8
            },
            {
                'id': '2',
                'date': '2021-05-20',
                'actors': ['Trump', 'Thiel'],
                'tags': ['corruption', 'finance'],
                'importance': 9
            }
        ]

        result = self.client.analyze_actor('Trump')

        self.assertEqual(result['actor'], 'Trump')
        self.assertEqual(result['total_events'], 2)
        self.assertEqual(sorted(result['active_years']), ['2020', '2021'])
        self.assertIn('corruption', result['common_tags'])
        self.assertIn('Musk', result['frequent_co_actors'])
        self.assertIn('Thiel', result['frequent_co_actors'])
        self.assertNotIn('Trump', result['frequent_co_actors'])  # Target actor removed
        self.assertEqual(result['avg_importance'], 8.5)
        self.assertEqual(result['max_importance'], 9)
        self.assertEqual(result['date_range']['start'], '2020-01-15')
        self.assertEqual(result['date_range']['end'], '2021-05-20')

    @patch.object(TimelineResearchClient, 'search_events')
    def test_analyze_actor_no_events(self, mock_search):
        """Test analyze_actor with no events found"""
        mock_search.return_value = []

        result = self.client.analyze_actor('Unknown Actor')

        self.assertEqual(result['actor'], 'Unknown Actor')
        self.assertEqual(result['events'], [])
        self.assertEqual(result['total'], 0)

    @patch.object(TimelineResearchClient, 'search_events')
    def test_analyze_actor_missing_fields(self, mock_search):
        """Test analyze_actor handles events with missing fields gracefully"""
        mock_search.return_value = [
            {'id': '1', 'date': '2020-01-15'},  # Missing tags, actors, importance
            {'id': '2', 'actors': ['Trump']},  # Missing date, tags, importance
        ]

        result = self.client.analyze_actor('Trump')

        self.assertEqual(result['total_events'], 2)
        self.assertEqual(result['avg_importance'], 0)  # No importance values
        self.assertEqual(result['max_importance'], 0)


class TestTimelineResearchClientValidationRuns(unittest.TestCase):
    """Test validation run methods"""

    def setUp(self):
        """Set up test client"""
        with patch('research_client.get_research_monitor_url', return_value='http://localhost:5558'):
            self.client = TimelineResearchClient()

    @patch.object(TimelineResearchClient, '_request')
    def test_list_validation_runs(self, mock_request):
        """Test list_validation_runs"""
        mock_request.return_value = {
            'runs': [{'id': 1, 'run_type': 'source_quality'}]
        }

        result = self.client.list_validation_runs(status='active', run_type='source_quality', limit=10, offset=0)

        self.assertIn('runs', result)
        self.assertEqual(len(result['runs']), 1)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['params']['status'], 'active')
        # Note: run_type parameter is stored as 'type' in params
        self.assertEqual(call_args[1]['params']['type'], 'source_quality')

    @patch.object(TimelineResearchClient, '_request')
    def test_create_validation_run(self, mock_request):
        """Test create_validation_run"""
        mock_request.return_value = {'run_id': 1, 'status': 'active'}

        result = self.client.create_validation_run(
            'source_quality',
            target_count=30,
            min_importance=8,
            created_by='test-agent'
        )

        self.assertEqual(result['run_id'], 1)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['json']['run_type'], 'source_quality')
        self.assertEqual(call_args[1]['json']['target_count'], 30)

    @patch.object(TimelineResearchClient, '_request')
    def test_get_validation_run(self, mock_request):
        """Test get_validation_run"""
        mock_request.return_value = {
            'id': 1,
            'run_type': 'source_quality',
            'status': 'active'
        }

        result = self.client.get_validation_run(1)

        self.assertEqual(result['id'], 1)
        self.assertEqual(result['run_type'], 'source_quality')
        mock_request.assert_called_once()

    @patch.object(TimelineResearchClient, '_request')
    def test_get_next_validation_event(self, mock_request):
        """Test get_next_validation_event"""
        mock_request.return_value = {
            'run_event_id': 5,
            'event_id': 'test-123'
        }

        result = self.client.get_next_validation_event(1, validator_id='agent-1')

        self.assertEqual(result['run_event_id'], 5)
        self.assertEqual(result['event_id'], 'test-123')
        call_args = mock_request.call_args
        # Note: validator_id is passed as params, not json (GET request)
        self.assertEqual(call_args[1]['params']['validator_id'], 'agent-1')

    @patch.object(TimelineResearchClient, '_request')
    def test_complete_validation_run_event(self, mock_request):
        """Test complete_validation_run_event"""
        mock_request.return_value = {'status': 'success'}

        result = self.client.complete_validation_run_event(
            1, 5, status='validated', notes='Good quality'
        )

        self.assertEqual(result['status'], 'success')
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['json']['status'], 'validated')
        self.assertEqual(call_args[1]['json']['notes'], 'Good quality')

    @patch.object(TimelineResearchClient, '_request')
    def test_requeue_needs_work_events(self, mock_request):
        """Test requeue_needs_work_events"""
        mock_request.return_value = {'requeued': 3}

        result = self.client.requeue_needs_work_events(1)

        self.assertEqual(result['requeued'], 3)
        mock_request.assert_called_once()

    @patch.object(TimelineResearchClient, '_request')
    def test_list_validation_logs(self, mock_request):
        """Test list_validation_logs"""
        mock_request.return_value = {
            'logs': [{'id': 1, 'event_id': 'test-123'}]
        }

        result = self.client.list_validation_logs(
            event_id='test-123',
            validation_run_id=1,
            limit=50,
            offset=0
        )

        self.assertIn('logs', result)
        self.assertEqual(len(result['logs']), 1)
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['params']['event_id'], 'test-123')


class TestTimelineResearchClientCommitMessage(unittest.TestCase):
    """Test QA commit message generation"""

    def setUp(self):
        """Set up test client"""
        with patch('research_client.get_research_monitor_url', return_value='http://localhost:5558'):
            self.client = TimelineResearchClient()

    @patch.object(TimelineResearchClient, 'get_commit_status')
    def test_generate_qa_commit_message_success(self, mock_status):
        """Test get_qa_commit_message when commit is needed"""
        mock_status.return_value = {
            'commit_needed': True,
            'suggested_commit_message': {
                'title': 'Add 10 validated timeline events',
                'qa_summary': 'QA Summary: 10 events validated',
                'validation_rate': 'Validation rate: 90%'
            },
            'qa_validation': {
                'recent_validations_24h': 15,
                'total_events_with_metadata': 100
            }
        }

        result = self.client.get_qa_commit_message()

        self.assertIn('title', result)
        self.assertIn('body', result)
        self.assertIn('qa_metadata', result)
        self.assertEqual(result['title'], 'Add 10 validated timeline events')
        self.assertIn('15 validations in last 24h', result['body'])

    @patch.object(TimelineResearchClient, 'get_commit_status')
    def test_generate_qa_commit_message_not_needed(self, mock_status):
        """Test get_qa_commit_message when no commit needed"""
        mock_status.return_value = {'commit_needed': False}

        result = self.client.get_qa_commit_message()

        self.assertIn('error', result)
        self.assertIn('No commit needed', result['error'])

    @patch.object(TimelineResearchClient, 'get_commit_status')
    def test_generate_qa_commit_message_missing_metadata(self, mock_status):
        """Test get_qa_commit_message with missing QA metadata"""
        mock_status.return_value = {
            'commit_needed': True
            # Missing suggested_commit_message
        }

        result = self.client.get_qa_commit_message()

        self.assertIn('error', result)


class TestTimelineResearchClientConnectionMethods(unittest.TestCase):
    """Test research connection tracking methods"""

    def setUp(self):
        """Set up test client"""
        with patch('research_client.get_research_monitor_url', return_value='http://localhost:5558'):
            self.client = TimelineResearchClient()

    @patch.object(TimelineResearchClient, '_request')
    def test_add_event_connection(self, mock_request):
        """Test add_connection"""
        mock_request.return_value = {'status': 'success'}

        result = self.client.add_connection(
            'event-1',
            'event-2',
            connection_type='causal',
            strength=8,
            notes='Direct causation'
        )

        self.assertEqual(result['status'], 'success')
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['json']['event_id_1'], 'event-1')
        self.assertEqual(call_args[1]['json']['event_id_2'], 'event-2')
        self.assertEqual(call_args[1]['json']['connection_type'], 'causal')


if __name__ == '__main__':
    unittest.main()
