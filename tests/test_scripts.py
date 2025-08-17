#!/usr/bin/env python3
"""
Comprehensive test suite for all scripts in the repository.
Run with: python3 tests/test_scripts.py
"""

import unittest
import tempfile
import shutil
import json
import yaml
import sys
import os
from pathlib import Path
from datetime import date, datetime
from io import StringIO
from unittest.mock import patch, MagicMock

# Add tool directories to path to import scripts
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "generation"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "validation"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "archiving"))

# Import the scripts we're testing
import build_footnotes
import build_timeline_index
import check_whitespace
import gen_archive_qa
import validate_timeline_dates


class TestBuildFootnotes(unittest.TestCase):
    """Test the build_footnotes.py script"""
    
    def setUp(self):
        """Create temporary timeline directory with test data"""
        self.test_dir = tempfile.mkdtemp()
        self.timeline_dir = Path(self.test_dir) / "timeline_data" / "events"
        self.timeline_dir.mkdir(parents=True)
        
        # Save original TIMELINE path and replace with test path
        self.original_timeline = build_footnotes.TIMELINE
        build_footnotes.TIMELINE = self.timeline_dir
        
        # Create test events
        self.create_test_event("2025-01-15-test-event-1", {
            "id": "2025-01-15-test-event-1",
            "title": "Test Event 1",
            "date": "2025-01-15",
            "summary": "First test event",
            "tags": ["test", "sample"],
            "citations": [
                "https://example.com/article1",
                {"url": "https://example.com/article2", "archived": "https://archive.org/article2"}
            ]
        })
        
        self.create_test_event("2025-02-20-test-event-2", {
            "id": "2025-02-20-test-event-2",
            "title": "Test Event 2",
            "date": "2025-02-20",
            "summary": "Second test event",
            "tags": ["test", "different"],
            "citations": [
                "https://example.com/article3"
            ]
        })
        
        self.create_test_event("2024-12-01-old-event", {
            "id": "2024-12-01-old-event",
            "title": "Old Event",
            "date": "2024-12-01",
            "summary": "Event from 2024",
            "tags": ["historical"],
            "citations": [
                "https://example.com/old-article"
            ]
        })
    
    def tearDown(self):
        """Clean up test directory and restore original path"""
        shutil.rmtree(self.test_dir)
        build_footnotes.TIMELINE = self.original_timeline
    
    def create_test_event(self, filename, data):
        """Helper to create test event YAML files"""
        filepath = self.timeline_dir / f"{filename}.yaml"
        with open(filepath, 'w') as f:
            yaml.dump(data, f)
    
    def test_load_events(self):
        """Test that events are loaded correctly"""
        events = build_footnotes.load_events()
        self.assertEqual(len(events), 3)
        
        # Check event IDs are loaded
        event_ids = [e.get("id") for e in events]
        self.assertIn("2025-01-15-test-event-1", event_ids)
        self.assertIn("2025-02-20-test-event-2", event_ids)
        self.assertIn("2024-12-01-old-event", event_ids)
    
    def test_date_filtering(self):
        """Test filtering events by date range"""
        with patch('sys.argv', ['build_footnotes.py', '--start', '2025-01-01', '--end', '2025-01-31']):
            output = StringIO()
            with patch('sys.stdout', output):
                build_footnotes.main()
            
            result = output.getvalue()
            self.assertIn("https://example.com/article1", result)
            self.assertIn("https://archive.org/article2", result)  # Should use archived URL
            self.assertNotIn("https://example.com/article3", result)  # February event
            self.assertNotIn("https://example.com/old-article", result)  # 2024 event
    
    def test_tag_filtering(self):
        """Test filtering events by tags"""
        with patch('sys.argv', ['build_footnotes.py', '--start', '2025-01-01', '--end', '2025-12-31', '--tags', 'test']):
            output = StringIO()
            with patch('sys.stdout', output):
                build_footnotes.main()
            
            result = output.getvalue()
            self.assertIn("https://example.com/article1", result)
            self.assertIn("https://example.com/article3", result)
            self.assertNotIn("https://example.com/old-article", result)  # No 'test' tag
    
    def test_id_filtering(self):
        """Test filtering by specific event IDs"""
        with patch('sys.argv', ['build_footnotes.py', '--ids', '2025-02-20-test-event-2', '2024-12-01-old-event']):
            output = StringIO()
            with patch('sys.stdout', output):
                build_footnotes.main()
            
            result = output.getvalue()
            self.assertNotIn("https://example.com/article1", result)
            self.assertIn("https://example.com/article3", result)
            self.assertIn("https://example.com/old-article", result)
    
    def test_output_format(self):
        """Test that output is properly numbered footnotes"""
        with patch('sys.argv', ['build_footnotes.py', '--start', '2025-01-01', '--end', '2025-12-31']):
            output = StringIO()
            with patch('sys.stdout', output):
                build_footnotes.main()
            
            result = output.getvalue()
            lines = result.strip().split('\n')
            
            # Check numbering
            self.assertTrue(lines[0].startswith("[1]"))
            self.assertTrue(lines[1].startswith("[2]"))
            self.assertTrue(lines[2].startswith("[3]"))
    
    def test_output_to_file(self):
        """Test writing output to file"""
        output_file = Path(self.test_dir) / "test_output.md"
        with patch('sys.argv', ['build_footnotes.py', '--start', '2025-01-01', '--end', '2025-12-31', '-o', str(output_file)]):
            build_footnotes.main()
        
        self.assertTrue(output_file.exists())
        content = output_file.read_text()
        self.assertIn("https://example.com/article1", content)


