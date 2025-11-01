#!/usr/bin/env python3
"""
Unit tests for MarkdownEventParser.

Tests YAML frontmatter parsing, content mapping, date conversion, and error handling.
"""

import pytest
import sys
from pathlib import Path
from datetime import date

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

from parsers.markdown_parser import MarkdownEventParser


class TestMarkdownParserBasics:
    """Test basic markdown parser functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkdownEventParser()
        self.test_dir = Path(__file__).parent / 'fixtures'
        self.test_dir.mkdir(exist_ok=True)

    def test_can_parse_md_files(self):
        """Test that parser recognizes .md files."""
        assert self.parser.can_parse(Path('test.md'))
        assert self.parser.can_parse(Path('event.MD'))
        assert not self.parser.can_parse(Path('test.json'))
        assert not self.parser.can_parse(Path('test.yaml'))

    def test_parse_minimal_event(self, tmp_path):
        """Test parsing minimal valid markdown event."""
        event_file = tmp_path / 'minimal.md'
        event_file.write_text("""---
id: 2025-01-15--test-event
date: 2025-01-15
title: Test Event
---

This is the summary content.
""")

        data = self.parser.parse(event_file)

        assert data['id'] == '2025-01-15--test-event'
        assert data['date'] == '2025-01-15'
        assert data['title'] == 'Test Event'
        assert data['summary'] == 'This is the summary content.'

    def test_parse_complete_event(self, tmp_path):
        """Test parsing complete markdown event with all fields."""
        event_file = tmp_path / 'complete.md'
        event_file.write_text("""---
id: 2025-01-15--complete-event
date: 2025-01-15
title: Complete Test Event
importance: 8
tags:
  - test
  - corruption
actors:
  - Test Actor
sources:
  - url: https://example.com
    title: Example Source
    publisher: Example
    tier: 1
status: confirmed
---

This is a complete event with multiple paragraphs.

It demonstrates:
- YAML frontmatter
- Markdown content
- Multiple fields
""")

        data = self.parser.parse(event_file)

        assert data['id'] == '2025-01-15--complete-event'
        assert data['date'] == '2025-01-15'
        assert data['importance'] == 8
        assert 'test' in data['tags']
        assert 'corruption' in data['tags']
        assert 'Test Actor' in data['actors']
        assert len(data['sources']) == 1
        assert data['sources'][0]['url'] == 'https://example.com'
        assert data['status'] == 'confirmed'

    def test_date_conversion(self, tmp_path):
        """Test that YAML date objects are converted to ISO strings."""
        event_file = tmp_path / 'date_test.md'
        event_file.write_text("""---
id: 2025-01-15--date-test
date: 2025-01-15
title: Date Test
sources:
  - url: https://example.com
    title: Test
    date: 2025-01-15
---

Test content.
""")

        data = self.parser.parse(event_file)

        # Both date and source date should be strings, not date objects
        assert isinstance(data['date'], str)
        assert data['date'] == '2025-01-15'
        assert isinstance(data['sources'][0]['date'], str)
        assert data['sources'][0]['date'] == '2025-01-15'

    def test_summary_from_content(self, tmp_path):
        """Test that markdown content is mapped to summary field."""
        event_file = tmp_path / 'content_test.md'
        event_file.write_text("""---
id: 2025-01-15--content-test
date: 2025-01-15
title: Content Test
---

This should become the summary.
""")

        data = self.parser.parse(event_file)

        assert data['summary'] == 'This should become the summary.'

    def test_summary_in_frontmatter_overrides_content(self, tmp_path):
        """Test that explicit summary in frontmatter takes precedence."""
        event_file = tmp_path / 'explicit_summary.md'
        event_file.write_text("""---
id: 2025-01-15--explicit-summary
date: 2025-01-15
title: Explicit Summary Test
summary: This is the explicit summary.
---

This content should be ignored.
""")

        data = self.parser.parse(event_file)

        assert data['summary'] == 'This is the explicit summary.'

    def test_missing_id_uses_filename(self, tmp_path):
        """Test that missing id field is auto-generated from filename."""
        event_file = tmp_path / '2025-01-15--no-id-event.md'
        event_file.write_text("""---
date: 2025-01-15
title: No ID Event
---

Content.
""")

        data = self.parser.parse(event_file)

        # ID should be auto-generated from filename
        assert data['id'] == '2025-01-15--no-id-event'

    def test_missing_date_raises_error(self, tmp_path):
        """Test that missing date field raises ValueError."""
        event_file = tmp_path / 'no_date.md'
        event_file.write_text("""---
id: 2025-01-15--no-date
title: No Date Event
---

Content.
""")

        with pytest.raises(ValueError, match="Missing required fields.*date"):
            self.parser.parse(event_file)

    def test_missing_title_raises_error(self, tmp_path):
        """Test that missing title field raises ValueError."""
        event_file = tmp_path / 'no_title.md'
        event_file.write_text("""---
