"""
Markdown event parser for timeline events.

Handles parsing of Markdown-formatted event files with YAML frontmatter.
"""

import frontmatter
import yaml
from pathlib import Path
from typing import Dict, Any, List
from datetime import date, datetime

from parsers.base import EventParser


def convert_dates_to_strings(obj):
    """
    Recursively convert date/datetime objects to ISO format strings.
    YAML parser converts YYYY-MM-DD to date objects, but we need strings for JSON storage.
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_dates_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates_to_strings(item) for item in obj]
    else:
        return obj


class MarkdownEventParser(EventParser):
    """
    Parser for Markdown-formatted timeline events.

    Handles .md files with YAML frontmatter containing event metadata.
    The markdown body content is mapped to the 'summary' field.
    """

    def can_parse(self, file_path: Path) -> bool:
        """Check if this is a Markdown file."""
        return file_path.suffix.lower() == '.md'

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a Markdown event file with YAML frontmatter.

        Args:
            file_path: Path to the Markdown event file

        Returns:
            Dictionary containing event data

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If YAML frontmatter is invalid or required fields are missing
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Event file not found: {file_path}")

        try:
            # Parse frontmatter and content
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            # Extract metadata from frontmatter
            data = dict(post.metadata)

            # Map markdown content to summary field if not already present
            if post.content and post.content.strip():
                # Only set summary from content if not explicitly provided
                if 'summary' not in data or not data['summary']:
                    data['summary'] = post.content.strip()

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter in {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing markdown file {file_path}: {e}")

        # Generate ID from filename if not present (Hugo-compatible)
        if 'id' not in data:
            # Use filename without extension as ID
            data['id'] = file_path.stem

        # Validate required fields (id can now be auto-generated)
        required_fields = ['date', 'title']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(
                f"Missing required fields in {file_path} frontmatter: {', '.join(missing_fields)}"
            )

        # Convert all date/datetime objects to strings (YAML parser returns date objects)
        data = convert_dates_to_strings(data)

        # Ensure summary exists (either from frontmatter or content)
        if 'summary' not in data or not data['summary']:
            data['summary'] = ''

        return data

    def validate_format(self, file_path: Path) -> List[str]:
        """
        Validate Markdown format and YAML frontmatter.

        Args:
            file_path: Path to the Markdown event file

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            return errors

        try:
            # Try to parse frontmatter
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            data = dict(post.metadata)

            # Check required fields
            required_fields = ['id', 'date', 'title']
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field in frontmatter: {field}")

            # Check field types
            if 'id' in data and not isinstance(data['id'], str):
                errors.append("Field 'id' must be a string")

            # Accept both strings and date objects (YAML parser converts dates)
            if 'date' in data and not isinstance(data['date'], (str, date, datetime)):
                errors.append("Field 'date' must be a string or date object")

            if 'title' in data and not isinstance(data['title'], str):
                errors.append("Field 'title' must be a string")

            if 'importance' in data and not isinstance(data['importance'], (int, float)):
                errors.append("Field 'importance' must be a number")

            # Check for content or summary
            if not post.content.strip() and ('summary' not in data or not data['summary']):
                errors.append("Event must have either markdown content or summary field")

        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML frontmatter: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors
