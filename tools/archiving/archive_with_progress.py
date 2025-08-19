#!/usr/bin/env python3
"""
Respectful archiver for timeline links with proper rate limiting and progress tracking
Respects Archive.org rate limits and saves progress after each URL
"""

import os
import json
import time
import requests
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
import random
import sys
from pathlib import Path

class RespectfulArchiver:
    def __init__(self, events_dir: str = "timeline_data/events"):
        # Conservative rate limiting (Archive.org recommends max 15/min)
        self.requests_per_minute = 10  # Conservative but not too slow
        self.delay_between_requests = 60 / self.requests_per_minute  # 6 seconds
        
        # Backoff settings
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        self.backoff_multiplier = 2
        self.current_wait = self.delay_between_requests
        
        # Session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Kleptocracy Timeline Archiver - Respectful rate limit 10/min'
        })
        
        # Paths
        self.events_dir = Path(events_dir)
        self.progress_file = self.events_dir.parent / 'archive_progress.json'
        self.log_file = self.events_dir.parent / 'archive.log'
        
        # Progress tracking
        self.progress = self.load_progress()
        
        # Track 429 errors
        self.last_429_time = self.progress.get('last_429_time', None)
        self.start_time = time.time()
        
    def load_progress(self) -> Dict:
        """Load progress from file"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'archived': [],
            'failed': [],
            'skipped': [],
            'last_429_time': None,
            'last_run': None
        }
    
    def save_progress(self):
        """Save progress to file"""
        self.progress['last_run'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def wait_with_progress(self, seconds: float, reason: str = ""):
        """Wait with progress indicator"""
        if seconds <= 1:
            time.sleep(seconds)
            return
            
        print(f"  ⏳ Waiting {seconds:.0f}s {reason}...", end='', flush=True)
        
        # Show countdown for long waits
        if seconds > 30:
            for i in range(int(seconds)):
                time.sleep(1)
                remaining = int(seconds) - i - 1
                if remaining > 0 and remaining % 10 == 0:
                    print(f" {remaining}s", end='', flush=True)
        else:
            time.sleep(seconds)
        print(" ✓")
    
    def check_archive_exists(self, url: str) -> Optional[str]:
        """Check if URL is already archived"""
        check_api = f"https://archive.org/wayback/available?url={url}"
        
        try:
            response = self.session.get(check_api, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('archived_snapshots', {}).get('closest'):
                    snapshot = data['archived_snapshots']['closest']
                    if snapshot.get('available'):
                        return snapshot.get('url')
        except:
            pass
        return None
    
    def archive_url(self, url: str) -> bool:
        """Archive a single URL with proper error handling"""
        # First check if already archived recently (within 30 days)
        existing = self.check_archive_exists(url)
        if existing:
            # Check if recent enough
            try:
                timestamp = existing.split('/')[4]  # Extract timestamp from archive URL
                archive_date = datetime.strptime(timestamp[:8], "%Y%m%d")
                if (datetime.now() - archive_date).days < 30:
                    self.log(f"  ⏭️  Already archived recently: {timestamp[:8]}", "SKIP")
                    return True
            except:
                pass
        
        # Archive the URL
        save_api = f"https://web.archive.org/save/{url}"
        
        try:
            response = self.session.get(save_api, timeout=30)
            
            if response.status_code == 200:
                self.log(f"  ✅ Archived successfully", "SUCCESS")
                self.consecutive_failures = 0
                self.current_wait = self.delay_between_requests
                return True
                
            elif response.status_code == 429:
                self.log(f"  ⚠️  Rate limited (429) - Waiting 60 minutes", "WARN")
                self.last_429_time = time.time()
                self.progress['last_429_time'] = self.last_429_time
                self.save_progress()
                self.wait_with_progress(3600, "for rate limit cooldown")
                self.consecutive_failures = 0
                self.current_wait = self.delay_between_requests
                return False
                
            elif response.status_code == 404:
                self.log(f"  ❌ URL not found (404)", "ERROR")
                return False
                
            else:
                self.log(f"  ❌ Failed: Status {response.status_code}", "ERROR")
                self.consecutive_failures += 1
                return False
                
        except requests.exceptions.ConnectionError:
            self.log(f"  ❌ Connection refused - possible IP block", "ERROR")
            self.log(f"     Waiting 30 minutes before continuing...", "WARN")
            self.wait_with_progress(1800, "for connection recovery")
            return False
            
        except requests.exceptions.Timeout:
            self.log(f"  ❌ Timeout", "ERROR")
            self.consecutive_failures += 1
            return False
            
        except Exception as e:
            self.log(f"  ❌ Error: {str(e)[:100]}", "ERROR")
            self.consecutive_failures += 1
            return False
    
    def get_all_urls(self) -> List[str]:
        """Get all unique URLs from timeline events"""
        urls = set()
        
        if not self.events_dir.exists():
            self.log(f"Events directory not found: {self.events_dir}", "ERROR")
            return []
        
        yaml_files = list(self.events_dir.glob("*.yaml"))
        self.log(f"Found {len(yaml_files)} event files", "INFO")
        
        for filepath in yaml_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                if data and 'sources' in data:
                    for source in data['sources']:
                        if isinstance(source, dict) and 'url' in source:
                            url = source['url']
                            # Skip non-HTTP URLs and placeholder text
                            if url and url.startswith('http') and url != 'Research Document':
                                urls.add(url)
            except Exception as e:
                self.log(f"Error reading {filepath.name}: {e}", "WARN")
                continue
                
        return sorted(list(urls))
    
    def run(self):
        """Main archiving loop"""
        self.log("=" * 60, "INFO")
        self.log("RESPECTFUL TIMELINE ARCHIVER", "INFO")
        self.log(f"Rate: {self.requests_per_minute} requests per minute", "INFO")
        self.log(f"Events directory: {self.events_dir}", "INFO")
        self.log("=" * 60, "INFO")
        
        # Check for recent 429 error
        if self.last_429_time:
            elapsed = time.time() - self.last_429_time
            if elapsed < 3600:
                wait_time = 3600 - elapsed
                self.log(f"Previous rate limit detected {elapsed/60:.1f} minutes ago", "WARN")
                self.wait_with_progress(wait_time, "to complete cooldown")
        
        # Get all URLs
        all_urls = self.get_all_urls()
        
        if not all_urls:
            self.log("No URLs found to archive!", "ERROR")
            return
        
        # Filter out already processed URLs
        processed = set(self.progress['archived'] + self.progress['failed'] + self.progress['skipped'])
        urls_to_archive = [url for url in all_urls if url not in processed]
        
        self.log(f"Total unique URLs: {len(all_urls)}", "INFO")
        self.log(f"Already processed: {len(processed)}", "INFO")
        self.log(f"  - Archived: {len(self.progress['archived'])}", "INFO")
        self.log(f"  - Failed: {len(self.progress['failed'])}", "INFO")
        self.log(f"  - Skipped: {len(self.progress['skipped'])}", "INFO")
        self.log(f"URLs to archive: {len(urls_to_archive)}", "INFO")
        
        if not urls_to_archive:
            self.log("All URLs have been processed!", "SUCCESS")
            return
        
        estimated_time = len(urls_to_archive) * self.delay_between_requests / 60
        self.log(f"Estimated time: {estimated_time:.1f} minutes (without breaks)", "INFO")
        self.log("=" * 60, "INFO")
        
        # Process URLs
        for i, url in enumerate(urls_to_archive, 1):
            self.log(f"\n[{i}/{len(urls_to_archive)}] Processing: {url[:100]}...", "INFO")
            
            # Check for too many consecutive failures
            if self.consecutive_failures >= self.max_consecutive_failures:
                self.log("Too many consecutive failures, taking 5-minute break...", "WARN")
                self.wait_with_progress(300, "to avoid blocks")
                self.consecutive_failures = 0
            
            # Archive the URL
            success = self.archive_url(url)
            
            if success:
                self.progress['archived'].append(url)
            else:
                self.progress['failed'].append(url)
            
            # Save progress after every URL
            self.save_progress()
            
            # Show statistics every 10 URLs
            if i % 10 == 0:
                total_processed = len(self.progress['archived']) + len(self.progress['failed'])
                if total_processed > 0:
                    success_rate = len(self.progress['archived']) / total_processed * 100
                    elapsed = (time.time() - self.start_time) / 60
                    rate = i / elapsed if elapsed > 0 else 0
                    remaining = (len(urls_to_archive) - i) / rate if rate > 0 else 0
                    
                    self.log(f"\n--- Progress Report ---", "INFO")
                    self.log(f"Processed: {i}/{len(urls_to_archive)}", "INFO")
                    self.log(f"Success rate: {success_rate:.1f}%", "INFO")
                    self.log(f"Rate: {rate:.1f} URLs/min", "INFO")
                    self.log(f"Est. remaining: {remaining:.1f} min", "INFO")
                    self.log("-" * 23, "INFO")
            
            # Wait before next request (with jitter)
            if i < len(urls_to_archive):
                jitter = random.uniform(-0.5, 0.5)
                wait_time = max(self.current_wait + jitter, 3)
                self.wait_with_progress(wait_time, "before next request")
        
        # Final report
        self.log("\n" + "=" * 60, "INFO")
        self.log("ARCHIVING COMPLETE", "SUCCESS")
        self.log(f"Successfully archived: {len(self.progress['archived'])}", "INFO")
        self.log(f"Failed: {len(self.progress['failed'])}", "INFO")
        
        total = len(self.progress['archived']) + len(self.progress['failed'])
        if total > 0:
            success_rate = len(self.progress['archived']) / total * 100
            self.log(f"Success rate: {success_rate:.1f}%", "INFO")
        
        if self.progress['failed']:
            self.log(f"\nFailed URLs saved to {self.progress_file}", "INFO")
            self.log("Run this script again to retry failed URLs", "INFO")
        
        elapsed_total = (time.time() - self.start_time) / 60
        self.log(f"\nTotal time: {elapsed_total:.1f} minutes", "INFO")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Archive timeline event sources to Archive.org")
    parser.add_argument(
        '--events-dir',
        default='timeline_data/events',
        help='Path to events directory (default: timeline_data/events)'
    )
    parser.add_argument(
        '--retry-failed',
        action='store_true',
        help='Only retry previously failed URLs'
    )
    
    args = parser.parse_args()
    
    # Convert to absolute path if relative
    events_dir = Path(args.events_dir)
    if not events_dir.is_absolute():
        events_dir = Path.cwd() / events_dir
    
    archiver = RespectfulArchiver(str(events_dir))
    
    if args.retry_failed:
        # Move failed URLs back to pending
        archiver.log("Retrying previously failed URLs...", "INFO")
        failed_urls = archiver.progress.get('failed', [])
        archiver.progress['failed'] = []
        archiver.save_progress()
        archiver.log(f"Reset {len(failed_urls)} failed URLs for retry", "INFO")
    
    try:
        archiver.run()
    except KeyboardInterrupt:
        archiver.log("\n\nArchiving interrupted by user", "WARN")
        archiver.save_progress()
        archiver.log(f"Progress saved to {archiver.progress_file}", "INFO")
        archiver.log("You can resume by running this script again", "INFO")
        sys.exit(0)
    except Exception as e:
        archiver.log(f"\n\nUnexpected error: {e}", "ERROR")
        archiver.save_progress()
        archiver.log(f"Progress saved to {archiver.progress_file}", "INFO")
        sys.exit(1)


if __name__ == "__main__":
    main()