class TestBuildTimelineIndex(unittest.TestCase):
    """Test the build_timeline_index.py script"""
    
    def setUp(self):
        """Create temporary timeline directory with test data"""
        self.test_dir = tempfile.mkdtemp()
        self.timeline_dir = Path(self.test_dir) / "timeline_data" / "events"
        self.timeline_dir.mkdir(parents=True)
        
        # Create test events
        self.create_test_event("2025-01-15-test-event", {
            "id": "2025-01-15-test-event",
            "title": "Test Event",
            "date": date(2025, 1, 15),
            "tags": ["test", "sample"],
            "sources": [{"url": "https://example.com"}]
        })
        
        self.create_test_event("2025-02-20-another-event", {
            "id": "2025-02-20-another-event",
            "title": "Another Event",
            "date": date(2025, 2, 20),
            "tags": "single-tag",  # Test single tag conversion
            "citations": [{"url": "https://example.com"}]
        })
    
    def tearDown(self):
        """Clean up test directory"""
        shutil.rmtree(self.test_dir)
    
    def create_test_event(self, filename, data):
        """Helper to create test event YAML files"""
        filepath = self.timeline_dir / f"{filename}.yaml"
        with open(filepath, 'w') as f:
            yaml.dump(data, f)
    
    def test_index_generation(self):
        """Test that index.json is generated correctly"""
        output_file = self.timeline_dir / "index.json"
        build_timeline_index.main(str(self.timeline_dir), str(output_file))
        
        self.assertTrue(output_file.exists())
        
        with open(output_file) as f:
            data = json.load(f)
        
        self.assertIn("events", data)
        self.assertEqual(len(data["events"]), 2)
        
        # Check event structure
        event = data["events"][0]
        self.assertIn("_file", event)
        self.assertIn("_id_hash", event)
        self.assertIn("tags", event)
        
        # Check date conversion
        self.assertIsInstance(event["date"], str)
        self.assertEqual(event["date"], "2025-01-15")
    
    def test_tag_normalization(self):
        """Test that tags are normalized to arrays"""
        output_file = self.timeline_dir / "index.json"
        build_timeline_index.main(str(self.timeline_dir), str(output_file))
        
        with open(output_file) as f:
            data = json.load(f)
        
        for event in data["events"]:
            self.assertIsInstance(event["tags"], list)
            if event["id"] == "2025-02-20-another-event":
                self.assertEqual(event["tags"], ["single-tag"])
    
    def test_sources_to_citations_conversion(self):
        """Test that 'sources' is converted to 'citations' when needed"""
        output_file = self.timeline_dir / "index.json"
        build_timeline_index.main(str(self.timeline_dir), str(output_file))
        
        with open(output_file) as f:
            data = json.load(f)
        
        for event in data["events"]:
            if event["id"] == "2025-01-15-test-event":
                self.assertIn("citations", event)


