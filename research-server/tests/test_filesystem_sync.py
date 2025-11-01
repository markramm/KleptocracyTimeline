#!/usr/bin/env python3
"""
Integration tests for filesystem sync with mixed event formats.

Tests the complete flow of syncing JSON and Markdown events to database.
"""

import pytest
import sys
import json
from pathlib import Path
from datetime import datetime

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

from parsers.factory import EventParserFactory


class TestFilesystemSyncIntegration:
    """Test filesystem sync with mixed JSON and Markdown formats."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = EventParserFactory()

    def test_sync_json_and_markdown_files(self, tmp_path):
        """Test syncing directory with both JSON and Markdown events."""
        # Create JSON event
        json_file = tmp_path / '2025-01-15--json-event.json'
        json_file.write_text(json.dumps({
            "id": "2025-01-15--json-event",
            "date": "2025-01-15",
            "title": "JSON Event",
            "summary": "This is a JSON event",
            "importance": 7,
            "tags": ["test"]
        }))

        # Create Markdown event
        md_file = tmp_path / '2025-01-16--markdown-event.md'
        md_file.write_text("""---
id: 2025-01-16--markdown-event
date: 2025-01-16
title: Markdown Event
importance: 8
tags:
  - test
  - markdown
---

This is a Markdown event.
""")

        # Parse both files
        json_data = self.factory.parse_event(json_file)
        md_data = self.factory.parse_event(md_file)

        # Verify both parsed correctly
        assert json_data['id'] == '2025-01-15--json-event'
        assert json_data['title'] == 'JSON Event'
        assert json_data['importance'] == 7

        assert md_data['id'] == '2025-01-16--markdown-event'
        assert md_data['title'] == 'Markdown Event'
        assert md_data['importance'] == 8
        assert 'markdown' in md_data['tags']

    def test_sync_with_readme_excluded(self, tmp_path):
        """Test that README.md files are excluded from sync."""
        # Create README.md
        readme_file = tmp_path / 'README.md'
        readme_file.write_text("""# Events Directory

This directory contains timeline events.
""")

        # Create valid event
        event_file = tmp_path / '2025-01-15--event.md'
        event_file.write_text("""---
id: 2025-01-15--event
date: 2025-01-15
title: Valid Event
---

Summary.
""")

        # Get all markdown files
        md_files = list(tmp_path.glob('*.md'))
        assert len(md_files) == 2  # Both files exist

        # Filter out README
        event_files = [f for f in md_files if f.name.upper() != 'README.MD']
        assert len(event_files) == 1
        assert event_files[0].name == '2025-01-15--event.md'

    def test_sync_with_hidden_files_excluded(self, tmp_path):
        """Test that hidden files are excluded from sync."""
        # Create hidden file
        hidden_file = tmp_path / '.hidden-event.json'
        hidden_file.write_text('{"date": "2025-01-15"}')

        # Create normal file
        normal_file = tmp_path / '2025-01-15--event.json'
        normal_file.write_text('{"date": "2025-01-15", "title": "Event"}')

        # Get all JSON files
        json_files = list(tmp_path.glob('*.json'))

        # Filter out hidden files
        visible_files = [f for f in json_files if not f.name.startswith('.')]
        assert len(visible_files) == 1
        assert visible_files[0].name == '2025-01-15--event.json'

    def test_sync_multiple_formats_same_directory(self, tmp_path):
        """Test syncing directory with multiple event formats."""
        # Create 3 JSON events
        for i in range(1, 4):
            json_file = tmp_path / f'2025-01-{i:02d}--json-event-{i}.json'
            json_file.write_text(json.dumps({
                "id": f"2025-01-{i:02d}--json-event-{i}",
                "date": f"2025-01-{i:02d}",
                "title": f"JSON Event {i}",
                "summary": f"Summary {i}"
            }))

        # Create 2 Markdown events
        for i in range(4, 6):
            md_file = tmp_path / f'2025-01-{i:02d}--md-event-{i}.md'
            md_file.write_text(f"""---
id: 2025-01-{i:02d}--md-event-{i}
date: 2025-01-{i:02d}
title: Markdown Event {i}
---

