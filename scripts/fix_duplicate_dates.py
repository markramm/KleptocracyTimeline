#!/usr/bin/env python3
"""
Fix duplicate dates in filenames (from previous fix attempt)
"""

import re
from pathlib import Path

events_dir = Path("timeline_data/events")

for filepath in events_dir.glob("*.yaml"):
    # Pattern: date--date--id.yaml
    match = re.match(r'^(\d{4}-\d{2}-\d{2})--\d{4}-\d{2}-\d{2}--(.+)\.yaml$', filepath.name)
    if match:
        date = match.group(1)
        rest = match.group(2)
        new_name = f"{date}--{rest}.yaml"
        new_path = filepath.parent / new_name
        
        if not new_path.exists():
            filepath.rename(new_path)
            print(f"Fixed: {filepath.name} → {new_name}")
        else:
            print(f"Skipped (target exists): {filepath.name}")

print("\nDone!")