#!/usr/bin/env python3
"""
Respectful version of archive_links that automatically throttles based on errors.
Implements exponential backoff and adaptive rate limiting.
"""

import yaml
import json
import requests
import time
from pathlib import Path
from datetime import datetime
import sys
import random

class AdaptiveArchiver:
    def __init__(self):
        self.base_delay = 10  # Start with 10 seconds between requests
        self.current_delay = self.base_delay
        self.min_delay = 5
        self.max_delay = 300  # Max 5 minutes between requests
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.rate_limit_errors = 0
        self.connection_errors = 0
        self.total_attempts = 0
        
        # Files to skip due to YAML issues
        self.skip_files = {
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
    
    def adjust_delay(self, success=False, rate_limited=False, connection_error=False):
        """Adjust delay based on response."""
        if rate_limited:
            # Hit rate limit - back off significantly
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.rate_limit_errors += 1
            self.current_delay = min(self.current_delay * 2, self.max_delay)
            print(f"  ⚠️  Rate limited. Increasing delay to {self.current_delay}s")
            
            # If we hit multiple rate limits, take a longer break
            if self.rate_limit_errors > 3:
                wait_time = 60 * (self.rate_limit_errors - 2)  # Wait 1 min per excess error
                print(f"  ⏸️  Taking {wait_time}s break due to multiple rate limits...")
                time.sleep(wait_time)
                self.rate_limit_errors = 0  # Reset counter after break
                
        elif connection_error:
            # Connection error - might be temporary server issue
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.connection_errors += 1
            self.current_delay = min(self.current_delay * 1.5, self.max_delay)
            print(f"  ⚠️  Connection error. Adjusting delay to {self.current_delay}s")
            
            # If many connection errors, Archive.org might be down
            if self.connection_errors > 5:
                wait_time = 300  # Wait 5 minutes
                print(f"  ⏸️  Archive.org may be down. Waiting {wait_time}s...")
                time.sleep(wait_time)
                self.connection_errors = 0
                
        elif success:
            # Success - can gradually speed up
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            
            # Only speed up after multiple successes
            if self.consecutive_successes > 5:
                self.current_delay = max(self.current_delay * 0.9, self.min_delay)
                print(f"  ⚡ Speeding up to {self.current_delay:.1f}s delay")
                
        else:
            # Other failure - slightly increase delay
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.current_delay = min(self.current_delay * 1.2, self.max_delay)
    
    def wait(self):
        """Wait with jitter to avoid thundering herd."""
        jitter = random.uniform(0, self.current_delay * 0.1)  # Add up to 10% jitter
        wait_time = self.current_delay + jitter
        print(f"  ⏱️  Waiting {wait_time:.1f}s before next request...")
        time.sleep(wait_time)
    
    def archive_url(self, url):
        """Submit a URL to the Wayback Machine with retry logic."""
        self.total_attempts += 1
        
        try:
            save_api = f"https://web.archive.org/save/{url}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Kleptocracy Timeline Archiver - Respectful Bot)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Longer timeout for slow responses
            response = requests.get(save_api, headers=headers, timeout=60)
            
            if response.status_code == 200:
                if 'Content-Location' in response.headers:
                    archived_url = f"https://web.archive.org{response.headers['Content-Location']}"
                    self.adjust_delay(success=True)
                    return {'success': True, 'archive_url': archived_url}
                else:
                    self.adjust_delay(success=True)
                    return {'success': True, 'archive_url': f"https://web.archive.org/web/*/{url}"}
                    
            elif response.status_code == 429:
                # Rate limited
                self.adjust_delay(rate_limited=True)
                return {'success': False, 'error': f"Rate limited (429)", 'retry': True}
                
            elif response.status_code in [502, 503, 504]:
                # Server errors - temporary
                self.adjust_delay(connection_error=True)
                return {'success': False, 'error': f"Server error ({response.status_code})", 'retry': True}
                
            else:
                self.adjust_delay()
                return {'success': False, 'error': f"Status {response.status_code}", 'retry': False}
                
        except requests.exceptions.Timeout:
            self.adjust_delay()
            return {'success': False, 'error': 'Timeout', 'retry': True}
            
        except requests.exceptions.ConnectionError as e:
            self.adjust_delay(connection_error=True)
            return {'success': False, 'error': 'Connection refused', 'retry': True}
            
        except Exception as e:
            self.adjust_delay()
            return {'success': False, 'error': str(e)[:100], 'retry': False}
    
    def load_progress(self):
        """Load archiving progress from file."""
        progress_file = Path('archive_progress.json')
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                return json.load(f)
        return {
            'archived_urls': {},
            'failed_urls': {},
            'deferred_urls': {},  # URLs to retry later
            'last_run': None,
            'total_processed': 0,
            'total_success': 0,
            'total_failed': 0,
            'total_deferred': 0,
            'skipped_files': list(self.skip_files)
        }
    
    def save_progress(self, progress):
        """Save archiving progress to file."""
        with open('archive_progress.json', 'w') as f:
            json.dump(progress, f, indent=2, default=str)
    
    def extract_urls_from_events(self):
        """Extract all unique URLs from timeline events."""
        events_dir = Path('events')
        all_urls = set()
        url_to_files = {}
        skipped_count = 0
        
        for yaml_file in events_dir.glob('*.yaml'):
            if yaml_file.name in self.skip_files:
                skipped_count += 1
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
                self.skip_files.add(yaml_file.name)
                skipped_count += 1
        
        if skipped_count > 0:
            print(f"Skipped {skipped_count} files due to YAML errors")
        
        return all_urls, url_to_files
    
    def run(self):
        """Main archiving loop with adaptive throttling."""
        print("Starting Respectful Timeline Link Archiver...")
        print("=" * 50)
        print("Features:")
        print("- Adaptive rate limiting based on server responses")
        print("- Exponential backoff for errors")
        print("- Automatic breaks when rate limited")
        print("- Jitter to avoid thundering herd")
        print("=" * 50)
        
        progress = self.load_progress()
        all_urls, url_to_files = self.extract_urls_from_events()
        
        # Build list of URLs to process
        urls_to_archive = []
        
        # First, check deferred URLs that are ready to retry
        for url in list(progress.get('deferred_urls', {}).keys()):
            deferred_info = progress['deferred_urls'][url]
            last_attempt = deferred_info.get('last_attempt')
            if last_attempt:
                last_time = datetime.fromisoformat(last_attempt)
                # Retry deferred URLs after 1 hour
                if (datetime.now() - last_time).seconds >= 3600:
                    urls_to_archive.append(url)
        
        # Add new URLs
        for url in all_urls:
            if (url not in progress['archived_urls'] and 
                url not in progress['failed_urls'] and
                url not in progress.get('deferred_urls', {}) and
                url not in urls_to_archive):
                urls_to_archive.append(url)
        
        print(f"Total unique URLs found: {len(all_urls)}")
        print(f"Already archived: {len(progress['archived_urls'])}")
        print(f"Permanently failed: {len(progress['failed_urls'])}")
        print(f"Deferred (will retry): {len(progress.get('deferred_urls', {}))}")
        print(f"Ready to process: {len(urls_to_archive)}")
        print("=" * 50)
        
        if not urls_to_archive:
            print("No URLs to archive at this time!")
            if progress.get('deferred_urls'):
                print(f"Note: {len(progress['deferred_urls'])} URLs are deferred and will be retried later.")
            return
        
        # Archive URLs with adaptive rate limiting
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
            result = self.archive_url(url)
            
            if result['success']:
                archive_url_str = result['archive_url']
                print(f"  ✓ Archived: {archive_url_str[:80]}...")
                
                # Update progress
                progress['archived_urls'][url] = {
                    'archive_url': archive_url_str,
                    'timestamp': datetime.now().isoformat()
                }
                progress['total_success'] += 1
                
                # Remove from deferred if it was there
                if url in progress.get('deferred_urls', {}):
                    del progress['deferred_urls'][url]
                
            elif result.get('retry', False):
                # Defer for later retry
                print(f"  ⏸️  Deferring (will retry later)")
                
                if 'deferred_urls' not in progress:
                    progress['deferred_urls'] = {}
                
                if url not in progress['deferred_urls']:
                    progress['deferred_urls'][url] = {'attempts': 0}
                
                progress['deferred_urls'][url]['attempts'] += 1
                progress['deferred_urls'][url]['last_attempt'] = datetime.now().isoformat()
                progress['deferred_urls'][url]['last_error'] = result['error']
                progress['total_deferred'] = len(progress['deferred_urls'])
                
            else:
                # Permanent failure
                print(f"  ✗ Failed permanently: {result['error']}")
                
                if url not in progress['failed_urls']:
                    progress['failed_urls'][url] = {'attempts': 0}
                
                progress['failed_urls'][url]['attempts'] += 1
                progress['failed_urls'][url]['last_attempt'] = datetime.now().isoformat()
                progress['failed_urls'][url]['last_error'] = result['error']
                progress['total_failed'] += 1
            
            progress['total_processed'] += 1
            progress['last_run'] = datetime.now().isoformat()
            
            # Save progress every 5 URLs
            if i % 5 == 0:
                self.save_progress(progress)
                print(f"\n--- Progress: {progress['total_success']} archived, "
                      f"{len(progress.get('deferred_urls', {}))} deferred, "
                      f"{progress['total_failed']} failed ---")
                print(f"--- Current delay: {self.current_delay:.1f}s ---")
            
            # Wait before next request
            self.wait()
            
            # Emergency stop if too many consecutive failures
            if self.consecutive_failures > 10:
                print("\n⛔ Too many consecutive failures. Stopping for now.")
                print("Archive.org may be experiencing issues. Try again later.")
                break
        
        # Final save
        self.save_progress(progress)
        
        print("\n" + "=" * 50)
        print("Archiving Session Complete!")
        print(f"Total processed this session: {self.total_attempts}")
        print(f"Successfully archived: {progress['total_success']}")
        print(f"Deferred for retry: {len(progress.get('deferred_urls', {}))}")
        print(f"Permanently failed: {progress['total_failed']}")
        print(f"Current delay setting: {self.current_delay:.1f}s")
        print(f"Progress saved to: archive_progress.json")
        
        if progress.get('deferred_urls'):
            print(f"\nNote: Run again in 1 hour to retry {len(progress['deferred_urls'])} deferred URLs")

if __name__ == "__main__":
    archiver = AdaptiveArchiver()
    archiver.run()