class TestCheckWhitespace(unittest.TestCase):
    """Test the check_whitespace.py script"""
    
    def setUp(self):
        """Create temporary directory with test Python files"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Initialize git repo for whitespace checking
        os.system("git init > /dev/null 2>&1")
    
    def tearDown(self):
        """Clean up and restore directory"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_clean_file(self):
        """Test that clean files pass"""
        clean_file = Path("clean.py")
        clean_file.write_text("def hello():\n    print('Hello')\n")
        os.system("git add clean.py 2>/dev/null")
        
        result = check_whitespace.main()
        self.assertEqual(result, 0)
    
    def test_crlf_detection(self):
        """Test detection of CRLF line endings"""
        # Save current directory
        original_dir = os.getcwd()
        
        # Create a temp directory for the test
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Initialize git repo
            os.system("git init >/dev/null 2>&1")
            
            # Create file with CRLF endings using binary write
            bad_file = Path("crlf.py")
            bad_file.write_bytes(b"def hello():\r\n    print('Hello')\r\n")
            
            # Add file to git
            os.system("git add crlf.py")
            
            # Run check
            result = check_whitespace.main()
            
            # Restore original directory
            os.chdir(original_dir)
            
            # Should detect CRLF
            self.assertEqual(result, 1)


class TestIntegration(unittest.TestCase):
    """Integration tests for script interactions"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.timeline_dir = Path(self.test_dir) / "timeline_data" / "events"
        self.timeline_dir.mkdir(parents=True)
        
        # Create a comprehensive test event
        self.create_test_event("2025-03-15-integration-test", {
            "id": "2025-03-15-integration-test",
            "title": "Integration Test Event",
            "date": date(2025, 3, 15),
            "summary": "Testing script integration",
            "location": "Test Location",
            "actors": ["Test Actor 1", "Test Actor 2"],
            "tags": ["integration", "test"],
            "citations": [
                "https://example.com/source1",
                {"url": "https://example.com/source2", "archived": "https://archive.org/source2"}
            ],
            "sources": [
                {
                    "title": "Test Source",
                    "url": "https://example.com/source1",
                    "outlet": "Test Outlet",
                    "date": "2025-03-15"
                }
            ],
            "status": "confirmed",
            "notes": "Test notes"
        })
        
        # Save original paths
        self.original_footnotes_timeline = build_footnotes.TIMELINE
        build_footnotes.TIMELINE = self.timeline_dir
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
        build_footnotes.TIMELINE = self.original_footnotes_timeline
    
    def create_test_event(self, filename, data):
        """Helper to create test event YAML files"""
        filepath = self.timeline_dir / f"{filename}.yaml"
        with open(filepath, 'w') as f:
            yaml.dump(data, f)
    
    def test_pipeline_index_then_footnotes(self):
        """Test that index generation works with footnotes generation"""
        # Generate index
        index_file = self.timeline_dir / "index.json"
        build_timeline_index.main(str(self.timeline_dir), str(index_file))
        
        # Verify index exists and is valid
        self.assertTrue(index_file.exists())
        with open(index_file) as f:
            index_data = json.load(f)
        self.assertEqual(len(index_data["events"]), 1)
        
        # Generate footnotes
        with patch('sys.argv', ['build_footnotes.py', '--start', '2025-03-01', '--end', '2025-03-31']):
            output = StringIO()
            with patch('sys.stdout', output):
                build_footnotes.main()
            
            footnotes = output.getvalue()
            self.assertIn("[1] https://example.com/source1", footnotes)
            self.assertIn("[2] https://archive.org/source2", footnotes)


class TestValidateTimelineDates(unittest.TestCase):
    """Test the validate_timeline_dates.py script"""
    
    def setUp(self):
        """Create temporary timeline directory with test data"""
        self.test_dir = tempfile.mkdtemp()
        self.timeline_dir = Path(self.test_dir) / "timeline_data" / "events"
        self.timeline_dir.mkdir(parents=True)
        
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)
    
    def create_test_event(self, filename, data):
        """Helper to create test timeline files"""
        filepath = self.timeline_dir / f"{filename}.yaml"
        with open(filepath, 'w') as f:
            yaml.dump(data, f)
    
    def test_detect_future_confirmed_events(self):
        """Test detection of future events marked as confirmed"""
        # Create a future event marked as confirmed
        future_date = "2026-01-01"
        self.create_test_event("2026-01-01--future-event", {
            "id": "2026-01-01--future-event",
            "date": future_date,
            "title": "Future Event",
            "status": "confirmed",
            "summary": "This shouldn't be confirmed"
        })
        
        # Create a past event marked as confirmed (this is OK)
        self.create_test_event("2024-01-01--past-event", {
            "id": "2024-01-01--past-event", 
            "date": "2024-01-01",
            "title": "Past Event",
            "status": "confirmed",
            "summary": "This is properly confirmed"
        })
        
        # Run validation
        issues = validate_timeline_dates.validate_timeline_dates(self.timeline_dir)
        
        # Check that future confirmed event is detected
        self.assertEqual(len(issues['future_confirmed']), 1)
        self.assertIn('2026-01-01--future-event.yaml', issues['future_confirmed'][0]['file'])
    
    def test_detect_invalid_dates(self):
        """Test detection of invalid date formats"""
        # Create event with invalid date
        self.create_test_event("bad-date-event", {
            "id": "bad-date-event",
            "date": "not-a-date",
            "title": "Bad Date Event",
            "status": "pending"
        })
        
        # Run validation
        issues = validate_timeline_dates.validate_timeline_dates(self.timeline_dir)
        
        # Check that invalid date is detected
        self.assertEqual(len(issues['invalid_dates']), 1)
    
    def test_detect_missing_status(self):
        """Test detection of missing status field"""
        # Create event without status
        self.create_test_event("2024-01-01--no-status", {
            "id": "2024-01-01--no-status",
            "date": "2024-01-01",
            "title": "No Status Event"
        })
        
        # Run validation
        issues = validate_timeline_dates.validate_timeline_dates(self.timeline_dir)
        
        # Check that missing status is detected
        self.assertEqual(len(issues['missing_status']), 1)
    
    def test_future_predicted_allowed(self):
        """Test that future events can be marked as predicted"""
        # Create future event marked as predicted (this should be OK)
        self.create_test_event("2026-01-01--predicted", {
            "id": "2026-01-01--predicted",
            "date": "2026-01-01",
            "title": "Predicted Future Event",
            "status": "predicted",
            "summary": "This is a prediction"
        })
        
        # Run validation
        issues = validate_timeline_dates.validate_timeline_dates(self.timeline_dir)
        
        # Check that predicted future event is NOT flagged
        self.assertEqual(len(issues['future_confirmed']), 0)


class TestRunner:
    """Custom test runner with better output formatting"""
    
    @staticmethod
    def run():
        """Run all tests with formatted output"""
        print("=" * 70)
        print("Running Script Test Suite")
        print("=" * 70)
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test classes
        suite.addTests(loader.loadTestsFromTestCase(TestBuildFootnotes))
        suite.addTests(loader.loadTestsFromTestCase(TestBuildTimelineIndex))
        suite.addTests(loader.loadTestsFromTestCase(TestCheckWhitespace))
        suite.addTests(loader.loadTestsFromTestCase(TestValidateTimelineDates))
        suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
        
        # Run tests with verbosity
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print summary
        print("\n" + "=" * 70)
        if result.wasSuccessful():
            print("✅ All tests passed!")
        else:
            print(f"❌ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        print("=" * 70)
        
        return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(TestRunner.run())