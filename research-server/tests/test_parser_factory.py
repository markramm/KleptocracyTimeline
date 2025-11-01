#!/usr/bin/env python3
"""
Unit tests for EventParserFactory.

Tests parser selection, format dispatch, and error handling.
"""

import pytest
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

from parsers.factory import EventParserFactory
from parsers.json_parser import JsonEventParser
from parsers.markdown_parser import MarkdownEventParser


class TestParserFactorySelection:
    """Test parser factory selection logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = EventParserFactory()

    def test_get_parser_for_json(self):
        """Test factory returns JsonEventParser for .json files."""
        parser = self.factory.get_parser(Path('test.json'))
        assert isinstance(parser, JsonEventParser)

    def test_get_parser_for_markdown(self):
        """Test factory returns MarkdownEventParser for .md files."""
        parser = self.factory.get_parser(Path('test.md'))
        assert isinstance(parser, MarkdownEventParser)

    def test_get_parser_for_uppercase_extensions(self):
        """Test factory handles uppercase file extensions."""
        assert isinstance(self.factory.get_parser(Path('test.JSON')), JsonEventParser)
        assert isinstance(self.factory.get_parser(Path('test.MD')), MarkdownEventParser)

    def test_get_parser_for_unsupported_format(self):
        """Test factory returns None for unsupported formats."""
        assert self.factory.get_parser(Path('test.yaml')) is None
        assert self.factory.get_parser(Path('test.txt')) is None
        assert self.factory.get_parser(Path('test.xml')) is None


class TestParserFactoryParsing:
    """Test parser factory parsing methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = EventParserFactory()

    def test_parse_json_event(self, tmp_path):
        """Test parsing JSON event through factory."""
        event_file = tmp_path / 'test.json'
        event_file.write_text("""{
  "date": "2025-01-15",
  "title": "Test Event",
  "summary": "Test summary",
  "importance": 5
}""")

        data = self.factory.parse_event(event_file)
        assert data['date'] == '2025-01-15'
        assert data['title'] == 'Test Event'

    def test_parse_markdown_event(self, tmp_path):
        """Test parsing Markdown event through factory."""
        event_file = tmp_path / 'test.md'
        event_file.write_text("""---
id: 2025-01-15--test
date: 2025-01-15
title: Test Event
---

Test summary.
""")

        data = self.factory.parse_event(event_file)
        assert data['id'] == '2025-01-15--test'
        assert data['date'] == '2025-01-15'
        assert data['title'] == 'Test Event'

    def test_parse_unsupported_format_raises_error(self, tmp_path):
        """Test parsing unsupported format raises ValueError."""
        event_file = tmp_path / 'test.yaml'
        event_file.write_text("key: value")

        with pytest.raises(ValueError, match="Unsupported file format"):
            self.factory.parse_event(event_file)

    def test_parse_nonexistent_file_raises_error(self):
        """Test parsing non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            self.factory.parse_event(Path('/nonexistent/file.json'))

    def test_parse_invalid_json_raises_error(self, tmp_path):
        """Test parsing invalid JSON raises error."""
        event_file = tmp_path / 'invalid.json'
        event_file.write_text("{invalid json")

        with pytest.raises(ValueError):
            self.factory.parse_event(event_file)

    def test_parse_invalid_markdown_raises_error(self, tmp_path):
        """Test parsing invalid markdown raises error."""
        event_file = tmp_path / 'invalid.md'
        event_file.write_text("""---
date: 2025-01-15
---
No required fields.
""")

        with pytest.raises(ValueError):
            self.factory.parse_event(event_file)


class TestParserFactoryValidation:
    """Test parser factory validation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = EventParserFactory()

    def test_validate_json_format(self, tmp_path):
        """Test validation of JSON format."""
        event_file = tmp_path / 'valid.json'
        event_file.write_text("""{
  "date": "2025-01-15",
  "title": "Valid Event"
}""")

        errors = self.factory.validate_event_format(event_file)
        assert len(errors) == 0

    def test_validate_markdown_format(self, tmp_path):
        """Test validation of Markdown format."""
        event_file = tmp_path / 'valid.md'
        event_file.write_text("""---
id: 2025-01-15--valid
date: 2025-01-15
title: Valid Event
---

Content.
""")

        errors = self.factory.validate_event_format(event_file)
        assert len(errors) == 0

    def test_validate_unsupported_format(self, tmp_path):
        """Test validation of unsupported format returns error."""
        event_file = tmp_path / 'test.yaml'
        event_file.write_text("key: value")

        errors = self.factory.validate_event_format(event_file)
        assert len(errors) > 0
        assert any('Unsupported file format' in error for error in errors)

    def test_validate_invalid_json(self, tmp_path):
        """Test validation catches invalid JSON."""
        event_file = tmp_path / 'invalid.json'
        event_file.write_text("{invalid")

        errors = self.factory.validate_event_format(event_file)
        assert len(errors) > 0

    def test_validate_invalid_markdown(self, tmp_path):
        """Test validation catches invalid Markdown."""
        event_file = tmp_path / 'invalid.md'
        event_file.write_text("""---
title: Only Title
---

No required fields.
""")

        errors = self.factory.validate_event_format(event_file)
        assert len(errors) > 0


class TestParserFactoryIntegration:
    """Test parser factory with real-world scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = EventParserFactory()

    def test_parse_multiple_formats_same_directory(self, tmp_path):
        """Test parsing both JSON and Markdown from same directory."""
        # Create JSON event
        json_file = tmp_path / 'event1.json'
        json_file.write_text("""{
  "date": "2025-01-15",
  "title": "JSON Event"
}""")

        # Create Markdown event
        md_file = tmp_path / 'event2.md'
        md_file.write_text("""---
id: 2025-01-16--md-event
date: 2025-01-16
title: Markdown Event
---

Summary.
""")

        # Parse both
        json_data = self.factory.parse_event(json_file)
        md_data = self.factory.parse_event(md_file)

        assert json_data['title'] == 'JSON Event'
        assert md_data['title'] == 'Markdown Event'

    def test_consistent_output_format(self, tmp_path):
        """Test that both parsers return consistent data structure."""
        # Create JSON event
        json_file = tmp_path / 'event.json'
        json_file.write_text("""{
  "date": "2025-01-15",
  "title": "Test Event",
  "importance": 8,
  "tags": ["test", "example"]
}""")

        # Create equivalent Markdown event
        md_file = tmp_path / 'event.md'
        md_file.write_text("""---
id: 2025-01-15--test-event
date: 2025-01-15
title: Test Event
importance: 8
tags:
  - test
  - example
---

Summary.
""")

        json_data = self.factory.parse_event(json_file)
        md_data = self.factory.parse_event(md_file)

        # Both should have same keys for shared fields
        assert json_data['date'] == md_data['date']
        assert json_data['title'] == md_data['title']
        assert json_data['importance'] == md_data['importance']
        assert json_data['tags'] == md_data['tags']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
