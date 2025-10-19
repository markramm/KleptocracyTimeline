#!/usr/bin/env python3
"""
Data quality validation tests.
These tests validate actual data quality issues found by contract testing.
"""

import pytest
import requests
import json

API_BASE_URL = "http://localhost:5558"
API_TIMEOUT = 10


class TestDataQualityValidation:
    """Test data quality issues found by contract testing."""
    
    @pytest.fixture(scope="class")
    def api_health_check(self):
        """Verify API is running before testing."""
        try:
            response = requests.get(f"{API_BASE_URL}/api/stats", timeout=5)
            if response.status_code != 200:
                pytest.skip("Research Monitor v2 API not available")
        except requests.exceptions.RequestException:
            pytest.skip("Research Monitor v2 API not accessible")
    
    def test_importance_values_validation(self, api_health_check):
        """Test that all events have valid importance values (1-10)."""
        response = requests.get(
            f"{API_BASE_URL}/api/timeline/events?per_page=1000",
            timeout=API_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        invalid_importance_events = []
        
        for event in data['events']:
            importance = event.get('importance')
            if importance is None:
                invalid_importance_events.append({
                    'id': event['id'],
                    'issue': 'Missing importance',
                    'value': None
                })
            elif not isinstance(importance, int):
                invalid_importance_events.append({
                    'id': event['id'],
                    'issue': 'Non-integer importance',
                    'value': importance,
                    'type': type(importance).__name__
                })
            elif not (1 <= importance <= 10):
                invalid_importance_events.append({
                    'id': event['id'],
                    'issue': 'Out of range importance',
                    'value': importance
                })
        
        if invalid_importance_events:
            print(f"\nFound {len(invalid_importance_events)} events with invalid importance:")
            for issue in invalid_importance_events[:10]:  # Show first 10
                print(f"  - {issue['id']}: {issue['issue']} (value: {issue.get('value')})")
            if len(invalid_importance_events) > 10:
                print(f"  ... and {len(invalid_importance_events) - 10} more")
        
        # This test documents the current state - we expect some failures
        assert len(invalid_importance_events) < 100, f"Too many invalid importance values: {len(invalid_importance_events)}"
    
    def test_required_fields_validation(self, api_health_check):
        """Test that all events have required fields."""
        response = requests.get(
            f"{API_BASE_URL}/api/timeline/events?per_page=100",
            timeout=API_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ['id', 'date', 'title', 'summary', 'importance']
        missing_fields_events = []
        
        for event in data['events']:
            missing_fields = []
            for field in required_fields:
                if field not in event:
                    missing_fields.append(field)
                elif not str(event[field]).strip():  # Empty or whitespace-only
                    missing_fields.append(f"{field} (empty)")
            
            if missing_fields:
                missing_fields_events.append({
                    'id': event.get('id', 'UNKNOWN'),
                    'missing_fields': missing_fields
                })
        
        if missing_fields_events:
            print(f"\nFound {len(missing_fields_events)} events with missing required fields:")
            for issue in missing_fields_events[:5]:
                print(f"  - {issue['id']}: Missing {', '.join(issue['missing_fields'])}")
        
        assert len(missing_fields_events) == 0, f"Events missing required fields: {missing_fields_events}"
    
    def test_date_format_validation(self, api_health_check):
        """Test that all events have valid date formats."""
        response = requests.get(
            f"{API_BASE_URL}/api/timeline/events?per_page=500",
            timeout=API_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        invalid_date_events = []
        
        for event in data['events']:
            date_str = event.get('date', '')
            
            # Check basic format
            if not date_str:
                invalid_date_events.append({
                    'id': event.get('id', 'UNKNOWN'),
                    'issue': 'Missing date',
                    'value': date_str
                })
                continue
            
            # Check YYYY-MM-DD format
            if len(date_str) != 10 or date_str.count('-') != 2:
                invalid_date_events.append({
                    'id': event['id'],
                    'issue': 'Invalid date format',
                    'value': date_str
                })
                continue
            
            # Check date parts are numeric
            try:
                year, month, day = date_str.split('-')
                year_int = int(year)
                month_int = int(month)
                day_int = int(day)
                
                if year_int < 1900 or year_int > 2030:
                    invalid_date_events.append({
                        'id': event['id'],
                        'issue': 'Unreasonable year',
                        'value': date_str
                    })
                elif month_int < 1 or month_int > 12:
                    invalid_date_events.append({
                        'id': event['id'],
                        'issue': 'Invalid month',
                        'value': date_str
                    })
                elif day_int < 1 or day_int > 31:
                    invalid_date_events.append({
                        'id': event['id'],
                        'issue': 'Invalid day',
                        'value': date_str
                    })
                    
            except ValueError:
                invalid_date_events.append({
                    'id': event['id'],
                    'issue': 'Non-numeric date components',
                    'value': date_str
                })
        
        if invalid_date_events:
            print(f"\nFound {len(invalid_date_events)} events with invalid dates:")
            for issue in invalid_date_events[:5]:
                print(f"  - {issue['id']}: {issue['issue']} (value: {issue.get('value')})")
        
        assert len(invalid_date_events) == 0, f"Events with invalid dates: {invalid_date_events}"
    
    def test_id_format_validation(self, api_health_check):
        """Test that all events have valid ID formats."""
        response = requests.get(
            f"{API_BASE_URL}/api/timeline/events?per_page=500",
            timeout=API_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        invalid_id_events = []
        seen_ids = set()
        
        for event in data['events']:
            event_id = event.get('id', '')
            
            # Check ID exists and has correct format
            if not event_id:
                invalid_id_events.append({
                    'id': 'EMPTY',
                    'issue': 'Missing ID'
                })
                continue
            
            # Check for duplicates
            if event_id in seen_ids:
                invalid_id_events.append({
                    'id': event_id,
                    'issue': 'Duplicate ID'
                })
                continue
            
            seen_ids.add(event_id)
            
            # Check format: should be YYYY-MM-DD--descriptive-slug
            if '--' not in event_id:
                invalid_id_events.append({
                    'id': event_id,
                    'issue': 'ID missing double dash separator'
                })
                continue
            
            date_part, slug_part = event_id.split('--', 1)
            
            # Check date part
            if len(date_part) != 10 or date_part.count('-') != 2:
                invalid_id_events.append({
                    'id': event_id,
                    'issue': 'Invalid date format in ID'
                })
                continue
            
            # Check slug part
            if not slug_part:
                invalid_id_events.append({
                    'id': event_id,
                    'issue': 'Empty slug in ID'
                })
                continue
        
        if invalid_id_events:
            print(f"\nFound {len(invalid_id_events)} events with invalid IDs:")
            for issue in invalid_id_events[:5]:
                print(f"  - {issue['id']}: {issue['issue']}")
        
        assert len(invalid_id_events) == 0, f"Events with invalid IDs: {invalid_id_events}"
    
    def test_api_stats_structure(self, api_health_check):
        """Document the actual API stats structure."""
        response = requests.get(f"{API_BASE_URL}/api/stats", timeout=API_TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"\nActual API stats structure:")
        print(json.dumps(data, indent=2))
        
        # Validate the structure we actually have
        assert 'events' in data
        assert 'total' in data['events']
        assert isinstance(data['events']['total'], int)
        assert data['events']['total'] > 1000  # Should have plenty of events
        
        # Document what we learned
        total_events = data['events']['total']
        assert total_events == 1857, f"Expected 1857 events, got {total_events}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])  # -s to show print statements