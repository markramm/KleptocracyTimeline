#!/usr/bin/env python3
"""
Test suite for YAML Event Management Tools
"""

import unittest
import tempfile
import shutil
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yaml_tools import YamlEventManager, EditResult, SourceResult, BulkEditResult


class TestYamlEventManager(unittest.TestCase):
    """Test cases for YamlEventManager"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.events_dir = Path(self.test_dir) / "events"
        self.events_dir.mkdir()
        
        # Initialize manager
        self.manager = YamlEventManager(str(self.events_dir))
        
        # Create sample events
        self._create_sample_events()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def _create_sample_events(self):
        """Create sample event files for testing"""
        events = [
            {
                'id': 'event-001',
                'date': '2024-01-15',
                'title': 'Test Event One',
                'summary': 'This is a test event for unit testing purposes',
                'importance': 7,
                'status': 'confirmed',
                'actors': ['Actor One', 'Actor Two'],
                'tags': ['test', 'sample'],
                'sources': [
                    {
                        'title': 'Source One',
                        'outlet': 'Test News',
                        'url': 'https://example.com/1',
                        'date': '2024-01-15'
                    },
                    {
                        'title': 'Source Two',
                        'outlet': 'Sample Times',
                        'url': 'https://example.com/2',
                        'date': '2024-01-16'
                    }
                ]
            },
            {
                'id': 'event-002',
                'date': '2024-02-20',
                'title': 'Test Event Two',
                'summary': 'Another test event with different properties',
                'importance': 5,
                'status': 'reported',
                'actors': ['Actor Three'],
                'tags': ['test', 'different'],
                'sources': [
                    {
                        'title': 'Single Source',
                        'outlet': 'Solo News',
                        'url': 'https://example.com/3',
                        'date': '2024-02-20'
                    }
                ]
            },
            {
                'id': 'event-003',
                'date': '2024-03-10',
                'title': 'Test Event Three',
                'summary': 'Event with minimal sources',
                'importance': 3,
                'status': 'disputed',
                'actors': ['Actor One', 'Actor Four'],
                'tags': ['disputed', 'test']
            }
        ]
        
        for i, event in enumerate(events):
            file_path = self.events_dir / f"test-event-{i+1:03d}.yaml"
            with open(file_path, 'w') as f:
                yaml.dump(event, f, default_flow_style=False, sort_keys=False)
    
    def test_search_basic(self):
        """Test basic search functionality"""
        results = self.manager.yaml_search(query="Test Event", max_results=10)
        self.assertEqual(len(results), 3)
        self.assertTrue(all('Test Event' in r['title'] for r in results))
    
    def test_search_by_field(self):
        """Test searching specific fields"""
        results = self.manager.yaml_search(
            query="Actor One",
            fields=['actors'],
            max_results=10
        )
        self.assertEqual(len(results), 2)  # event-001 and event-003
    
    def test_search_by_date_range(self):
        """Test date range filtering"""
        results = self.manager.yaml_search(
            date_range=('2024-01-01', '2024-01-31'),
            max_results=10
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 'event-001')
    
    def test_search_by_importance(self):
        """Test importance filtering"""
        results = self.manager.yaml_search(
            importance=(5, 10),
            max_results=10
        )
        self.assertEqual(len(results), 2)  # event-001 (7) and event-002 (5)
    
    def test_search_by_status(self):
        """Test status filtering"""
        results = self.manager.yaml_search(
            status=['confirmed', 'disputed'],
            max_results=10
        )
        self.assertEqual(len(results), 2)  # event-001 and event-003
    
    def test_search_by_tags(self):
        """Test tag filtering"""
        results = self.manager.yaml_search(
            tags=['different'],
            max_results=10
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 'event-002')
    
    def test_edit_basic(self):
        """Test basic edit functionality"""
        file_path = self.events_dir / "test-event-001.yaml"
        
        result = self.manager.yaml_edit(
            file_path=str(file_path),
            updates={'importance': 9},
            dry_run=False
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.backup_path)
        
        # Verify the change
        with open(file_path, 'r') as f:
            event = yaml.safe_load(f)
        self.assertEqual(event['importance'], 9)
    
    def test_edit_validation(self):
        """Test edit with validation"""
        file_path = self.events_dir / "test-event-001.yaml"
        
        # Try invalid importance value
        result = self.manager.yaml_edit(
            file_path=str(file_path),
            updates={'importance': 15},  # Invalid: > 10
            dry_run=False
        )
        
        # Should succeed but have validation errors
        self.assertTrue(result.success)
        self.assertTrue(any('Importance' in e for e in result.validation_errors))
    
    def test_edit_dry_run(self):
        """Test dry run mode"""
        file_path = self.events_dir / "test-event-001.yaml"
        
        # Get original value
        with open(file_path, 'r') as f:
            original = yaml.safe_load(f)
        
        result = self.manager.yaml_edit(
            file_path=str(file_path),
            updates={'importance': 8},
            dry_run=True
        )
        
        self.assertTrue(result.success)
        self.assertIsNone(result.backup_path)  # No backup in dry run
        
        # Verify no change was made
        with open(file_path, 'r') as f:
            after = yaml.safe_load(f)
        self.assertEqual(original['importance'], after['importance'])
    
    def test_bulk_edit(self):
        """Test bulk edit functionality"""
        result = self.manager.yaml_bulk_edit(
            search_criteria={'tags': ['test']},
            updates={'location': 'Test Location'},
            interactive=False
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.total_changes, 3)  # All have 'test' tag
        
        # Verify changes
        for file_path in self.events_dir.glob("*.yaml"):
            with open(file_path, 'r') as f:
                event = yaml.safe_load(f)
            if 'test' in event.get('tags', []):
                self.assertEqual(event.get('location'), 'Test Location')
    
    def test_manage_sources_add(self):
        """Test adding sources"""
        file_path = self.events_dir / "test-event-003.yaml"
        
        new_source = {
            'title': 'New Source',
            'outlet': 'New Outlet',
            'url': 'https://example.com/new',
            'date': '2024-03-11'
        }
        
        result = self.manager.manage_sources(
            file_path=str(file_path),
            action='add',
            sources=[new_source]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.added), 1)
        
        # Verify source was added
        with open(file_path, 'r') as f:
            event = yaml.safe_load(f)
        self.assertEqual(len(event.get('sources', [])), 1)
    
    def test_manage_sources_duplicate_detection(self):
        """Test duplicate source detection"""
        file_path = self.events_dir / "test-event-001.yaml"
        
        # Try adding existing source
        duplicate_source = {
            'title': 'Source One',
            'outlet': 'Test News',
            'url': 'https://example.com/1',
            'date': '2024-01-15'
        }
        
        result = self.manager.manage_sources(
            file_path=str(file_path),
            action='add',
            sources=[duplicate_source],
            check_duplicates=True
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.added), 0)
        self.assertEqual(len(result.duplicates_found), 1)
    
    def test_manage_sources_validate(self):
        """Test source validation"""
        file_path = self.events_dir / "test-event-002.yaml"
        
        result = self.manager.manage_sources(
            file_path=str(file_path),
            action='validate',
            prefer_free=True
        )
        
        self.assertTrue(result.success)
        # Should suggest adding more sources (only has 1)
        self.assertTrue(any('only one source' in s.lower() for s in result.suggestions))
    
    def test_manage_sources_replace(self):
        """Test replacing sources"""
        file_path = self.events_dir / "test-event-001.yaml"
        
        new_sources = [
            {
                'title': 'Replacement Source',
                'outlet': 'New Outlet',
                'url': 'https://example.com/replacement',
                'date': '2024-01-20'
            }
        ]
        
        result = self.manager.manage_sources(
            file_path=str(file_path),
            action='replace',
            sources=new_sources
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.removed), 2)  # Original had 2 sources
        self.assertEqual(len(result.added), 1)
        
        # Verify replacement
        with open(file_path, 'r') as f:
            event = yaml.safe_load(f)
        self.assertEqual(len(event['sources']), 1)
        self.assertEqual(event['sources'][0]['title'], 'Replacement Source')
    
    def test_validation_required_fields(self):
        """Test validation of required fields"""
        event = {
            'id': 'test',
            'date': '2024-01-01',
            # Missing title, summary, importance, status
        }
        
        errors = self.manager._validate_event(event)
        self.assertTrue(any('title' in e.lower() for e in errors))
        self.assertTrue(any('summary' in e.lower() for e in errors))
        self.assertTrue(any('importance' in e.lower() for e in errors))
        self.assertTrue(any('status' in e.lower() for e in errors))
    
    def test_validation_date_format(self):
        """Test date format validation"""
        event = {
            'id': 'test',
            'date': '01/15/2024',  # Wrong format
            'title': 'Test',
            'summary': 'Test summary',
            'importance': 5,
            'status': 'confirmed'
        }
        
        errors = self.manager._validate_event(event)
        self.assertTrue(any('date format' in e.lower() for e in errors))
    
    def test_validation_status_values(self):
        """Test status value validation"""
        event = {
            'id': 'test',
            'date': '2024-01-01',
            'title': 'Test',
            'summary': 'Test summary',
            'importance': 5,
            'status': 'invalid_status'  # Invalid status
        }
        
        errors = self.manager._validate_event(event)
        self.assertTrue(any('status' in e.lower() for e in errors))
    
    def test_parse_date_query(self):
        """Test flexible date parsing"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Test relative dates
        self.assertEqual(self.manager._parse_date_query('today'), today)
        
        # Test year-only
        self.assertEqual(self.manager._parse_date_query('2024'), '2024-01-01')
        
        # Test month-year
        self.assertEqual(self.manager._parse_date_query('mar 2024'), '2024-03-01')
        
        # Test already formatted
        self.assertEqual(self.manager._parse_date_query('2024-03-15'), '2024-03-15')
    
    def test_suggest_improvements(self):
        """Test improvement suggestions"""
        event = {
            'id': 'test',
            'date': '2024-01-01',
            'title': 'Test',
            'summary': 'Very brief',  # Too short
            'importance': 5,
            'status': 'confirmed',
            'actors': ['Single Actor'],  # Only one actor
            'sources': [
                {'title': 'Source', 'outlet': 'News'},
                {'title': 'Source 2', 'outlet': 'News'}  # Same outlet
            ]
        }
        
        suggestions = self.manager._suggest_improvements(event)
        
        # Should suggest: brief summary, single actor, source diversity
        self.assertTrue(any('brief' in s.lower() for s in suggestions))
        self.assertTrue(any('actor' in s.lower() for s in suggestions))
        self.assertTrue(any('divers' in s.lower() for s in suggestions))
    
    def test_cache_functionality(self):
        """Test file caching"""
        file_path = self.events_dir / "test-event-001.yaml"
        
        # Load file twice
        event1 = self.manager._load_event(file_path)
        event2 = self.manager._load_event(file_path)
        
        # Should be same object from cache
        self.assertIs(event1, event2)
        
        # Modify file
        self.manager.yaml_edit(
            file_path=str(file_path),
            updates={'importance': 8},
            dry_run=False
        )
        
        # Load again - should get new version
        event3 = self.manager._load_event(file_path)
        self.assertIsNot(event1, event3)
        self.assertEqual(event3['importance'], 8)
    
    def test_backup_creation(self):
        """Test backup file creation"""
        file_path = self.events_dir / "test-event-001.yaml"
        
        result = self.manager.yaml_edit(
            file_path=str(file_path),
            updates={'importance': 9},
            create_backup=True,
            dry_run=False
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.backup_path)
        
        # Verify backup exists
        backup_path = Path(result.backup_path)
        self.assertTrue(backup_path.exists())
        
        # Verify backup content
        with open(backup_path, 'r') as f:
            backup = yaml.safe_load(f)
        self.assertEqual(backup['importance'], 7)  # Original value


