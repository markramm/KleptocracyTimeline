#!/usr/bin/env python3

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'research_monitor'))

from event_validator import EventValidator

def validate_event_file(filepath):
    """Validate an event file and return results"""
    try:
        with open(filepath, 'r') as f:
            event = json.load(f)
        
        is_valid, errors, metadata = EventValidator.validate_event(event)
        
        print(f"Event File: {filepath}")
        print(f"Validation Score: {metadata['validation_score']:.3f}")
        print(f"Is Valid: {is_valid}")
        print(f"Total Errors: {len(errors)}")
        
        if errors:
            print("\nValidation Errors:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
        
        # Get suggestions
        suggestions = EventValidator.suggest_fixes(event, errors)
        if any(suggestions.values()):
            print("\nSuggested Fixes:")
            for category, fixes in suggestions.items():
                if fixes:
                    print(f"  {category.replace('_', ' ').title()}:")
                    for fix in fixes:
                        print(f"    - {fix}")
        
        return metadata['validation_score'], errors, suggestions
        
    except Exception as e:
        print(f"Error validating event: {e}")
        return 0.0, [str(e)], {}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 validate_event.py <event_file_path>")
        sys.exit(1)
    
    event_file = sys.argv[1]
    validate_event_file(event_file)