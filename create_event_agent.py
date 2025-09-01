#!/usr/bin/env python3
"""
Agent-friendly event creation tool for the Kleptocracy Timeline.
Can be called programmatically or via command line with all parameters.
"""

import yaml
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import re

def sanitize_id(text: str) -> str:
    """Convert text to valid ID format."""
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')[:50]

def generate_id(date: str, title: str) -> str:
    """Generate event ID from date and title."""
    title_part = sanitize_id(title)
    return f"{date}--{title_part}"

def validate_date(date_str: str) -> bool:
    """Validate date format."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_event(event: Dict) -> List[str]:
    """Validate event structure and return any errors."""
    errors = []
    
    # Required fields
    required = ['id', 'date', 'title', 'summary', 'importance', 'actors', 'tags', 'sources']
    for field in required:
        if field not in event:
            errors.append(f"Missing required field: {field}")
        elif field in ['actors', 'tags', 'sources'] and not event[field]:
            errors.append(f"Field '{field}' cannot be empty")
    
    # Validate date
    if 'date' in event and not validate_date(event['date']):
        errors.append(f"Invalid date format: {event['date']} (use YYYY-MM-DD)")
    
    # Validate importance
    if 'importance' in event:
        if not isinstance(event['importance'], int) or not 1 <= event['importance'] <= 10:
            errors.append(f"Importance must be integer 1-10, got: {event['importance']}")
    
    # Validate status
    valid_statuses = ['confirmed', 'reported', 'developing', 'disputed']
    if 'status' in event and event['status'] not in valid_statuses:
        errors.append(f"Invalid status: {event['status']} (must be one of: {', '.join(valid_statuses)})")
    
    # Validate sources structure
    if 'sources' in event:
        for i, source in enumerate(event['sources']):
            if not isinstance(source, dict):
                errors.append(f"Source {i+1} must be a dictionary")
            elif not source.get('title') or not source.get('url') or not source.get('outlet'):
                errors.append(f"Source {i+1} missing required fields (title, url, outlet)")
    
    return errors

def create_event(
    date: str,
    title: str,
    summary: str,
    importance: int,
    actors: List[str],
    tags: List[str],
    sources: List[Dict],
    status: str = 'confirmed',
    notes: Optional[str] = None,
    event_id: Optional[str] = None
) -> Dict:
    """
    Create an event dictionary with validation.
    
    Args:
        date: Event date in YYYY-MM-DD format
        title: Event title (concise, <15 words recommended)
        summary: Event summary/description
        importance: Importance rating 1-10
        actors: List of people/organizations involved
        tags: List of tags/categories
        sources: List of source dictionaries with keys: title, url, outlet, date
        status: Event status (confirmed/reported/developing/disputed)
        notes: Optional additional notes
        event_id: Optional custom ID (auto-generated if not provided)
    
    Returns:
        Dict: Event dictionary ready for YAML serialization
    
    Raises:
        ValueError: If validation fails
    """
    # Generate ID if not provided
    if not event_id:
        event_id = generate_id(date, title)
    
    # Build event
    event = {
        'id': event_id,
        'date': date,
        'importance': importance,
        'title': title,
        'summary': summary,
        'actors': actors,
        'tags': tags,
        'status': status,
        'sources': sources
    }
    
    if notes:
        event['notes'] = notes
    
    # Validate
    errors = validate_event(event)
    if errors:
        raise ValueError(f"Event validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return event

def save_event(event: Dict, output_dir: str = "timeline_data/events", overwrite: bool = False) -> Path:
    """
    Save event to YAML file.
    
    Args:
        event: Event dictionary
        output_dir: Directory to save events
        overwrite: Whether to overwrite existing files
    
    Returns:
        Path: Path to saved file
    
    Raises:
        FileExistsError: If file exists and overwrite=False
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filename = f"{event['id']}.yaml"
    filepath = output_path / filename
    
    if filepath.exists() and not overwrite:
        raise FileExistsError(f"Event file already exists: {filepath}")
    
    with open(filepath, 'w') as f:
        yaml.dump(event, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    return filepath

def main():
    """Command-line interface for agent use."""
    parser = argparse.ArgumentParser(
        description='Create timeline events programmatically',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create event with minimal info (will fail validation without sources)
  %(prog)s --date 2025-01-01 --title "Example Event" --summary "Something happened" --importance 5
  
  # Create complete event via JSON
  %(prog)s --json '{"date": "2025-01-01", "title": "Example", ...}'
  
  # Create from JSON file
  %(prog)s --json-file event.json
  
  # Pipe JSON from another command
  echo '{"date": "2025-01-01", ...}' | %(prog)s --json -
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('--json', metavar='JSON', 
                            help='Complete event as JSON string (use "-" for stdin)')
    input_group.add_argument('--json-file', metavar='FILE',
                            help='Read event from JSON file')
    
    # Individual fields (used if not providing JSON)
    parser.add_argument('--date', help='Event date (YYYY-MM-DD)')
    parser.add_argument('--title', help='Event title')
    parser.add_argument('--summary', help='Event summary')
    parser.add_argument('--importance', type=int, help='Importance (1-10)')
    parser.add_argument('--actors', nargs='+', help='List of actors')
    parser.add_argument('--tags', nargs='+', help='List of tags')
    parser.add_argument('--status', default='confirmed', 
                       choices=['confirmed', 'reported', 'developing', 'disputed'],
                       help='Event status')
    parser.add_argument('--notes', help='Optional notes')
    parser.add_argument('--id', help='Custom event ID (auto-generated if not provided)')
    
    # Source arguments (can be repeated)
    parser.add_argument('--source', action='append', metavar='JSON',
                       help='Source as JSON dict (can be repeated)')
    
    # Output options
    parser.add_argument('--output-dir', default='timeline_data/events',
                       help='Output directory (default: timeline_data/events)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Validate and print, don\'t save')
    parser.add_argument('--overwrite', action='store_true',
                       help='Overwrite existing files')
    parser.add_argument('--output-format', choices=['yaml', 'json'], default='yaml',
                       help='Output format for dry-run')
    
    args = parser.parse_args()
    
    try:
        # Parse event from JSON if provided
        if args.json:
            if args.json == '-':
                event_data = json.load(sys.stdin)
            else:
                event_data = json.loads(args.json)
        elif args.json_file:
            with open(args.json_file, 'r') as f:
                event_data = json.load(f)
        else:
            # Build from individual arguments
            if not all([args.date, args.title, args.summary, args.importance]):
                parser.error("Must provide either --json or all required fields (date, title, summary, importance)")
            
            # Parse sources
            sources = []
            if args.source:
                for source_json in args.source:
                    sources.append(json.loads(source_json))
            
            event_data = {
                'date': args.date,
                'title': args.title,
                'summary': args.summary,
                'importance': args.importance,
                'actors': args.actors or [],
                'tags': args.tags or [],
                'sources': sources,
                'status': args.status
            }
            
            if args.notes:
                event_data['notes'] = args.notes
            if args.id:
                event_data['event_id'] = args.id
        
        # Create event with validation
        event = create_event(
            date=event_data['date'],
            title=event_data['title'],
            summary=event_data['summary'],
            importance=event_data['importance'],
            actors=event_data.get('actors', []),
            tags=event_data.get('tags', []),
            sources=event_data.get('sources', []),
            status=event_data.get('status', 'confirmed'),
            notes=event_data.get('notes'),
            event_id=event_data.get('event_id') or event_data.get('id')
        )
        
        if args.dry_run:
            # Output without saving
            if args.output_format == 'json':
                print(json.dumps(event, indent=2, default=str))
            else:
                print(yaml.dump(event, default_flow_style=False, allow_unicode=True))
            print(f"\n# Would save to: {args.output_dir}/{event['id']}.yaml", file=sys.stderr)
            return 0
        
        # Save event
        filepath = save_event(event, args.output_dir, args.overwrite)
        
        # Output result as JSON for agent parsing
        result = {
            'success': True,
            'event_id': event['id'],
            'filepath': str(filepath),
            'message': f"Event saved successfully"
        }
        print(json.dumps(result))
        
        return 0
        
    except (ValueError, FileExistsError) as e:
        # Output error as JSON for agent parsing
        error = {
            'success': False,
            'error': str(e)
        }
        print(json.dumps(error), file=sys.stderr)
        return 1
    except Exception as e:
        error = {
            'success': False,
            'error': f"Unexpected error: {e}"
        }
        print(json.dumps(error), file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())