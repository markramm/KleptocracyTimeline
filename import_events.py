#!/usr/bin/env python3
"""
Batch import tool for timeline events.
Converts structured text or CSV data into properly formatted YAML events.
"""

import yaml
import csv
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import re

def parse_text_format(text: str) -> List[Dict]:
    """
    Parse a simple text format for batch event creation.
    
    Format:
    ---
    Date: YYYY-MM-DD
    Title: Event title
    Summary: Event summary
    Importance: 1-10
    Actors: Person 1, Person 2
    Tags: tag1, tag2, tag3
    Source: Title | URL | Outlet | Date
    ---
    """
    events = []
    current_event = {}
    sources = []
    
    for line in text.strip().split('\n'):
        line = line.strip()
        
        if line == '---':
            if current_event:
                if sources:
                    current_event['sources'] = sources
                events.append(current_event)
                current_event = {}
                sources = []
            continue
        
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'date':
                current_event['date'] = value
            elif key == 'title':
                current_event['title'] = value
            elif key == 'summary':
                current_event['summary'] = value
            elif key == 'importance':
                current_event['importance'] = int(value)
            elif key == 'actors':
                current_event['actors'] = [a.strip() for a in value.split(',')]
            elif key == 'tags':
                current_event['tags'] = [t.strip() for t in value.split(',')]
            elif key == 'status':
                current_event['status'] = value
            elif key == 'source':
                # Parse source format: Title | URL | Outlet | Date
                parts = value.split('|')
                if len(parts) >= 3:
                    source = {
                        'title': parts[0].strip(),
                        'url': parts[1].strip(),
                        'outlet': parts[2].strip()
                    }
                    if len(parts) > 3:
                        source['date'] = parts[3].strip()
                    sources.append(source)
    
    # Don't forget the last event
    if current_event:
        if sources:
            current_event['sources'] = sources
        events.append(current_event)
    
    return events

def parse_csv_format(csv_path: str) -> List[Dict]:
    """
    Parse CSV file with event data.
    
    Expected columns:
    date, title, summary, importance, actors, tags, status, source_title, source_url, source_outlet, source_date
    """
    events = []
    current_event = None
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Check if this is a new event or additional source for existing event
            if row.get('date') and row.get('title'):
                # Save previous event if exists
                if current_event:
                    events.append(current_event)
                
                # Start new event
                current_event = {
                    'date': row['date'].strip(),
                    'title': row['title'].strip(),
                    'summary': row.get('summary', '').strip(),
                    'importance': int(row.get('importance', 5)),
                    'actors': [a.strip() for a in row.get('actors', '').split(',') if a.strip()],
                    'tags': [t.strip() for t in row.get('tags', '').split(',') if t.strip()],
                    'status': row.get('status', 'confirmed').strip(),
                    'sources': []
                }
            
            # Add source if provided
            if current_event and row.get('source_title'):
                source = {
                    'title': row['source_title'].strip(),
                    'url': row.get('source_url', '').strip(),
                    'outlet': row.get('source_outlet', '').strip(),
                    'date': row.get('source_date', '').strip()
                }
                current_event['sources'].append(source)
    
    # Don't forget the last event
    if current_event:
        events.append(current_event)
    
    return events

def generate_id(date: str, title: str) -> str:
    """Generate event ID from date and title."""
    # Sanitize title for ID
    title_part = re.sub(r'[^\w\s-]', '', title.lower())
    title_part = re.sub(r'[-\s]+', '-', title_part)[:50].strip('-')
    return f"{date}--{title_part}"

def validate_events(events: List[Dict]) -> tuple[List[Dict], List[str]]:
    """Validate and fix events, return (valid_events, errors)."""
    valid_events = []
    errors = []
    
    for i, event in enumerate(events):
        event_errors = []
        
        # Add generated ID if missing
        if 'id' not in event:
            event['id'] = generate_id(event.get('date', ''), event.get('title', ''))
        
        # Validate required fields
        required = ['date', 'title', 'summary', 'importance']
        for field in required:
            if field not in event or not event[field]:
                event_errors.append(f"Event {i+1}: Missing {field}")
        
        # Validate date format
        if 'date' in event:
            try:
                datetime.strptime(event['date'], '%Y-%m-%d')
            except:
                event_errors.append(f"Event {i+1}: Invalid date format: {event['date']}")
        
        # Set defaults
        event.setdefault('actors', [])
        event.setdefault('tags', [])
        event.setdefault('status', 'confirmed')
        event.setdefault('sources', [])
        
        # Validate importance
        if 'importance' in event:
            try:
                event['importance'] = int(event['importance'])
                if not 1 <= event['importance'] <= 10:
                    event_errors.append(f"Event {i+1}: Importance must be 1-10")
            except:
                event_errors.append(f"Event {i+1}: Invalid importance value")
        
        if event_errors:
            errors.extend(event_errors)
        else:
            valid_events.append(event)
    
    return valid_events, errors

def save_events(events: List[Dict], output_dir: str = "timeline_data/events", dry_run: bool = False):
    """Save events to YAML files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    saved = []
    skipped = []
    
    for event in events:
        filename = f"{event['id']}.yaml"
        filepath = output_path / filename
        
        if filepath.exists():
            skipped.append(filename)
            print(f"⚠️  Skipping existing file: {filename}")
            continue
        
        if not dry_run:
            with open(filepath, 'w') as f:
                yaml.dump(event, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        saved.append(filename)
        print(f"✅ {'Would save' if dry_run else 'Saved'}: {filename}")
    
    return saved, skipped

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch import timeline events')
    parser.add_argument('input', help='Input file (CSV or text format) or "-" for stdin')
    parser.add_argument('--format', choices=['csv', 'text', 'auto'], default='auto',
                       help='Input format (default: auto-detect)')
    parser.add_argument('--output-dir', default='timeline_data/events',
                       help='Output directory for YAML files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview without saving')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate, don\'t save')
    
    args = parser.parse_args()
    
    # Read input
    if args.input == '-':
        content = sys.stdin.read()
        if args.format == 'csv':
            print("❌ CSV format requires a file path, not stdin")
            return 1
        events = parse_text_format(content)
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ File not found: {args.input}")
            return 1
        
        # Auto-detect format
        if args.format == 'auto':
            if input_path.suffix.lower() == '.csv':
                args.format = 'csv'
            else:
                args.format = 'text'
        
        # Parse input
        if args.format == 'csv':
            events = parse_csv_format(args.input)
        else:
            with open(args.input, 'r') as f:
                events = parse_text_format(f.read())
    
    print(f"📥 Parsed {len(events)} events")
    
    # Validate events
    valid_events, errors = validate_events(events)
    
    if errors:
        print("\n❌ Validation errors:")
        for error in errors:
            print(f"  - {error}")
        
        if not valid_events:
            print("\nNo valid events to import")
            return 1
        
        print(f"\n⚠️  {len(valid_events)} valid events out of {len(events)}")
    else:
        print(f"✅ All {len(valid_events)} events validated")
    
    if args.validate_only:
        return 0 if not errors else 1
    
    # Save events
    print(f"\n💾 Saving events to {args.output_dir}")
    saved, skipped = save_events(valid_events, args.output_dir, args.dry_run)
    
    print(f"\n📊 Summary:")
    print(f"  Saved: {len(saved)}")
    print(f"  Skipped (existing): {len(skipped)}")
    
    if saved and not args.dry_run:
        print("\n✅ Import complete!")
        print("\nNext steps:")
        print("1. Run: ./validate_new_events.sh")
        print("2. Run: python3 api/generate_static_api.py")
        print("3. Update RAG: cd rag && python3 update_rag_index.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())