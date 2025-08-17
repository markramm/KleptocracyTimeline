#!/usr/bin/env python3
"""
Rename timeline files to use -- as separator between date and description.
Also updates the IDs inside the files to match.
"""

import yaml
import shutil
from pathlib import Path

def rename_timeline_files():
    timeline_dir = Path("timeline_data")
    renames = []
    
    # First pass: collect all renames needed
    for yaml_file in sorted(timeline_dir.glob("*.yaml")):
        # Skip non-timeline files
        if yaml_file.name in ["README.md", "TIMELINE_README.md", "QUALITY_ASSURANCE.md", 
                              "Complete_Annotated_Timeline.md", "Timeline_Generation_Report.md",
                              "index.json", "archive_report.json"]:
            continue
        
        # Skip files that already use -- separator
        if "--" in yaml_file.name:
            continue
            
        # Check if file has the date_description pattern
        if yaml_file.stem.count('_') >= 1 and yaml_file.stem[:10].count('-') == 2:
            # Split on first underscore after date
            parts = yaml_file.stem.split('_', 1)
            if len(parts) == 2 and len(parts[0]) == 10:  # YYYY-MM-DD is 10 chars
                date_part = parts[0]
                desc_part = parts[1]
                new_name = f"{date_part}--{desc_part}.yaml"
                new_path = timeline_dir / new_name
                
                if not new_path.exists():  # Only rename if target doesn't exist
                    renames.append((yaml_file, new_path))
    
    # Execute renames and update IDs
    for old_path, new_path in renames:
        print(f"Renaming: {old_path.name} -> {new_path.name}")
        
        # Load the file
        with open(old_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Update the ID to match new filename
        if data and 'id' in data:
            data['id'] = new_path.stem
            
            # Write to new location with updated ID
            with open(new_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            # Remove old file
            old_path.unlink()
        else:
            # Just rename if no ID field
            shutil.move(str(old_path), str(new_path))
    
    return renames

def update_references():
    """Update any references to old filenames in other files"""
    # Update references in posts
    posts_dir = Path("posts")
    if posts_dir.exists():
        for post_file in posts_dir.rglob("*.md"):
            content = post_file.read_text()
            updated = False
            
            # Replace references to old timeline IDs
            for old_path, new_path in renames:
                old_id = old_path.stem
                new_id = new_path.stem
                if old_id in content:
                    content = content.replace(old_id, new_id)
                    updated = True
            
            if updated:
                post_file.write_text(content)
                print(f"Updated references in: {post_file}")

if __name__ == "__main__":
    print("Renaming timeline files to use -- separator...")
    print("=" * 60)
    
    renames = rename_timeline_files()
    
    if renames:
        print(f"\n✅ Renamed {len(renames)} files")
        print("\nUpdating references in other files...")
        update_references()
        print("\n✅ Complete! New naming convention: YYYY-MM-DD--description.yaml")
    else:
        print("\n✅ No files need renaming - all files already follow the convention")