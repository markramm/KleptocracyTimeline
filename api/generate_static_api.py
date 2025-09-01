#!/usr/bin/env python3
"""
Generate static JSON files for the React viewer app.
These files replace the need for API endpoints.
"""

import json
import yaml
from pathlib import Path
from collections import defaultdict
import datetime

# Configuration
BASE_DIR = Path(__file__).parent.parent
TIMELINE_DIR = BASE_DIR / "timeline_data" / "events"
OUTPUT_DIR = BASE_DIR / "api" / "static_api"

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles date/datetime objects."""
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

def load_timeline_events():
    """Load all timeline events from YAML files"""
    events = []
    
    if TIMELINE_DIR.exists():
        for yaml_file in TIMELINE_DIR.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    event = yaml.safe_load(f)
                    if event and event.get('id'):
                        # Convert dates to strings for JSON serialization
                        if 'date' in event:
                            if hasattr(event['date'], 'isoformat'):
                                event['date'] = event['date'].isoformat()
                            else:
                                event['date'] = str(event['date'])
                        events.append(event)
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")
    
    # Sort by date
    events.sort(key=lambda x: x.get('date', '9999-12-31'))
    return events

def extract_all_tags(events):
    """Extract all unique tags from events"""
    tags = set()
    for event in events:
        if 'tags' in event:
            if isinstance(event['tags'], list):
                tags.update(event['tags'])
            else:
                tags.add(event['tags'])
    return sorted(list(tags))

def extract_all_actors(events):
    """Extract all unique actors from events"""
    actors = set()
    for event in events:
        if 'actors' in event:
            if isinstance(event['actors'], list):
                actors.update(event['actors'])
            else:
                actors.add(event['actors'])
    return sorted(list(actors))

def extract_all_capture_lanes(events):
    """Extract all unique capture lanes from events"""
    capture_lanes = set()
    for event in events:
        if 'capture_lanes' in event:
            if isinstance(event['capture_lanes'], list):
                capture_lanes.update(event['capture_lanes'])
            else:
                capture_lanes.add(event['capture_lanes'])
    return sorted(list(capture_lanes))

def generate_stats(events):
    """Generate statistics from events"""
    events_by_year = defaultdict(int)
    events_by_status = defaultdict(int)
    
    for event in events:
        if 'date' in event:
            year = event['date'][:4]
            events_by_year[year] += 1
        
        status = event.get('status', 'confirmed')
        events_by_status[status] += 1
    
    # Count monitoring events
    monitoring_events = [e for e in events if e.get('monitoring_status')]
    active_monitoring = [e for e in monitoring_events if e.get('monitoring_status') == 'active']
    
    return {
        'total_events': len(events),
        'events_by_year': dict(events_by_year),
        'events_by_status': dict(events_by_status),
        'monitoring_summary': {
            'total': len(monitoring_events),
            'active': len(active_monitoring),
            'dormant': len([e for e in monitoring_events if e.get('monitoring_status') == 'dormant']),
            'completed': len([e for e in monitoring_events if e.get('monitoring_status') == 'completed'])
        },
        'date_range': {
            'start': events[0]['date'] if events else None,
            'end': events[-1]['date'] if events else None
        }
    }

def main():
    """Generate all static API files"""
    print("Generating static API files...")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load events
    events = load_timeline_events()
    print(f"Loaded {len(events)} events")
    
    # Generate timeline.json (main events file)
    timeline_file = OUTPUT_DIR / "timeline.json"
    with open(timeline_file, 'w', encoding='utf-8') as f:
        json.dump({
            'events': events,
            'total': len(events)
        }, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
    print(f"Generated: {timeline_file}")
    
    # Generate tags.json
    tags = extract_all_tags(events)
    tags_file = OUTPUT_DIR / "tags.json"
    with open(tags_file, 'w', encoding='utf-8') as f:
        json.dump({
            'tags': tags,
            'total': len(tags)
        }, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
    print(f"Generated: {tags_file}")
    
    # Generate actors.json
    actors = extract_all_actors(events)
    actors_file = OUTPUT_DIR / "actors.json"
    with open(actors_file, 'w', encoding='utf-8') as f:
        json.dump({
            'actors': actors,
            'total': len(actors)
        }, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
    print(f"Generated: {actors_file}")
    
    # Generate capture_lanes.json
    capture_lanes = extract_all_capture_lanes(events)
    capture_lanes_file = OUTPUT_DIR / "capture_lanes.json"
    with open(capture_lanes_file, 'w', encoding='utf-8') as f:
        json.dump({
            'capture_lanes': capture_lanes,
            'total': len(capture_lanes)
        }, f, indent=2, ensure_ascii=False)
    print(f"Generated: {capture_lanes_file}")
    
    # Generate stats.json
    stats = generate_stats(events)
    stats_file = OUTPUT_DIR / "stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
    print(f"Generated: {stats_file}")
    
    # Generate monitoring.json (events with monitoring status)
    monitoring_events = [e for e in events if e.get('monitoring_status')]
    monitoring_file = OUTPUT_DIR / "monitoring.json"
    with open(monitoring_file, 'w', encoding='utf-8') as f:
        json.dump({
            'monitoring_events': monitoring_events,
            'total': len(monitoring_events)
        }, f, indent=2, ensure_ascii=False)
    print(f"Generated: {monitoring_file}")
    
    print(f"\nSuccess! Generated 6 static API files in {OUTPUT_DIR}")
    print("\nTo use these files:")
    print("1. Serve them with any static web server")
    print("2. Or copy them to your React app's public folder")
    print("3. Update your React app to fetch from /api/static_api/*.json")

if __name__ == '__main__':
    main()
