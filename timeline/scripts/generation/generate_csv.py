#!/usr/bin/env python3
"""Generate CSV export using centralized utilities."""

from pathlib import Path
from utils.events import EventManager
from utils.exporters import CSVExporter, JSONExporter
from utils.cli import (
    create_base_parser, 
    add_output_arguments, 
    add_filter_arguments,
    copy_to_viewer,
    print_statistics
)

def main():
    """Main function."""
    # Setup command-line parser
    parser = create_base_parser(
        'Generate CSV and JSON exports from timeline events'
    )
    add_output_arguments(parser, default_output='timeline_events.csv')
    add_filter_arguments(parser)
    parser.add_argument('--json', action='store_true', 
                       help='Also generate JSON export')
    args = parser.parse_args()
    
    # Initialize event manager
    print("Loading timeline events...")
    manager = EventManager()
    events = manager.load_all_events()
    print(f"Loaded {len(events)} events")
    
    # Apply filters if provided
    if args.date_start and args.date_end:
        events = manager.get_events_by_date_range(args.date_start, args.date_end)
        print(f"Filtered to {len(events)} events by date range")
    if args.tags:
        events = manager.get_events_by_tags(args.tags)
        print(f"Filtered to {len(events)} events by tags")
    if args.actors:
        events = manager.get_events_by_actors(args.actors)
        print(f"Filtered to {len(events)} events by actors")
    
    # Sort events by date
    events = manager.get_sorted_events()
    
    # Generate CSV
    csv_path = Path(args.output)
    print(f"\nGenerating CSV: {csv_path}")
    csv_exporter = CSVExporter(events)
    count = csv_exporter.export(csv_path)
    file_size = csv_path.stat().st_size / 1024  # KB
    print(f"✓ Wrote {count} events to {csv_path} ({file_size:.1f} KB)")
    
    # Generate JSON if requested
    if args.json:
        json_path = csv_path.with_suffix('.json')
        print(f"\nGenerating JSON: {json_path}")
        json_exporter = JSONExporter(events)
        count = json_exporter.export(json_path)
        file_size = json_path.stat().st_size / 1024
        print(f"✓ Wrote {count} events to {json_path} ({file_size:.1f} KB)")
    
    # Copy to viewer directory if specified
    if args.viewer_dir:
        copy_to_viewer(csv_path, args.viewer_dir)
        if args.json:
            copy_to_viewer(json_path, args.viewer_dir)
    
    # Print statistics if not quiet
    if not args.quiet:
        stats = manager.calculate_statistics()
        print_statistics(stats, quiet=args.quiet, verbose=args.verbose)

if __name__ == "__main__":
    main()