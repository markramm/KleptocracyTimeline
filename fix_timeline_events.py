#!/usr/bin/env python3
"""
Systematic Timeline Event Validator and Fixer

Processes timeline events in batches, applies comprehensive validation,
and writes fixed events back to the filesystem.
"""

import os
import json
from typing import List, Dict
from enhanced_event_validator import validate_and_fix_events

def load_events(directory: str) -> List[Dict]:
    """Load all JSON event files from a directory"""
    events = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r') as f:
                    event = json.load(f)
                    events.append(event)
            except json.JSONDecodeError:
                print(f"Error decoding JSON in {filename}")
    return events

def save_events(fixed_events: List[Dict], directory: str):
    """Save fixed events back to filesystem"""
    os.makedirs(directory, exist_ok=True)
    for event in fixed_events:
        filename = f"{event['id']}.json"
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w') as f:
            json.dump(event, f, indent=2)

def main():
    events_dir = '/Users/markr/kleptocracy-timeline/timeline_data/events'
    output_dir = '/Users/markr/kleptocracy-timeline/timeline_data/events'
    
    events = load_events(events_dir)
    
    print(f"Total events loaded: {len(events)}")
    
    # Process events in batches of 100
    batch_size = 100
    for i in range(0, len(events), batch_size):
        batch = events[i:i+batch_size]
        validation_result = validate_and_fix_events(batch)
        
        print(f"\nBatch {i//batch_size + 1} Summary:")
        print(json.dumps(validation_result['summary'], indent=2))
        
        save_events(validation_result['fixed_events'], output_dir)
    
    print("\nValidation and fixing process complete.")

if __name__ == "__main__":
    main()