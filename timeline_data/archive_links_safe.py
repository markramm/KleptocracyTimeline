#!/usr/bin/env python3
"""
Safe version of archive_links that skips problematic files.
"""

import yaml
import json
import requests
import time
from pathlib import Path
from datetime import datetime
import sys

# Files to skip due to YAML issues
SKIP_FILES = {
    '2016-08-21--stone-podesta-tweet.yaml',
    '2025-08-01--court-defiance-35-percent-pattern.yaml',
    '2025-07-23--house-oversight-subpoenas-doj.yaml',
    '2016-08-01--stone-guccifer-communications.yaml',
    '2025-06-01--federal-layoffs-275000.yaml',
    '2025-08-01--gsa-northwest-90-percent-fired.yaml',
    '2025-05-15--bondi-briefs-trump-name-in-files.yaml',
    '2024-06-28--scotus_loper_bright_overrules_chevron.yaml',
    '2025-01-31--eo_14171_schedule_f.yaml',
    '2025-03-10--civicus-watchlist-us-democracy.yaml',
    '2025-07-01--doj-blocks-epstein-releases.yaml'
}

def archive_url(url):
    """Submit a URL to the Wayback Machine for archiving."""
    try:
        save_api = f"https://web.archive.org/save/{url}"
        headers = {'User-Agent': 'Mozilla/5.0 (Kleptocracy Timeline Archiver)'}
        
        response = requests.get(save_api, headers=headers, timeout=30)
        
        if response.status_code == 200:
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
        'total_failed': 0,
        'skipped_files': list(SKIP_FILES)
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
    skipped_count = 0
    
    for yaml_file in events_dir.glob('*.yaml'):
        # Skip problematic files
        if yaml_file.name in SKIP_FILES:
            skipped_count += 1
            print(f"Skipping problematic file: {yaml_file.name}")
            continue
            
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
            SKIP_FILES.add(yaml_file.name)
            skipped_count += 1
    
    if skipped_count > 0:
        print(f"Skipped {skipped_count} files due to YAML errors")
    
    return all_urls, url_to_files

def main():
    """Main archiving loop."""
    print("Starting Safe Timeline Link Archiver...")
    print("=" * 50)
    
    progress = load_progress()
    all_urls, url_to_files = extract_urls_from_events()
    
    urls_to_archive = []
    for url in all_urls:
        if url not in progress['archived_urls'] and url not in progress['failed_urls']:
            urls_to_archive.append(url)
        elif url in progress['failed_urls']:
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
    print(f"Files skipped: {len(SKIP_FILES)}")
    print("=" * 50)
    
    if not urls_to_archive:
        print("No URLs to archive. All accessible links are already processed!")
        return
    
    # Archive URLs with rate limiting
    for i, url in enumerate(urls_to_archive, 1):
        print(f"\n[{i}/{len(urls_to_archive)}] Archiving: {url[:80]}...")
        
        if 'web.archive.org' in url or 'archive.org' in url:
            print("  → Skipping (already an archive URL)")
            progress['archived_urls'][url] = {
                'archive_url': url,
                'timestamp': datetime.now().isoformat(),
                'is_archive': True
            }
            continue
        
        result = archive_url(url)
        
        if result['success']:
            archive_url_str = result['archive_url']
            print(f"  ✓ Archived: {archive_url_str[:80]}...")
            
            progress['archived_urls'][url] = {
                'archive_url': archive_url_str,
                'timestamp': datetime.now().isoformat()
            }
            progress['total_success'] += 1
            
        else:
            print(f"  ✗ Failed: {result['error']}")
            
            if url not in progress['failed_urls']:
                progress['failed_urls'][url] = {'attempts': 0}
            
            progress['failed_urls'][url]['attempts'] += 1
            progress['failed_urls'][url]['last_attempt'] = datetime.now().isoformat()
            progress['failed_urls'][url]['last_error'] = result['error']
            progress['total_failed'] += 1
        
        progress['total_processed'] += 1
        progress['last_run'] = datetime.now().isoformat()
        
        if i % 10 == 0:
            save_progress(progress)
            print(f"\n--- Progress saved: {progress['total_success']} successful, {progress['total_failed']} failed ---")
        
        time.sleep(5)  # Rate limiting
    
    save_progress(progress)
    
    print("\n" + "=" * 50)
    print("Archiving Complete!")
    print(f"Total processed: {progress['total_processed']}")
    print(f"Successful: {progress['total_success']}")
    print(f"Failed: {progress['total_failed']}")
    print(f"Progress saved to: archive_progress.json")

if __name__ == "__main__":
    main()