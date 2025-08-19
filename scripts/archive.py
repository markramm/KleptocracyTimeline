#!/usr/bin/env python3
"""
Unified archiving script for timeline sources.

This script consolidates all archiving functionality:
- Archive all sources to Archive.org
- Check existing archives
- Generate archive reports
- Handle rate limiting properly
"""

import argparse
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    get_event_files,
    load_event,
    load_json_file,
    save_json_file,
    setup_logger,
    log_info,
    log_warning,
    log_error,
    log_success,
    print_header,
    print_summary,
    progress_bar,
    check_archive_exists,
    archive_url,
    extract_urls_from_event,
    RateLimiter
)


class TimelineArchiver:
    """Archive timeline sources to prevent link rot."""
    
    def __init__(
        self,
        events_dir: str = "timeline_data/events",
        progress_file: str = "timeline_data/archive_progress.json",
        log_file: str = "timeline_data/archive.log",
        requests_per_minute: int = 10
    ):
        """
        Initialize the archiver.
        
        Args:
            events_dir: Path to events directory
            progress_file: Path to progress tracking file
            log_file: Path to log file
            requests_per_minute: Maximum requests per minute
        """
        self.events_dir = Path(events_dir)
        self.progress_file = Path(progress_file)
        self.logger = setup_logger('archiver', log_file=log_file)
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.progress = self.load_progress()
        self.start_time = time.time()
        
    def load_progress(self) -> Dict:
        """Load progress from file."""
        if self.progress_file.exists():
            return load_json_file(self.progress_file)
        return {
            'archived': [],
            'failed': [],
            'skipped': [],
            'last_run': None
        }
    
    def save_progress(self) -> None:
        """Save progress to file."""
        self.progress['last_run'] = datetime.now().isoformat()
        save_json_file(self.progress_file, self.progress)
    
    def get_all_urls(self) -> List[str]:
        """Get all unique URLs from timeline events."""
        urls = set()
        
        for filepath in get_event_files(self.events_dir):
            event = load_event(filepath)
            if event:
                event_urls = extract_urls_from_event(event)
                urls.update(event_urls)
        
        # Filter out placeholder text
        urls = {url for url in urls if url != "Research Document"}
        
        return sorted(list(urls))
    
    def archive_all(self, retry_failed: bool = False) -> None:
        """
        Archive all timeline sources.
        
        Args:
            retry_failed: Whether to retry previously failed URLs
        """
        print_header("TIMELINE SOURCE ARCHIVER")
        
        # Get all URLs
        all_urls = self.get_all_urls()
        
        if not all_urls:
            log_error("No URLs found to archive!")
            return
        
        # Reset failed URLs if retrying
        if retry_failed and self.progress['failed']:
            log_info(f"Resetting {len(self.progress['failed'])} failed URLs for retry")
            self.progress['failed'] = []
            self.save_progress()
        
        # Filter out already processed URLs
        processed = set(self.progress['archived'] + self.progress['failed'] + self.progress['skipped'])
        urls_to_archive = [url for url in all_urls if url not in processed]
        
        # Print statistics
        print_summary({
            'Total URLs': len(all_urls),
            'Already Archived': len(self.progress['archived']),
            'Failed': len(self.progress['failed']),
            'Skipped': len(self.progress['skipped']),
            'To Archive': len(urls_to_archive)
        })
        
        if not urls_to_archive:
            log_success("All URLs have been processed!")
            return
        
        # Estimate time
        estimated_minutes = len(urls_to_archive) * (60 / self.rate_limiter.requests_per_minute) / 60
        log_info(f"Estimated time: {estimated_minutes:.1f} minutes (without breaks)")
        print()
        
        # Archive URLs
        for i, url in enumerate(urls_to_archive, 1):
            # Show progress
            progress_bar(i - 1, len(urls_to_archive), prefix="Progress:")
            
            # Check if already archived recently
            existing = check_archive_exists(url, max_age_days=30)
            if existing:
                log_info(f"[{i}/{len(urls_to_archive)}] Already archived: {url[:80]}...")
                self.progress['skipped'].append(url)
                self.save_progress()
                continue
            
            # Archive the URL
            log_info(f"[{i}/{len(urls_to_archive)}] Archiving: {url[:80]}...")
            result = archive_url(url, self.rate_limiter)
            
            if result['success']:
                log_success(f"  {result['message']}")
                self.progress['archived'].append(url)
            else:
                log_error(f"  {result['message']}")
                self.progress['failed'].append(url)
            
            # Save progress periodically
            if i % 5 == 0:
                self.save_progress()
                self._print_progress_stats()
        
        # Final progress bar update
        progress_bar(len(urls_to_archive), len(urls_to_archive), prefix="Progress:")
        
        # Final save and report
        self.save_progress()
        self._print_final_report()
    
    def check_coverage(self) -> None:
        """Generate archive coverage report."""
        print_header("ARCHIVE COVERAGE REPORT")
        
        all_urls = self.get_all_urls()
        archived_count = 0
        recent_count = 0
        missing_count = 0
        
        log_info(f"Checking archive status for {len(all_urls)} URLs...")
        print()
        
        for i, url in enumerate(all_urls, 1):
            progress_bar(i, len(all_urls), prefix="Checking:")
            
            archive_url = check_archive_exists(url, max_age_days=None)
            if archive_url:
                archived_count += 1
                # Check if recent
                if check_archive_exists(url, max_age_days=30):
                    recent_count += 1
            else:
                missing_count += 1
        
        print()
        coverage_percent = (archived_count / len(all_urls) * 100) if all_urls else 0
        recent_percent = (recent_count / len(all_urls) * 100) if all_urls else 0
        
        print_summary({
            'Total Sources': len(all_urls),
            'Archived (Any Time)': f"{archived_count} ({coverage_percent:.1f}%)",
            'Recently Archived (30d)': f"{recent_count} ({recent_percent:.1f}%)",
            'Not Archived': missing_count
        })
        
        if missing_count > 0:
            log_warning(f"{missing_count} sources need archiving")
            log_info("Run 'archive.py' to archive missing sources")
    
    def _print_progress_stats(self) -> None:
        """Print progress statistics during archiving."""
        total_processed = len(self.progress['archived']) + len(self.progress['failed'])
        if total_processed > 0:
            success_rate = len(self.progress['archived']) / total_processed * 100
            elapsed = (time.time() - self.start_time) / 60
            
            self.logger.info(f"Progress: {total_processed} processed, "
                           f"{success_rate:.1f}% success rate, "
                           f"{elapsed:.1f} minutes elapsed")
    
    def _print_final_report(self) -> None:
        """Print final archiving report."""
        print()
        print_header("ARCHIVING COMPLETE", width=60)
        
        total = len(self.progress['archived']) + len(self.progress['failed'])
        success_rate = (len(self.progress['archived']) / total * 100) if total > 0 else 0
        elapsed = (time.time() - self.start_time) / 60
        
        print_summary({
            'Successfully Archived': len(self.progress['archived']),
            'Failed': len(self.progress['failed']),
            'Skipped (Recent)': len(self.progress['skipped']),
            'Success Rate': f"{success_rate:.1f}%",
            'Time Elapsed': f"{elapsed:.1f} minutes"
        })
        
        if self.progress['failed']:
            log_warning(f"Failed URLs saved to {self.progress_file}")
            log_info("Run with --retry-failed to retry them")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Archive timeline sources to Archive.org',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Archive all sources
  %(prog)s --retry-failed     # Retry previously failed URLs
  %(prog)s --check-coverage   # Check archive coverage only
  %(prog)s --rate 5           # Use slower rate (5 req/min)
        """
    )
    
    parser.add_argument(
        '--events-dir',
        default='timeline_data/events',
        help='Path to events directory'
    )
    
    parser.add_argument(
        '--progress-file',
        default='timeline_data/archive_progress.json',
        help='Path to progress tracking file'
    )
    
    parser.add_argument(
        '--log-file',
        default='timeline_data/archive.log',
        help='Path to log file'
    )
    
    parser.add_argument(
        '--rate',
        type=int,
        default=10,
        help='Requests per minute (default: 10, max: 15)'
    )
    
    parser.add_argument(
        '--retry-failed',
        action='store_true',
        help='Retry previously failed URLs'
    )
    
    parser.add_argument(
        '--check-coverage',
        action='store_true',
        help='Check archive coverage without archiving'
    )
    
    args = parser.parse_args()
    
    # Validate rate limit
    if args.rate > 15:
        log_error("Rate cannot exceed 15 requests per minute (Archive.org limit)")
        sys.exit(1)
    
    # Create archiver
    archiver = TimelineArchiver(
        events_dir=args.events_dir,
        progress_file=args.progress_file,
        log_file=args.log_file,
        requests_per_minute=args.rate
    )
    
    try:
        if args.check_coverage:
            archiver.check_coverage()
        else:
            archiver.archive_all(retry_failed=args.retry_failed)
    except KeyboardInterrupt:
        print("\n")
        log_warning("Archiving interrupted by user")
        archiver.save_progress()
        log_info(f"Progress saved to {archiver.progress_file}")
        log_info("You can resume by running this script again")
        sys.exit(0)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        archiver.save_progress()
        sys.exit(1)


if __name__ == '__main__':
    main()