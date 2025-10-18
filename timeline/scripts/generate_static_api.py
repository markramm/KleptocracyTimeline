#!/usr/bin/env python3
"""
Generate static API JSON files from markdown or JSON event files.

This script reads event files in either format and generates the static
JSON API files that the React timeline viewer needs.

Usage:
    # Generate from markdown files
    python generate_static_api.py --events-dir content/events --output-dir public/api

    # Generate from JSON files (backward compatible)
    python generate_static_api.py --events-dir ../../timeline_data/events --output-dir public/api
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter
from datetime import datetime

# Add research-server to path for parser imports
research_server_path = Path(__file__).parent.parent.parent / "research-server"
sys.path.insert(0, str(research_server_path))
sys.path.insert(0, str(research_server_path / "server"))

from parsers.factory import EventParserFactory


class StaticAPIGenerator:
    """Generate static API JSON files from timeline events."""

    def __init__(self, events_dir: Path, output_dir: Path):
        """
        Initialize the generator.

        Args:
            events_dir: Directory containing event files (JSON or markdown)
            output_dir: Directory to output API JSON files
        """
        self.events_dir = Path(events_dir)
        self.output_dir = Path(output_dir)
        self.events = []
        self.parser_factory = EventParserFactory()

    def load_events(self) -> None:
        """Load all events from directory (supports both JSON and markdown)."""
        self.events = []

        # Find all event files
        json_files = list(self.events_dir.rglob("*.json"))
        md_files = list(self.events_dir.rglob("*.md"))

        # Filter out README files
        md_files = [f for f in md_files if f.name.lower() != 'readme.md']

        all_files = json_files + md_files

        print(f"Found {len(json_files)} JSON and {len(md_files)} markdown files")

        # Parse all events
        for filepath in all_files:
            try:
                parser = self.parser_factory.get_parser(filepath)
                event_dict = parser.parse(filepath)

                # Ensure required fields
                if 'id' not in event_dict:
                    # Generate ID from filename
                    event_dict['id'] = filepath.stem

                self.events.append(event_dict)

            except Exception as e:
                print(f"⚠️  Error parsing {filepath.name}: {e}")
                continue

        # Sort by date
        self.events.sort(key=lambda x: x.get('date', ''))

        print(f"✅ Loaded {len(self.events)} events total")

    def generate_api_files(self) -> None:
        """Generate all static API JSON files."""
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nGenerating static API files in {self.output_dir}...")

        # 1. timeline.json - Full event list
        self._generate_timeline_json()

        # 2. tags.json - Tag index with counts
        self._generate_tags_json()

        # 3. actors.json - Actor index with counts
        self._generate_actors_json()

        # 4. stats.json - Statistics
        self._generate_stats_json()

        print("✅ Static API generation complete!\n")

    def _generate_timeline_json(self) -> None:
        """Generate timeline.json with all events."""
        output_file = self.output_dir / "timeline.json"

        # Clean events for JSON serialization
        clean_events = []
        for event in self.events:
            clean_event = {}
            for key, value in event.items():
                # Convert dates to strings
                if key == 'date' and hasattr(value, 'isoformat'):
                    clean_event[key] = value.isoformat()
                else:
                    clean_event[key] = value
            clean_events.append(clean_event)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(clean_events, f, indent=2, ensure_ascii=False)

        file_size = output_file.stat().st_size / 1024  # KB
        print(f"  ✓ timeline.json - {len(clean_events)} events ({file_size:.1f} KB)")

    def _generate_tags_json(self) -> None:
        """Generate tags.json with tag counts."""
        output_file = self.output_dir / "tags.json"

        tag_counter = Counter()
        for event in self.events:
            if 'tags' in event and isinstance(event['tags'], list):
                for tag in event['tags']:
                    if isinstance(tag, str):
                        tag_counter[tag] += 1

        tags = [
            {'name': tag, 'count': count}
            for tag, count in tag_counter.most_common()
        ]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tags, f, indent=2, ensure_ascii=False)

        print(f"  ✓ tags.json - {len(tags)} unique tags")

    def _generate_actors_json(self) -> None:
        """Generate actors.json with actor counts."""
        output_file = self.output_dir / "actors.json"

        actor_counter = Counter()
        for event in self.events:
            if 'actors' in event and isinstance(event['actors'], list):
                for actor in event['actors']:
                    if isinstance(actor, str):
                        actor_counter[actor] += 1

        actors = [
            {'name': actor, 'count': count}
            for actor, count in actor_counter.most_common()
        ]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(actors, f, indent=2, ensure_ascii=False)

        print(f"  ✓ actors.json - {len(actors)} unique actors")

    def _generate_stats_json(self) -> None:
        """Generate stats.json with timeline statistics."""
        output_file = self.output_dir / "stats.json"

        # Count sources
        total_sources = sum(
            len(event.get('sources', []))
            for event in self.events
        )

        # Get date range
        dates = [str(e.get('date', ''))[:10] for e in self.events if e.get('date')]
        date_range = {
            'start': min(dates) if dates else '',
            'end': max(dates) if dates else ''
        }

        # Events by year
        events_by_year = Counter()
        for event in self.events:
            if 'date' in event:
                year = str(event['date'])[:4]
                events_by_year[year] += 1

        # Tag counts
        tag_counter = Counter()
        for event in self.events:
            if 'tags' in event:
                tag_counter.update(event['tags'])

        # Actor counts
        actor_counter = Counter()
        for event in self.events:
            if 'actors' in event:
                actor_counter.update(event['actors'])

        stats = {
            'total_events': len(self.events),
            'total_tags': len(tag_counter),
            'total_actors': len(actor_counter),
            'total_sources': total_sources,
            'date_range': date_range,
            'events_by_year': dict(events_by_year),
            'top_tags': [
                {'name': tag, 'count': count}
                for tag, count in tag_counter.most_common(10)
            ],
            'top_actors': [
                {'name': actor, 'count': count}
                for actor, count in actor_counter.most_common(10)
            ],
            'generated': datetime.utcnow().isoformat() + 'Z'
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print(f"  ✓ stats.json - Timeline statistics")


def main():
    parser = argparse.ArgumentParser(
        description='Generate static API JSON files from event files (JSON or markdown)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from markdown files
  %(prog)s --events-dir content/events --output-dir public/api

  # Generate from JSON files (backward compatible)
  %(prog)s --events-dir ../../timeline_data/events --output-dir public/api

  # Default (from parent timeline_data)
  %(prog)s
        """
    )

    parser.add_argument(
        '--events-dir',
        type=Path,
        default='../../timeline_data/events',
        help='Directory containing event files (default: ../../timeline_data/events)'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default='../public/api',
        help='Output directory for API files (default: ../public/api)'
    )

    args = parser.parse_args()

    print("="*60)
    print("STATIC API GENERATOR")
    print("="*60)
    print(f"Events directory: {args.events_dir}")
    print(f"Output directory: {args.output_dir}")
    print()

    # Create generator
    generator = StaticAPIGenerator(args.events_dir, args.output_dir)

    # Load and generate
    try:
        generator.load_events()

        if not generator.events:
            print("❌ No events found!")
            sys.exit(1)

        generator.generate_api_files()

        print("="*60)
        print("SUCCESS!")
        print("="*60)
        print(f"\nStatic API files ready in {args.output_dir}/")
        print("React viewer can now load these files.\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
