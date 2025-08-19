#!/usr/bin/env python3
"""
Fix inconsistent event IDs to match filename format.
"""

import yaml
import sys
from pathlib import Path

def fix_event_ids(events_dir="timeline_data/events"):
    """Fix event IDs to match their filenames."""
    events_path = Path(events_dir)
    fixed_count = 0
    
    for yaml_file in events_path.glob("*.yaml"):
        # Load the event
        with open(yaml_file, 'r', encoding='utf-8') as f:
            try:
                event = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"Error loading {yaml_file}: {e}")
                continue
        
        if not event:
            continue
            
        # Get expected ID from filename
        expected_id = yaml_file.stem
        current_id = event.get('id')
        
        # Fix missing or incorrect ID
        if current_id != expected_id:
            print(f"Fixing {yaml_file.name}: '{current_id}' -> '{expected_id}'")
            event['id'] = expected_id
            
            # Write back the file
            with open(yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(event, f, default_flow_style=False, sort_keys=False, 
                         allow_unicode=True, width=1000)
            
            fixed_count += 1
    
    print(f"Fixed {fixed_count} event IDs")
    return fixed_count

if __name__ == "__main__":
    events_dir = sys.argv[1] if len(sys.argv) > 1 else "timeline_data/events"
    fix_event_ids(events_dir)