#!/usr/bin/env python3
"""
Update RAG data from timeline YAML files
Handles proper conversion and error checking
"""

import yaml
import json
import glob
from pathlib import Path
from datetime import date, datetime
import sys

def convert_to_serializable(obj):
    """Convert Python objects to JSON-serializable format"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj

def load_timeline_events():
    """Load all timeline events from YAML files"""
    events = []
    errors = []
    timeline_dir = Path(__file__).parent.parent / 'timeline_data' / 'events'
    
    yaml_files = list(timeline_dir.glob('*.yaml'))
    print(f"Found {len(yaml_files)} YAML files in {timeline_dir}")
    
    for file_path in yaml_files:
        try:
            with open(file_path, 'r') as f:
                event = yaml.safe_load(f)
                if event:
                    # Convert dates and other non-serializable objects
                    event = convert_to_serializable(event)
                    
                    # Ensure required fields exist
                    if 'id' not in event:
                        event['id'] = file_path.stem
                    if 'date' not in event:
                        event['date'] = 'Unknown'
                    if 'title' not in event:
                        event['title'] = 'Untitled Event'
                    if 'summary' not in event:
                        event['summary'] = ''
                    if 'actors' not in event:
                        event['actors'] = []
                    if 'tags' not in event:
                        event['tags'] = []
                    if 'importance' not in event:
                        event['importance'] = 5
                    if 'sources' not in event:
                        event['sources'] = []
                    
                    events.append(event)
        except Exception as e:
            errors.append(f"Error loading {file_path.name}: {e}")
    
    if errors:
        print(f"\nEncountered {len(errors)} errors:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
    
    return events

def export_to_rag_format(events, output_path='timeline_events.json'):
    """Export events to JSON format for RAG system"""
    rag_dir = Path(__file__).parent
    output_file = rag_dir / output_path
    
    # RAG system expects a list of events directly
    with open(output_file, 'w') as f:
        json.dump(events, f, indent=2, default=str)
    
    print(f"\nExported {len(events)} events to {output_file}")
    return output_file

def verify_rag_data(file_path):
    """Verify the exported data can be loaded by RAG"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print(f"\nVerification successful:")
        print(f"  - Total events: {len(data)}")
        
        # Check for Epstein events
        epstein_count = sum(1 for event in data 
                          if 'epstein' in str(event).lower())
        print(f"  - Epstein-related events: {epstein_count}")
        
        # Sample some events
        if data:
            print(f"\nSample events:")
            for event in data[:3]:
                print(f"  - {event.get('date', 'Unknown')}: {event.get('title', 'Unknown')[:60]}...")
        
        return True
    except Exception as e:
        print(f"\nVerification failed: {e}")
        return False

def main():
    """Main function to update RAG data"""
    print("="*60)
    print("RAG Data Update Tool")
    print("="*60)
    
    # Load events
    print("\n1. Loading timeline events...")
    events = load_timeline_events()
    
    if not events:
        print("ERROR: No events loaded!")
        sys.exit(1)
    
    # Export to RAG format
    print("\n2. Exporting to RAG format...")
    output_file = export_to_rag_format(events)
    
    # Verify the export
    print("\n3. Verifying exported data...")
    if verify_rag_data(output_file):
        print("\n✅ RAG data successfully updated!")
    else:
        print("\n❌ RAG data verification failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()