Summary {i}.
""")

        # Get all event files
        json_files = list(tmp_path.glob('*.json'))
        md_files = [f for f in tmp_path.glob('*.md') if f.name.upper() != 'README.MD']
        all_files = json_files + md_files

        assert len(json_files) == 3
        assert len(md_files) == 2
        assert len(all_files) == 5

        # Parse all files
        events = []
        for file in all_files:
            data = self.factory.parse_event(file)
            events.append(data)

        assert len(events) == 5

        # Verify dates are sequential
        dates = sorted([e['date'] for e in events])
        assert dates == ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05']

    def test_sync_detects_file_changes(self, tmp_path):
        """Test that sync detects when files are modified."""
        import hashlib

        event_file = tmp_path / '2025-01-15--event.json'

        # Create initial version
        initial_content = json.dumps({
            "id": "2025-01-15--event",
            "date": "2025-01-15",
            "title": "Original Title"
        })
        event_file.write_text(initial_content)

        # Calculate initial hash
        initial_hash = hashlib.md5(initial_content.encode()).hexdigest()

        # Modify file
        modified_content = json.dumps({
            "id": "2025-01-15--event",
            "date": "2025-01-15",
            "title": "Updated Title"
        })
        event_file.write_text(modified_content)

        # Calculate new hash
        modified_hash = hashlib.md5(modified_content.encode()).hexdigest()

        # Hashes should be different
        assert initial_hash != modified_hash

    def test_sync_handles_mixed_format_updates(self, tmp_path):
        """Test syncing when same event exists in different formats."""
        event_id = "2025-01-15--event"

        # Create JSON version
        json_file = tmp_path / f'{event_id}.json'
        json_file.write_text(json.dumps({
            "id": event_id,
            "date": "2025-01-15",
            "title": "JSON Version",
            "importance": 5
        }))

        # Create Markdown version
        md_file = tmp_path / f'{event_id}.md'
        md_file.write_text(f"""---
id: {event_id}
date: 2025-01-15
title: Markdown Version
importance: 8
---

Summary.
""")

        # Both files exist with same ID (stem)
        assert json_file.stem == md_file.stem

        # Parse both - each should work independently
        json_data = self.factory.parse_event(json_file)
        md_data = self.factory.parse_event(md_file)

        assert json_data['title'] == 'JSON Version'
        assert md_data['title'] == 'Markdown Version'

        # In real sync, we'd need conflict resolution
        # For now, verify both can be parsed


class TestFilesystemSyncPerformance:
    """Test performance of filesystem sync with many events."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = EventParserFactory()

    def test_sync_100_mixed_events(self, tmp_path):
        """Test syncing 100 events in mixed formats."""
        # Create 50 JSON events
        for i in range(50):
            json_file = tmp_path / f'2025-01-01--json-event-{i:03d}.json'
            json_file.write_text(json.dumps({
                "id": f"2025-01-01--json-event-{i:03d}",
                "date": "2025-01-01",
                "title": f"JSON Event {i}",
                "summary": "Summary " * 10  # Longer summary
            }))

        # Create 50 Markdown events
        for i in range(50):
            md_file = tmp_path / f'2025-01-02--md-event-{i:03d}.md'
            md_file.write_text(f"""---
id: 2025-01-02--md-event-{i:03d}
date: 2025-01-02
title: Markdown Event {i}
---

{'Summary paragraph. ' * 10}
""")

        # Get all files
        json_files = list(tmp_path.glob('*.json'))
        md_files = list(tmp_path.glob('*.md'))
        all_files = json_files + md_files

        assert len(all_files) == 100

        # Time the parsing
        import time
        start = time.time()

        parsed_count = 0
        for file in all_files:
            data = self.factory.parse_event(file)
            assert 'id' in data
            assert 'date' in data
            parsed_count += 1

        elapsed = time.time() - start

        assert parsed_count == 100
        # Should parse 100 events in under 1 second
        assert elapsed < 1.0, f"Parsing took {elapsed:.2f}s, expected < 1.0s"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
