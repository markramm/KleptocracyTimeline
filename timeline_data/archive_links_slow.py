#!/usr/bin/env python3
"""
Very slow, respectful archiver for timeline links
Respects Archive.org rate limits: max 15 requests per minute
Includes exponential backoff and proper 429 handling
"""

import os
import json
import time
import requests
import yaml
from datetime import datetime
from typing import Dict, List, Set
import random

class SlowArchiver:
    def __init__(self):
        # Conservative rate limiting
        self.requests_per_minute = 5  # Very conservative - only 5 requests per minute
        self.delay_between_requests = 60 / self.requests_per_minute  # 12 seconds
        
        # Backoff settings
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        self.backoff_multiplier = 2
        self.current_wait = self.delay_between_requests
        
        # Session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Kleptocracy Timeline Archiver) - Respectful archiving at 10 req/min'
        })
        
        # Progress tracking
        self.progress_file = 'archive_progress_slow.json'
        self.progress = self.load_progress()
        
        # Track 429 errors
        self.last_429_time = self.progress.get('last_429_time', None)
        
    def load_progress(self) -> Dict:
        """Load progress from file"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'archived': [],
            'failed': [],
            'skipped': []
        }
    
    def save_progress(self):
        """Save progress to file"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def wait_with_message(self, seconds: float, reason: str = ""):
        """Wait with countdown message"""
        print(f"  ⏳ Waiting {seconds:.0f}s {reason}...", end='', flush=True)
        for i in range(int(seconds)):
            time.sleep(1)
            remaining = int(seconds) - i - 1
            if remaining > 0 and remaining % 10 == 0:
                print(f" {remaining}s", end='', flush=True)
        print(" Done")
    
    def archive_url(self, url: str) -> bool:
        """Archive a single URL with proper error handling"""
        save_api = f"https://web.archive.org/save/{url}"
        
        try:
            response = self.session.get(save_api, timeout=30)
            
            if response.status_code == 200:
                print(f"  ✓ Archived successfully")
                self.consecutive_failures = 0
                self.current_wait = self.delay_between_requests
                return True
                
            elif response.status_code == 429:
                print(f"  ⚠️  Rate limited (429) - Must wait 1 hour to avoid IP ban")
                # Documentation says ignoring 429 for >1 minute triggers IP ban
                # And subsequent violations double the ban time
                self.last_429_time = time.time()
                self.progress['last_429_time'] = self.last_429_time
                self.save_progress()
                self.wait_with_message(3600, "to respect rate limit and avoid IP ban")
                self.consecutive_failures = 0  # Reset since we're taking proper break
                self.current_wait = self.delay_between_requests
                return False
                
            elif response.status_code == 404:
                print(f"  ✗ URL not found (404)")
                return False
                
            else:
                print(f"  ✗ Failed: Status {response.status_code}")
                self.consecutive_failures += 1
                return False
                
        except requests.exceptions.ConnectionError as e:
            print(f"  ✗ Connection refused - likely IP blocked")
            print(f"     Waiting 1 hour before continuing...")
            self.wait_with_message(3600, "for IP block to clear")
            return False
            
        except requests.exceptions.Timeout:
            print(f"  ✗ Timeout")
            self.consecutive_failures += 1
            return False
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:100]}")
            self.consecutive_failures += 1
            return False
    
    def get_all_urls(self) -> List[str]:
        """Get all unique URLs from timeline events"""
        urls = set()
        events_dir = 'events'
        
        for filename in os.listdir(events_dir):
            if not filename.endswith('.yaml'):
                continue
                
            filepath = os.path.join(events_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                if data and 'sources' in data:
                    for source in data['sources']:
                        if isinstance(source, dict) and 'url' in source:
                            url = source['url']
                            if url != 'Research Document' and url.startswith('http'):
                                urls.add(url)
            except:
                continue
                
        return sorted(list(urls))
    
    def run(self):
        """Main archiving loop"""
        print("=" * 60)
        print("ULTRA-SLOW RESPECTFUL ARCHIVER")
        print("Rate: 5 requests per minute (12 second delay)")
        print("Auto-pauses 1 hour after ANY 429 error")
        print("=" * 60)
        
        # Check if we need to wait from a previous 429
        if self.last_429_time:
            time_since_429 = time.time() - self.last_429_time
            if time_since_429 < 3600:
                wait_remaining = 3600 - time_since_429
                print(f"\n⚠️  Previous 429 error detected {time_since_429/60:.1f} minutes ago")
                self.wait_with_message(wait_remaining, "to complete 1-hour cooldown")
                print("Cooldown complete, resuming...")
        
        all_urls = self.get_all_urls()
        
        # Filter out already processed URLs
        processed = set(self.progress['archived'] + self.progress['failed'] + self.progress['skipped'])
        urls_to_archive = [url for url in all_urls if url not in processed]
        
        print(f"Total unique URLs: {len(all_urls)}")
        print(f"Already processed: {len(processed)}")
        print(f"  - Archived: {len(self.progress['archived'])}")
        print(f"  - Failed: {len(self.progress['failed'])}")
        print(f"  - Skipped: {len(self.progress['skipped'])}")
        print(f"URLs to archive: {len(urls_to_archive)}")
        
        if not urls_to_archive:
            print("\nNo URLs to archive!")
            return
        
        print(f"\nEstimated time: {len(urls_to_archive) * 12 / 60:.1f} minutes (without breaks)")
        print("=" * 60)
        
        for i, url in enumerate(urls_to_archive, 1):
            print(f"\n[{i}/{len(urls_to_archive)}] {url[:80]}...")
            
            # Check for too many consecutive failures
            if self.consecutive_failures >= self.max_consecutive_failures:
                print(f"  ⚠️  Too many failures, taking extended break...")
                self.wait_with_message(300, "to avoid further blocks")
                self.consecutive_failures = 0
            
            # Archive the URL
            success = self.archive_url(url)
            
            if success:
                self.progress['archived'].append(url)
            else:
                self.progress['failed'].append(url)
            
            # Save progress every 5 URLs
            if i % 5 == 0:
                self.save_progress()
                archived_count = len(self.progress['archived'])
                failed_count = len(self.progress['failed'])
                success_rate = (archived_count / (archived_count + failed_count) * 100) if (archived_count + failed_count) > 0 else 0
                print(f"\n--- Progress: {archived_count} successful ({success_rate:.1f}%), {failed_count} failed ---")
            
            # Wait before next request
            if i < len(urls_to_archive):
                # Add random jitter to avoid appearing too robotic
                jitter = random.uniform(-0.5, 0.5)
                wait_time = max(self.current_wait + jitter, 3)  # Never less than 3 seconds
                self.wait_with_message(wait_time, "before next request")
        
        # Final save
        self.save_progress()
        
        # Print summary
        print("\n" + "=" * 60)
        print("ARCHIVING COMPLETE")
        print(f"Successfully archived: {len(self.progress['archived'])}")
        print(f"Failed: {len(self.progress['failed'])}")
        print(f"Success rate: {len(self.progress['archived']) / (len(self.progress['archived']) + len(self.progress['failed'])) * 100:.1f}%")
        
        if self.progress['failed']:
            print(f"\nFailed URLs saved to {self.progress_file}")
            print("You can re-run this script later to retry failed URLs")


if __name__ == "__main__":
    archiver = SlowArchiver()
    try:
        archiver.run()
    except KeyboardInterrupt:
        print("\n\nArchiving interrupted by user")
        archiver.save_progress()
        print(f"Progress saved to {archiver.progress_file}")
        print("You can resume by running this script again")