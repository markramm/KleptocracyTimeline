#!/usr/bin/env python3
"""Analyze event sources and capture_lane fields using centralized utilities."""

from utils.events import EventManager
from utils.cli import create_base_parser, add_filter_arguments, print_statistics

def main():
    """Main function."""
    # Setup command-line parser
    parser = create_base_parser(
        'Analyze timeline event sources and capture_lane fields'
    )
    add_filter_arguments(parser)
    args = parser.parse_args()
    
    # Initialize event manager
    manager = EventManager()
    events = manager.load_all_events()
    
    # Apply filters if provided
    if args.date_start and args.date_end:
        events = manager.get_events_by_date_range(args.date_start, args.date_end)
    if args.tags:
        events = manager.get_events_by_tags(args.tags)
    if args.actors:
        events = manager.get_events_by_actors(args.actors)
    
    # Calculate statistics
    stats = manager.calculate_statistics()
    
    # Source analysis
    source_stats = stats['source_statistics']
    total = len(events)
    
    print(f"Total events analyzed: {total}")
    print(f"\nSource Analysis:")
    print(f"  • Single source: {source_stats['single_source']} ({source_stats['single_source']*100/total:.1f}%)")
    print(f"  • Multiple sources: {source_stats['multiple_sources']} ({source_stats['multiple_sources']*100/total:.1f}%)")
    print(f"  • No sources: {source_stats['no_sources']} ({source_stats['no_sources']*100/total:.1f}%)")
    print(f"  • Average sources per event: {source_stats['average_sources']:.2f}")
    
    # Capture lane analysis
    missing_capture_lane = len(manager.find_events_missing_field('capture_lane'))
    has_capture_lane = total - missing_capture_lane
    
    print(f"\nCapture Lane Analysis:")
    print(f"  • Missing capture_lane: {missing_capture_lane} ({missing_capture_lane*100/total:.1f}%)")
    print(f"  • Has capture_lane: {has_capture_lane} ({has_capture_lane*100/total:.1f}%)")
    
    # Print additional statistics if verbose
    if args.verbose:
        print_statistics(stats, quiet=args.quiet, verbose=args.verbose)

if __name__ == "__main__":
    main()