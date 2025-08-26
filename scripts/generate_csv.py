#!/usr/bin/env python3
"""Generate CSV file from timeline events for analysis and export."""

import csv
import yaml
import json
from pathlib import Path
from datetime import datetime
import argparse

def load_events():
    """Load all events from YAML files."""
    events_dir = Path(__file__).parent.parent / 'timeline_data' / 'events'
    events = []
    
    for yaml_file in sorted(events_dir.glob('*.yaml')):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                event = yaml.safe_load(f)
                if event:
                    events.append(event)
        except Exception as e:
            print(f"Error loading {yaml_file}: {e}")
    
    # Sort by date (handle both string and date objects)
    def get_date_key(event):
        date_val = event.get('date', '')
        if isinstance(date_val, str):
            return date_val
        elif hasattr(date_val, 'strftime'):
            return date_val.strftime('%Y-%m-%d')
        else:
            return str(date_val)
    
    events.sort(key=get_date_key)
    return events

def format_list_field(items):
    """Format a list field for CSV (semicolon-separated)."""
    if not items:
        return ''
    if isinstance(items, list):
        return '; '.join(str(item) for item in items)
    return str(items)

def format_sources(sources):
    """Format sources for CSV."""
    if not sources:
        return '', ''
    
    urls = []
    outlets = []
    
    for source in sources[:3]:  # Limit to first 3 sources
        if source.get('url'):
            urls.append(source['url'])
        if source.get('outlet'):
            outlets.append(source['outlet'])
    
    return '; '.join(urls), '; '.join(outlets)

def generate_csv(events, output_file):
    """Generate CSV file from events."""
    # Define CSV columns
    fieldnames = [
        'date',
        'year',
        'month',
        'day',
        'title',
        'summary',
        'description',
        'importance',
        'status',
        'location',
        'actors',
        'tags',
        'patterns',
        'capture_type',
        'source_urls',
        'source_outlets',
        'notes',
        'id'
    ]
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for event in events:
            # Parse date components
            date_str = str(event.get('date', ''))
            try:
                if date_str:
                    # Handle both string dates and date objects
                    if isinstance(event.get('date'), str):
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        date_obj = event.get('date')
                    year = date_obj.year
                    month = date_obj.month
                    day = date_obj.day
                else:
                    year = month = day = ''
            except:
                year = date_str[:4] if len(date_str) >= 4 else ''
                month = date_str[5:7] if len(date_str) >= 7 else ''
                day = date_str[8:10] if len(date_str) >= 10 else ''
            
            # Format sources
            source_urls, source_outlets = format_sources(event.get('sources', []))
            
            # Write row
            row = {
                'date': date_str,
                'year': year,
                'month': month,
                'day': day,
                'title': event.get('title', ''),
                'summary': event.get('summary', ''),
                'description': event.get('description', ''),
                'importance': event.get('importance', ''),
                'status': event.get('status', ''),
                'location': event.get('location', ''),
                'actors': format_list_field(event.get('actors', [])),
                'tags': format_list_field(event.get('tags', [])),
                'patterns': format_list_field(event.get('patterns', [])),
                'capture_type': event.get('capture_type', ''),
                'source_urls': source_urls,
                'source_outlets': source_outlets,
                'notes': event.get('notes', ''),
                'id': event.get('id', '')
            }
            
            writer.writerow(row)
    
    return len(events)

def generate_json(events, output_file):
    """Also generate a JSON file for the web app."""
    # Prepare events for JSON (ensure date serialization)
    json_events = []
    for event in events:
        json_event = {}
        for key, value in event.items():
            # Convert date objects to strings
            if hasattr(value, 'strftime'):
                json_event[key] = value.strftime('%Y-%m-%d')
            # Handle lists with date objects
            elif isinstance(value, list):
                json_event[key] = []
                for item in value:
                    if hasattr(item, 'strftime'):
                        json_event[key].append(item.strftime('%Y-%m-%d'))
                    elif isinstance(item, dict):
                        # Handle nested dicts (like sources)
                        clean_item = {}
                        for k, v in item.items():
                            if hasattr(v, 'strftime'):
                                clean_item[k] = v.strftime('%Y-%m-%d')
                            else:
                                clean_item[k] = v
                        json_event[key].append(clean_item)
                    else:
                        json_event[key].append(item)
            else:
                json_event[key] = value
        json_events.append(json_event)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_events, f, indent=2, ensure_ascii=False)
    
    return len(json_events)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate CSV from timeline events')
    parser.add_argument('--output', '-o', 
                       default='timeline_events.csv',
                       help='Output CSV file path')
    parser.add_argument('--json', '-j',
                       action='store_true',
                       help='Also generate JSON file')
    parser.add_argument('--viewer-dir',
                       default=None,
                       help='Copy files to viewer directory')
    
    args = parser.parse_args()
    
    print("Loading timeline events...")
    events = load_events()
    print(f"Loaded {len(events)} events")
    
    # Generate CSV
    output_path = Path(args.output)
    print(f"\nGenerating CSV: {output_path}")
    count = generate_csv(events, output_path)
    print(f"✓ Wrote {count} events to {output_path}")
    
    # Generate JSON if requested
    if args.json:
        json_path = output_path.with_suffix('.json')
        print(f"\nGenerating JSON: {json_path}")
        count = generate_json(events, json_path)
        print(f"✓ Wrote {count} events to {json_path}")
    
    # Copy to viewer directory if specified
    if args.viewer_dir:
        viewer_path = Path(args.viewer_dir)
        if viewer_path.exists():
            # Copy CSV to public directory
            public_dir = viewer_path / 'public'
            public_dir.mkdir(exist_ok=True)
            
            csv_dest = public_dir / 'timeline_events.csv'
            import shutil
            shutil.copy(output_path, csv_dest)
            print(f"\n✓ Copied CSV to {csv_dest}")
            
            if args.json:
                json_dest = public_dir / 'timeline_events.json'
                shutil.copy(output_path.with_suffix('.json'), json_dest)
                print(f"✓ Copied JSON to {json_dest}")
    
    # Print statistics
    print("\n" + "=" * 50)
    print("CSV GENERATION COMPLETE")
    print("=" * 50)
    print(f"Total events: {len(events)}")
    print(f"Date range: {events[0].get('date')} to {events[-1].get('date')}")
    print(f"Output file: {output_path.absolute()}")
    print("\nThe CSV file can be used for:")
    print("  • Data analysis in Excel/Google Sheets")
    print("  • Statistical analysis in R/Python")
    print("  • Visualization in Tableau/PowerBI")
    print("  • Database import")

if __name__ == "__main__":
    main()