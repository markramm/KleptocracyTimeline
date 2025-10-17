"""Command-line interface utilities for timeline scripts."""

import argparse
from pathlib import Path
from typing import Optional

def create_base_parser(description: str, add_common: bool = True) -> argparse.ArgumentParser:
    """
    Create base parser with common arguments.
    
    Args:
        description: Parser description
        add_common: Whether to add common arguments
        
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    if add_common:
        add_verbosity_arguments(parser)
    
    return parser

def add_output_arguments(parser: argparse.ArgumentParser, 
                        default_output: str = None,
                        multiple_formats: bool = False) -> None:
    """
    Add common output arguments.
    
    Args:
        parser: ArgumentParser to add arguments to
        default_output: Default output file path
        multiple_formats: Whether to support multiple output formats
    """
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=default_output,
        help='Output file path'
    )
    
    if multiple_formats:
        parser.add_argument(
            '--format', '-f',
            choices=['json', 'csv', 'yaml', 'yaml-minimal'],
            default='json',
            help='Output format (default: json)'
        )
    
    parser.add_argument(
        '--viewer-dir',
        type=str,
        default=None,
        help='Copy output files to viewer directory'
    )

def add_filter_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add common filter arguments.
    
    Args:
        parser: ArgumentParser to add arguments to
    """
    parser.add_argument(
        '--date-start',
        type=str,
        help='Start date for filtering (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--date-end',
        type=str,
        help='End date for filtering (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--tags',
        nargs='+',
        help='Filter by tags'
    )
    
    parser.add_argument(
        '--actors',
        nargs='+',
        help='Filter by actors'
    )
    
    parser.add_argument(
        '--importance',
        choices=['critical', 'high', 'medium', 'low'],
        help='Filter by importance level'
    )
    
    parser.add_argument(
        '--status',
        choices=['ongoing', 'completed', 'planned'],
        help='Filter by status'
    )

def add_verbosity_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add verbosity control arguments.
    
    Args:
        parser: ArgumentParser to add arguments to
    """
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    verbosity_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-essential output'
    )

def add_input_arguments(parser: argparse.ArgumentParser,
                        default_dir: str = "timeline_data/events") -> None:
    """
    Add input source arguments.
    
    Args:
        parser: ArgumentParser to add arguments to
        default_dir: Default events directory
    """
    parser.add_argument(
        '--events-dir',
        type=str,
        default=default_dir,
        help='Directory containing event YAML files'
    )
    
    parser.add_argument(
        '--input-file',
        type=str,
        help='Input file to process (alternative to events-dir)'
    )

def validate_date_format(date_str: str) -> str:
    """
    Validate date string format.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        Validated date string
        
    Raises:
        argparse.ArgumentTypeError: If date format is invalid
    """
    import re
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        raise argparse.ArgumentTypeError(f"Date must be in YYYY-MM-DD format: {date_str}")
    return date_str

def setup_output_path(args: argparse.Namespace, default_name: str) -> Path:
    """
    Setup output file path from arguments.
    
    Args:
        args: Parsed arguments
        default_name: Default output filename
        
    Returns:
        Path object for output file
    """
    if args.output:
        return Path(args.output)
    else:
        return Path(default_name)

def copy_to_viewer(file_path: Path, viewer_dir: str, target_name: Optional[str] = None) -> bool:
    """
    Copy file to viewer public directory.
    
    Args:
        file_path: Source file path
        viewer_dir: Viewer directory path
        target_name: Target filename (defaults to source filename)
        
    Returns:
        True if successful, False otherwise
    """
    import shutil
    
    viewer_path = Path(viewer_dir)
    if not viewer_path.exists():
        print(f"Warning: Viewer directory does not exist: {viewer_dir}")
        return False
    
    public_dir = viewer_path / 'public'
    public_dir.mkdir(exist_ok=True)
    
    target_file = target_name or file_path.name
    dest_path = public_dir / target_file
    
    try:
        shutil.copy(file_path, dest_path)
        print(f"✓ Copied to {dest_path}")
        return True
    except Exception as e:
        print(f"Error copying to viewer: {e}")
        return False

def print_statistics(stats: dict, quiet: bool = False, verbose: bool = False) -> None:
    """
    Print statistics in a consistent format.
    
    Args:
        stats: Statistics dictionary
        quiet: Suppress output
        verbose: Show detailed output
    """
    if quiet:
        return
    
    print("\n" + "=" * 50)
    print("STATISTICS")
    print("=" * 50)
    
    if 'total_events' in stats:
        print(f"Total events: {stats['total_events']}")
    
    if 'date_range' in stats:
        dr = stats['date_range']
        print(f"Date range: {dr.get('start', 'N/A')} to {dr.get('end', 'N/A')}")
    
    if verbose:
        if 'tag_counts' in stats:
            print(f"\nTop 10 tags:")
            for tag, count in stats['tag_counts'].most_common(10):
                print(f"  • {tag}: {count}")
        
        if 'actor_counts' in stats:
            print(f"\nTop 10 actors:")
            for actor, count in stats['actor_counts'].most_common(10):
                print(f"  • {actor}: {count}")
        
        if 'events_by_year' in stats:
            print(f"\nEvents by year (last 5 years):")
            years = sorted(stats['events_by_year'].items(), reverse=True)[:5]
            for year, count in years:
                print(f"  • {year}: {count}")
    
    print("=" * 50)