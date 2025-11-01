#!/usr/bin/env python3
"""
Link Validator Service - Validates source URLs for timeline events

Provides URL validation, broken link detection, and source quality assessment.
"""

import logging
import requests
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime, timezone
import time

logger = logging.getLogger(__name__)


class LinkValidator:
    """Validates source URLs and detects broken links"""

    # Suspicious URL patterns that don't need HTTP checking
    SUSPICIOUS_PATTERNS = [
        'example.com',
        'TBD',
        'internal-research',
        'internal-research-portal',
        'localhost',
        '127.0.0.1',
        'placeholder',
    ]

    # Severity levels
    SEVERITY_CRITICAL = 'critical'  # example.com, TBD, etc.
    SEVERITY_HIGH = 'high'          # 404, DNS failure
    SEVERITY_MEDIUM = 'medium'      # Timeout, redirect issues
    SEVERITY_LOW = 'low'            # Minor issues

    def __init__(self, timeout: int = 10, max_redirects: int = 5):
        """
        Initialize LinkValidator

        Args:
            timeout: Request timeout in seconds
            max_redirects: Maximum number of redirects to follow
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.session = requests.Session()
        self.session.max_redirects = max_redirects

    def validate_url(self, url: str, check_http: bool = False) -> Dict[str, Any]:
        """
        Validate a single URL

        Args:
            url: URL to validate
            check_http: Whether to perform HTTP HEAD request

        Returns:
            Dict with validation results:
            {
                'url': str,
                'valid': bool,
                'severity': str,
                'issues': List[str],
                'status_code': Optional[int],
                'redirected': bool,
                'final_url': Optional[str],
                'checked_at': str
            }
        """
        result = {
            'url': url,
            'valid': True,
            'severity': None,
            'issues': [],
            'status_code': None,
            'redirected': False,
            'final_url': None,
            'checked_at': datetime.now(timezone.utc).isoformat()
        }

        # Check for None or empty
        if not url:
            result['valid'] = False
            result['severity'] = self.SEVERITY_CRITICAL
            result['issues'].append('URL is empty or None')
            return result

        # Check for non-string
        if not isinstance(url, str):
            result['valid'] = False
            result['severity'] = self.SEVERITY_CRITICAL
            result['issues'].append(f'URL is not a string: {type(url).__name__}')
            return result

        # Check for suspicious patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern.lower() in url.lower():
                result['valid'] = False
                result['severity'] = self.SEVERITY_CRITICAL
                result['issues'].append(f'Suspicious URL pattern: {pattern}')

        # Validate URL structure
        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                result['valid'] = False
                result['severity'] = self.SEVERITY_CRITICAL
                result['issues'].append('Missing URL scheme (http/https)')
            if not parsed.netloc:
                result['valid'] = False
                result['severity'] = self.SEVERITY_CRITICAL
                result['issues'].append('Missing domain/netloc')
        except Exception as e:
            result['valid'] = False
            result['severity'] = self.SEVERITY_CRITICAL
            result['issues'].append(f'Invalid URL structure: {str(e)}')
            return result

        # Perform HTTP check if requested and URL structure is valid
        if check_http and result['valid']:
            http_result = self._check_http(url)
            result.update(http_result)

        return result

    def _check_http(self, url: str) -> Dict[str, Any]:
        """
        Perform HTTP HEAD request to check URL accessibility

        Args:
            url: URL to check

        Returns:
            Dict with HTTP check results
        """
        result = {
            'status_code': None,
            'redirected': False,
            'final_url': None,
            'valid': True,
            'issues': [],
            'severity': None
        }

        try:
            # Use HEAD request for efficiency
            response = self.session.head(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                headers={'User-Agent': 'Research-Monitor-Link-Validator/1.0'}
            )

            result['status_code'] = response.status_code

            # Check if redirected
            if response.history:
                result['redirected'] = True
                result['final_url'] = response.url
                result['issues'].append(f'Redirected through {len(response.history)} hop(s)')
                result['severity'] = self.SEVERITY_LOW

            # Check status code
            if response.status_code == 404:
                result['valid'] = False
                result['severity'] = self.SEVERITY_HIGH
                result['issues'].append('404 Not Found')
            elif response.status_code == 403:
                result['valid'] = False
                result['severity'] = self.SEVERITY_MEDIUM
                result['issues'].append('403 Forbidden (access denied)')
            elif response.status_code >= 500:
                result['valid'] = False
                result['severity'] = self.SEVERITY_MEDIUM
                result['issues'].append(f'Server error: {response.status_code}')
            elif response.status_code >= 400:
                result['valid'] = False
                result['severity'] = self.SEVERITY_MEDIUM
                result['issues'].append(f'Client error: {response.status_code}')

        except requests.exceptions.Timeout:
            result['valid'] = False
            result['severity'] = self.SEVERITY_MEDIUM
            result['issues'].append(f'Timeout after {self.timeout}s')
        except requests.exceptions.TooManyRedirects:
            result['valid'] = False
            result['severity'] = self.SEVERITY_MEDIUM
            result['issues'].append(f'Too many redirects (>{self.max_redirects})')
        except requests.exceptions.ConnectionError:
            result['valid'] = False
            result['severity'] = self.SEVERITY_HIGH
            result['issues'].append('Connection failed (DNS/network error)')
        except requests.exceptions.SSLError as e:
            result['valid'] = False
            result['severity'] = self.SEVERITY_MEDIUM
            result['issues'].append(f'SSL/TLS error: {str(e)[:100]}')
        except Exception as e:
            result['valid'] = False
            result['severity'] = self.SEVERITY_MEDIUM
            result['issues'].append(f'Unexpected error: {str(e)[:100]}')
            logger.warning(f"Error checking URL {url}: {e}")

        return result

    def validate_event_sources(self, event: Dict[str, Any], check_http: bool = False) -> Dict[str, Any]:
        """
        Validate all sources in an event

        Args:
            event: Event dictionary with 'sources' field
            check_http: Whether to perform HTTP checks

        Returns:
            Dict with validation summary:
            {
                'event_id': str,
                'total_sources': int,
                'valid_sources': int,
                'invalid_sources': int,
                'suspicious_sources': int,
                'severity': str (highest severity found),
                'issues': List[Dict],  # Issue details per source
                'checked_at': str
            }
        """
        result = {
            'event_id': event.get('id', 'unknown'),
            'total_sources': 0,
            'valid_sources': 0,
            'invalid_sources': 0,
            'suspicious_sources': 0,
            'severity': None,
            'issues': [],
            'checked_at': datetime.now(timezone.utc).isoformat()
        }

        sources = event.get('sources', [])
        if not isinstance(sources, list):
            result['issues'].append({
                'issue': 'Sources field is not a list',
                'severity': self.SEVERITY_CRITICAL
            })
            result['severity'] = self.SEVERITY_CRITICAL
            return result

        result['total_sources'] = len(sources)

        for idx, source in enumerate(sources):
            if not isinstance(source, dict):
                result['issues'].append({
                    'index': idx,
                    'issue': 'Source is not a dictionary',
                    'severity': self.SEVERITY_CRITICAL
                })
                result['invalid_sources'] += 1
                continue

            url = source.get('url')
            validation = self.validate_url(url, check_http=check_http)

            if not validation['valid']:
                result['invalid_sources'] += 1
                result['issues'].append({
                    'index': idx,
                    'url': url,
                    'outlet': source.get('outlet', 'Unknown'),
                    'title': source.get('title', 'Unknown'),
                    'validation': validation
                })

                # Track highest severity
                if validation['severity'] == self.SEVERITY_CRITICAL:
                    result['suspicious_sources'] += 1
                    result['severity'] = self.SEVERITY_CRITICAL
                elif validation['severity'] == self.SEVERITY_HIGH and result['severity'] != self.SEVERITY_CRITICAL:
                    result['severity'] = self.SEVERITY_HIGH
                elif validation['severity'] == self.SEVERITY_MEDIUM and not result['severity']:
                    result['severity'] = self.SEVERITY_MEDIUM
            else:
                result['valid_sources'] += 1

        return result

    def generate_report(self, events: List[Dict[str, Any]], check_http: bool = False) -> Dict[str, Any]:
        """
        Generate comprehensive broken link report for multiple events

        Args:
            events: List of event dictionaries
            check_http: Whether to perform HTTP checks

        Returns:
            Dict with report summary
        """
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_events': len(events),
            'events_with_issues': 0,
            'total_sources': 0,
            'valid_sources': 0,
            'invalid_sources': 0,
            'suspicious_sources': 0,
            'severity_breakdown': {
                self.SEVERITY_CRITICAL: 0,
                self.SEVERITY_HIGH: 0,
                self.SEVERITY_MEDIUM: 0,
                self.SEVERITY_LOW: 0,
            },
            'events': []
        }

        for event in events:
            validation = self.validate_event_sources(event, check_http=check_http)

            report['total_sources'] += validation['total_sources']
            report['valid_sources'] += validation['valid_sources']
            report['invalid_sources'] += validation['invalid_sources']
            report['suspicious_sources'] += validation['suspicious_sources']

            if validation['invalid_sources'] > 0:
                report['events_with_issues'] += 1
                report['events'].append(validation)

                # Count severity breakdown
                if validation['severity']:
                    report['severity_breakdown'][validation['severity']] += 1

        return report
