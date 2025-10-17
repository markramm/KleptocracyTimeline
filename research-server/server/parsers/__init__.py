"""
Event parsers for timeline data.

Provides a factory pattern for parsing events from multiple formats:
- JSON (.json files)
- Markdown (.md files with YAML frontmatter)
"""

from parsers.base import EventParser
from parsers.json_parser import JsonEventParser
from parsers.markdown_parser import MarkdownEventParser
from parsers.factory import EventParserFactory

__all__ = [
    'EventParser',
    'JsonEventParser',
    'MarkdownEventParser',
    'EventParserFactory'
]
