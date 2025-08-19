#!/usr/bin/env python3
"""
Tests for static site generation scripts.
"""

import pytest
import tempfile
import shutil
import yaml
import json
from pathlib import Path
import sys
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate import TimelineGenerator


class TestStaticGeneration:
    
    @pytest.fixture
    def test_environment(self):
        """Create test environment with sample data."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.timeline_dir = self.test_dir / "timeline_data"
        self.events_dir = self.timeline_dir / "events"
        self.api_dir = self.timeline_dir / "api"
        
        self.timeline_dir.mkdir()
        self.events_dir.mkdir()
        self.api_dir.mkdir()
        
        # Create test events
        self._create_test_events()
        
        yield self.test_dir
        
        # Cleanup
        shutil.rmtree(self.test_dir)
    
    def _create_test_events(self):
        """Create test timeline events."""
        events = [
            {
                'id': '2025-01-01--test-event-1',
                'date': '2025-01-01',
                'title': 'Test Event 1',
                'summary': 'This is a test event for static generation',
                'status': 'confirmed',
                'tags': ['test', 'static-generation'],
                'actors': ['Test Actor 1'],
                'location': 'Test Location',
                'sources': [
                    {
                        'title': 'Test Source 1',
                        'url': 'https://example.com/test1',
                        'outlet': 'Test Outlet 1',
                        'date': '2025-01-01'
                    }
                ],
                'monitoring_status': 'active',
                'followup_schedule': 'daily',
                'search_keywords': ['test event', 'generation'],
                'related_events': ['2025-01-02--test-event-2'],
                'trigger_events': ['test trigger'],
                'fallout_indicators': ['test indicator']
            },
            {
                'id': '2025-01-02--test-event-2',
                'date': '2025-01-02',
                'title': 'Test Event 2',
                'summary': 'Second test event for testing relationships',
                'status': 'pending',
                'tags': ['test', 'relationships'],
                'actors': ['Test Actor 2', 'Test Actor 1'],
                'location': 'Test Location 2',
                'sources': [
                    {
                        'title': 'Test Source 2',
                        'url': 'https://example.com/test2',
                        'outlet': 'Test Outlet 2',
                        'date': '2025-01-02'
                    }
                ],
                'monitoring_status': 'dormant',
                'followup_schedule': 'weekly'
            },
            {
                'id': '2024-12-31--historical-event',
                'date': '2024-12-31',
                'title': 'Historical Test Event',
                'summary': 'Historical event for testing date ranges',
                'status': 'confirmed',
                'tags': ['historical', 'test'],
                'actors': ['Historical Actor'],
                'sources': [
                    {
                        'title': 'Historical Source',
                        'url': 'https://example.com/historical',
                        'outlet': 'Historical Outlet',
                        'date': '2024-12-31'
                    }
                ]
            }
        ]
        
        for event in events:
            event_file = self.events_dir / f"{event['id']}.yaml"
            with open(event_file, 'w') as f:
                yaml.dump(event, f, default_flow_style=False)
    
    def test_timeline_generator_initialization(self, test_environment):
        """Test TimelineGenerator initialization."""
        events_dir = str(self.events_dir)
        output_dir = str(test_environment / "timeline_data")
        generator = TimelineGenerator(events_dir, output_dir)
        assert generator.events_dir == Path(events_dir)
        assert generator.output_dir == Path(output_dir)
        assert generator.events_dir.exists()
    
    def test_load_events(self, test_environment):
        """Test loading events from YAML files."""
        generator = TimelineGenerator(str(self.events_dir), str(test_environment / "timeline_data"))
        generator.load_events()  # load_events() doesn't return, it populates self.events
        
        assert len(generator.events) == 3
        assert generator.events[0]['id'] == '2024-12-31--historical-event'  # Should be sorted by date
        assert generator.events[1]['id'] == '2025-01-01--test-event-1'
        assert generator.events[2]['id'] == '2025-01-02--test-event-2'
    
    def test_generate_api_files(self, test_environment):
        """Test generation of API JSON files."""
        generator = TimelineGenerator(str(self.events_dir), str(test_environment / "timeline_data"))
        generator.load_events()
        generator.generate_static_api()
        
        # Check that API files were created
        api_files = [
            'timeline.json',
            'actors.json',
            'tags.json',
            'stats.json'
        ]
        
        api_dir = test_environment / "timeline_data" / "api"
        for file_name in api_files:
            api_file = api_dir / file_name
            assert api_file.exists(), f"API file {file_name} was not created"
            
            # Validate JSON content
            with open(api_file) as f:
                data = json.load(f)
                assert isinstance(data, (dict, list)), f"Invalid JSON in {file_name}"
    
    def test_timeline_json_structure(self, test_environment):
        """Test structure of generated timeline.json."""
        generator = TimelineGenerator(str(test_environment))
        generator.generate_api_files()
        
        with open(self.api_dir / 'timeline.json') as f:
            timeline_data = json.load(f)
        
        assert 'events' in timeline_data
        assert 'metadata' in timeline_data
        assert len(timeline_data['events']) == 3
        
        # Check event structure
        event = timeline_data['events'][0]
        required_fields = ['id', 'date', 'title', 'summary', 'status', 'sources']
        for field in required_fields:
            assert field in event, f"Missing required field: {field}"
        
        # Check monitoring fields are preserved
        monitoring_event = next((e for e in timeline_data['events'] if e.get('monitoring_status')), None)
        assert monitoring_event is not None
        assert 'search_keywords' in monitoring_event
        assert 'trigger_events' in monitoring_event
    
    def test_actors_json_generation(self, test_environment):
        """Test generation of actors.json."""
        generator = TimelineGenerator(str(test_environment))
        generator.generate_api_files()
        
        with open(self.api_dir / 'actors.json') as f:
            actors_data = json.load(f)
        
        assert 'actors' in actors_data
        assert len(actors_data['actors']) >= 4  # At least 4 unique actors
        
        # Check actor structure
        actor = actors_data['actors'][0]
        assert 'name' in actor
        assert 'event_count' in actor
        assert 'events' in actor
    
    def test_tags_json_generation(self, test_environment):
        """Test generation of tags.json."""
        generator = TimelineGenerator(str(test_environment))
        generator.generate_api_files()
        
        with open(self.api_dir / 'tags.json') as f:
            tags_data = json.load(f)
        
        assert 'tags' in tags_data
        assert len(tags_data['tags']) >= 4  # At least 4 unique tags
        
        # Check tag structure
        tag = tags_data['tags'][0]
        assert 'name' in tag
        assert 'event_count' in tag
        assert 'events' in tag
    
    def test_stats_json_generation(self, test_environment):
        """Test generation of stats.json."""
        generator = TimelineGenerator(str(test_environment))
        generator.generate_api_files()
        
        with open(self.api_dir / 'stats.json') as f:
            stats_data = json.load(f)
        
        required_stats = [
            'total_events',
            'events_by_status',
            'events_by_year',
            'events_by_month',
            'top_actors',
            'top_tags',
            'monitoring_summary'
        ]
        
        for stat in required_stats:
            assert stat in stats_data, f"Missing statistic: {stat}"
        
        # Verify specific values
        assert stats_data['total_events'] == 3
        assert stats_data['events_by_status']['confirmed'] == 2
        assert stats_data['events_by_status']['pending'] == 1
        
        # Check monitoring summary
        monitoring = stats_data['monitoring_summary']
        assert monitoring['total_monitored'] == 2
        assert monitoring['active'] == 1
        assert monitoring['dormant'] == 1
    
    def test_monitoring_events_extraction(self, test_environment):
        """Test extraction of monitoring events."""
        generator = TimelineGenerator(str(test_environment))
        events = generator.load_events()
        
        monitoring_events = [e for e in events if e.get('monitoring_status')]
        assert len(monitoring_events) == 2
        
        active_events = [e for e in monitoring_events if e['monitoring_status'] == 'active']
        assert len(active_events) == 1
        assert active_events[0]['followup_schedule'] == 'daily'
    
    def test_search_keywords_aggregation(self, test_environment):
        """Test aggregation of search keywords for monitoring."""
        generator = TimelineGenerator(str(test_environment))
        events = generator.load_events()
        
        all_keywords = []
        for event in events:
            if 'search_keywords' in event:
                all_keywords.extend(event['search_keywords'])
        
        assert 'test event' in all_keywords
        assert 'generation' in all_keywords
        assert len(set(all_keywords)) >= 2  # At least 2 unique keywords
    
    def test_related_events_validation(self, test_environment):
        """Test validation of related events references."""
        generator = TimelineGenerator(str(test_environment))
        events = generator.load_events()
        events_by_id = {e['id']: e for e in events}
        
        for event in events:
            if 'related_events' in event:
                for related_id in event['related_events']:
                    assert related_id in events_by_id, f"Related event {related_id} not found"
    
    def test_date_sorting(self, test_environment):
        """Test that events are properly sorted by date."""
        generator = TimelineGenerator(str(test_environment))
        events = generator.load_events()
        
        # Events should be sorted chronologically
        dates = [event['date'] for event in events]
        assert dates == sorted(dates), "Events are not sorted by date"
    
    def test_build_script_execution(self, test_environment):
        """Test execution of build script."""
        # Change to test directory
        original_cwd = Path.cwd()
        try:
            # Create a simple build script for testing
            build_script = test_environment / "scripts" / "timeline.py"
            build_script.parent.mkdir(exist_ok=True)
            
            # Copy our timeline script to test location
            import shutil
            scripts_dir = Path(__file__).parent.parent / "scripts"
            if (scripts_dir / "timeline.py").exists():
                shutil.copy(scripts_dir / "timeline.py", build_script)
                
                # Run the build script
                result = subprocess.run(
                    [sys.executable, str(build_script)],
                    cwd=str(test_environment),
                    capture_output=True,
                    text=True
                )
                
                # Should complete without errors
                assert result.returncode == 0, f"Build script failed: {result.stderr}"
                
                # Check that API files were generated
                api_dir = test_environment / "timeline_data" / "api"
                assert (api_dir / "timeline.json").exists()
                
        finally:
            # Restore original working directory
            pass
    
    def test_error_handling_invalid_yaml(self, test_environment):
        """Test handling of invalid YAML files."""
        # Create invalid YAML file
        invalid_file = self.events_dir / "invalid-event.yaml"
        with open(invalid_file, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        generator = TimelineGenerator(str(test_environment))
        events = generator.load_events()
        
        # Should handle gracefully and skip invalid files
        assert len(events) == 3  # Only valid events loaded
    
    def test_missing_required_fields(self, test_environment):
        """Test handling of events with missing required fields."""
        # Create event with missing required fields
        incomplete_event = {
            'id': '2025-01-03--incomplete-event',
            'date': '2025-01-03',
            'title': 'Incomplete Event'
            # Missing summary, status, sources
        }
        
        incomplete_file = self.events_dir / "incomplete-event.yaml"
        with open(incomplete_file, 'w') as f:
            yaml.dump(incomplete_event, f)
        
        generator = TimelineGenerator(str(test_environment))
        
        # Should handle gracefully (implementation dependent)
        try:
            events = generator.load_events()
            # May include or exclude incomplete events based on validation
            assert len(events) >= 3
        except Exception as e:
            # Or may raise validation error
            assert "required" in str(e).lower() or "missing" in str(e).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])