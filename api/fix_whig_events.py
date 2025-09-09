#!/usr/bin/env python3
"""
Fix WHIG events that are missing required fields
"""
import json
import os
from pathlib import Path

def fix_whig_event(filepath):
    """Fix a single WHIG event file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Check if missing required fields
    needs_fix = False
    
    # Add missing summary field from description if present
    if 'summary' not in data and 'description' in data:
        data['summary'] = data['description']
        needs_fix = True
    
    # Add default actors if missing
    if 'actors' not in data:
        # Determine actors based on event
        if 'whig' in filepath.name.lower():
            data['actors'] = [
                "White House Iraq Group",
                "Dick Cheney",
                "Karl Rove",
                "Condoleezza Rice",
                "Karen Hughes"
            ]
        elif 'osp' in filepath.name.lower():
            data['actors'] = [
                "Office of Special Plans",
                "Douglas Feith",
                "Paul Wolfowitz",
                "Donald Rumsfeld"
            ]
        else:
            data['actors'] = ["Bush Administration"]
        needs_fix = True
    
    # Ensure status field
    if 'status' not in data:
        data['status'] = 'confirmed'
        needs_fix = True
    
    if needs_fix:
        # Save fixed file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    return False

def main():
    events_dir = Path("timeline_data/events")
    
    # Find all potentially broken WHIG/OSP events
    patterns = [
        "2002-*whig*.json",
        "2002-*osp*.json", 
        "2003-*whig*.json",
        "2001-*att*.json",
        "2007-*verizon*.json",
        "2008-*sprint*.json",
        "2003-*nsa*.json"
    ]
    
    files_to_check = []
    for pattern in patterns:
        files_to_check.extend(events_dir.glob(pattern))
    
    fixed_count = 0
    error_count = 0
    
    print(f"Checking {len(files_to_check)} files...")
    
    for filepath in files_to_check:
        try:
            if fix_whig_event(filepath):
                print(f"✅ Fixed: {filepath.name}")
                fixed_count += 1
        except Exception as e:
            print(f"❌ Error with {filepath.name}: {e}")
            error_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Files checked: {len(files_to_check)}")
    print(f"   Files fixed: {fixed_count}")
    print(f"   Errors: {error_count}")

if __name__ == "__main__":
    main()