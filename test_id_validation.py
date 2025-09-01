#!/usr/bin/env python3
"""
Test that all YAML files have IDs matching their filenames.
This should be run as part of the test suite.
"""

import yaml
from pathlib import Path
import sys
import unittest

class TestTimelineIDValidation(unittest.TestCase):
    """Test that all timeline YAML files have correct IDs."""
    
    def test_all_ids_match_filenames(self):
        """Verify that every YAML file's ID field matches its filename."""
        events_dir = Path('timeline_data/events')
        mismatches = []
        
        # Check if events directory exists
        self.assertTrue(events_dir.exists(), f"Events directory {events_dir} does not exist")
        
        yaml_files = list(events_dir.glob('*.yaml'))
        self.assertGreater(len(yaml_files), 0, "No YAML files found in events directory")
        
        for yaml_file in yaml_files:
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
        
        # Assert no mismatches found
        if mismatches:
            error_msg = "ID/filename mismatches found:\n" + "\n".join(f"  - {m}" for m in mismatches)
            self.fail(error_msg)
    
    def test_all_yaml_files_valid(self):
        """Verify that all YAML files can be parsed without errors."""
        events_dir = Path('timeline_data/events')
        parse_errors = []
        
        for yaml_file in events_dir.glob('*.yaml'):
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
        events_dir = Path('timeline_data/events')
        required_fields = ['id', 'date', 'title', 'summary']
        missing_fields = []
        
        for yaml_file in events_dir.glob('*.yaml'):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                for field in required_fields:
                    if field not in data or data[field] is None:
                        missing_fields.append(f"{yaml_file.name}: missing required field '{field}'")
                        
            except Exception as e:
                # Already tested in test_all_yaml_files_valid
                pass
        
        if missing_fields:
            error_msg = "Missing required fields:\n" + "\n".join(f"  - {m}" for m in missing_fields)
            self.fail(error_msg)

def run_tests():
    """Run the ID validation tests and return exit code."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTimelineIDValidation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return 0 if all tests passed, 1 otherwise
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())