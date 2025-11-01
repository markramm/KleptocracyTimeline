"""
End-to-end tests for the critical event submission pipeline
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Import services
from api.services import EventService, ValidationService, DatabaseService
from research_monitor.validation_functions import calculate_validation_score

# Import fixtures
from tests.fixtures.events import valid_event, minimal_event, events_batch
from tests.fixtures.filesystem import temp_dir


@pytest.mark.integration
class TestEventSubmissionPipeline:
    """Test the complete event submission workflow"""
    
    def test_full_submission_pipeline(self, temp_dir):
        """Test complete event submission from creation to validation"""
        # Initialize services
        event_service = EventService(temp_dir / 'events')
        validation_service = ValidationService()
        db_service = DatabaseService('sqlite:///:memory:')
        
        # Step 1: Create initial event
        initial_event = {
            'date': '2024-01-15',
            'title': 'Major Corruption Investigation Launched',
            'summary': 'Federal authorities announced a comprehensive investigation into alleged corruption involving multiple government officials and corporate executives.',
            'actors': ['Department of Justice', 'FBI', 'John Doe (CEO)', 'Jane Smith (Senator)'],
            'sources': [
                {'title': 'DOJ Press Release', 'url': 'https://justice.gov/news/2024/investigation'},
                {'title': 'FBI Statement', 'url': 'https://fbi.gov/news/2024/corruption-probe'},
                {'title': 'Reuters Report', 'url': 'https://reuters.com/article/corruption-2024'}
            ],
            'tags': ['corruption', 'investigation', 'federal-probe'],
            'status': 'developing',
            'importance': 8
        }
        
        # Step 2: Validate event
        validation_result = validation_service.validate_event(initial_event)
        assert validation_result['valid'] is True
        assert validation_result['score'] >= 0.7
        
        # Step 3: Create event in filesystem
        success, result = event_service.create_event(initial_event)
        assert success is True
        assert 'id' in result
        event_id = result['id']
        
        # Step 4: Log validation to database
        db_service.log_validation(
            event_id,
            validation_result['score'],
            len(validation_result['errors'])
        )
        
        # Step 5: Verify event was saved correctly
        saved_event = event_service.get_event_by_id(event_id)
        assert saved_event is not None
        assert saved_event['title'] == initial_event['title']
        assert len(saved_event['actors']) == 4
        assert len(saved_event['sources']) == 3
        
        # Step 6: Verify validation history
        history = db_service.get_validation_history(event_id)
        assert len(history) > 0
        assert history[0]['validation_score'] == validation_result['score']
    
    def test_pipeline_with_invalid_event(self, temp_dir):
        """Test pipeline handling of invalid events"""
        event_service = EventService(temp_dir / 'events')
        validation_service = ValidationService()
        
        # Create invalid event (missing required fields)
        invalid_event = {
            'date': '2024-01-20',
            'title': 'Bad',  # Too short
            'summary': 'Short',  # Too short
            'actors': [],  # Empty
            'sources': [],  # Empty
            'tags': []  # Empty
        }
        
        # Validate - should fail
        validation_result = validation_service.validate_event(invalid_event)
        assert validation_result['valid'] is False
        assert validation_result['score'] < 0.7
        assert len(validation_result['errors']) > 0
        
        # Attempt to create - should be rejected based on validation
        # In real system, this would be blocked at API level
        assert validation_result['score'] < 0.7
    
    def test_pipeline_with_enhancement(self, temp_dir):
        """Test event enhancement in the pipeline"""
        event_service = EventService(temp_dir / 'events')
        validation_service = ValidationService()
        db_service = DatabaseService('sqlite:///:memory:')
        
        # Start with minimal event
        minimal = {
            'date': '2024-02-01',
            'title': 'Investigation Update Released',
            'summary': 'Authorities provided an update on the ongoing corruption investigation.',
            'actors': ['DOJ', 'FBI'],
            'sources': [
                {'title': 'Update', 'url': 'https://example.com/1'},
                {'title': 'Report', 'url': 'https://example.com/2'}
            ],
            'tags': ['update', 'investigation']
        }
        
        # Initial validation
        initial_validation = validation_service.validate_event(minimal)
        initial_score = initial_validation['score']
        
        # Enhance event
        enhanced = minimal.copy()
        enhanced['summary'] = (
            'Federal authorities provided a comprehensive update on the ongoing corruption investigation, '
            'revealing new evidence and additional suspects. The investigation has expanded to include '
            'multiple jurisdictions and involves complex financial transactions.'
        )
        enhanced['actors'].extend(['SEC', 'Treasury Department'])
        enhanced['sources'].append({
            'title': 'SEC Filing',
            'url': 'https://sec.gov/filing/2024',
            'date': '2024-02-01'
        })
        enhanced['tags'].extend(['federal', 'financial-crimes'])
        enhanced['status'] = 'developing'
        enhanced['importance'] = 7
        
        # Validate enhanced version
        enhanced_validation = validation_service.validate_event(enhanced)
        enhanced_score = enhanced_validation['score']
        
        # Score should improve
        assert enhanced_score > initial_score
        assert enhanced_validation['valid'] is True
        
        # Create enhanced event
        success, result = event_service.create_event(enhanced)
        assert success is True
        
        # Log both validations
        db_service.log_validation(result['id'], initial_score, len(initial_validation['errors']))
        db_service.log_validation(result['id'], enhanced_score, len(enhanced_validation['errors']))
        
        # Verify history shows improvement
        history = db_service.get_validation_history(result['id'])
        assert len(history) == 2
        assert history[1]['validation_score'] > history[0]['validation_score']
    
    def test_batch_submission_pipeline(self, temp_dir, events_batch):
        """Test submitting multiple events through the pipeline"""
        event_service = EventService(temp_dir / 'events')
        validation_service = ValidationService()
        db_service = DatabaseService('sqlite:///:memory:')
        
        created_events = []
        validation_scores = []
        
        # Process batch
        for event_data in events_batch[:5]:
            # Validate
            validation = validation_service.validate_event(event_data)
            validation_scores.append(validation['score'])
            
            if validation['valid']:
                # Create event
                success, result = event_service.create_event(event_data)
                if success:
                    created_events.append(result['id'])
                    # Log validation
                    db_service.log_validation(
                        result['id'],
                        validation['score'],
                        len(validation['errors'])
                    )
        
        # Verify results
        assert len(created_events) == 5
        assert all(score >= 0.7 for score in validation_scores)
        
        # Verify all events exist
        for event_id in created_events:
            event = event_service.get_event_by_id(event_id)
            assert event is not None
        
        # Check batch validation stats
        batch_result = validation_service.validate_batch(events_batch[:5])
        assert batch_result['total_events'] == 5
        assert batch_result['valid_events'] == 5
        assert batch_result['average_score'] >= 0.7
    
    def test_pipeline_error_handling(self, temp_dir):
        """Test pipeline handling of various error conditions"""
        event_service = EventService(temp_dir / 'events')
        validation_service = ValidationService()
        
        # Test duplicate ID handling
        event1 = {
            'id': 'duplicate-test',
            'date': '2024-03-01',
            'title': 'First Event',
            'summary': 'This is the first event with this ID',
            'actors': ['Actor 1', 'Actor 2'],
            'sources': [
                {'title': 'Source', 'url': 'https://example.com'}
            ],
            'tags': ['test']
        }
        
        # Create first event
        success1, result1 = event_service.create_event(event1)
        assert success1 is True
        
        # Try to create duplicate
        success2, result2 = event_service.create_event(event1)
        assert success2 is False
        assert 'already exists' in result2.get('error', '').lower()
        
        # Test malformed event handling
        malformed = {
            'date': 'not-a-date',
            'title': 123,  # Should be string
            'actors': 'not-a-list',  # Should be list
            'sources': None  # Should be list
        }
        
        validation = validation_service.validate_event(malformed)
        assert validation['valid'] is False
        assert len(validation['errors']) > 0
    
    def test_pipeline_with_file_persistence(self, temp_dir):
        """Test that events persist correctly in filesystem"""
        event_service = EventService(temp_dir / 'events')
        
        # Create event
        event = {
            'date': '2024-04-01',
            'title': 'Persistence Test Event',
            'summary': 'Testing that events are correctly saved to filesystem',
            'actors': ['Test Actor 1', 'Test Actor 2'],
            'sources': [
                {'title': 'Test Source', 'url': 'https://test.com'}
            ],
            'tags': ['test', 'persistence']
        }
        
        success, result = event_service.create_event(event)
        assert success is True
        event_id = result['id']
        
        # Verify file exists
        event_file = temp_dir / 'events' / f'{event_id}.json'
        assert event_file.exists()
        
        # Verify file content
        with open(event_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['title'] == event['title']
        assert saved_data['id'] == event_id
        
        # Create new service instance and verify event still accessible
        new_service = EventService(temp_dir / 'events')
        retrieved = new_service.get_event_by_id(event_id)
        assert retrieved is not None
        assert retrieved['title'] == event['title']


@pytest.mark.integration
class TestValidationPipeline:
    """Test the validation-specific pipeline"""
    
    def test_validation_score_calculation(self):
        """Test validation score calculation accuracy"""
        from research_monitor.validation_functions import calculate_validation_score
        
        # Perfect event
        perfect_event = {
            'date': '2024-01-01',
            'title': 'Comprehensive Investigation Into Government Corruption Unveiled',
            'summary': 'A major federal investigation has uncovered extensive corruption involving multiple government officials and corporate executives. The investigation spans several years and involves complex financial schemes.',
            'status': 'confirmed',
            'importance': 8,
            'actors': ['DOJ', 'FBI', 'SEC', 'John Doe', 'Jane Smith'],
            'sources': [
                {'title': 'DOJ Press Release', 'url': 'https://justice.gov/1', 'date': '2024-01-01'},
                {'title': 'FBI Report', 'url': 'https://fbi.gov/2', 'date': '2024-01-01'},
                {'title': 'SEC Filing', 'url': 'https://sec.gov/3', 'date': '2024-01-01'}
            ],
            'tags': ['corruption', 'investigation', 'federal', 'financial-crime', 'indictment']
        }
        
        score = calculate_validation_score(perfect_event, [])
        assert score >= 0.9
        
        # Minimal acceptable event
        minimal_event = {
            'date': '2024-01-01',
            'title': 'Investigation Announced Today',
            'summary': 'Federal authorities announced a new investigation into alleged misconduct.',
            'actors': ['DOJ', 'FBI'],
            'sources': [
                {'title': 'News', 'url': 'https://example.com/1'},
                {'title': 'Report', 'url': 'https://example.com/2'}
            ],
            'tags': ['investigation', 'federal']
        }
        
        score = calculate_validation_score(minimal_event, [])
        assert 0.5 <= score <= 0.8
        
        # Poor event
        poor_event = {
            'date': '2024-01-01',
            'title': 'Event',
            'summary': 'Something happened.',
            'actors': ['Someone'],
            'sources': [{'url': 'https://example.com'}],
            'tags': ['tag']
        }
        
        errors = ['Title too short', 'Summary too short', 'Not enough actors']
        score = calculate_validation_score(poor_event, errors)
        assert score < 0.5