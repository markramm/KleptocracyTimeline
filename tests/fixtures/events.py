"""
Test fixtures for timeline events
"""

import pytest
from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def valid_event():
    """A complete, valid event with all required fields"""
    return {
        "id": "2024-01-01--test-event-corruption-scandal",
        "date": "2024-01-01",
        "title": "Major Corruption Scandal Exposed in Test Case",
        "summary": "A comprehensive investigation revealed widespread corruption involving multiple government officials and corporate executives in a complex scheme that diverted public funds.",
        "status": "confirmed",
        "importance": 8,
        "actors": [
            "John Doe (Former Minister)",
            "Jane Smith (CEO of ACME Corp)",
            "Department of Justice",
            "Securities and Exchange Commission"
        ],
        "sources": [
            {
                "title": "Corruption Scandal Rocks Government",
                "url": "https://reuters.com/article/corruption-2024",
                "date": "2024-01-01",
                "outlet": "Reuters"
            },
            {
                "title": "DOJ Announces Major Indictments",
                "url": "https://justice.gov/press/2024/corruption-case",
                "date": "2024-01-02",
                "outlet": "Department of Justice"
            },
            {
                "title": "SEC Files Charges Against ACME Corp",
                "url": "https://sec.gov/litigation/2024/acme-charges",
                "date": "2024-01-03",
                "outlet": "SEC"
            }
        ],
        "tags": [
            "corruption",
            "government-fraud",
            "corporate-crime",
            "investigation",
            "indictment"
        ]
    }


@pytest.fixture
def minimal_event():
    """Event with only required fields"""
    return {
        "date": "2024-01-15",
        "title": "Minimal Test Event",
        "summary": "This is a minimal event with just the required fields for testing validation.",
        "actors": ["Actor One", "Actor Two"],
        "sources": [
            {"title": "Source", "url": "https://example.com"},
            {"title": "Source 2", "url": "https://example.org"}
        ],
        "tags": ["test", "minimal", "validation"]
    }


@pytest.fixture
def invalid_event():
    """Event with multiple validation errors"""
    return {
        "date": "01/15/2024",  # Wrong format
        "title": "Short",  # Too short
        "summary": "Too short",  # Too short
        "status": "unknown",  # Invalid status
        "importance": 15,  # Out of range
        "actors": ["Only One"],  # Too few
        "sources": ["https://example.com"],  # Legacy format
        "tags": ["tag with spaces"]  # Should use hyphens
    }


@pytest.fixture
def event_missing_fields():
    """Event missing several required fields"""
    return {
        "date": "2024-01-20",
        "title": "Event Missing Required Fields"
        # Missing: summary, actors, sources, tags
    }


@pytest.fixture
def events_batch():
    """Multiple events for batch testing"""
    return [
        {
            "id": f"2024-01-{i:02d}--test-event-{i}",
            "date": f"2024-01-{i:02d}",
            "title": f"Test Event {i}",
            "summary": f"This is test event number {i} with a detailed summary that meets minimum length requirements.",
            "actors": [f"Actor {i}", f"Organization {i}"],
            "sources": [
                {"title": f"Source {i}", "url": f"https://example.com/{i}"},
                {"title": f"Source {i}b", "url": f"https://example.org/{i}"}
            ],
            "tags": [f"tag-{i}", "test", "batch"]
        }
        for i in range(1, 11)
    ]


@pytest.fixture
def future_event():
    """Event with future date (for testing predictions)"""
    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    return {
        "date": future_date,
        "title": "Predicted Future Event",
        "summary": "This event is predicted to occur in the future based on current trends and analysis.",
        "status": "predicted",
        "actors": ["Future Actor", "Predicted Organization"],
        "sources": [
            {"title": "Analysis Report", "url": "https://example.com/analysis"},
            {"title": "Trend Forecast", "url": "https://example.com/forecast"}
        ],
        "tags": ["prediction", "future", "analysis"]
    }


@pytest.fixture
def disputed_event():
    """Event with disputed status"""
    return {
        "date": "2023-06-15",
        "title": "Disputed Allegations of Misconduct",
        "summary": "Allegations of misconduct have been made but are strongly disputed by the parties involved, with conflicting evidence presented.",
        "status": "disputed",
        "importance": 6,
        "actors": [
            "Accused Party",
            "Accusing Party",
            "Investigation Committee"
        ],
        "sources": [
            {
                "title": "Initial Allegations Report",
                "url": "https://news.com/allegations",
                "date": "2023-06-15",
                "outlet": "News Outlet"
            },
            {
                "title": "Denial Statement",
                "url": "https://accused.com/statement",
                "date": "2023-06-16",
                "outlet": "Accused Party PR"
            }
        ],
        "tags": ["disputed", "allegations", "investigation-pending"]
    }


class EventFactory:
    """Factory for creating test events with specific characteristics"""
    
    @staticmethod
    def create_with_validation_score(target_score: float) -> dict:
        """Create an event with approximately the target validation score"""
        event = {
            "date": "2024-01-01",
            "title": "Test Event for Score Testing"
        }
        
        if target_score > 0.2:
            event["summary"] = "A" * 60  # Minimal valid summary
        
        if target_score > 0.4:
            event["status"] = "confirmed"
            event["importance"] = 5
        
        if target_score > 0.6:
            event["actors"] = ["Actor 1", "Actor 2"]
            event["tags"] = ["tag-1", "tag-2", "tag-3"]
        
        if target_score > 0.8:
            event["sources"] = [
                {"title": "Source 1", "url": "https://example.com/1"},
                {"title": "Source 2", "url": "https://example.com/2"}
            ]
            event["summary"] = "A" * 120  # Longer summary
        
        if target_score > 0.9:
            event["actors"].append("Actor 3")
            event["sources"].append(
                {"title": "Source 3", "url": "https://example.com/3"}
            )
        
        return event
    
    @staticmethod
    def create_batch(count: int, start_date: str = "2024-01-01") -> list:
        """Create a batch of valid events"""
        events = []
        base_date = datetime.strptime(start_date, "%Y-%m-%d")
        
        for i in range(count):
            event_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            events.append({
                "id": f"{event_date}--batch-event-{i}",
                "date": event_date,
                "title": f"Batch Event {i}: Significant Development",
                "summary": f"Event {i} represents a significant development in the ongoing investigation. " * 3,
                "status": "confirmed" if i % 2 == 0 else "reported",
                "importance": min(10, 5 + (i % 6)),
                "actors": [f"Actor {i}A", f"Actor {i}B", f"Organization {i}"],
                "sources": [
                    {
                        "title": f"Report on Event {i}",
                        "url": f"https://source1.com/event-{i}",
                        "date": event_date,
                        "outlet": "Source One"
                    },
                    {
                        "title": f"Analysis of Event {i}",
                        "url": f"https://source2.com/event-{i}",
                        "date": event_date,
                        "outlet": "Source Two"
                    }
                ],
                "tags": ["batch-test", f"category-{i % 3}", "investigation"]
            })
        
        return events


@pytest.fixture
def event_factory():
    """Provide the EventFactory class to tests"""
    return EventFactory