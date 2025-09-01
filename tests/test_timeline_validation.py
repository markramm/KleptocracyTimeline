#!/usr/bin/env python3
"""
Test suite for timeline event validation.
Ensures data integrity and consistency across all timeline events.
"""

import yaml
import unittest
from pathlib import Path
from datetime import datetime, date
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestTimelineValidation(unittest.TestCase):
    """Comprehensive validation tests for timeline events."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.events_dir = Path('timeline_data/events')
        cls.yaml_files = list(cls.events_dir.glob('*.yaml'))
        
    def test_events_directory_exists(self):
        """Test that the events directory exists."""
        self.assertTrue(self.events_dir.exists(), 
                       f"Events directory {self.events_dir} does not exist")
        
    def test_has_yaml_files(self):
        """Test that there are YAML files to validate."""
        self.assertGreater(len(self.yaml_files), 0, 
                          "No YAML files found in events directory")
    
    def test_all_ids_match_filenames(self):
        """Verify that every YAML file's ID field matches its filename."""
        mismatches = []
        
        for yaml_file in self.yaml_files:
            expected_id = yaml_file.stem  # filename without extension
            
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                actual_id = data.get('id')
                
                if actual_id != expected_id:
                    mismatches.append(
                        f"{yaml_file.name}: expected ID '{expected_id}', got '{actual_id}'"
                    )
                    
            except Exception as e:
                self.fail(f"Error loading {yaml_file.name}: {e}")
        
        if mismatches:
            error_msg = "ID/filename mismatches found:\n" + "\n".join(f"  - {m}" for m in mismatches)
            self.fail(error_msg)
    
    def test_all_yaml_files_valid(self):
        """Verify that all YAML files can be parsed without errors."""
        parse_errors = []
        
        for yaml_file in self.yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                parse_errors.append(f"{yaml_file.name}: {e}")
            except Exception as e:
                parse_errors.append(f"{yaml_file.name}: {e}")
        
        if parse_errors:
            error_msg = "YAML parsing errors found:\n" + "\n".join(f"  - {e}" for e in parse_errors)
            self.fail(error_msg)
    
    def test_required_fields_present(self):
        """Verify that all YAML files have required fields."""
        required_fields = ['id', 'date', 'title', 'summary']
        missing_fields = []
        
        for yaml_file in self.yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                for field in required_fields:
                    if field not in data or data[field] is None:
                        missing_fields.append(
                            f"{yaml_file.name}: missing required field '{field}'"
                        )
                        
            except Exception:
                # Already tested in test_all_yaml_files_valid
                pass
        
        if missing_fields:
            error_msg = "Missing required fields:\n" + "\n".join(f"  - {m}" for m in missing_fields)
            self.fail(error_msg)
    
    def test_date_format_valid(self):
        """Verify that all dates are in YYYY-MM-DD format."""
        date_errors = []
        
        for yaml_file in self.yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                date_str = data.get('date')
                if date_str:
                    try:
                        # Try to parse the date
                        datetime.strptime(str(date_str), '%Y-%m-%d')
                    except ValueError:
                        date_errors.append(
                            f"{yaml_file.name}: invalid date format '{date_str}' (expected YYYY-MM-DD)"
                        )
            except Exception:
                # Already tested in other tests
                pass
        
        if date_errors:
            error_msg = "Date format errors found:\n" + "\n".join(f"  - {e}" for e in date_errors)
            self.fail(error_msg)
    
    def test_status_values_valid(self):
        """Verify that status values are from the allowed set."""
        allowed_statuses = {'confirmed', 'alleged', 'speculative', 'developing'}
        status_errors = []
        
        for yaml_file in self.yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                status = data.get('status')
                if status and status not in allowed_statuses:
                    status_errors.append(
                        f"{yaml_file.name}: invalid status '{status}' (allowed: {allowed_statuses})"
                    )
            except Exception:
                pass
        
        if status_errors:
            error_msg = "Invalid status values found:\n" + "\n".join(f"  - {e}" for e in status_errors)
            self.fail(error_msg)
    
    def test_future_dates_not_confirmed(self):
        """Verify that future events are not marked as confirmed."""
        today = date.today()
        future_confirmed = []
        
        for yaml_file in self.yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                date_str = data.get('date')
                status = data.get('status')
                
                if date_str and status == 'confirmed':
                    event_date = datetime.strptime(str(date_str), '%Y-%m-%d').date()
                    if event_date > today:
                        future_confirmed.append(
                            f"{yaml_file.name}: future date {date_str} cannot be 'confirmed'"
                        )
            except Exception:
                pass
        
        if future_confirmed:
            error_msg = "Future events marked as confirmed:\n" + "\n".join(f"  - {e}" for e in future_confirmed)
            self.fail(error_msg)
    
    def test_sources_have_required_fields(self):
        """Verify that all sources have required fields when present."""
        source_errors = []
        required_source_fields = ['title', 'url', 'date']
        
        for yaml_file in self.yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                sources = data.get('sources', [])
                for i, source in enumerate(sources):
                    for field in required_source_fields:
                        if field not in source or not source[field]:
                            source_errors.append(
                                f"{yaml_file.name}: source {i+1} missing field '{field}'"
                            )
            except Exception:
                pass
        
        if source_errors:
            # Only show first 20 errors to avoid overwhelming output
            display_errors = source_errors[:20]
            if len(source_errors) > 20:
                display_errors.append(f"... and {len(source_errors) - 20} more errors")
            error_msg = "Source field errors found:\n" + "\n".join(f"  - {e}" for e in display_errors)
            self.fail(error_msg)
    
    def test_no_duplicate_ids(self):
        """Verify that there are no duplicate IDs across all files."""
        id_map = {}
        duplicates = []
        
        for yaml_file in self.yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                event_id = data.get('id')
                if event_id:
                    if event_id in id_map:
                        duplicates.append(
                            f"Duplicate ID '{event_id}' in {yaml_file.name} and {id_map[event_id]}"
                        )
                    else:
                        id_map[event_id] = yaml_file.name
            except Exception:
                pass
        
        if duplicates:
            error_msg = "Duplicate IDs found:\n" + "\n".join(f"  - {d}" for d in duplicates)
            self.fail(error_msg)

def run_tests():
    """Run all validation tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTimelineValidation)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())