class TestCLI(unittest.TestCase):
    """Test command-line interface"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.events_dir = Path(self.test_dir) / "events"
        self.events_dir.mkdir()
        
        # Create a simple test event
        event = {
            'id': 'cli-test',
            'date': '2024-01-15',
            'title': 'CLI Test Event',
            'summary': 'Event for CLI testing',
            'importance': 5,
            'status': 'confirmed',
            'sources': [
                {
                    'title': 'Test Source',
                    'outlet': 'Test News',
                    'url': 'https://example.com/test'
                }
            ]
        }
        
        self.test_file = self.events_dir / "cli-test.yaml"
        with open(self.test_file, 'w') as f:
            yaml.dump(event, f, default_flow_style=False, sort_keys=False)
        
        # Save original argv
        self.original_argv = sys.argv
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
        sys.argv = self.original_argv
    
    def test_cli_search(self):
        """Test CLI search command"""
        from yaml_tools import main
        import io
        from contextlib import redirect_stdout
        
        sys.argv = ['yaml_tools.py', 'search', 'CLI Test']
        
        # Capture output
        f = io.StringIO()
        with redirect_stdout(f):
            # Need to patch the base path for testing
            import yaml_tools
            original_init = yaml_tools.YamlEventManager.__init__
            test_events_dir = self.events_dir  # Capture in local variable
            
            def patched_init(self, base_path=None):
                original_init(self, str(test_events_dir))
            
            yaml_tools.YamlEventManager.__init__ = patched_init
            
            try:
                main()
            finally:
                yaml_tools.YamlEventManager.__init__ = original_init
        
        output = f.getvalue()
        self.assertIn('CLI Test Event', output)


if __name__ == '__main__':
    unittest.main()