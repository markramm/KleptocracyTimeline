#!/usr/bin/env python3
"""
Unified generation script for timeline outputs.

This script consolidates all generation functionality:
- Build timeline index JSON
- Generate static API files
- Create footnotes/citations
- Generate statistics
"""

import argparse
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    get_event_files,
    load_event,
    save_json_file,
    ensure_dir,
    setup_logger,
    log_info,
    log_success,
    log_error,
    print_header,
    print_summary
)


class TimelineGenerator:
    """Generate various outputs from timeline events."""
    
    def __init__(self, events_dir: str = "timeline_data/events", output_dir: str = "timeline_data"):
        """
        Initialize the generator.
        
        Args:
            events_dir: Path to events directory
            output_dir: Path to output directory
        """
        self.events_dir = Path(events_dir)
        self.output_dir = Path(output_dir)
        self.logger = setup_logger('generator')
        self.events = []
        self.stats = {}
    
    def load_events(self) -> None:
        """Load all events from the events directory."""
        self.events = []
        
        for filepath in get_event_files(self.events_dir):
            event = load_event(filepath)
            if event:
                # Add ID hash for consistency
                if 'id' in event:
                    event['_id_hash'] = hashlib.sha256(event['id'].encode()).hexdigest()
                self.events.append(event)
        
        # Sort by date
        self.events.sort(key=lambda x: x.get('date', ''))
        
        log_info(f"Loaded {len(self.events)} events")
    
    def generate_index(self) -> None:
        """Generate the main timeline index JSON."""
        output_file = self.output_dir / "timeline_index.json"
        
        log_info("Generating timeline index...")
        
        # Prepare events for JSON serialization
        clean_events = []
        for event in self.events:
            clean_event = event.copy()
            # Ensure date is string
            if 'date' in clean_event and hasattr(clean_event['date'], 'isoformat'):
                clean_event['date'] = clean_event['date'].isoformat()
            clean_events.append(clean_event)
        
        # Save index
        save_json_file(output_file, {'events': clean_events})
        log_success(f"Generated {output_file} with {len(clean_events)} events")
    
    def generate_static_api(self) -> None:
        """Generate static API JSON files for GitHub Pages."""
        api_dir = ensure_dir(self.output_dir / "api")
        
        log_info("Generating static API files...")
        
        # Generate timeline.json
        save_json_file(api_dir / "timeline.json", self.events)
        
        # Generate tags.json
        tags = self._extract_tags()
        save_json_file(api_dir / "tags.json", tags)
        
        # Generate actors.json
        actors = self._extract_actors()
        save_json_file(api_dir / "actors.json", actors)
        
        # Generate stats.json
        stats = self._calculate_stats()
        save_json_file(api_dir / "stats.json", stats)
        
        log_success(f"Generated 4 API files in {api_dir}")
    
    def generate_footnotes(self, output_format: str = "markdown") -> None:
        """
        Generate footnotes/citations for all events.
        
        Args:
            output_format: Output format (markdown, html, json)
        """
        output_file = self.output_dir / f"citations.{output_format.lower()}"
        
        log_info(f"Generating {output_format} citations...")
        
        if output_format.lower() == "markdown":
            content = self._generate_markdown_citations()
            output_file = output_file.with_suffix('.md')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        elif output_format.lower() == "json":
            citations = self._generate_json_citations()
            save_json_file(output_file, citations)
        
        elif output_format.lower() == "html":
            content = self._generate_html_citations()
            output_file = output_file.with_suffix('.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        else:
            log_error(f"Unsupported format: {output_format}")
            return
        
        log_success(f"Generated citations in {output_file}")
    
    def generate_statistics(self) -> None:
        """Generate detailed statistics report."""
        output_file = self.output_dir / "statistics.md"
        
        log_info("Generating statistics report...")
        
        stats = self._calculate_stats()
        
        # Create markdown report
        content = ["# Timeline Statistics Report"]
        content.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        content.append("## Overview")
        content.append(f"- **Total Events**: {stats['total_events']}")
        content.append(f"- **Date Range**: {stats['date_range']['start']} to {stats['date_range']['end']}")
        content.append(f"- **Total Sources**: {stats['total_sources']}")
        content.append(f"- **Unique Tags**: {stats['total_tags']}")
        content.append(f"- **Unique Actors**: {stats['total_actors']}")
        
        content.append("\n## Event Status")
        for status, count in stats['status_counts'].items():
            content.append(f"- **{status.title()}**: {count}")
        
        content.append("\n## Top Tags")
        for tag_info in stats['top_tags'][:20]:
            content.append(f"- {tag_info['name']}: {tag_info['count']} events")
        
        content.append("\n## Top Actors")
        for actor_info in stats['top_actors'][:20]:
            content.append(f"- {actor_info['name']}: {actor_info['count']} events")
        
        content.append("\n## Events by Year")
        events_by_year = Counter()
        for event in self.events:
            if 'date' in event:
                year = str(event['date'])[:4]
                events_by_year[year] += 1
        
        for year in sorted(events_by_year.keys()):
            content.append(f"- {year}: {events_by_year[year]} events")
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        log_success(f"Generated statistics report in {output_file}")
    
    def _extract_tags(self) -> List[Dict[str, Any]]:
        """Extract and count all tags."""
        tag_counter = Counter()

        for event in self.events:
            if 'tags' in event and isinstance(event['tags'], list):
                for tag in event['tags']:
                    # Only count string tags (skip dicts or other non-hashable types)
                    if isinstance(tag, str):
                        tag_counter[tag] += 1
                    else:
                        self.logger.warning(f"Skipping non-string tag in {event.get('id', 'unknown')}: {type(tag)}")

        return [{'name': tag, 'count': count} for tag, count in tag_counter.most_common()]

    def _extract_actors(self) -> List[Dict[str, Any]]:
        """Extract and count all actors."""
        actor_counter = Counter()

        for event in self.events:
            if 'actors' in event and isinstance(event['actors'], list):
                for actor in event['actors']:
                    # Only count string actors (skip dicts or other non-hashable types)
                    if isinstance(actor, str):
                        actor_counter[actor] += 1
                    else:
                        self.logger.warning(f"Skipping non-string actor in {event.get('id', 'unknown')}: {type(actor)}")

        return [{'name': actor, 'count': count} for actor, count in actor_counter.most_common()]
    
    def _calculate_stats(self) -> Dict[str, Any]:
        """Calculate comprehensive statistics."""
        tags = self._extract_tags()
        actors = self._extract_actors()
        
        # Count sources
        total_sources = sum(
            len(event.get('sources', []))
            for event in self.events
        )
        
        # Get date range
        dates = [e.get('date', '') for e in self.events if e.get('date')]
        date_range = {
            'start': min(dates) if dates else '',
            'end': max(dates) if dates else ''
        }
        
        # Count statuses
        status_counts = Counter(e.get('status', 'unknown') for e in self.events)
        
        return {
            'total_events': len(self.events),
            'total_tags': len(tags),
            'total_actors': len(actors),
            'total_sources': total_sources,
            'date_range': date_range,
            'status_counts': dict(status_counts),
            'top_tags': tags[:10],
            'top_actors': actors[:10],
            'generated': datetime.now().isoformat()
        }
    
    def _generate_markdown_citations(self) -> str:
        """Generate markdown formatted citations."""
        lines = ["# Timeline Event Citations\n"]
        
        for event in self.events:
            lines.append(f"## {event.get('title', 'Untitled')}")
            lines.append(f"*Date: {event.get('date', 'Unknown')}*\n")
            
            if 'sources' in event:
                for i, source in enumerate(event['sources'], 1):
                    if isinstance(source, dict):
                        title = source.get('title', 'Untitled')
                        url = source.get('url', '')
                        lines.append(f"{i}. [{title}]({url})")
            
            lines.append("")  # Blank line between events
        
        return '\n'.join(lines)
    
    def _generate_json_citations(self) -> List[Dict[str, Any]]:
        """Generate JSON formatted citations."""
        citations = []
        
        for event in self.events:
            citation = {
                'id': event.get('id', ''),
                'title': event.get('title', ''),
                'date': str(event.get('date', ''))[:10],
                'sources': []
            }
            
            if 'sources' in event:
                for source in event['sources']:
                    if isinstance(source, dict):
                        citation['sources'].append({
                            'title': source.get('title', ''),
                            'url': source.get('url', ''),
                            'date': source.get('date', '')
                        })
            
            citations.append(citation)
        
        return citations
    
    def _generate_html_citations(self) -> str:
        """Generate HTML formatted citations."""
        html = ['<!DOCTYPE html>']
        html.append('<html><head>')
        html.append('<title>Timeline Citations</title>')
        html.append('<style>')
        html.append('body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }')
        html.append('h2 { color: #333; border-bottom: 1px solid #ccc; padding-bottom: 5px; }')
        html.append('.date { color: #666; font-style: italic; }')
        html.append('ul { margin: 10px 0; }')
        html.append('</style>')
        html.append('</head><body>')
        html.append('<h1>Timeline Event Citations</h1>')
        
        for event in self.events:
            html.append(f"<h2>{event.get('title', 'Untitled')}</h2>")
            html.append(f"<p class='date'>Date: {event.get('date', 'Unknown')}</p>")
            
            if 'sources' in event:
                html.append('<ul>')
                for source in event['sources']:
                    if isinstance(source, dict):
                        title = source.get('title', 'Untitled')
                        url = source.get('url', '#')
                        html.append(f'<li><a href="{url}" target="_blank">{title}</a></li>')
                html.append('</ul>')
        
        html.append('</body></html>')
        return '\n'.join(html)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate various outputs from timeline events',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all              # Generate all outputs
  %(prog)s --index            # Generate timeline index only
  %(prog)s --api              # Generate static API files
  %(prog)s --citations md     # Generate markdown citations
  %(prog)s --stats            # Generate statistics report
        """
    )
    
    parser.add_argument(
        '--events-dir',
        default='timeline_data/events',
        help='Path to events directory'
    )
    
    parser.add_argument(
        '--output-dir',
        default='timeline_data',
        help='Path to output directory'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Generate all outputs'
    )
    
    parser.add_argument(
        '--index',
        action='store_true',
        help='Generate timeline index JSON'
    )
    
    parser.add_argument(
        '--api',
        action='store_true',
        help='Generate static API files'
    )
    
    parser.add_argument(
        '--citations',
        choices=['markdown', 'md', 'json', 'html'],
        help='Generate citations in specified format'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Generate statistics report'
    )
    
    args = parser.parse_args()
    
    # Default to --all if no specific output requested
    if not any([args.all, args.index, args.api, args.citations, args.stats]):
        args.all = True
    
    # Create generator
    generator = TimelineGenerator(args.events_dir, args.output_dir)
    
    print_header("TIMELINE GENERATOR")
    
    # Load events
    generator.load_events()
    
    if not generator.events:
        log_error("No events found!")
        sys.exit(1)
    
    # Generate requested outputs
    try:
        if args.all or args.index:
            generator.generate_index()
        
        if args.all or args.api:
            generator.generate_static_api()
        
        if args.all or args.citations:
            format_map = {'md': 'markdown'}
            fmt = format_map.get(args.citations, args.citations or 'markdown')
            generator.generate_footnotes(fmt)
        
        if args.all or args.stats:
            generator.generate_statistics()
        
        print()
        log_success("Generation complete!")
        
    except Exception as e:
        log_error(f"Generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()