id: 2025-01-15--no-title
date: 2025-01-15
---

Content.
""")

        with pytest.raises(ValueError, match="Missing required fields.*title"):
            self.parser.parse(event_file)

    def test_invalid_yaml_raises_error(self, tmp_path):
        """Test that invalid YAML frontmatter raises ValueError."""
        event_file = tmp_path / 'invalid_yaml.md'
        event_file.write_text("""---
id: 2025-01-15--invalid
date: [2025-01-15
title: Invalid YAML
---

Content.
""")

        with pytest.raises(ValueError, match="Invalid YAML"):
            self.parser.parse(event_file)

    def test_file_not_found_raises_error(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse(Path('/nonexistent/file.md'))


class TestMarkdownParserValidation:
    """Test markdown parser validation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkdownEventParser()

    def test_validate_valid_file(self, tmp_path):
        """Test validation of valid markdown file."""
        event_file = tmp_path / 'valid.md'
        event_file.write_text("""---
id: 2025-01-15--valid
date: 2025-01-15
title: Valid Event
---

Content.
""")

        errors = self.parser.validate_format(event_file)
        assert len(errors) == 0

    def test_validate_missing_fields(self, tmp_path):
        """Test validation catches missing required fields."""
        event_file = tmp_path / 'missing_fields.md'
        event_file.write_text("""---
title: Only Title
---

Content.
""")

        errors = self.parser.validate_format(event_file)
        assert len(errors) > 0
        assert any('id' in error for error in errors)
        assert any('date' in error for error in errors)

    def test_validate_wrong_types(self, tmp_path):
        """Test validation catches wrong field types."""
        event_file = tmp_path / 'wrong_types.md'
        event_file.write_text("""---
id: 123
date: 2025-01-15
title: ['Wrong', 'Type']
importance: "not a number"
---

Content.
""")

        errors = self.parser.validate_format(event_file)
        assert len(errors) > 0
        assert any('id' in error and 'string' in error for error in errors)
        assert any('importance' in error and 'number' in error for error in errors)

    def test_validate_no_content_or_summary(self, tmp_path):
        """Test validation catches missing content/summary."""
        event_file = tmp_path / 'no_content.md'
        event_file.write_text("""---
id: 2025-01-15--no-content
date: 2025-01-15
title: No Content
---

""")

        errors = self.parser.validate_format(event_file)
        assert len(errors) > 0
        assert any('content' in error or 'summary' in error for error in errors)

    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        errors = self.parser.validate_format(Path('/nonexistent/file.md'))
        assert len(errors) > 0
        assert any('not found' in error.lower() for error in errors)


class TestMarkdownParserEdgeCases:
    """Test edge cases and special scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkdownEventParser()

    def test_empty_frontmatter(self, tmp_path):
        """Test handling of empty frontmatter."""
        event_file = tmp_path / 'empty_frontmatter.md'
        event_file.write_text("""---
---

Content.
""")

        with pytest.raises(ValueError, match="Missing required fields"):
            self.parser.parse(event_file)

    def test_no_frontmatter(self, tmp_path):
        """Test handling of file with no frontmatter."""
        event_file = tmp_path / 'no_frontmatter.md'
        event_file.write_text("Just plain markdown content.")

        with pytest.raises(ValueError):
            self.parser.parse(event_file)

    def test_multiline_summary(self, tmp_path):
        """Test handling of multiline markdown content."""
        event_file = tmp_path / 'multiline.md'
        event_file.write_text("""---
id: 2025-01-15--multiline
date: 2025-01-15
title: Multiline Test
---

This is paragraph one.

This is paragraph two.

- Bullet point 1
- Bullet point 2
""")

        data = self.parser.parse(event_file)
        assert 'paragraph one' in data['summary']
        assert 'paragraph two' in data['summary']
        assert 'Bullet point' in data['summary']

    def test_special_characters_in_content(self, tmp_path):
        """Test handling of special characters in markdown."""
        event_file = tmp_path / 'special_chars.md'
        event_file.write_text("""---
id: 2025-01-15--special
date: 2025-01-15
title: Special Characters Test
---

Testing special characters: &, <, >, ", ', *, _, #
""")

        data = self.parser.parse(event_file)
        assert '&' in data['summary']
        assert '<' in data['summary']

    def test_unicode_content(self, tmp_path):
        """Test handling of Unicode content."""
        event_file = tmp_path / 'unicode.md'
        event_file.write_text("""---
id: 2025-01-15--unicode
date: 2025-01-15
title: Unicode Test 中文
---

Testing Unicode: 日本語, العربية, Ελληνικά
""", encoding='utf-8')

        data = self.parser.parse(event_file)
        assert '中文' in data['title']
        assert '日本語' in data['summary']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
