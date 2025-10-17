#!/usr/bin/env python3
"""
JSON to Hugo Markdown Converter

Converts timeline events from JSON format to Hugo-compatible markdown format.
Supports single file conversion, batch conversion, and directory conversion.

Usage:
    # Convert single file
    python json_to_hugo.py --input event.json --output content/events/

    # Convert all JSON files in directory
    python json_to_hugo.py --batch timeline_data/events/*.json --output content/events/

    # Dry run (validation only)
    python json_to_hugo.py --batch timeline_data/events/*.json --dry-run
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import re


class HugoConverter:
    """Converts JSON timeline events to Hugo markdown format"""

    def __init__(self, output_dir: Path, dry_run: bool = False):
        self.output_dir = Path(output_dir)
        self.dry_run = dry_run
        self.stats = {
            "processed": 0,
            "success": 0,
            "errors": 0,
            "skipped": 0
        }

    def convert_event(self, json_path: Path) -> Optional[Path]:
        """Convert a single JSON event to Hugo markdown"""
        try:
            # Read JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                event = json.load(f)

            # Validate required fields
            if not self._validate_event(event):
                print(f"❌ Validation failed: {json_path.name}")
                self.stats["errors"] += 1
                return None

            # Generate Hugo markdown
            markdown = self._generate_markdown(event)

            # Determine output path
            output_path = self._get_output_path(event)

            if self.dry_run:
                print(f"✓ Would create: {output_path}")
                self.stats["success"] += 1
                return output_path

            # Create directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write markdown file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)

            print(f"✅ Converted: {json_path.name} → {output_path}")
            self.stats["success"] += 1
            return output_path

        except Exception as e:
            print(f"❌ Error converting {json_path.name}: {e}")
            self.stats["errors"] += 1
            return None

    def _validate_event(self, event: Dict[str, Any]) -> bool:
        """Validate event has required fields"""
        required = ["date", "title", "summary"]
        for field in required:
            if field not in event:
                print(f"  Missing required field: {field}")
                return False
        return True

    def _generate_markdown(self, event: Dict[str, Any]) -> str:
        """Generate Hugo markdown content from JSON event"""
        # Build front matter
        front_matter = self._build_front_matter(event)

        # Build content body
        body = self._build_content_body(event)

        # Combine
        return f"---\n{front_matter}\n---\n\n{body}\n"

    def _build_front_matter(self, event: Dict[str, Any]) -> str:
        """Build YAML front matter"""
        lines = []

        # Required fields
        lines.append(f'title: "{self._escape_yaml(event["title"])}"')
        lines.append(f'date: {event["date"]}')
        lines.append(f'importance: {event.get("importance", 5)}')
        lines.append('draft: false')
        lines.append('')

        # Tags
        if "tags" in event and event["tags"]:
            lines.append('tags:')
            for tag in event["tags"]:
                lines.append(f'  - {tag}')
            lines.append('')

        # Actors
        if "actors" in event and event["actors"]:
            lines.append('actors:')
            for actor in event["actors"]:
                lines.append(f'  - {actor}')
            lines.append('')

        # Optional metadata
        if "location" in event:
            lines.append(f'location: "{self._escape_yaml(event["location"])}"')

        if "impact_score" in event:
            lines.append(f'impact_score: {event["impact_score"]}')

        lines.append('verification_status: "pending"')
        lines.append(f'last_updated: {datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}')

        return '\n'.join(lines)

    def _build_content_body(self, event: Dict[str, Any]) -> str:
        """Build markdown content body"""
        sections = []

        # Summary
        summary = event.get("summary", "")
        sections.append(summary)
        sections.append('')

        # Sources
        if "sources" in event and event["sources"]:
            sections.append('## Sources')
            sections.append('')
            for idx, source in enumerate(event["sources"], 1):
                source_line = self._format_source(source, idx)
                sections.append(source_line)
            sections.append('')

        # Related events
        if "related_events" in event and event["related_events"]:
            sections.append('## Related Events')
            sections.append('')
            for related in event["related_events"]:
                sections.append(f'- [{related["title"]}]({related["url"]})')
            sections.append('')

        # Analysis (if present)
        if "analysis" in event:
            sections.append('## Analysis')
            sections.append('')
            sections.append(event["analysis"])
            sections.append('')

        # Metadata footer
        sections.append('---')
        sections.append('')
        sections.append(f'**Last Updated**: {datetime.utcnow().strftime("%B %d, %Y")}')
        sections.append(f'**Importance Score**: {event.get("importance", 5)}/10')

        return '\n'.join(sections)

    def _format_source(self, source: Any, number: int) -> str:
        """Format a source as markdown link"""
        if isinstance(source, dict):
            url = source.get("url", "")
            title = source.get("title", "Source")
            source_type = source.get("type", "")
            if source_type:
                return f'{number}. [{title}]({url}) - {source_type.title()}'
            return f'{number}. [{title}]({url})'
        elif isinstance(source, str):
            # Simple URL
            return f'{number}. [Source]({source})'
        return f'{number}. {source}'

    def _get_output_path(self, event: Dict[str, Any]) -> Path:
        """Generate output file path from event data"""
        date = event["date"]
        year = date[:4]

        # Generate slug from title or use ID
        if "id" in event:
            # Extract slug from ID (format: YYYY-MM-DD--slug)
            parts = event["id"].split("--")
            if len(parts) == 2:
                slug = parts[1]
            else:
                slug = self._slugify(event["title"])
        else:
            slug = self._slugify(event["title"])

        # Hugo filename format: YYYY-MM-DD-slug.md
        filename = f'{date}-{slug}.md'

        return self.output_dir / year / filename

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug"""
        # Convert to lowercase
        slug = text.lower()
        # Replace spaces and underscores with hyphens
        slug = re.sub(r'[\s_]+', '-', slug)
        # Remove special characters
        slug = re.sub(r'[^\w\-]', '', slug)
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        # Trim hyphens from ends
        slug = slug.strip('-')
        # Limit length
        return slug[:100]

    def _escape_yaml(self, text: str) -> str:
        """Escape quotes and special characters for YAML"""
        return text.replace('"', '\\"').replace('\n', ' ')

    def convert_batch(self, json_paths: List[Path]) -> None:
        """Convert multiple JSON files"""
        print(f"\n{'='*60}")
        print(f"Converting {len(json_paths)} JSON files to Hugo markdown")
        print(f"Output directory: {self.output_dir}")
        if self.dry_run:
            print("DRY RUN MODE - No files will be created")
        print(f"{'='*60}\n")

        for json_path in json_paths:
            self.stats["processed"] += 1
            self.convert_event(json_path)

        # Print summary
        self._print_summary()

    def _print_summary(self) -> None:
        """Print conversion statistics"""
        print(f"\n{'='*60}")
        print("CONVERSION SUMMARY")
        print(f"{'='*60}")
        print(f"Processed:  {self.stats['processed']}")
        print(f"✅ Success:  {self.stats['success']}")
        print(f"❌ Errors:   {self.stats['errors']}")
        print(f"⏭️  Skipped:  {self.stats['skipped']}")
        print(f"{'='*60}\n")

        if self.stats['errors'] > 0:
            print("⚠️  Some files failed to convert. Check error messages above.")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSON timeline events to Hugo markdown format"
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Single JSON file to convert"
    )
    parser.add_argument(
        "--batch",
        nargs="+",
        type=Path,
        help="Multiple JSON files to convert"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default="content/events",
        help="Output directory for Hugo markdown files (default: content/events)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview without creating files"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.input and not args.batch:
        parser.error("Either --input or --batch is required")

    # Create converter
    converter = HugoConverter(args.output, dry_run=args.dry_run)

    # Convert
    if args.input:
        converter.convert_event(args.input)
        converter._print_summary()
    elif args.batch:
        # Filter for JSON files only
        json_files = [p for p in args.batch if p.suffix == '.json' and p.is_file()]
        if not json_files:
            print("❌ No valid JSON files found")
            sys.exit(1)
        converter.convert_batch(json_files)


if __name__ == "__main__":
    main()
