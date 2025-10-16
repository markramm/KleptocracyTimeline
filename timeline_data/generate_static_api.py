#!/usr/bin/env python3
"""
Generate static API JSON files for the timeline viewer
"""

import json
import yaml
import os
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, date
import decimal

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    elif hasattr(obj, '__str__'):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def get_sort_date(event):
    """Get sortable date from event, handling both string and date objects"""
    event_date = event.get('date', '')
    if isinstance(event_date, date):
        return event_date.isoformat()
    elif isinstance(event_date, str):
        return event_date
    else:
        return str(event_date)

def main():
    # Handle running from either timeline_data or root directory
    if Path('timeline_data/events').exists():
        events_dir = Path('timeline_data/events')
        output_dir = Path('viewer/public/api')
    else:
        events_dir = Path('events')
        output_dir = Path('../viewer/public/api')
    
    # Ensure the output directory exists
    try:
        output_dir.mkdir(exist_ok=True, parents=True)
        print(f'📁 Output directory: {output_dir.absolute()}')
    except Exception as e:
        print(f'❌ Failed to create output directory: {e}')
        return 1

    # Load all events
    events = []
    all_tags = set()
    all_actors = set()
    all_capture_lanes = set()

    # Support both JSON and YAML formats (prioritize JSON)
    for event_file in list(events_dir.glob('*.json')) + list(events_dir.glob('*.yaml')):
        try:
            with open(event_file, 'r') as f:
                if event_file.suffix == '.json':
                    event = json.load(f)
                else:
                    event = yaml.safe_load(f)
                if event:
                    # Add ID from filename if not present
                    if 'id' not in event:
                        event['id'] = event_file.stem
                    
                    # Convert all date objects to strings recursively
                    def convert_dates(obj):
                        if isinstance(obj, dict):
                            return {k: convert_dates(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_dates(v) for v in obj]
                        elif isinstance(obj, (date, datetime)):
                            return obj.isoformat()
                        return obj
                    
                    event = convert_dates(event)
                    events.append(event)
                    
                    # Collect metadata
                    if event.get('tags'):
                        all_tags.update(event['tags'])
                    if event.get('actors'):
                        # Handle both string actors and structured actor objects
                        actors = event['actors']
                        if isinstance(actors, list):
                            for actor in actors:
                                if isinstance(actor, str):
                                    all_actors.add(actor)
                                elif isinstance(actor, dict) and 'name' in actor:
                                    all_actors.add(actor['name'])
                        elif isinstance(actors, str):
                            all_actors.add(actors)
                    if event.get('capture_lanes'):
                        all_capture_lanes.update(event['capture_lanes'])
        except Exception as e:
            print(f'Error loading {event_file}: {e}')

    # Sort events by date
    events.sort(key=get_sort_date)

    # Generate timeline.json
    with open(output_dir / 'timeline.json', 'w') as f:
        json.dump({'events': events}, f, indent=2, default=json_serial)

    # Generate tags.json
    with open(output_dir / 'tags.json', 'w') as f:
        json.dump({'tags': sorted(list(all_tags))}, f, indent=2)

    # Generate actors.json
    with open(output_dir / 'actors.json', 'w') as f:
        json.dump({'actors': sorted(list(all_actors))}, f, indent=2)

    # Generate capture_lanes.json
    capture_lanes_data = {
        'capture_lanes': [
            'Executive Power & Emergency Authority',
            'Judicial Capture & Corruption',
            'Financial Corruption & Kleptocracy',
            'Foreign Influence Operations',
            'Federal Workforce Capture',
            'Corporate Capture & Regulatory Breakdown',
            'Law Enforcement Weaponization',
            'Election System Attack',
            'Information & Media Control',
            'Constitutional & Democratic Breakdown',
            'Epstein Network & Kompromat',
            'Immigration & Border Militarization',
            'International Democracy Impact'
        ]
    }
    with open(output_dir / 'capture_lanes.json', 'w') as f:
        json.dump(capture_lanes_data, f, indent=2)

    # Generate stats.json
    stats = {
        'total_events': len(events),
        'years_covered': len(set(get_sort_date(e)[:4] for e in events if e.get('date'))),
        'total_sources': sum(len(e.get('sources', [])) for e in events),
        'events_by_year': {},
        'events_by_importance': {}
    }

    # Count events by year
    year_counts = defaultdict(int)
    importance_counts = defaultdict(int)
    
    for event in events:
        if event.get('date'):
            year = get_sort_date(event)[:4]
            year_counts[year] += 1
        if event.get('importance'):
            importance_counts[str(event['importance'])] += 1
    
    stats['events_by_year'] = dict(year_counts)
    stats['events_by_importance'] = dict(importance_counts)

    with open(output_dir / 'stats.json', 'w') as f:
        json.dump(stats, f, indent=2, default=json_serial)

    print(f'✅ Generated static API data:')
    print(f'  - {len(events)} events')
    print(f'  - {len(all_tags)} unique tags')
    print(f'  - {len(all_actors)} unique actors')
    print(f'  - 13 capture lanes')
    print(f'  - Files saved to: {output_dir.absolute()}')
    
    return 0  # Success

if __name__ == '__main__':
    result = main()
    if result:
        sys.exit(result)