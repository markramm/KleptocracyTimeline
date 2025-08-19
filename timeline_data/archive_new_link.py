#!/usr/bin/env python3
"""
Archive a single URL or all URLs in a specific event file.
Use this when adding new sources to ensure they're archived immediately.
"""

import sys
import yaml
import requests
import time
from pathlib import Path
from archive_links import archive_url, update_event_with_archive

def archive_event_urls(yaml_file):
    """Archive all URLs in a specific event file."""
    yaml_path = Path(yaml_file)
    if not yaml_path.exists():
        yaml_path = Path('events') / yaml_file
    
    if not yaml_path.exists():
        print(f"Error: File {yaml_file} not found")
        return False
    
    archived_count = 0
    
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if data and 'sources' in data:
            sources = data['sources']
            if isinstance(sources, list):
                for source in sources:
                    if isinstance(source, dict) and 'url' in source:
                        url = source['url']
                        
                        # Skip if already has archive_url
                        if 'archive_url' in source and source['archive_url'].startswith('https://web.archive.org/web/2'):
                            print(f"✓ Already archived: {url[:60]}...")
                            continue
                        
                        # Skip archive.org URLs
                        if 'web.archive.org' in url or 'archive.org' in url:
                            print(f"→ Skipping archive URL: {url[:60]}...")
                            continue
                        
                        print(f"Archiving: {url[:60]}...")
                        result = archive_url(url)
                        
                        if result['success']:
                            archive_url_str = result['archive_url']
                            print(f"  ✓ Success: {archive_url_str[:60]}...")
                            
                            # Update the file immediately
                            if update_event_with_archive(yaml_path, url, archive_url_str):
                                print(f"  ✓ Updated file with archive URL")
                                archived_count += 1
                        else:
                            print(f"  ✗ Failed: {result['error']}")
                        
                        # Rate limiting
                        time.sleep(5)
        
        print(f"\nCompleted: {archived_count} URLs archived for {yaml_path.name}")
        return True
        
    except Exception as e:
        print(f"Error processing {yaml_file}: {e}")
        return False

def archive_single_url(url):
    """Archive a single URL and print the result."""
    if 'web.archive.org' in url or 'archive.org' in url:
        print(f"This is already an archive URL: {url}")
        return
    
    print(f"Archiving: {url}")
    result = archive_url(url)
    
    if result['success']:
        print(f"✓ Success!")
        print(f"Archive URL: {result['archive_url']}")
    else:
        print(f"✗ Failed: {result['error']}")

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Archive single URL:  python3 archive_new_link.py <URL>")
        print("  Archive event file:  python3 archive_new_link.py <event.yaml>")
        print("\nExamples:")
        print("  python3 archive_new_link.py https://example.com/article")
        print("  python3 archive_new_link.py 2025-01-20--cabinet-wealth-450-billion.yaml")
        return
    
    arg = sys.argv[1]
    
    # Check if it's a URL or a file
    if arg.startswith('http://') or arg.startswith('https://'):
        archive_single_url(arg)
    else:
        archive_event_urls(arg)

if __name__ == "__main__":
    main()