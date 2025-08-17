#!/usr/bin/env python3
"""
Fix timeline ID/filename inconsistencies.
Convention: 
- Filenames: YYYY-MM-DD_rest-of-name.yaml
- IDs: Should match filename without .yaml extension
"""

import yaml
from pathlib import Path

def fix_timeline_ids():
    timeline_dir = Path("timeline_data")
    fixes_made = []
    
    for yaml_file in timeline_dir.glob("*.yaml"):
        # Skip non-event files
        if yaml_file.name in ["README.md", "TIMELINE_README.md", "QUALITY_ASSURANCE.md", 
                              "Complete_Annotated_Timeline.md", "Timeline_Generation_Report.md",
                              "index.json", "archive_report.json"]:
            continue
            
        # Expected ID is filename without .yaml
        expected_id = yaml_file.stem
        
        # Load the file
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data or 'id' not in data:
            print(f"Warning: {yaml_file.name} has no ID field")
            continue
            
        current_id = data['id']
        
        # Check if ID matches filename
        if current_id != expected_id:
            print(f"Fixing: {yaml_file.name}")
            print(f"  Old ID: {current_id}")
            print(f"  New ID: {expected_id}")
            
            # Update the ID
            data['id'] = expected_id
            
            # Write back
            with open(yaml_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            fixes_made.append({
                'file': yaml_file.name,
                'old_id': current_id,
                'new_id': expected_id
            })
    
    return fixes_made

if __name__ == "__main__":
    print("Fixing timeline ID/filename inconsistencies...")
    print("=" * 60)
    
    fixes = fix_timeline_ids()
    
    if fixes:
        print(f"\n✅ Fixed {len(fixes)} files")
        for fix in fixes:
            print(f"  - {fix['file']}")
    else:
        print("\n✅ No fixes needed - all IDs match filenames")