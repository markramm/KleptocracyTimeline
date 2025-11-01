"""
JSON event parser for timeline events.

Handles parsing of JSON-formatted event files.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

from parsers.base import EventParser


class JsonEventParser(EventParser):
    """
    Parser for JSON-formatted timeline events.

    Handles .json files containing timeline event data.
    """

    def can_parse(self, file_path: Path) -> bool:
        """Check if this is a JSON file."""
        return file_path.suffix.lower() == '.json'

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a JSON event file.

        Args:
            file_path: Path to the JSON event file

        Returns:
            Dictionary containing event data

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If JSON is invalid or required fields are missing
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Event file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")

        # Validate required fields
        required_fields = ['date', 'title']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(
                f"Missing required fields in {file_path}: {', '.join(missing_fields)}"
            )

        return data

    def validate_format(self, file_path: Path) -> List[str]:
        """
        Validate JSON format without fully parsing event data.

        Args:
            file_path: Path to the JSON event file

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            return errors

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check required fields
            required_fields = ['date', 'title']
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")

            # Check field types
            if 'date' in data and not isinstance(data['date'], str):
                errors.append("Field 'date' must be a string")

            if 'title' in data and not isinstance(data['title'], str):
                errors.append("Field 'title' must be a string")

            if 'importance' in data and not isinstance(data['importance'], (int, float)):
                errors.append("Field 'importance' must be a number")

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors
