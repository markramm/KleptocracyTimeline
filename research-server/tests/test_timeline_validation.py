#!/usr/bin/env python3
"""
Test suite for timeline event validation.
Ensures data integrity and consistency across all timeline events.
"""

import json
import unittest
from pathlib import Path
from datetime import datetime, date
import sys
import os

# Add server directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

# Import validation constants
from validation_functions import VALID_STATUSES

class TestTimelineValidation(unittest.TestCase):
    """Comprehensive validation tests for timeline events."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.events_dir = Path('timeline/data/events')
        cls.md_files = list(cls.events_dir.glob('*.md'))
        # Exclude README.md from validation
        cls.md_files = [f for f in cls.md_files if f.name != 'README.md']
        
    def test_events_directory_exists(self):
        """Test that the events directory exists."""
        self.assertTrue(self.events_dir.exists(), 
                       f"Events directory {self.events_dir} does not exist")
        
    def test_has_markdown_files(self):
        """Test that there are markdown files to validate."""
        self.assertGreater(len(self.md_files), 0,
                          "No markdown files found in events directory")
    
    def test_all_ids_match_filenames(self):
        """Verify that every markdown file's ID field matches its filename."""
        import yaml
        mismatches = []

        for md_file in self.md_files:
            expected_id = md_file.stem  # filename without extension

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract YAML frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        actual_id = frontmatter.get('id')

                        if actual_id != expected_id:
                            mismatches.append(
                                f"{md_file.name}: expected ID '{expected_id}', got '{actual_id}'"
                            )

            except Exception as e:
                self.fail(f"Error loading {md_file.name}: {e}")

        if mismatches:
            error_msg = "ID/filename mismatches found:\n" + "\n".join(f"  - {m}" for m in mismatches)
            self.fail(error_msg)
    
    def test_all_markdown_files_valid(self):
        """Verify that all markdown files can be parsed without errors."""
        import yaml
        parse_errors = []

        for md_file in self.md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract and parse YAML frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        yaml.safe_load(parts[1])
            except yaml.YAMLError as e:
                parse_errors.append(f"{md_file.name}: {e}")
            except Exception as e:
                parse_errors.append(f"{md_file.name}: {e}")

        if parse_errors:
            error_msg = "Markdown/YAML parsing errors found:\n" + "\n".join(f"  - {e}" for e in parse_errors)
            self.fail(error_msg)
    
    def test_required_fields_present(self):
        """Verify that all markdown files have required fields."""
        import yaml
        required_fields = ['id', 'date', 'title']  # summary is in markdown body
        missing_fields = []

        for md_file in self.md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract YAML frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])

                        for field in required_fields:
                            if field not in frontmatter or frontmatter[field] is None:
                                missing_fields.append(
                                    f"{md_file.name}: missing required field '{field}'"
                                )

            except Exception:
                # Already tested in test_all_markdown_files_valid
                pass

        if missing_fields:
            error_msg = "Missing required fields:\n" + "\n".join(f"  - {m}" for m in missing_fields)
            self.fail(error_msg)
    
    def test_date_format_valid(self):
        """Verify that all dates are in YYYY-MM-DD format."""
        import yaml
        date_errors = []

        for md_file in self.md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract YAML frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        date_str = frontmatter.get('date')

                        if date_str:
                            try:
                                # Try to parse the date
                                datetime.strptime(str(date_str), '%Y-%m-%d')
                            except ValueError:
                                date_errors.append(
                                    f"{md_file.name}: invalid date format '{date_str}' (expected YYYY-MM-DD)"
                                )
            except Exception:
                # Already tested in other tests
                pass

        if date_errors:
            error_msg = "Date format errors found:\n" + "\n".join(f"  - {e}" for e in date_errors)
            self.fail(error_msg)
    
    def test_status_values_valid(self):
        """Verify that status values are from the allowed set."""
        import yaml
        # Use VALID_STATUSES from validation_functions module
        allowed_statuses = set(VALID_STATUSES)
        status_errors = []

        for md_file in self.md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract YAML frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        status = frontmatter.get('status')

                        if status and status not in allowed_statuses:
                            status_errors.append(
                                f"{md_file.name}: invalid status '{status}' (allowed: {sorted(allowed_statuses)})"
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
        
        for md_file in self.md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    import yaml
                    content_str = f.read()
                    if content_str.startswith('---'):
                        parts = content_str.split('---', 2)
                        if len(parts) >= 3:
                            data = yaml.safe_load(parts[1])
                        else:
                            data = {}
                    else:
                        data = {}
                
                date_str = data.get('date')
                status = data.get('status')
                
                if date_str and status == 'confirmed':
                    event_date = datetime.strptime(str(date_str), '%Y-%m-%d').date()
                    if event_date > today:
                        future_confirmed.append(
                            f"{md_file.name}: future date {date_str} cannot be 'confirmed'"
                        )
            except Exception:
                pass
        
        if future_confirmed:
            error_msg = "Future events marked as confirmed:\n" + "\n".join(f"  - {e}" for e in future_confirmed)
            self.fail(error_msg)
    
    def test_sources_have_required_fields(self):
        """Verify that all sources have required fields when present."""
        source_errors = []
        # Sources must have 'title' and 'url' fields present (for structure)
        # At least ONE of title or url must be non-empty (for usefulness)
        # date and outlet are recommended but not required (per validation_functions.py)
        required_source_fields = ['title', 'url']

        for md_file in self.md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    import yaml
                    content_str = f.read()
                    if content_str.startswith('---'):
                        parts = content_str.split('---', 2)
                        if len(parts) >= 3:
                            data = yaml.safe_load(parts[1])
                        else:
                            data = {}
                    else:
                        data = {}

                sources = data.get('sources', [])
                for i, source in enumerate(sources):
                    # Check that source is a dict with required fields
                    if not isinstance(source, dict):
                        source_errors.append(
                            f"{md_file.name}: source {i+1} is not a dict (got {type(source).__name__})"
                        )
                        continue

                    # Check that required fields exist
                    for field in required_source_fields:
                        if field not in source:
                            source_errors.append(
                                f"{md_file.name}: source {i+1} missing field '{field}'"
                            )

                    # Check that at least ONE field has content
                    title = (source.get('title') or '').strip()
                    url = (source.get('url') or '').strip()
                    if not title and not url:
                        source_errors.append(
                            f"{md_file.name}: source {i+1} has empty title AND url"
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
        
        for md_file in self.md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    import yaml
                    content_str = f.read()
                    if content_str.startswith('---'):
                        parts = content_str.split('---', 2)
                        if len(parts) >= 3:
                            data = yaml.safe_load(parts[1])
                        else:
                            data = {}
                    else:
                        data = {}
                
                event_id = data.get('id')
                if event_id:
                    if event_id in id_map:
                        duplicates.append(
                            f"Duplicate ID '{event_id}' in {md_file.name} and {id_map[event_id]}"
                        )
                    else:
                        id_map[event_id] = md_file.name
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