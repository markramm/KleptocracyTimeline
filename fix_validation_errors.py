#!/usr/bin/env python3
"""
Fix validation errors in JSON event files.
"""

import json
from pathlib import Path
from timeline_event_manager import TimelineEventManager

def fix_validation_errors():
    """Fix common validation errors in event files."""
    
    manager = TimelineEventManager()
    errors = manager.validate_all_events()
    
    if not errors:
        print("✅ No validation errors found!")
        return 0
    
    print(f"Found {len(errors)} files with validation errors")
    fixed_count = 0
    
    for filename, error_list in errors.items():
        filepath = manager.events_dir / filename
        
        try:
            with open(filepath, 'r') as f:
                event = json.load(f)
            
            fixed = False
            
            for error in error_list:
                # Fix ID date mismatch
                if "ID date mismatch" in error:
                    # Extract the actual date from the error message
                    if "event date is" in error:
                        actual_date = error.split("event date is ")[-1].strip()
                        new_id = manager.generate_id(actual_date, event.get('title', ''))
                        
                        # Update the ID
                        event['id'] = new_id
                        
                        # Rename the file
                        new_filepath = manager.events_dir / f"{new_id}.json"
                        if filepath != new_filepath:
                            print(f"  Renaming {filename} -> {new_id}.json")
                            with open(new_filepath, 'w') as f:
                                json.dump(event, f, indent=2, ensure_ascii=False)
                            filepath.unlink()  # Delete old file
                            fixed = True
                            continue
                
                # Fix missing actors field
                if "Missing required field: actors" in error:
                    event['actors'] = []
                    fixed = True
                    print(f"  Added empty actors field to {filename}")
            
            # Save the fixed event if changes were made
            if fixed and filepath.exists():
                with open(filepath, 'w') as f:
                    json.dump(event, f, indent=2, ensure_ascii=False)
                fixed_count += 1
                
        except Exception as e:
            print(f"  Error processing {filename}: {e}")
    
    print(f"\n✅ Fixed {fixed_count} files")
    
    # Re-validate to check remaining issues
    print("\nRe-validating...")
    errors = manager.validate_all_events()
    if errors:
        print(f"Still {len(errors)} files with errors:")
        for file, errs in list(errors.items())[:5]:
            print(f"  {file}:")
            for err in errs:
                print(f"    - {err}")
    else:
        print("✅ All validation errors fixed!")
    
    return 0

if __name__ == '__main__':
    exit(fix_validation_errors())