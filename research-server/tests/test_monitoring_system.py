#!/usr/bin/env python3
"""
Tests for the monitoring system functionality.
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMonitoringSystem:
    
    @pytest.fixture
    def test_environment(self):
        """Create test environment with monitoring events."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.events_dir = self.test_dir / "timeline_data" / "events"
        self.events_dir.mkdir(parents=True)
        
        # Create test events with monitoring fields
        self._create_monitoring_events()
        
        yield self.test_dir
        
        # Cleanup
        shutil.rmtree(self.test_dir)
    
    def _create_monitoring_events(self):
        """Create test events with monitoring configurations."""
        events = [
            {
                'id': '2025-01-20--doge-establishment',
                'date': '2025-01-20',
                'title': 'DOGE Establishment Test',
                'summary': 'Test event for DOGE monitoring',
                'status': 'confirmed',
                'tags': ['doge', 'government-efficiency'],
                'actors': ['Elon Musk'],
                'sources': [{'title': 'Test', 'url': 'https://example.com'}],
                'monitoring_status': 'active',
                'followup_schedule': 'weekly',
                'search_keywords': [
                    'DOGE Department Government Efficiency',
                    'Elon Musk government efficiency',
                    'federal layoffs DOGE'
                ],
                'related_events': ['2025-01-21--border-emergency'],
                'trigger_events': [
                    'mass layoffs announced',
                    'contract awards to Musk companies'
                ],
                'fallout_indicators': [
                    'federal workforce reduction',
                    'government efficiency metrics'
                ]
            },
            {
                'id': '2025-01-21--border-emergency',
                'date': '2025-01-21',
                'title': 'Border Emergency Declaration',
                'summary': 'Test border emergency monitoring',
                'status': 'confirmed',
                'tags': ['border', 'emergency'],
                'actors': ['Donald Trump'],
                'sources': [{'title': 'Test', 'url': 'https://example.com'}],
                'monitoring_status': 'active',
                'followup_schedule': 'daily',
                'search_keywords': [
                    'border emergency troops deployment',
                    'Mexico military operations'
                ],
                'trigger_events': [
                    'troop deployment increases',
                    'cross-border incidents'
                ],
                'fallout_indicators': [
                    'military operations Mexico',
                    'diplomatic crisis Mexico'
                ]
            },
            {
                'id': '2025-01-22--inactive-event',
                'date': '2025-01-22',
                'title': 'Inactive Event',
                'summary': 'Event without monitoring',
                'status': 'confirmed',
                'tags': ['inactive'],
                'actors': ['Test Actor'],
                'sources': [{'title': 'Test', 'url': 'https://example.com'}]
            },
            {
                'id': '2025-01-23--dormant-monitoring',
                'date': '2025-01-23',
                'title': 'Dormant Monitoring Event',
                'summary': 'Event with dormant monitoring',
                'status': 'confirmed',
                'tags': ['dormant'],
                'actors': ['Test Actor'],
                'sources': [{'title': 'Test', 'url': 'https://example.com'}],
                'monitoring_status': 'dormant',
                'followup_schedule': 'monthly',
                'search_keywords': ['dormant event monitoring']
            }
        ]
        
        for event in events:
            event_file = self.events_dir / f"{event['id']}.yaml"
            with open(event_file, 'w') as f:
                yaml.dump(event, f, default_flow_style=False)
    
    def test_monitoring_event_identification(self, test_environment):
        """Test identification of events requiring monitoring."""
        # Load events and identify monitoring events
        monitoring_events = []
        
        for yaml_file in self.events_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                event = yaml.safe_load(f)
                if event and event.get('monitoring_status'):
                    monitoring_events.append(event)
        
        assert len(monitoring_events) == 3  # active, active, dormant
        
        active_events = [e for e in monitoring_events if e['monitoring_status'] == 'active']
        assert len(active_events) == 2
        
        dormant_events = [e for e in monitoring_events if e['monitoring_status'] == 'dormant']
        assert len(dormant_events) == 1
    
    def test_search_keyword_extraction(self, test_environment):
        """Test extraction of search keywords for monitoring."""
        all_keywords = set()
        
        for yaml_file in self.events_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                event = yaml.safe_load(f)
                if event and 'search_keywords' in event:
                    all_keywords.update(event['search_keywords'])
        
        # Verify expected keywords are present
        expected_keywords = [
            'DOGE Department Government Efficiency',
            'border emergency troops deployment',
            'dormant event monitoring'
        ]
        
        for keyword in expected_keywords:
            assert keyword in all_keywords
    
    def test_followup_schedule_classification(self, test_environment):
        """Test classification of events by followup schedule."""
        schedule_counts = {'daily': 0, 'weekly': 0, 'monthly': 0}
        
        for yaml_file in self.events_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                event = yaml.safe_load(f)
                if event and 'followup_schedule' in event:
                    schedule = event['followup_schedule']
                    if schedule in schedule_counts:
                        schedule_counts[schedule] += 1
        
        assert schedule_counts['daily'] == 1    # border emergency
        assert schedule_counts['weekly'] == 1   # DOGE
        assert schedule_counts['monthly'] == 1  # dormant event
    
    def test_trigger_events_validation(self, test_environment):
        """Test validation of trigger events."""
        trigger_events = set()
        
        for yaml_file in self.events_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                event = yaml.safe_load(f)
                if event and 'trigger_events' in event:
                    trigger_events.update(event['trigger_events'])
        
        # Verify expected trigger events
        expected_triggers = [
            'mass layoffs announced',
            'troop deployment increases',
            'cross-border incidents'
        ]
        
        for trigger in expected_triggers:
            assert trigger in trigger_events
    
    def test_fallout_indicators_collection(self, test_environment):
        """Test collection of fallout indicators."""
        fallout_indicators = set()
        
        for yaml_file in self.events_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                event = yaml.safe_load(f)
                if event and 'fallout_indicators' in event:
                    fallout_indicators.update(event['fallout_indicators'])
        
        # Verify expected indicators
        expected_indicators = [
            'federal workforce reduction',
            'military operations Mexico',
            'diplomatic crisis Mexico'
        ]
        
        for indicator in expected_indicators:
            assert indicator in fallout_indicators
    
    def test_related_events_tracking(self, test_environment):
        """Test tracking of related events."""
        events_with_relations = []
        
        for yaml_file in self.events_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                event = yaml.safe_load(f)
                if event and 'related_events' in event:
                    events_with_relations.append(event)
        
        assert len(events_with_relations) == 1  # Only DOGE event has related events
        
        doge_event = events_with_relations[0]
        assert '2025-01-21--border-emergency' in doge_event['related_events']
    
    def test_monitoring_status_validation(self, test_environment):
        """Test validation of monitoring status values."""
        valid_statuses = {'active', 'dormant', 'completed'}
        
        for yaml_file in self.events_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                event = yaml.safe_load(f)
                if event and 'monitoring_status' in event:
                    status = event['monitoring_status']
                    assert status in valid_statuses, f"Invalid monitoring status: {status}"
    
    def test_search_query_generation(self, test_environment):
        """Test generation of search queries from monitoring data."""
        search_queries = []
        
        for yaml_file in self.events_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                event = yaml.safe_load(f)
                if event and event.get('monitoring_status') == 'active':
                    # Generate search queries for active monitoring
                    event_id = event['id']
                    keywords = event.get('search_keywords', [])
                    actors = event.get('actors', [])
                    
                    # Create queries combining keywords and actors
                    for keyword in keywords:
                        search_queries.append(f'"{keyword}"')
                    
                    for actor in actors:
                        for keyword in keywords[:2]:  # Limit combinations
                            search_queries.append(f'"{actor}" AND "{keyword}"')
        
        # Should generate multiple search queries
        assert len(search_queries) >= 6
        assert '"DOGE Department Government Efficiency"' in search_queries
        assert '"border emergency troops deployment"' in search_queries
    
    def test_monitoring_summary_generation(self, test_environment):
        """Test generation of monitoring summary statistics."""
        monitoring_summary = {
            'total_monitored': 0,
            'active': 0,
            'dormant': 0,
            'completed': 0,
            'daily_followup': 0,
            'weekly_followup': 0,
            'monthly_followup': 0
        }
        
        for yaml_file in self.events_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                event = yaml.safe_load(f)
                if event and 'monitoring_status' in event:
                    monitoring_summary['total_monitored'] += 1
                    status = event['monitoring_status']
                    monitoring_summary[status] += 1
                    
                    schedule = event.get('followup_schedule')
                    if schedule:
                        monitoring_summary[f'{schedule}_followup'] += 1
        
        assert monitoring_summary['total_monitored'] == 3
        assert monitoring_summary['active'] == 2
        assert monitoring_summary['dormant'] == 1
        assert monitoring_summary['daily_followup'] == 1
        assert monitoring_summary['weekly_followup'] == 1
        assert monitoring_summary['monthly_followup'] == 1
    
    def test_monitoring_field_validation(self, test_environment):
        """Test validation of monitoring field structures."""
        for yaml_file in self.events_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                event = yaml.safe_load(f)
                if event and 'monitoring_status' in event:
                    # Validate monitoring fields
                    assert isinstance(event['monitoring_status'], str)
                    
                    if 'search_keywords' in event:
                        assert isinstance(event['search_keywords'], list)
                        for keyword in event['search_keywords']:
                            assert isinstance(keyword, str)
                            assert len(keyword.strip()) > 0
                    
                    if 'trigger_events' in event:
                        assert isinstance(event['trigger_events'], list)
                        for trigger in event['trigger_events']:
                            assert isinstance(trigger, str)
                    
                    if 'fallout_indicators' in event:
                        assert isinstance(event['fallout_indicators'], list)
                        for indicator in event['fallout_indicators']:
                            assert isinstance(indicator, str)
                    
                    if 'related_events' in event:
                        assert isinstance(event['related_events'], list)
                        for related_id in event['related_events']:
                            assert isinstance(related_id, str)
                            # Should follow ID format
                            assert '--' in related_id
    
    def test_keyword_deduplication(self, test_environment):
        """Test deduplication of search keywords across events."""
        all_keywords = []
        
        for yaml_file in self.events_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                event = yaml.safe_load(f)
                if event and 'search_keywords' in event:
                    all_keywords.extend(event['search_keywords'])
        
        unique_keywords = set(all_keywords)
        
        # Should have collected all unique keywords
        assert len(unique_keywords) >= 4
        assert 'DOGE Department Government Efficiency' in unique_keywords
        assert 'border emergency troops deployment' in unique_keywords


if __name__ == '__main__':
    pytest.main([__file__, '-v'])