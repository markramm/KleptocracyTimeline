#!/usr/bin/env python3
"""
Archive all working links in timeline events to the Wayback Machine.
Runs in background and tracks progress.
"""

import yaml
import json
import requests
import time
from pathlib import Path
from datetime import datetime
import sys
import os

def archive_url(url):
    """Submit a URL to the Wayback Machine for archiving."""
    try:
        # Submit to Wayback Machine Save API
        save_api = f"https://web.archive.org/save/{url}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Kleptocracy Timeline Archiver)'
        }
        
        response = requests.get(save_api, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Get the archived URL from response headers
            if 'Content-Location' in response.headers:
                archived_url = f"https://web.archive.org{response.headers['Content-Location']}"
                return {'success': True, 'archive_url': archived_url}
            else:
                return {'success': True, 'archive_url': f"https://web.archive.org/web/*/{url}"}
        else:
            return {'success': False, 'error': f"Status {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def load_progress():
    """Load archiving progress from file."""
    progress_file = Path('archive_progress.json')
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {
        'archived_urls': {},
        'failed_urls': {},
        'last_run': None,
        'total_processed': 0,
        'total_success': 0,
        'total_failed': 0
    }

def save_progress(progress):
    """Save archiving progress to file."""
    with open('archive_progress.json', 'w') as f:
        json.dump(progress, f, indent=2, default=str)

def extract_urls_from_events():
    """Extract all unique URLs from timeline events."""
    events_dir = Path('events')
    all_urls = set()
    url_to_files = {}
    
    for yaml_file in events_dir.glob('*.yaml'):
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
                if data and 'sources' in data:
                    sources = data['sources']
                    if isinstance(sources, list):
                        for source in sources:
                            if isinstance(source, dict) and 'url' in source:
                                url = source['url']
                                all_urls.add(url)
                                if url not in url_to_files:
                                    url_to_files[url] = []
                                url_to_files[url].append(yaml_file.name)
        except Exception as e:
            print(f"Error reading {yaml_file}: {e}", file=sys.stderr)
    
    return all_urls, url_to_files

def update_event_with_archive(yaml_file, url, archive_url):
    """Update a YAML file with archive URL for a source."""
    try:
        with open(yaml_file, 'r') as f:
            content = f.read()
            data = yaml.safe_load(content)
        
        if data and 'sources' in data:
            sources = data['sources']
            if isinstance(sources, list):
                modified = False
                for source in sources:
                    if isinstance(source, dict) and source.get('url') == url:
                        if 'archive_url' not in source or not source['archive_url'].startswith('https://web.archive.org/web/2'):
                            source['archive_url'] = archive_url
                            modified = True
                
                if modified:
                    # Write back with minimal changes to preserve formatting
                    with open(yaml_file, 'w') as f:
                        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                    return True
    except Exception as e:
        print(f"Error updating {yaml_file}: {e}", file=sys.stderr)
    return False

def main():
    """Main archiving loop."""
    print("Starting Timeline Link Archiver...")
    print("=" * 50)
    
    # Load previous progress
    progress = load_progress()
    
    # Extract all URLs
    all_urls, url_to_files = extract_urls_from_events()
    
    # Filter out already processed URLs
    urls_to_archive = []
    for url in all_urls:
        if url not in progress['archived_urls'] and url not in progress['failed_urls']:
            urls_to_archive.append(url)
        elif url in progress['failed_urls']:
            # Retry failed URLs after 24 hours
            last_attempt = progress['failed_urls'][url].get('last_attempt')
            if last_attempt:
                last_time = datetime.fromisoformat(last_attempt)
                if (datetime.now() - last_time).days >= 1:
                    urls_to_archive.append(url)
    
    print(f"Total unique URLs found: {len(all_urls)}")
    print(f"Already archived: {len(progress['archived_urls'])}")
    print(f"Failed (to retry): {len([u for u in urls_to_archive if u in progress['failed_urls']])}")
    print(f"New URLs to archive: {len([u for u in urls_to_archive if u not in progress['failed_urls']])}")
    print(f"Total to process: {len(urls_to_archive)}")
    print("=" * 50)
    
    if not urls_to_archive:
        print("No URLs to archive. All links are already processed!")
        return
    
    # Archive URLs with rate limiting
    for i, url in enumerate(urls_to_archive, 1):
        print(f"\n[{i}/{len(urls_to_archive)}] Archiving: {url[:80]}...")
        
        # Skip archive.org URLs
        if 'web.archive.org' in url or 'archive.org' in url:
            print("  → Skipping (already an archive URL)")
            progress['archived_urls'][url] = {
                'archive_url': url,
                'timestamp': datetime.now().isoformat(),
                'is_archive': True
            }
            continue
        
        # Archive the URL
        result = archive_url(url)
        
        if result['success']:
            archive_url_str = result['archive_url']
            print(f"  ✓ Archived: {archive_url_str[:80]}...")
            
            # Update progress
            progress['archived_urls'][url] = {
                'archive_url': archive_url_str,
                'timestamp': datetime.now().isoformat()
            }
            progress['total_success'] += 1
            
            # Update YAML files with archive URL
            if url in url_to_files:
                for yaml_file in url_to_files[url]:
                    yaml_path = Path('events') / yaml_file
                    if update_event_with_archive(yaml_path, url, archive_url_str):
                        print(f"  ✓ Updated: {yaml_file}")
            
        else:
            print(f"  ✗ Failed: {result['error']}")
            
            # Track failure
            if url not in progress['failed_urls']:
                progress['failed_urls'][url] = {'attempts': 0}
            
            progress['failed_urls'][url]['attempts'] += 1
            progress['failed_urls'][url]['last_attempt'] = datetime.now().isoformat()
            progress['failed_urls'][url]['last_error'] = result['error']
            progress['total_failed'] += 1
        
        progress['total_processed'] += 1
        progress['last_run'] = datetime.now().isoformat()
        
        # Save progress every 10 URLs
        if i % 10 == 0:
            save_progress(progress)
            print(f"\n--- Progress saved: {progress['total_success']} successful, {progress['total_failed']} failed ---")
        
        # Rate limiting - be respectful to Archive.org
        time.sleep(5)  # Wait 5 seconds between requests
    
    # Final save
    save_progress(progress)
    
    print("\n" + "=" * 50)
    print("Archiving Complete!")
    print(f"Total processed: {progress['total_processed']}")
    print(f"Successful: {progress['total_success']}")
    print(f"Failed: {progress['total_failed']}")
    print(f"Progress saved to: archive_progress.json")

if __name__ == "__main__":
    main()