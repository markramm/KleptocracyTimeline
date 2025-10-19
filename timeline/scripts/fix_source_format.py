#!/usr/bin/env python3
"""
Fix malformed source fields in timeline events.

Converts sources from plain strings to structured objects with 'title' and 'url' fields.
Handles two malformed formats:
1. Plain strings with descriptive text (e.g., "NBC News: 'Title'")
2. Plain URL strings (e.g., "https://example.com")
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import re


def is_url(text: str) -> bool:
    """Check if text is a URL."""
    return text.startswith(('http://', 'https://', 'www.'))


def extract_source_info(source_str: str) -> Dict[str, str]:
    """
    Convert a plain string source to structured format.

    Args:
        source_str: Plain string source (either description or URL)

    Returns:
        Dict with 'title' and 'url' fields
    """
    if is_url(source_str):
        # Plain URL - extract domain as title
        url = source_str
        # Extract domain from URL for title
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        title = domain_match.group(1) if domain_match else "Source"
        return {"title": title, "url": url}
    else:
        # Descriptive string - use as title, no URL
        return {"title": source_str, "url": ""}


def fix_event_sources(event_data: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
    """
    Fix sources in an event if they're malformed.

    Args:
        event_data: Event dictionary

    Returns:
        Tuple of (fixed_event_data, was_modified)
    """
    if 'sources' not in event_data or not event_data['sources']:
        return event_data, False

    sources = event_data['sources']

    # Check if sources are already in correct format
    if all(isinstance(s, dict) and 'title' in s and 'url' in s for s in sources):
        return event_data, False

    # Fix malformed sources
    fixed_sources = []
    for source in sources:
        if isinstance(source, str):
            # Convert string to structured format
            fixed_sources.append(extract_source_info(source))
        elif isinstance(source, dict):
            # Already a dict, but may be missing fields
            if 'title' not in source or 'url' not in source:
                # Add missing fields
                fixed_source = {
                    'title': source.get('title', source.get('url', 'Unknown')),
                    'url': source.get('url', '')
                }
                fixed_sources.append(fixed_source)
            else:
                fixed_sources.append(source)
        else:
            print(f"Warning: Unexpected source type: {type(source)}")
            fixed_sources.append({"title": str(source), "url": ""})

    event_data['sources'] = fixed_sources
    return event_data, True


def main():
    """Fix all malformed sources in timeline events."""
    events_dir = Path('timeline_data/events')

    if not events_dir.exists():
        print(f"Error: Events directory {events_dir} not found")
        sys.exit(1)

    json_files = list(events_dir.glob('*.json'))
    print(f"Found {len(json_files)} event files")

    fixed_count = 0
    error_count = 0

    for json_file in json_files:
        try:
            # Read event
            with open(json_file, 'r', encoding='utf-8') as f:
                event_data = json.load(f)

            # Fix sources
            fixed_event, was_modified = fix_event_sources(event_data)

            if was_modified:
                # Write back to file
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(fixed_event, f, indent=2, ensure_ascii=False)
                    f.write('\n')  # Add trailing newline

                print(f"✓ Fixed: {json_file.name}")
                fixed_count += 1

        except Exception as e:
            print(f"✗ Error processing {json_file.name}: {e}")
            error_count += 1

    print(f"\nResults:")
    print(f"  Fixed: {fixed_count} files")
    print(f"  Errors: {error_count} files")
    print(f"  Total processed: {len(json_files)} files")

    if error_count == 0:
        print("\n✅ All source fields successfully fixed!")
    else:
        print(f"\n⚠️  {error_count} files had errors")
        sys.exit(1)


if __name__ == '__main__':
    main()
