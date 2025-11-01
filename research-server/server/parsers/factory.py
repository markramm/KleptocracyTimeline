"""
Event parser factory for dispatching to appropriate parser based on file format.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from parsers.base import EventParser
from parsers.json_parser import JsonEventParser
from parsers.markdown_parser import MarkdownEventParser

logger = logging.getLogger(__name__)


class EventParserFactory:
    """
    Factory for creating and dispatching to appropriate event parsers.

    Automatically selects the correct parser based on file extension.
    Supports:
    - .json files (JsonEventParser)
    - .md files (MarkdownEventParser)
    """

    def __init__(self):
        """Initialize factory with registered parsers."""
        self.parsers: List[EventParser] = [
            JsonEventParser(),
            MarkdownEventParser(),
        ]

    def get_parser(self, file_path: Path) -> Optional[EventParser]:
        """
        Get the appropriate parser for a given file.

        Args:
            file_path: Path to the event file

        Returns:
            EventParser instance that can handle the file, or None if unsupported
        """
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        return None

    def parse_event(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse an event file using the appropriate parser.

        Args:
            file_path: Path to the event file

        Returns:
            Dictionary containing event data

        Raises:
            ValueError: If file format is unsupported or parsing fails
            FileNotFoundError: If file does not exist
        """
        parser = self.get_parser(file_path)

        if parser is None:
            raise ValueError(
                f"Unsupported file format: {file_path.suffix}. "
                f"Supported formats: .json, .md"
            )

        try:
            return parser.parse(file_path)
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            raise

    def validate_event_format(self, file_path: Path) -> List[str]:
        """
        Validate an event file format without fully parsing.

        Args:
            file_path: Path to the event file

        Returns:
            List of validation error messages (empty if valid)
        """
        parser = self.get_parser(file_path)

        if parser is None:
            return [
                f"Unsupported file format: {file_path.suffix}. "
                f"Supported formats: .json, .md"
            ]

        try:
            return parser.validate_format(file_path)
        except Exception as e:
            logger.error(f"Error validating {file_path}: {e}")
            return [f"Validation error: {str(e)}"]
