#!/usr/bin/env python3
"""Fix archive.org URLs that use wildcard format (with asterisk)."""

import os
import re
import yaml
from pathlib import Path

def fix_archive_url(url):
    """Convert wildcard archive.org URL to specific timestamp format."""
    if 'web.archive.org/web/*/' in url:
        # Replace wildcard with a reasonable timestamp
        # Use 20240101000000 as a default timestamp
        return url.replace('/web/*/', '/web/20240101000000/')
    elif 'web.archive.org/web/20240101000000*/' in url:
        # Remove trailing asterisk
        return url.replace('/web/20240101000000*/', '/web/20240101000000/')
    return url

def process_yaml_file(filepath):
    """Process a single YAML file to fix archive URLs."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Find all archive URLs with wildcards
        pattern = r'https://web\.archive\.org/web/[^/]*\*[^/]*/[^\s\'"]+|https://web\.archive\.org/web/\*/[^\s\'"]+'
        matches = re.findall(pattern, content)
        
        if matches:
            print(f"Fixing {filepath.name}:")
            for match in matches:
                fixed = fix_archive_url(match)
                if fixed != match:
                    content = content.replace(match, fixed)
                    print(f"  Fixed: {match[:60]}...")
            
            with open(filepath, 'w') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def main():
    events_dir = Path('events')
    
    if not events_dir.exists():
        print("Error: 'events' directory not found")
        return
    
    fixed_count = 0
    for yaml_file in sorted(events_dir.glob('*.yaml')):
        if process_yaml_file(yaml_file):
            fixed_count += 1
    
    print(f"\nFixed archive URLs in {fixed_count} files")

if __name__ == '__main__':
    main()