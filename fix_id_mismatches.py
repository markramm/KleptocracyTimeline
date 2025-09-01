#!/usr/bin/env python3
"""
Fix ID/filename mismatches in timeline YAML files.
The ID field inside each YAML file must match the filename (without .yaml extension).
"""

import yaml
from pathlib import Path
import sys

def fix_id_mismatches():
    """Fix all ID/filename mismatches in the events directory."""
    events_dir = Path('timeline_data/events')
    fixed_count = 0
    errors = []
    
    for yaml_file in events_dir.glob('*.yaml'):
        expected_id = yaml_file.stem  # filename without extension
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                data = yaml.safe_load(content)
            
            if data.get('id') != expected_id:
                print(f"Fixing {yaml_file.name}: '{data.get('id')}' -> '{expected_id}'")
                data['id'] = expected_id
                
                # Write back with preserved formatting
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                
                fixed_count += 1
                
        except Exception as e:
            errors.append(f"Error processing {yaml_file.name}: {e}")
    
    print(f"\n✅ Fixed {fixed_count} ID/filename mismatches")
    
    if errors:
        print("\n❌ Errors encountered:")
        for error in errors:
            print(f"  - {error}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(fix_id_mismatches())