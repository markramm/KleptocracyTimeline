#!/usr/bin/env python3
"""
Generate CSV and JSON exports of timeline events.
"""

import csv
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import get_event_files, load_event


def load_events(events_dir):
    """Load all timeline events from event files (.yaml, .yml, .md, .json)."""
    events = []

    for filepath in get_event_files(events_dir):
        event = load_event(filepath)
        if event:
            events.append(event)

    return events

def generate_csv(events, output_file):
    """Generate CSV export of events."""
    if not events:
        print("No events to export")
        return
    
    # Define CSV columns
    fieldnames = [
        'id', 'date', 'title', 'summary', 'importance', 
        'status', 'actors', 'tags', 'sources'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for event in events:
            # Convert date to string if it's a date object
            date_val = event.get('date', '')
            if hasattr(date_val, 'isoformat'):
                date_val = date_val.isoformat()

            # Helper to safely convert list items to strings
            def to_string_list(items):
                """Convert list items to strings, handling dicts and other types."""
                if not items:
                    return []
                result = []
                for item in items:
                    if isinstance(item, str):
                        result.append(item)
                    elif isinstance(item, dict):
                        # For dicts, use the 'name' field if available, else JSON
                        result.append(item.get('name', json.dumps(item)))
                    else:
                        result.append(str(item))
                return result

            row = {
                'id': event.get('id', ''),
                'date': date_val,
                'title': event.get('title', ''),
                'summary': event.get('summary', ''),
                'importance': event.get('importance', ''),
                'status': event.get('status', 'confirmed'),
                'actors': '|'.join(to_string_list(event.get('actors', []))),
                'tags': '|'.join(to_string_list(event.get('tags', []))),
                'sources': json.dumps(event.get('sources', []), default=str)
            }
            writer.writerow(row)
    
    print(f"✅ CSV exported to {output_file}")

def generate_json(events, output_file):
    """Generate JSON export of events."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, default=str)
    
    print(f"✅ JSON exported to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate CSV and JSON exports of timeline events')
    parser.add_argument('--events-dir', default='data/events', 
                        help='Directory containing event YAML files')
    parser.add_argument('--viewer-dir', default='viewer',
                        help='Viewer directory for output files')
    parser.add_argument('--json', action='store_true',
                        help='Also generate JSON export')
    
    args = parser.parse_args()
    
    # Load events
    events = load_events(args.events_dir)
    print(f"Loaded {len(events)} events")
    
    # Sort by date (handle both string and date objects)
    def get_date_key(event):
        date_val = event.get('date', '')
        if hasattr(date_val, 'isoformat'):
            return date_val.isoformat()
        return str(date_val)
    
    events.sort(key=get_date_key)
    
    # Generate CSV
    csv_output = Path(args.viewer_dir) / 'public' / 'timeline_events.csv'
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    generate_csv(events, csv_output)
    
    # Generate JSON if requested
    if args.json:
        json_output = Path(args.viewer_dir) / 'public' / 'timeline_events.json'
        generate_json(events, json_output)

if __name__ == '__main__':
    main()