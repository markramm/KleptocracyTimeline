#!/usr/bin/env python3
"""
Fix naming convention issues in timeline events.
Converts underscores to hyphens in both IDs and filenames.
"""

import sys
from pathlib import Path
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import get_event_files, load_yaml_file, save_yaml_file, log_info, log_success, log_error, print_header

def fix_naming_conventions():
    """Fix all naming convention issues."""
    print_header("FIXING NAMING CONVENTIONS")
    
    events_dir = Path("timeline_data/events")
    files_to_fix = []
    
    # Find files that need fixing
    for filepath in get_event_files(events_dir):
        try:
            data = load_yaml_file(filepath)
            if not data or 'id' not in data:
                continue
                
            old_id = data['id']
            # Check if ID contains underscores
            if '_' in old_id:
                files_to_fix.append((filepath, old_id))
        except Exception as e:
            log_error(f"Error checking {filepath}: {e}")
    
    if not files_to_fix:
        log_success("No naming issues found!")
        return
    
    log_info(f"Found {len(files_to_fix)} files with naming issues")
    
    # Fix each file
    for filepath, old_id in files_to_fix:
        try:
            # Load the file
            data = load_yaml_file(filepath)
            
            # Fix the ID (replace underscores with hyphens)
            new_id = old_id.replace('_', '-')
            data['id'] = new_id
            
            # Save with updated ID
            save_yaml_file(filepath, data)
            
            # Rename the file if needed
            old_filename = filepath.name
            expected_filename = f"{str(data['date'])[:10]}--{new_id}.yaml"
            
            if old_filename != expected_filename:
                new_filepath = filepath.parent / expected_filename
                filepath.rename(new_filepath)
                log_success(f"Fixed: {old_filename} → {expected_filename}")
            else:
                log_success(f"Fixed ID in: {old_filename}")
                
        except Exception as e:
            log_error(f"Failed to fix {filepath}: {e}")
    
    log_info("\nNaming convention fixes complete!")
    log_info("Run 'python3 scripts/validate.py' to verify")

if __name__ == "__main__":
    fix_naming_conventions()