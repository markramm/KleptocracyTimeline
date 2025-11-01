#!/usr/bin/env python3
"""
Convert timeline events from JSON to Markdown format.

Usage:
    python3 convert_to_markdown.py event-id.json
    python3 convert_to_markdown.py --all  # Convert all events
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any


def json_to_markdown(json_file: Path, output_file: Path = None) -> bool:
    """
    Convert a JSON event file to Markdown format with YAML frontmatter.

    Args:
        json_file: Path to the JSON event file
        output_file: Path to save markdown file (optional, defaults to same name with .md extension)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract summary (will become markdown body)
        summary = data.pop('summary', '')

        # Determine output path
        if output_file is None:
            output_file = json_file.with_suffix('.md')

        # Write markdown file with YAML frontmatter
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write YAML frontmatter
            f.write('---\n')
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            f.write('---\n\n')

            # Write markdown body (summary)
            f.write(summary)
            f.write('\n')

        print(f"✓ Converted {json_file.name} → {output_file.name}")
        return True

    except Exception as e:
        print(f"✗ Error converting {json_file}: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 convert_to_markdown.py <event-file.json>")
        print("       python3 convert_to_markdown.py --all")
        sys.exit(1)

    events_dir = Path(__file__).parent.parent / 'data' / 'events'

    if sys.argv[1] == '--all':
        # Convert all JSON files
        json_files = list(events_dir.glob('*.json'))
        print(f"Converting {len(json_files)} JSON events to Markdown...\n")

        success_count = 0
        for json_file in json_files:
            if json_to_markdown(json_file):
                success_count += 1

        print(f"\n✓ Successfully converted {success_count}/{len(json_files)} events")

    else:
        # Convert specific file
        json_file = Path(sys.argv[1])

        # If just filename provided, look in events directory
        if not json_file.is_absolute():
            json_file = events_dir / json_file

        if not json_file.exists():
            print(f"✗ File not found: {json_file}", file=sys.stderr)
            sys.exit(1)

        if json_to_markdown(json_file):
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == '__main__':
    main()
