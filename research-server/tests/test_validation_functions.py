"""
Unit tests for pure validation functions
"""

import pytest
from datetime import datetime
import sys
import os

# Add server directory to path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

from validation_functions import (
    validate_date_format,
    validate_title,
    validate_summary,
    validate_status,
    validate_actors,
    validate_single_source,
    validate_sources,
    validate_tags,
    validate_importance,
    calculate_validation_score,
    validate_required_fields,
    suggest_fixes,
    VALID_STATUSES
)


class TestDateValidation:
    """Test date validation functions"""
    
    def test_valid_date_format(self):
        """Test valid date formats"""
        is_valid, error = validate_date_format("2024-01-01")
        assert is_valid is True
        assert error is None
    
    def test_invalid_date_format(self):
        """Test invalid date formats"""
        is_valid, error = validate_date_format("01/01/2024")
        assert is_valid is False
        assert "Invalid date format" in error
    
    def test_empty_date(self):
        """Test empty date string"""
        is_valid, error = validate_date_format("")
        assert is_valid is False
        assert "Date is empty" in error
    
    def test_invalid_date_value(self):
        """Test invalid date values like Feb 31"""
        is_valid, error = validate_date_format("2024-02-31")
        assert is_valid is False
        assert "Invalid date value" in error


class TestTitleValidation:
    """Test title validation"""
    
    def test_valid_title(self):
        """Test valid title"""
        is_valid, errors = validate_title("This is a valid title for an event")
        assert is_valid is True
        assert len(errors) == 0
    
    def test_title_too_short(self):
        """Test title that's too short"""
        is_valid, errors = validate_title("Short")
        assert is_valid is False
        assert "at least 10 characters" in errors[0]
    
    def test_title_too_long(self):
        """Test title that's too long"""
        long_title = "x" * 201
        is_valid, errors = validate_title(long_title)
        assert is_valid is False
        assert "less than 200 characters" in errors[0]
    
    def test_empty_title(self):
        """Test empty title"""
        is_valid, errors = validate_title("")
        assert is_valid is False
        assert len(errors) > 0


class TestSummaryValidation:
    """Test summary validation"""
    
    def test_valid_summary(self):
        """Test valid summary"""
        summary = "This is a detailed summary that provides comprehensive information about the event and its context."
        is_valid, errors = validate_summary(summary)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_summary_too_short(self):
        """Test summary that's too short"""
        is_valid, errors = validate_summary("Too short")
        assert is_valid is False
        assert "at least 50 characters" in errors[0]


class TestStatusValidation:
    """Test status validation"""
    
    def test_valid_statuses(self):
        """Test all valid status values"""
        for status in VALID_STATUSES:
            is_valid, error = validate_status(status)
            assert is_valid is True
            assert error is None
    
    def test_invalid_status(self):
        """Test invalid status"""
        is_valid, error = validate_status("invalid")
        assert is_valid is False
        assert "Invalid status" in error
        assert "must be one of" in error


class TestActorsValidation:
    """Test actors validation"""
    
    def test_valid_actors(self):
        """Test valid actors list"""
        actors = ["John Doe", "Jane Smith", "ACME Corporation"]
        is_valid, errors = validate_actors(actors)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_actors_not_list(self):
        """Test actors that's not a list"""
        is_valid, errors = validate_actors("single actor string")
        assert is_valid is False
        assert "must be a list" in errors[0]
    
    def test_empty_actors(self):
        """Test empty actors list"""
        is_valid, errors = validate_actors([])
        assert is_valid is False
        assert "cannot be empty" in errors[0]
    
    def test_too_few_actors(self):
        """Test too few actors"""
        is_valid, errors = validate_actors(["Only One"])
        assert is_valid is False
        assert "At least 2 actors" in errors[0]
    
    def test_invalid_actor_type(self):
        """Test non-string actor"""
        is_valid, errors = validate_actors(["Valid", 123, "Another"])
        assert is_valid is False
        assert "must be a string" in errors[0]


class TestSourceValidation:
    """Test source validation"""
    
    def test_valid_source(self):
        """Test valid source object"""
        source = {
            "title": "Article Title",
            "url": "https://example.com/article",
            "date": "2024-01-01",
            "outlet": "Example News"
        }
        errors = validate_single_source(source, 1)
        assert len(errors) == 0
    
    def test_legacy_source_format(self):
        """Test deprecated URL-only format"""
        errors = validate_single_source("https://example.com", 1)
        assert len(errors) == 1
        assert "deprecated format" in errors[0]
    
    def test_source_missing_title(self):
        """Test source missing title"""
        source = {
            "url": "https://example.com",
            "date": "2024-01-01",
            "outlet": "Example News"
        }
        errors = validate_single_source(source, 1)
        assert any("missing required field: title" in e for e in errors)
    
    def test_source_invalid_url(self):
        """Test source with invalid URL"""
        source = {
            "title": "Article",
            "url": "not-a-url",
            "date": "2024-01-01",
            "outlet": "News"
        }
        errors = validate_single_source(source, 1)
        assert any("must start with http" in e for e in errors)
    
    def test_sources_list_validation(self):
        """Test sources list validation"""
        sources = [
            {
                "title": "Article 1",
                "url": "https://example.com/1",
                "date": "2024-01-01",
                "outlet": "News 1"
            },
            {
                "title": "Article 2",
                "url": "https://example.com/2",
                "date": "2024-01-02",
                "outlet": "News 2"
            }
        ]
        is_valid, errors = validate_sources(sources)
        assert is_valid is True
        assert len(errors) == 0


