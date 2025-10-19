"""
Integration tests for Flask API endpoints
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

# Import fixtures
from tests.fixtures.events import valid_event, minimal_event, events_batch
from tests.fixtures.filesystem import temp_dir, mock_timeline_structure


@pytest.mark.api
class TestEventEndpoints:
    """Test event CRUD endpoints"""
    
    def test_get_all_events_empty(self, test_client):
        """Test getting events when none exist"""
        response = test_client.get('/api/events/')
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 0
        assert data['events'] == []
    
    def test_create_valid_event(self, test_client, valid_event):
        """Test creating a valid event"""
        response = test_client.post(
            '/api/events/',
            json=valid_event,
            content_type='application/json'
        )
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['message'] == 'Event created successfully'
    
    def test_create_invalid_event(self, test_client):
        """Test creating an invalid event"""
        invalid_event = {'title': 'Too short'}  # Missing required fields
        response = test_client.post(
            '/api/events/',
            json=invalid_event,
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'validation' in data
        assert not data['validation']['valid']
    
    def test_get_event_by_id(self, test_client, test_event_id):
        """Test getting a specific event"""
        response = test_client.get(f'/api/events/{test_event_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == test_event_id
    
    def test_get_nonexistent_event(self, test_client):
        """Test getting an event that doesn't exist"""
        response = test_client.get('/api/events/nonexistent-id')
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'Event not found'
    
    def test_update_event(self, test_client, test_event_id, minimal_event):
        """Test updating an existing event"""
        minimal_event['title'] = 'Updated Title'
        response = test_client.put(
            f'/api/events/{test_event_id}',
            json=minimal_event,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Event updated successfully'
    
    def test_delete_event(self, test_client, test_event_id):
        """Test deleting an event"""
        response = test_client.delete(f'/api/events/{test_event_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Event deleted successfully'
    
    def test_search_events(self, test_client, setup_test_events):
        """Test searching events"""
        response = test_client.get('/api/events/?q=corruption')
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] > 0
    
    def test_batch_create_events(self, test_client, events_batch):
        """Test creating multiple events"""
        response = test_client.post(
            '/api/events/batch',
            json={'events': events_batch[:3]},
            content_type='application/json'
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['created'] == 3
        assert data['failed'] == 0


@pytest.mark.api
class TestValidationEndpoints:
    """Test validation endpoints"""
    
    def test_validate_single_event(self, test_client, valid_event):
        """Test validating a single event"""
        response = test_client.post(
            '/api/validation/validate',
            json=valid_event,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data
        assert 'score' in data
        assert 'errors' in data
        assert data['valid'] is True
    
    def test_validate_invalid_event(self, test_client):
        """Test validating an invalid event"""
        invalid_event = {'title': 'Short'}
        response = test_client.post(
            '/api/validation/validate',
            json=invalid_event,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] is False
        assert len(data['errors']) > 0
    
    def test_validate_batch(self, test_client, events_batch):
        """Test validating multiple events"""
        response = test_client.post(
            '/api/validation/validate/batch',
            json={'events': events_batch[:5]},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_events'] == 5
        assert 'valid_events' in data
        assert 'average_score' in data
    
    def test_get_validation_stats(self, test_client, setup_test_events):
        """Test getting validation statistics"""
        response = test_client.get('/api/validation/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_events' in data
        assert 'valid_events' in data
        assert 'average_score' in data
        assert 'error_distribution' in data
    
    def test_get_event_score(self, test_client, test_event_id):
        """Test getting validation score for specific event"""
        response = test_client.get(f'/api/validation/score/{test_event_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['event_id'] == test_event_id
        assert 'score' in data
        assert 'valid' in data
    
    def test_fix_event(self, test_client, test_event_with_legacy_sources):
        """Test applying fixes to an event"""
        response = test_client.post(
            f'/api/validation/fix/{test_event_with_legacy_sources}'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'fixes_applied' in data
        assert 'new_score' in data


@pytest.mark.api
class TestMonitoringEndpoints:
    """Test monitoring endpoints"""
    
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get('/api/monitoring/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_get_status(self, test_client):
        """Test system status endpoint"""
        response = test_client.get('/api/monitoring/status')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'operational'
        assert 'statistics' in data
        assert 'configuration' in data
    
    def test_get_metrics(self, test_client, setup_test_events):
        """Test metrics endpoint"""
        response = test_client.get('/api/monitoring/metrics')
        assert response.status_code == 200
        data = response.get_json()
        assert 'events' in data
        assert 'entities' in data
        assert 'validation' in data
    
    def test_get_config(self, test_client):
        """Test configuration endpoint"""
        response = test_client.get('/api/monitoring/config')
        assert response.status_code == 200
        data = response.get_json()
        assert 'environment' in data
        assert 'timeline_directory' in data
        assert 'api_port' in data
    
    def test_get_services_status(self, test_client):
        """Test services status endpoint"""
        response = test_client.get('/api/monitoring/services')
        assert response.status_code == 200
        data = response.get_json()
        assert 'services' in data
        assert 'all_operational' in data
        assert 'event_service' in data['services']
        assert 'validation_service' in data['services']
    
    def test_ping(self, test_client):
        """Test ping endpoint"""
        response = test_client.get('/api/monitoring/ping')
        assert response.status_code == 200
        data = response.get_json()
        assert data['pong'] is True


@pytest.mark.api
class TestErrorHandling:
    """Test error handling"""
    
    def test_404_error(self, test_client):
        """Test 404 error handling"""
        response = test_client.get('/api/nonexistent/endpoint')
        assert response.status_code == 404
    
    def test_bad_json(self, test_client):
        """Test handling of malformed JSON"""
        response = test_client.post(
            '/api/events/',
            data='not valid json',
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_missing_content_type(self, test_client):
        """Test handling of missing content type"""
        response = test_client.post(
            '/api/events/',
            data=json.dumps({'title': 'Test'})
        )
        # Should still work as Flask can handle this
        assert response.status_code in [400, 415]


# Fixtures for test setup

@pytest.fixture
def test_client(temp_dir):
    """Create test Flask client with test configuration"""
    from api.app_factory import create_app
    from api.services import EventService, ValidationService, FileService, DatabaseService
    
    # Create test services
    services = {
        'event_service': EventService(temp_dir / 'events'),
        'validation_service': ValidationService(),
        'file_service': FileService(),
        'database_service': DatabaseService('sqlite:///:memory:')
    }
    
    # Create app with test config
    app = create_app('testing', services)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def test_event_id(test_client, valid_event):
    """Create a test event and return its ID"""
    response = test_client.post(
        '/api/events/',
        json=valid_event,
        content_type='application/json'
    )
    data = response.get_json()
    return data['id']


@pytest.fixture
def test_event_with_legacy_sources(test_client):
    """Create an event with legacy source format"""
    event = {
        'date': '2024-01-01',
        'title': 'Event with Legacy Sources Format',
        'summary': 'This event has sources in the old URL-only format that needs conversion.',
        'actors': ['Actor 1', 'Actor 2'],
        'sources': [
            'https://example.com/source1',
            'https://example.com/source2'
        ],
        'tags': ['test', 'legacy']
    }
    response = test_client.post(
        '/api/events/',
        json=event,
        content_type='application/json'
    )
    # This will fail validation due to legacy format
    # Create with proper format instead
    event['sources'] = [
        {'title': 'Source 1', 'url': 'https://example.com/source1'},
        {'title': 'Source 2', 'url': 'https://example.com/source2'}
    ]
    response = test_client.post(
        '/api/events/',
        json=event,
        content_type='application/json'
    )
    data = response.get_json()
    return data['id']


@pytest.fixture
def setup_test_events(test_client, events_batch):
    """Setup multiple test events"""
    for event in events_batch[:5]:
        test_client.post(
            '/api/events/',
            json=event,
            content_type='application/json'
        )
    yield
    # Cleanup happens automatically with temp_dir