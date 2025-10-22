#!/usr/bin/env python3
"""
Event Normalizer - Ensures deterministic formatting for clean git diffs

All events are normalized before writing to ensure:
- Alphabetically sorted lists (actors, tags)
- Consistent field ordering
- Stable source ordering (by tier, then title)
- Deterministic JSON serialization
"""

import json
from collections import OrderedDict
from typing import Any, Dict, List
from pathlib import Path


class EventNormalizer:
    """Ensure deterministic event formatting for clean git diffs"""

    # Standard field order for consistent diffs
    FIELD_ORDER = [
        'id',
        'date',
        'title',
        'summary',
        'importance',
        'status',
        'actors',
        'tags',
        'sources',
        'related_events',
        'notes'
    ]

    # Source field order
    SOURCE_FIELD_ORDER = [
        'url',
        'title',
        'publisher',
        'date',
        'tier',
        'archive_url'
    ]

    def normalize(self, event: Dict[str, Any]) -> OrderedDict:
        """
        Normalize event for deterministic serialization

        Args:
            event: Event dictionary to normalize

        Returns:
            OrderedDict with normalized, consistently ordered fields
        """
        normalized = OrderedDict()

        # Add fields in standard order
        for field in self.FIELD_ORDER:
            if field in event:
                normalized[field] = self._normalize_field(field, event[field])

        # Add any extra fields (sorted alphabetically)
        extra_fields = sorted(set(event.keys()) - set(self.FIELD_ORDER))
        for field in extra_fields:
            normalized[field] = self._normalize_field(field, event[field])

        return normalized

    def _normalize_field(self, field: str, value: Any) -> Any:
        """Normalize specific field types"""

        if field in ('actors', 'tags'):
            # Sort lists alphabetically (case-insensitive)
            if isinstance(value, list):
                return sorted(value, key=lambda x: x.lower() if isinstance(x, str) else str(x))
            return value

        elif field == 'sources':
            # Sort sources by tier (ascending), then title (alphabetical)
            if isinstance(value, list):
                normalized_sources = [self._normalize_source(s) for s in value]
                return sorted(
                    normalized_sources,
                    key=lambda s: (s.get('tier', 99), (s.get('title', '') or '').lower())
                )
            return value

        elif field == 'related_events':
            # Sort related event IDs
            if isinstance(value, list):
                return sorted(value)
            return value

        else:
            return value

    def _normalize_source(self, source: Dict[str, Any]) -> OrderedDict:
        """
        Normalize source for stable diffs

        Ensures consistent field ordering and removes None/empty values
        """
        normalized = OrderedDict()

        # Add fields in standard order
        for field in self.SOURCE_FIELD_ORDER:
            if field in source and source[field] is not None and source[field] != '':
                normalized[field] = source[field]

        # Add any extra fields (sorted)
        extra_fields = sorted(set(source.keys()) - set(self.SOURCE_FIELD_ORDER))
        for field in extra_fields:
            if source[field] is not None and source[field] != '':
                normalized[field] = source[field]

        return normalized

    def serialize(self, event: Dict[str, Any]) -> str:
        """
        Serialize event to deterministic JSON string

        Args:
            event: Event dictionary to serialize

        Returns:
            Formatted JSON string with trailing newline
        """
        normalized = self.normalize(event)
        return json.dumps(
            normalized,
            indent=2,              # 2-space indent (GitHub default)
            ensure_ascii=False,    # Allow unicode characters
            separators=(',', ': ') # Consistent spacing
        ) + '\n'  # Trailing newline (POSIX standard)

    def write_event_file(self, event: Dict[str, Any], file_path: Path) -> None:
        """
        Write event to file with deterministic formatting

        Args:
            event: Event dictionary to write
            file_path: Path to write event file
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.serialize(event))

    def normalize_file(self, file_path: Path) -> bool:
        """
        Normalize an existing event file in-place

        Args:
            file_path: Path to event file to normalize

        Returns:
            True if file was changed, False if already normalized
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Parse event
        event = json.loads(original_content)

        # Normalize and serialize
        normalized_content = self.serialize(event)

        # Check if changed
        if original_content == normalized_content:
            return False

        # Write normalized version
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(normalized_content)

        return True


def normalize_all_events(events_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Normalize all events in a directory

    Args:
        events_dir: Directory containing event files
        dry_run: If True, don't write changes, just report

    Returns:
        Dictionary with normalization statistics
    """
    normalizer = EventNormalizer()
    stats = {
        'total': 0,
        'normalized': 0,
        'unchanged': 0,
        'errors': 0,
        'files': []
    }

    for event_file in events_dir.glob('*.json'):
        stats['total'] += 1

        try:
            if dry_run:
                # Just check if would change
                with open(event_file, 'r') as f:
                    original = f.read()
                event = json.loads(original)
                normalized = normalizer.serialize(event)

                if original != normalized:
                    stats['normalized'] += 1
                    stats['files'].append(str(event_file.name))
                else:
                    stats['unchanged'] += 1
            else:
                # Actually normalize
                if normalizer.normalize_file(event_file):
                    stats['normalized'] += 1
                    stats['files'].append(str(event_file.name))
                else:
                    stats['unchanged'] += 1

        except Exception as e:
            stats['errors'] += 1
            print(f"Error normalizing {event_file}: {e}")

    return stats


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: event_normalizer.py <events_directory> [--dry-run]")
        sys.exit(1)

    events_dir = Path(sys.argv[1])
    dry_run = '--dry-run' in sys.argv

    if not events_dir.exists():
        print(f"Error: Directory not found: {events_dir}")
        sys.exit(1)

    print(f"Normalizing events in: {events_dir}")
    if dry_run:
        print("DRY RUN - no files will be modified")

    stats = normalize_all_events(events_dir, dry_run=dry_run)

    print(f"\nResults:")
    print(f"  Total events: {stats['total']}")
    print(f"  Normalized: {stats['normalized']}")
    print(f"  Unchanged: {stats['unchanged']}")
    print(f"  Errors: {stats['errors']}")

    if stats['files'] and len(stats['files']) <= 20:
        print(f"\nModified files:")
        for filename in stats['files']:
            print(f"  - {filename}")
    elif stats['files']:
        print(f"\n{len(stats['files'])} files modified (showing first 20):")
        for filename in stats['files'][:20]:
            print(f"  - {filename}")
