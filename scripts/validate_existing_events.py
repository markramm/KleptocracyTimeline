#!/usr/bin/env python3
import os
import sys
import json

# Add the research_monitor directory to the Python path
sys.path.append('/Users/markr/kleptocracy-timeline/research_monitor')

from enhanced_event_validator import validate_events_in_directory

def main():
    """
    Validate all existing timeline events and report issues
    
    Usage:
    python validate_existing_events.py [directory_path]
    """
    # Use default directory if not specified
    events_dir = sys.argv[1] if len(sys.argv) > 1 else '/Users/markr/kleptocracy-timeline/timeline_data/events'
    
    print(f"Validating events in: {events_dir}")
    
    # Validate all events
    validation_results = validate_events_in_directory(events_dir)
    
    # Print summary
    print("\n=== Validation Summary ===")
    print(json.dumps(validation_results['summary'], indent=2))
    
    # Detailed error reporting
    if validation_results['errors']:
        print("\n=== Detailed Errors ===")
        for error in validation_results['errors']:
            print(error)
    
    # Option to fix or output problematic events
    print("\n=== Fixing Events ===")
    if 'events' in validation_results:
        # Optionally write corrected events
        output_dir = os.path.join(events_dir, 'validated')
        os.makedirs(output_dir, exist_ok=True)
        
        for event in validation_results['events']:
            # Write fixed event if changed
            output_path = os.path.join(output_dir, f"{event['id']}.json")
            with open(output_path, 'w') as f:
                json.dump(event, f, indent=2)
    
    # Exit with non-zero status if errors found
    sys.exit(1 if validation_results['summary']['invalid_events'] > 0 else 0)

if __name__ == '__main__':
    main()