class TestTagsValidation:
    """Test tags validation"""
    
    def test_valid_tags(self):
        """Test valid tags"""
        tags = ["political-corruption", "financial-crime", "investigation"]
        is_valid, errors = validate_tags(tags)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_tags_with_spaces(self):
        """Test tags with spaces instead of hyphens"""
        tags = ["political corruption", "financial-crime", "investigation"]
        is_valid, errors = validate_tags(tags)
        assert is_valid is False
        assert any("should use hyphens" in e for e in errors)
    
    def test_too_few_tags(self):
        """Test too few tags"""
        tags = ["only-one"]
        is_valid, errors = validate_tags(tags)
        assert is_valid is False
        assert "At least 3 tags" in errors[0]


class TestImportanceValidation:
    """Test importance validation"""
    
    def test_valid_importance(self):
        """Test valid importance values"""
        for importance in range(1, 11):
            is_valid, errors = validate_importance(importance)
            assert is_valid is True
            assert len(errors) == 0
    
    def test_importance_too_low(self):
        """Test importance below minimum"""
        is_valid, errors = validate_importance(0)
        assert is_valid is False
        assert "between 1 and 10" in errors[0]
    
    def test_importance_too_high(self):
        """Test importance above maximum"""
        is_valid, errors = validate_importance(11)
        assert is_valid is False
        assert "between 1 and 10" in errors[0]
    
    def test_importance_not_integer(self):
        """Test non-integer importance"""
        is_valid, errors = validate_importance("5")
        assert is_valid is False
        assert "must be an integer" in errors[0]


class TestValidationScore:
    """Test validation score calculation"""
    
    def test_perfect_score(self):
        """Test event with perfect validation score"""
        event = {
            "date": "2024-01-01",
            "title": "Valid Event Title",
            "summary": "A comprehensive summary that provides detailed information about the event",
            "status": "confirmed",
            "importance": 8,
            "actors": ["Actor 1", "Actor 2", "Actor 3"],
            "sources": [
                {"title": "Source 1", "url": "https://example.com/1"},
                {"title": "Source 2", "url": "https://example.com/2"},
                {"title": "Source 3", "url": "https://example.com/3"}
            ],
            "tags": ["tag-1", "tag-2", "tag-3"]
        }
        score = calculate_validation_score(event, [])
        assert score > 0.9
    
    def test_minimal_score(self):
        """Test event with minimal fields"""
        event = {
            "date": "2024-01-01",
            "title": "Minimal Event"
        }
        score = calculate_validation_score(event, ["Missing summary", "Missing actors"])
        assert score < 0.5
    
    def test_score_with_errors(self):
        """Test that errors reduce the score"""
        event = {
            "date": "2024-01-01",
            "title": "Event with Errors",
            "summary": "Summary text",
            "actors": ["Actor 1"],
            "sources": [],
            "tags": []
        }
        score_no_errors = calculate_validation_score(event, [])
        score_with_errors = calculate_validation_score(event, ["Error 1", "Error 2", "Error 3"])
        assert score_with_errors < score_no_errors


class TestRequiredFields:
    """Test required fields validation"""
    
    def test_all_required_fields_present(self):
        """Test event with all required fields"""
        event = {
            "date": "2024-01-01",
            "title": "Title",
            "summary": "Summary",
            "actors": ["Actor"],
            "sources": [{"url": "http://example.com"}],
            "tags": ["tag"]
        }
        all_present, missing = validate_required_fields(event)
        assert all_present is True
        assert len(missing) == 0
    
    def test_missing_required_fields(self):
        """Test event missing required fields"""
        event = {
            "date": "2024-01-01",
            "title": "Title"
        }
        all_present, missing = validate_required_fields(event)
        assert all_present is False
        assert "summary" in missing
        assert "actors" in missing
        assert "sources" in missing
        assert "tags" in missing


class TestSuggestFixes:
    """Test fix suggestions"""
    
    def test_suggest_missing_field_fixes(self):
        """Test suggestions for missing fields"""
        errors = ["Missing required field: actors", "Missing required field: sources"]
        suggestions = suggest_fixes({}, errors)
        assert len(suggestions['requires_research']) == 2
        assert any("Research and add actors" in s for s in suggestions['requires_research'])
    
    def test_suggest_format_fixes(self):
        """Test suggestions for format errors"""
        errors = ["Source 1 using deprecated format - must be object"]
        suggestions = suggest_fixes({}, errors)
        assert len(suggestions['format_fixes']) == 1
        assert "Convert source URLs" in suggestions['format_fixes'][0]
    
    def test_suggest_tag_fixes(self):
        """Test suggestions for tag errors"""
        errors = ["Tag 1 should use hyphens instead of spaces"]
        suggestions = suggest_fixes({}, errors)
        assert len(suggestions['fixable_errors']) == 1
        assert "Replace spaces with hyphens" in suggestions['fixable_errors'][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])