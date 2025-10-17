"""
Base parser interface for timeline events.

Defines the abstract interface that all event parsers must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List


class EventParser(ABC):
    """
    Abstract base class for event parsers.

    All event parsers must implement this interface to be compatible
    with the EventParserFactory.
    """

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file.

        Args:
            file_path: Path to the event file

        Returns:
            True if this parser can handle the file format, False otherwise
        """
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse an event file and return event data.

        Args:
            file_path: Path to the event file

        Returns:
            Dictionary containing event data conforming to timeline_event_schema.json

        Raises:
            ValueError: If file format is invalid or required fields are missing
            FileNotFoundError: If file does not exist
        """
        pass

    @abstractmethod
    def validate_format(self, file_path: Path) -> List[str]:
        """
        Validate file format without fully parsing.

        Args:
            file_path: Path to the event file

        Returns:
            List of validation error messages (empty list if valid)
        """
        pass
