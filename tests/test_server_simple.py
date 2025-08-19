#!/usr/bin/env python3
"""
Simple tests for the enhanced timeline server.
"""

import pytest
import json
import tempfile
import shutil
import yaml
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from api.enhanced_server import app
    SERVER_AVAILABLE = True
except ImportError:
    SERVER_AVAILABLE = False
    print("Warning: Enhanced server not available for testing")


@pytest.mark.skipif(not SERVER_AVAILABLE, reason="Enhanced server not available")
class TestServerBasic:
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
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
        # Should return some events (from real data)
        assert isinstance(data['events'], list)
    
    def test_api_stats_endpoint(self, client):
        """Test the stats API endpoint."""
        response = client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        required_fields = ['total_events', 'events_by_status', 'events_by_year']
        for field in required_fields:
            assert field in data
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get('/api/events')
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_nonexistent_endpoint(self, client):
        """Test 404 for nonexistent endpoints."""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404


class TestStaticGenerationBasic:
    
    @pytest.fixture
    def test_environment(self):
        """Create test environment with sample data."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.events_dir = self.test_dir / "events"
        self.events_dir.mkdir(parents=True)
        
        # Create a simple test event
        test_event = {
            'id': '2025-01-01--test-event',
            'date': '2025-01-01',
            'title': 'Test Event',
            'summary': 'This is a test event',
            'status': 'confirmed',
            'tags': ['test'],
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
            'search_keywords': ['test event'],
            'trigger_events': ['test trigger'],
            'fallout_indicators': ['test indicator']
        }
        
        with open(self.events_dir / "test-event.yaml", 'w') as f:
            yaml.dump(test_event, f, default_flow_style=False)
        
        yield self.test_dir
        
        # Cleanup
        shutil.rmtree(self.test_dir)
    
    def test_yaml_loading(self, test_environment):
        """Test basic YAML loading functionality."""
        # Load the test event we created
        event_file = self.events_dir / "test-event.yaml"
        assert event_file.exists()
        
        with open(event_file) as f:
            event = yaml.safe_load(f)
        
        assert event['id'] == '2025-01-01--test-event'
        assert event['monitoring_status'] == 'active'
        assert 'search_keywords' in event
    
    def test_monitoring_fields_preserved(self, test_environment):
        """Test that monitoring fields are preserved in YAML."""
        event_file = self.events_dir / "test-event.yaml"
        
        with open(event_file) as f:
            event = yaml.safe_load(f)
        
        # Verify all monitoring fields are present
        monitoring_fields = [
            'monitoring_status',
            'followup_schedule', 
            'search_keywords',
            'trigger_events',
            'fallout_indicators'
        ]
        
        for field in monitoring_fields:
            assert field in event, f"Missing monitoring field: {field}"


class TestValidationIntegration:
    
    def test_validation_passes_clean(self):
        """Test that validation passes on the clean timeline."""
        # This is an integration test using the real validation script
        import subprocess
        import sys
        
        result = subprocess.run(
            [sys.executable, "scripts/validate.py"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        # Should complete successfully
        assert result.returncode == 0
        assert "All files passed validation!" in result.stdout
    
    def test_monitoring_events_exist(self):
        """Test that monitoring events exist in the timeline."""
        timeline_dir = Path(__file__).parent.parent / "timeline_data" / "events"
        
        monitoring_events = []
        for yaml_file in timeline_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                try:
                    event = yaml.safe_load(f)
                    if event and event.get('monitoring_status'):
                        monitoring_events.append(event)
                except yaml.YAMLError:
                    continue
        
        # Should have at least the 6 events we tagged
        assert len(monitoring_events) >= 6
        
        # Check for specific events we know we tagged
        monitoring_ids = {e['id'] for e in monitoring_events}
        expected_ids = [
            '2025-06-07--la-national-guard-deployment',
            '2025-01-20--doge-established-musk-ramaswamy',
            '2025-01-21--border-emergency'
        ]
        
        for expected_id in expected_ids:
            assert expected_id in monitoring_ids, f"Missing monitoring event: {expected_id}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])