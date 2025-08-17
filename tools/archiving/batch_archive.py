#!/usr/bin/env python3
"""
Batch archive all working URLs from timeline events.
Creates archive.org snapshots and updates events with archive links.
"""

import json
import yaml
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

def save_to_archive_org(url: str, max_retries: int = 3) -> Optional[str]:
    """Submit a URL to archive.org for archiving."""
    save_api = "https://web.archive.org/save/"
    
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            # Submit URL for archiving
            response = requests.get(save_api + url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Get the archived URL from response headers or construct it
                location = response.headers.get('Content-Location', '')
                if location:
                    return f"https://web.archive.org{location}"
                else:
                    # Construct archive URL with today's date
                    date_str = datetime.now().strftime("%Y%m%d")
                    return f"https://web.archive.org/web/{date_str}000000/{url}"
            
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"  Error archiving {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retry
    
    return None

def check_existing_archive(url: str) -> Optional[str]:
    """Check if URL already has an archive.org snapshot."""
    try:
        # Check availability API
        check_url = f"https://archive.org/wayback/available?url={urllib.parse.quote(url)}"
        response = requests.get(check_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('archived_snapshots', {}).get('closest', {}).get('available'):
                return data['archived_snapshots']['closest']['url']
    except:
        pass
    
    return None

def update_event_with_archives(event_file: Path, archive_map: Dict[str, str]):
    """Update an event file with archive links."""
    try:
        with open(event_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return False
        
        updated = False
        
        # Update citations
        citations = data.get('citations', [])
        for i, citation in enumerate(citations):
            if isinstance(citation, str) and citation in archive_map:
                # Convert to dict format with archive
                citations[i] = {
                    'url': citation,
                    'archived': archive_map[citation]
                }
                updated = True
            elif isinstance(citation, dict) and 'url' in citation:
                url = citation['url']
                if url in archive_map and 'archived' not in citation:
                    citation['archived'] = archive_map[url]
                    updated = True
        
        if updated:
            with open(event_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error updating {event_file.name}: {e}")
        return False

def main():
    # Load the link check report
    report_dir = Path(__file__).parents[2] / "timeline_data" / "qa_reports"
    timeline_dir = Path(__file__).parents[2] / "timeline_data" / "events"
    
    # Find most recent link check report
    link_reports = sorted(report_dir.glob("link_check_*.json"), reverse=True)
    if not link_reports:
        print("No link check report found. Run check_all_links.py first.")
        return
    
    with open(link_reports[0], 'r') as f:
        link_report = json.load(f)
    
    working_urls = link_report.get('working_urls', {})
    print(f"Found {len(working_urls)} working URLs to archive")
    
    # Check which URLs already have archives
    print("Checking for existing archives...")
    archive_map = {}
    needs_archiving = []
    
    for url in working_urls.keys():
        existing = check_existing_archive(url)
        if existing:
            archive_map[url] = existing
            print(f"  ✓ Already archived: {url[:50]}...")
        else:
            needs_archiving.append(url)
    
    print(f"\n{len(archive_map)} URLs already archived")
    print(f"{len(needs_archiving)} URLs need archiving")
    
    if needs_archiving:
        print("\nArchiving new URLs (this may take a while)...")
        
        # Archive in batches to avoid rate limiting
        batch_size = 5
        for i in range(0, len(needs_archiving), batch_size):
            batch = needs_archiving[i:i+batch_size]
            print(f"\nBatch {i//batch_size + 1}/{(len(needs_archiving) + batch_size - 1)//batch_size}")
            
            for url in batch:
                print(f"  Archiving: {url[:80]}...")
                archived = save_to_archive_org(url)
                if archived:
                    archive_map[url] = archived
                    print(f"    ✓ Archived to: {archived[:80]}...")
                else:
                    print(f"    ✗ Failed to archive")
                time.sleep(2)  # Rate limiting between requests
    
    # Save archive map
    archive_file = report_dir / f"archive_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(archive_file, 'w', encoding='utf-8') as f:
        json.dump({
            'generated': datetime.now().isoformat(),
            'total_archives': len(archive_map),
            'archives': archive_map
        }, f, indent=2)
    
    print(f"\nArchive map saved to: {archive_file}")
    
    # Update events with archive links
    print("\nUpdating events with archive links...")
    updated_events = 0
    
    for event_file in timeline_dir.glob("*.yaml"):
        if update_event_with_archives(event_file, archive_map):
            updated_events += 1
            print(f"  Updated: {event_file.name}")
    
    print(f"\n=== Archive Summary ===")
    print(f"Total archives available: {len(archive_map)}")
    print(f"Events updated with archives: {updated_events}")
    print(f"Archive map saved to: {archive_file}")

if __name__ == "__main__":
    main()