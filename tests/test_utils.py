#!/usr/bin/env python3
"""Tests for script utilities."""

import pytest
import tempfile
import yaml
import json
import csv
from pathlib import Path
from datetime import date, datetime
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from utils.events import EventManager
from utils.cli import create_base_parser, add_filter_arguments, validate_date_format
from utils.exporters import CSVExporter, JSONExporter, YAMLExporter, ExporterFactory


class TestEventManager:
    """Test EventManager functionality."""
    
    def setup_method(self):
        """Create test events."""
        self.test_events = [
            {
                'id': 'test-001',
                'date': '2024-01-01',
                'title': 'Test Event 1',
                'summary': 'Summary 1',
                'tags': ['tag1', 'tag2'],
                'actors': ['Actor A', 'Actor B'],
                'importance': 'high',
                'sources': [{'url': 'http://example.com'}]
            },
            {
                'id': 'test-002', 
                'date': '2024-02-15',
                'title': 'Test Event 2',
                'summary': 'Summary 2',
                'tags': ['tag2', 'tag3'],
                'actors': ['Actor B', 'Actor C'],
                'importance': 'medium',
                'sources': [
                    {'url': 'http://example.com/1'},
                    {'url': 'http://example.com/2'}
                ]
            },
            {
                'id': 'test-003',
                'date': '2024-03-30',
                'title': 'Test Event 3',
                'summary': 'Summary 3',
                'tags': ['tag1'],
                'actors': ['Actor A'],
                'importance': 'critical',
                'capture_lane': 'judicial',
                'sources': []
            }
        ]
    
    def test_normalize_date(self):
        """Test date normalization."""
        assert EventManager.normalize_date('2024-01-01') == '2024-01-01'
        assert EventManager.normalize_date(date(2024, 1, 1)) == '2024-01-01'
        assert EventManager.normalize_date(datetime(2024, 1, 1, 12, 0)) == '2024-01-01'
        assert EventManager.normalize_date(None) is None
    
    def test_get_date_key(self):
        """Test date key extraction."""
        event = {'date': '2024-01-01'}
        assert EventManager._get_date_key(event) == '2024-01-01'
        
        event = {'date': date(2024, 1, 1)}
        assert EventManager._get_date_key(event) == '2024-01-01'
    
    def test_statistics_calculation(self):
        """Test statistics calculation with mock data."""
        # Create temporary directory with test events
        with tempfile.TemporaryDirectory() as tmpdir:
            events_dir = Path(tmpdir) / 'events'
            events_dir.mkdir()
            
            # Write test events
            for event in self.test_events:
                file_path = events_dir / f"{event['id']}.yaml"
                with open(file_path, 'w') as f:
                    yaml.dump(event, f)
            
            # Create manager and test
            manager = EventManager(f'{tmpdir}/events')
            events = manager.load_all_events()
            
            assert len(events) == 3
            
            stats = manager.calculate_statistics()
            assert stats['total_events'] == 3
            assert stats['date_range']['start'] == '2024-01-01'
            assert stats['date_range']['end'] == '2024-03-30'
            assert stats['tag_counts']['tag1'] == 2
            assert stats['tag_counts']['tag2'] == 2
            assert stats['tag_counts']['tag3'] == 1
            assert stats['actor_counts']['Actor A'] == 2
            assert stats['actor_counts']['Actor B'] == 2
            assert stats['source_statistics']['no_sources'] == 1
            assert stats['source_statistics']['single_source'] == 1
            assert stats['source_statistics']['multiple_sources'] == 1
    
    def test_event_filtering(self):
        """Test event filtering methods."""
        with tempfile.TemporaryDirectory() as tmpdir:
            events_dir = Path(tmpdir) / 'events'
            events_dir.mkdir()
            
            # Write test events
            for event in self.test_events:
                file_path = events_dir / f"{event['id']}.yaml"
                with open(file_path, 'w') as f:
                    yaml.dump(event, f)
            
            manager = EventManager(f'{tmpdir}/events')
            manager.load_all_events()
            
            # Test date range filtering
            filtered = manager.get_events_by_date_range('2024-01-01', '2024-02-28')
            assert len(filtered) == 2
            assert filtered[0]['id'] == 'test-001'
            assert filtered[1]['id'] == 'test-002'
            
            # Test tag filtering
            filtered = manager.get_events_by_tags(['tag1'])
            assert len(filtered) == 2
            assert all('tag1' in e['tags'] for e in filtered)
            
            # Test actor filtering
            filtered = manager.get_events_by_actors(['Actor C'])
            assert len(filtered) == 1
            assert filtered[0]['id'] == 'test-002'
    
    def test_missing_field_detection(self):
        """Test finding events missing fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            events_dir = Path(tmpdir) / 'events'
            events_dir.mkdir()
            
            # Write test events
            for event in self.test_events:
                file_path = events_dir / f"{event['id']}.yaml"
                with open(file_path, 'w') as f:
                    yaml.dump(event, f)
            
            manager = EventManager(f'{tmpdir}/events')
            manager.load_all_events()
            
            # Test finding missing capture_lane
            missing = manager.find_events_missing_field('capture_lane')
            assert len(missing) == 2  # Only test-003 has capture_lane
            
            # Test finding missing description (all missing)
            missing = manager.find_events_missing_field('description')
            assert len(missing) == 3


class TestCLIUtilities:
    """Test CLI utility functions."""
    
    def test_create_base_parser(self):
        """Test base parser creation."""
        parser = create_base_parser('Test parser')
        assert parser.description == 'Test parser'
        
        # Test with common arguments
        parser = create_base_parser('Test', add_common=True)
        args = parser.parse_args(['--verbose'])
        assert args.verbose is True
    
    def test_add_filter_arguments(self):
        """Test filter argument addition."""
        parser = create_base_parser('Test')
        add_filter_arguments(parser)
        
        args = parser.parse_args([
            '--date-start', '2024-01-01',
            '--date-end', '2024-12-31',
            '--tags', 'tag1', 'tag2',
            '--importance', 'high'
        ])
        
        assert args.date_start == '2024-01-01'
        assert args.date_end == '2024-12-31'
        assert args.tags == ['tag1', 'tag2']
        assert args.importance == 'high'
    
    def test_validate_date_format(self):
        """Test date format validation."""
        assert validate_date_format('2024-01-01') == '2024-01-01'
        
        with pytest.raises(Exception):
            validate_date_format('2024/01/01')
        
        with pytest.raises(Exception):
            validate_date_format('01-01-2024')


class TestExporters:
    """Test exporter classes."""
    
    def setup_method(self):
        """Create test events."""
        self.test_events = [
            {
                'id': 'test-001',
                'date': '2024-01-01',
                'title': 'Test Event 1',
                'summary': 'Summary 1',
                'tags': ['tag1', 'tag2'],
                'actors': ['Actor A'],
                'sources': [{'url': 'http://example.com', 'outlet': 'Test Outlet'}]
            },
            {
                'id': 'test-002',
                'date': date(2024, 2, 15),  # Test date object
                'title': 'Test Event 2',
                'summary': 'Summary 2',
                'tags': ['tag3'],
                'actors': ['Actor B', 'Actor C'],
                'sources': []
            }
        ]
    
    def test_csv_exporter(self):
        """Test CSV export."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            output_file = Path(f.name)
        
        try:
            exporter = CSVExporter(self.test_events)
            count = exporter.export(output_file)
            
            assert count == 2
            assert output_file.exists()
            
            # Read and verify CSV
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]['title'] == 'Test Event 1'
            assert rows[0]['date'] == '2024-01-01'
            assert rows[0]['actors'] == 'Actor A'
            assert rows[0]['tags'] == 'tag1; tag2'
            assert rows[1]['title'] == 'Test Event 2'
            assert rows[1]['date'] == '2024-02-15'
            assert rows[1]['actors'] == 'Actor B; Actor C'
        
        finally:
            output_file.unlink(missing_ok=True)
    
    def test_json_exporter(self):
        """Test JSON export."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_file = Path(f.name)
        
        try:
            exporter = JSONExporter(self.test_events)
            count = exporter.export(output_file)
            
            assert count == 2
            assert output_file.exists()
            
            # Read and verify JSON
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]['title'] == 'Test Event 1'
            assert data[0]['date'] == '2024-01-01'
            assert data[1]['title'] == 'Test Event 2'
            assert data[1]['date'] == '2024-02-15'  # Date object serialized
        
        finally:
            output_file.unlink(missing_ok=True)
    
    def test_yaml_exporter(self):
        """Test YAML export."""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            output_file = Path(f.name)
        
        try:
            exporter = YAMLExporter(self.test_events)
            count = exporter.export(output_file)
            
            assert count == 2
            assert output_file.exists()
            
            # Read and verify YAML
            with open(output_file, 'r') as f:
                data = yaml.safe_load(f)
            
            assert 'metadata' in data
            assert data['metadata']['event_count'] == 2
            assert len(data['events']) == 2
            assert data['events'][0]['title'] == 'Test Event 1'
        
        finally:
            output_file.unlink(missing_ok=True)
    
    def test_exporter_factory(self):
        """Test exporter factory."""
        exporter = ExporterFactory.create_exporter('csv', self.test_events)
        assert isinstance(exporter, CSVExporter)
        
        exporter = ExporterFactory.create_exporter('json', self.test_events)
        assert isinstance(exporter, JSONExporter)
        
        exporter = ExporterFactory.create_exporter('yaml', self.test_events)
        assert isinstance(exporter, YAMLExporter)
        
        with pytest.raises(ValueError):
            ExporterFactory.create_exporter('invalid', self.test_events)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])