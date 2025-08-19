#!/usr/bin/env python3
"""
Properly fix naming convention issues in timeline events.
Converts underscores to hyphens in IDs while preserving correct filename format.
"""

import sys
from pathlib import Path
import yaml
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import get_event_files, load_yaml_file, save_yaml_file, log_info, log_success, log_error, print_header

def extract_date_and_id_from_filename(filename):
    """Extract date and ID from filename."""
    # Pattern: YYYY-MM-DD--rest-of-id.yaml
    match = re.match(r'^(\d{4}-\d{2}-\d{2})--(.+)\.yaml$', filename)
    if match:
        return match.group(1), match.group(2)
    return None, None

def fix_naming_properly():
    """Fix all naming convention issues properly."""
    print_header("FIXING NAMING CONVENTIONS PROPERLY")
    
    events_dir = Path("timeline_data/events")
    fixes_made = 0
    
    # Process all event files
    for filepath in sorted(events_dir.glob("*.yaml")):
        try:
            # Skip hidden files
            if filepath.name.startswith('.'):
                continue
                
            # Extract current date and ID from filename
            file_date, file_id = extract_date_and_id_from_filename(filepath.name)
            if not file_date:
                log_error(f"Cannot parse filename: {filepath.name}")
                continue
            
            # Load the file
            data = load_yaml_file(filepath)
            if not data:
                continue
            
            # Check if ID needs fixing
            needs_id_fix = False
            needs_rename = False
            
            # Get the ID from the file
            current_id = data.get('id', '')
            
            # Fix ID if it contains underscores
            if '_' in current_id:
                new_id = current_id.replace('_', '-')
                data['id'] = new_id
                needs_id_fix = True
            else:
                new_id = current_id
            
            # Check if filename needs fixing
            # The ID part of the filename might have double dates or underscores
            if file_id != new_id:
                needs_rename = True
            
            # If the file_id contains a duplicate date pattern, clean it
            if file_date in file_id:
                # Remove the duplicate date from the ID part
                clean_id = file_id.replace(file_date + '--', '')
                if clean_id != new_id:
                    new_id = clean_id.replace('_', '-')
                    data['id'] = new_id
                    needs_id_fix = True
                needs_rename = True
            
            # Apply fixes if needed
            if needs_id_fix or needs_rename:
                # Save the updated data
                save_yaml_file(filepath, data)
                
                # Rename file if needed
                if needs_rename:
                    new_filename = f"{file_date}--{new_id}.yaml"
                    new_filepath = filepath.parent / new_filename
                    
                    # Only rename if the new path is different
                    if filepath != new_filepath:
                        # Check if target exists
                        if new_filepath.exists():
                            log_error(f"Target already exists: {new_filename}")
                            continue
                        
                        filepath.rename(new_filepath)
                        log_success(f"Fixed: {filepath.name} → {new_filename}")
                    else:
                        log_success(f"Fixed ID in: {filepath.name}")
                else:
                    log_success(f"Fixed ID in: {filepath.name}")
                
                fixes_made += 1
                
        except Exception as e:
            log_error(f"Failed to process {filepath}: {e}")
    
    if fixes_made == 0:
        log_success("No naming issues found!")
    else:
        log_info(f"\nFixed {fixes_made} files")
        log_info("Run 'python3 scripts/validate.py' to verify")

if __name__ == "__main__":
    fix_naming_properly()