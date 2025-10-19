"""
Shared pytest fixtures for all test modules.

Provides common test infrastructure including:
- Database fixtures with proper table creation
- Temporary directory fixtures
- Sample event data fixtures
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Add server to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))


@pytest.fixture
def test_db():
    """Create in-memory test database with all tables and FTS."""
    from models import Base

    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    # Initialize FTS tables
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create FTS virtual table
    session.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS events_fts
        USING fts5(id, title, summary, content='timeline_events', content_rowid='rowid')
    """)

    session.commit()
    session.close()

    yield engine

    engine.dispose()


@pytest.fixture
def test_session(test_db):
    """Create a test database session."""
    Session = sessionmaker(bind=test_db)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def test_events_dir(tmp_path):
    """Create temporary events directory with correct structure."""
    events_dir = tmp_path / 'timeline' / 'data' / 'events'
    events_dir.mkdir(parents=True)

    yield events_dir

    # Cleanup handled by tmp_path


@pytest.fixture
def test_priorities_dir(tmp_path):
    """Create temporary priorities directory."""
    priorities_dir = tmp_path / 'research_priorities'
    priorities_dir.mkdir(parents=True)

    yield priorities_dir

    # Cleanup handled by tmp_path


@pytest.fixture
def sample_event_markdown():
    """Sample markdown event for testing."""
    return """---
id: 2025-01-15--test-event
date: 2025-01-15
title: Test Event
importance: 8
status: confirmed
tags:
  - test
  - sample
actors:
  - Test Actor
sources:
  - url: https://example.com/article
    title: Test Article
    publisher: Test Publisher
    date: 2025-01-15
    tier: 1
---

This is a test event summary for testing purposes.

## Background

This event was created for testing the timeline system.

## Significance

Used to verify markdown parsing and event validation.
"""


@pytest.fixture
def sample_event_json():
    """Sample JSON event for testing (legacy support)."""
    return {
        "id": "2025-01-15--test-event-json",
        "date": "2025-01-15",
        "title": "Test JSON Event",
        "summary": "Test event in JSON format",
        "importance": 7,
        "status": "confirmed",
        "tags": ["test", "json"],
        "actors": ["Test Actor JSON"],
        "sources": [
            {
                "url": "https://example.com/test",
                "title": "Test Source",
                "publisher": "Test Pub",
                "date": "2025-01-15",
                "tier": 1
            }
        ]
    }


@pytest.fixture
def sample_priority():
    """Sample research priority for testing."""
    return {
        "id": "RP-TEST-001",
        "title": "Test Research Priority",
        "description": "A test priority for automated testing",
        "priority": 8,
        "status": "pending",
        "estimated_events": 5,
        "category": "test",
        "tags": ["test", "automated"],
        "time_period": "2025-01",
        "research_notes": "This is a test priority",
        "estimated_importance": 7
    }


@pytest.fixture
def populated_test_db(test_db):
    """Test database with sample events and priorities."""
    from models import TimelineEvent, ResearchPriority, init_database

    Session = sessionmaker(bind=test_db)
    session = Session()

    # Add sample events
    event1 = TimelineEvent(
        id="2025-01-01--test-event-1",
        json_content='{"date": "2025-01-01", "title": "Event 1"}',
        date="2025-01-01",
        title="Test Event 1",
        summary="First test event",
        importance=7,
        status="confirmed",
        file_path="/tmp/event1.md",
        file_hash="hash1"
    )

    event2 = TimelineEvent(
        id="2025-01-02--test-event-2",
        json_content='{"date": "2025-01-02", "title": "Event 2"}',
        date="2025-01-02",
        title="Test Event 2",
        summary="Second test event",
        importance=8,
        status="confirmed",
        file_path="/tmp/event2.md",
        file_hash="hash2"
    )

    session.add(event1)
    session.add(event2)

    # Add sample priority
    priority = ResearchPriority(
        id="RP-TEST-001",
        title="Test Priority",
        description="Test research priority",
        priority=8,
        status="pending",
        estimated_events=5,
        category="test"
    )

    session.add(priority)
    session.commit()
    session.close()

    yield test_db


@pytest.fixture
def mock_git_repo(tmp_path):
    """Create a mock git repository for testing."""
    repo_dir = tmp_path / 'mock-repo'
    repo_dir.mkdir()

    # Create basic git structure (for mocking, not a real repo)
    git_dir = repo_dir / '.git'
    git_dir.mkdir()

    events_dir = repo_dir / 'timeline' / 'data' / 'events'
    events_dir.mkdir(parents=True)

    yield repo_dir

    # Cleanup handled by tmp_path


@pytest.fixture
def app_client(test_db, monkeypatch, tmp_path):
    """Flask test client with test database."""
    import os

    # Set test environment
    monkeypatch.setenv('RESEARCH_MONITOR_API_KEY', 'test-key')
    monkeypatch.setenv('RESEARCH_DB_PATH', ':memory:')
    monkeypatch.setenv('COMMIT_THRESHOLD', '3')

    # Create test directories
    events_dir = tmp_path / 'timeline' / 'data' / 'events'
    events_dir.mkdir(parents=True)

    priorities_dir = tmp_path / 'research_priorities'
    priorities_dir.mkdir(parents=True)

    from app_v2 import app

    app.config['TESTING'] = True
    app.config['DATABASE'] = test_db

    with app.test_client() as client:
        yield client
