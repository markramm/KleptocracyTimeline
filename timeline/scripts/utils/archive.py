"""
Archive.org utilities for timeline scripts
"""

import time
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import random


class RateLimiter:
    """
    Rate limiter for API requests with exponential backoff.
    """
    
    def __init__(self, requests_per_minute: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.delay_between_requests = 60 / requests_per_minute
        self.last_request_time = 0
        self.consecutive_failures = 0
        self.last_429_time = None
        
    def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limits."""
        # Check for recent 429 error
        if self.last_429_time:
            elapsed = time.time() - self.last_429_time
            if elapsed < 3600:  # 1 hour cooldown for 429 errors
                wait_time = 3600 - elapsed
                print(f"⏳ Waiting {wait_time:.0f}s for rate limit cooldown...")
                time.sleep(wait_time)
                self.last_429_time = None
        
        # Regular rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay_between_requests:
            wait_time = self.delay_between_requests - elapsed
            # Add small random jitter
            wait_time += random.uniform(-0.5, 0.5)
            wait_time = max(wait_time, 1)  # Minimum 1 second
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def handle_429(self) -> None:
        """Handle 429 rate limit response."""
        self.last_429_time = time.time()
        self.consecutive_failures = 0
    
    def handle_failure(self) -> None:
        """Handle request failure with backoff."""
        self.consecutive_failures += 1
        if self.consecutive_failures >= 3:
            # Take a break after multiple failures
            print("⏳ Multiple failures, taking 5-minute break...")
            time.sleep(300)
            self.consecutive_failures = 0
    
    def handle_success(self) -> None:
        """Reset failure counter on success."""
        self.consecutive_failures = 0


def check_archive_exists(url: str, max_age_days: int = 30) -> Optional[str]:
    """
    Check if a URL is already archived.
    
    Args:
        url: URL to check
        max_age_days: Maximum age in days to consider archive recent
        
    Returns:
        Archive URL if exists and recent enough, None otherwise
    """
    check_api = f"https://archive.org/wayback/available?url={url}"
    
    try:
        response = requests.get(check_api, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('archived_snapshots', {}).get('closest'):
                snapshot = data['archived_snapshots']['closest']
                if snapshot.get('available'):
                    archive_url = snapshot.get('url')
                    # Check age if max_age_days is specified
                    if max_age_days and archive_url:
                        try:
                            # Extract timestamp from archive URL
                            timestamp = archive_url.split('/')[4]
                            archive_date = datetime.strptime(timestamp[:8], "%Y%m%d")
                            age = (datetime.now() - archive_date).days
                            if age <= max_age_days:
                                return archive_url
                        except:
                            pass
                    elif not max_age_days:
                        return archive_url
    except Exception as e:
        print(f"Error checking archive: {e}")
    
    return None


def archive_url(url: str, rate_limiter: Optional[RateLimiter] = None) -> Dict[str, Any]:
    """
    Archive a URL to Archive.org.
    
    Args:
        url: URL to archive
        rate_limiter: Optional rate limiter instance
        
    Returns:
        Dictionary with 'success' boolean and 'message' string
    """
    if rate_limiter:
        rate_limiter.wait_if_needed()
    
    save_api = f"https://web.archive.org/save/{url}"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Kleptocracy Timeline Archiver - Respectful rate limiting'
    })
    
    try:
        response = session.get(save_api, timeout=30)
        
        if response.status_code == 200:
            if rate_limiter:
                rate_limiter.handle_success()
            return {'success': True, 'message': 'Archived successfully'}
        
        elif response.status_code == 429:
            if rate_limiter:
                rate_limiter.handle_429()
            return {'success': False, 'message': 'Rate limited (429)'}
        
        elif response.status_code == 404:
            return {'success': False, 'message': 'URL not found (404)'}
        
        else:
            if rate_limiter:
                rate_limiter.handle_failure()
            return {'success': False, 'message': f'HTTP {response.status_code}'}
            
    except requests.exceptions.ConnectionError:
        if rate_limiter:
            rate_limiter.handle_failure()
        return {'success': False, 'message': 'Connection refused'}
        
    except requests.exceptions.Timeout:
        if rate_limiter:
            rate_limiter.handle_failure()
        return {'success': False, 'message': 'Request timeout'}
        
    except Exception as e:
        if rate_limiter:
            rate_limiter.handle_failure()
        return {'success': False, 'message': str(e)[:100]}


def get_archive_url(original_url: str) -> str:
    """
    Get the Archive.org URL for a given URL.
    
    Args:
        original_url: Original URL
        
    Returns:
        Archive.org URL format
    """
    return f"https://web.archive.org/web/*/{original_url}"


def extract_urls_from_event(event: Dict[str, Any]) -> list:
    """
    Extract all URLs from an event.
    
    Args:
        event: Event dictionary
        
    Returns:
        List of URLs found in the event
    """
    urls = []
    
    # Extract from sources
    if 'sources' in event and isinstance(event['sources'], list):
        for source in event['sources']:
            if isinstance(source, dict) and 'url' in source:
                url = source['url']
                if url and isinstance(url, str) and url.startswith('http'):
                    urls.append(url)
    
    # Could also extract from archive_urls if present
    if 'archive_urls' in event and isinstance(event['archive_urls'], list):
        urls.extend([url for url in event['archive_urls'] if url.startswith('http')])
    
    return urls