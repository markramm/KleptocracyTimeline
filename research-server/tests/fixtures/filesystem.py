"""
Test fixtures for filesystem operations
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, List, Any


@pytest.fixture
def temp_dir():
    """Create a temporary directory that's cleaned up after tests"""
    temp_path = tempfile.mkdtemp(prefix="test_timeline_")
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_timeline_structure(temp_dir):
    """Create a mock timeline directory structure"""
    # Create directory structure
    events_dir = temp_dir / "timeline_data" / "events"
    events_dir.mkdir(parents=True)
    
    reports_dir = temp_dir / "timeline_data" / "reports"
    reports_dir.mkdir(parents=True)
    
    api_dir = temp_dir / "api"
    api_dir.mkdir(parents=True)
    
    # Create some sample event files
    sample_events = [
        {
            "id": "2024-01-01--sample-event-1",
            "date": "2024-01-01",
            "title": "Sample Event 1",
            "summary": "This is a sample event for testing filesystem operations and validation.",
            "actors": ["Actor 1", "Actor 2"],
            "sources": [
                {"title": "Source 1", "url": "https://example.com/1"},
                {"title": "Source 2", "url": "https://example.com/2"}
            ],
            "tags": ["test", "sample", "filesystem"]
        },
        {
            "id": "2024-01-02--sample-event-2",
            "date": "2024-01-02",
            "title": "Sample Event 2",
            "summary": "Another sample event with different characteristics for testing purposes.",
            "actors": ["Actor 3", "Actor 4"],
            "sources": [
                {"title": "Source 3", "url": "https://example.com/3"},
                {"title": "Source 4", "url": "https://example.com/4"}
            ],
            "tags": ["test", "sample", "validation"]
        }
    ]
    
    for event in sample_events:
        event_file = events_dir / f"{event['id']}.json"
        with open(event_file, 'w') as f:
            json.dump(event, f, indent=2)
    
    return {
        "root": temp_dir,
        "events_dir": events_dir,
        "reports_dir": reports_dir,
        "api_dir": api_dir,
        "event_files": list(events_dir.glob("*.json"))
    }


@pytest.fixture
def mock_database_file(temp_dir):
    """Create a mock SQLite database file"""
    db_path = temp_dir / "test_research.db"
    # Touch the file to create it
    db_path.touch()
    return db_path


class FilesystemHelper:
    """Helper class for filesystem operations in tests"""
    
    @staticmethod
    def create_event_file(directory: Path, event: Dict[str, Any]) -> Path:
        """Create an event JSON file"""
        event_id = event.get('id', 'test-event')
        file_path = directory / f"{event_id}.json"
        with open(file_path, 'w') as f:
            json.dump(event, f, indent=2)
        return file_path
    
    @staticmethod
    def create_events_batch(directory: Path, events: List[Dict[str, Any]]) -> List[Path]:
        """Create multiple event files"""
        paths = []
        for event in events:
            path = FilesystemHelper.create_event_file(directory, event)
            paths.append(path)
        return paths
    
    @staticmethod
    def read_event_file(file_path: Path) -> Dict[str, Any]:
        """Read an event JSON file"""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def count_files_with_pattern(directory: Path, pattern: str) -> int:
        """Count files matching a pattern"""
        return len(list(directory.glob(pattern)))
    
    @staticmethod
    def create_config_file(directory: Path, config: Dict[str, Any]) -> Path:
        """Create a configuration file"""
        config_path = directory / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return config_path


@pytest.fixture
def filesystem_helper():
    """Provide the FilesystemHelper to tests"""
    return FilesystemHelper


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock configuration"""
    config = {
        "database_url": "sqlite:///test.db",
        "api_port": 5558,
        "debug": True,
        "validation": {
            "min_score": 0.7,
            "required_sources": 2,
            "required_actors": 2
        }
    }
    config_path = temp_dir / "config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    return config_path, config


@pytest.fixture
def mock_validation_report(temp_dir):
    """Create a mock validation report"""
    report = {
        "validation_timestamp": "2024-01-01T00:00:00",
        "events_validated": 100,
        "events_passed": 85,
        "events_failed": 15,
        "average_score": 0.82,
        "common_errors": [
            "Missing sources",
            "Invalid date format",
            "Actors too few"
        ]
    }
    report_path = temp_dir / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    return report_path, report


@pytest.fixture
def cleanup_files():
    """Fixture to track and cleanup files created during tests"""
    files_to_cleanup = []
    
    def add_file(path):
        files_to_cleanup.append(path)
    
    yield add_file
    
    # Cleanup
    for path in files_to_cleanup:
        if isinstance(path, Path):
            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)