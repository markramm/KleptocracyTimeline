#!/usr/bin/env python3
"""
Check all links in timeline events and create a status report.
This helps identify broken links that need fixing during QA.
"""

import json
import yaml
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse

def check_url(url: str, timeout: int = 10) -> Tuple[str, bool, int, str]:
    """Check if a URL is accessible."""
    try:
        # Handle different URL formats
        if not url.startswith(('http://', 'https://')):
            return url, False, 0, "Invalid URL format"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        if response.status_code == 405:  # Method not allowed, try GET
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
        
        is_valid = response.status_code < 400
        return url, is_valid, response.status_code, "OK" if is_valid else f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return url, False, 0, "Timeout"
    except requests.exceptions.ConnectionError:
        return url, False, 0, "Connection error"
    except Exception as e:
        return url, False, 0, str(e)[:50]

def extract_urls_from_event(event_data: dict) -> List[str]:
    """Extract all URLs from an event."""
    urls = []
    
    # Check citations
    for citation in event_data.get('citations', []):
        if isinstance(citation, str):
            urls.append(citation)
        elif isinstance(citation, dict):
            if 'url' in citation:
                urls.append(citation['url'])
            if 'archived' in citation:
                urls.append(citation['archived'])
    
    # Check sources (legacy field)
    for source in event_data.get('sources', []):
        if isinstance(source, str):
            urls.append(source)
        elif isinstance(source, dict):
            if 'url' in source:
                urls.append(source['url'])
    
    return [u for u in urls if u and isinstance(u, str)]

def check_archive_availability(url: str) -> str:
    """Generate archive.org URL for a given URL."""
    if 'archive.org' in url:
        return url
    # Use wildcard archive URL to find any archived version
    encoded_url = urllib.parse.quote(url, safe='')
    return f"https://web.archive.org/web/*/{url}"

def main():
    timeline_dir = Path(__file__).parents[2] / "timeline_data" / "events"
    report_dir = Path(__file__).parents[2] / "timeline_data" / "qa_reports"
    report_dir.mkdir(exist_ok=True)
    
    print("Scanning timeline events for URLs...")
    
    all_urls = {}
    event_urls = {}
    
    # Collect all URLs from events
    for yaml_file in sorted(timeline_dir.glob("*.yaml")):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                continue
            
            urls = extract_urls_from_event(data)
            if urls:
                event_urls[yaml_file.name] = urls
                for url in urls:
                    if url not in all_urls:
                        all_urls[url] = []
                    all_urls[url].append(yaml_file.name)
        except Exception as e:
            print(f"Error reading {yaml_file.name}: {e}")
    
    print(f"Found {len(all_urls)} unique URLs across {len(event_urls)} events")
    print("Checking URL status (this may take a few minutes)...")
    
    # Check URLs in parallel
    url_status = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_url, url): url for url in all_urls.keys()}
        
        completed = 0
        for future in as_completed(future_to_url):
            url, is_valid, status_code, message = future.result()
            url_status[url] = {
                'valid': is_valid,
                'status_code': status_code,
                'message': message,
                'used_in': all_urls[url],
                'archive_url': check_archive_availability(url) if not is_valid else None
            }
            completed += 1
            if completed % 10 == 0:
                print(f"  Checked {completed}/{len(all_urls)} URLs...")
    
    # Generate report
    broken_urls = {url: info for url, info in url_status.items() if not info['valid']}
    working_urls = {url: info for url, info in url_status.items() if info['valid']}
    
    report = {
        'generated': datetime.now().isoformat(),
        'summary': {
            'total_urls': len(all_urls),
            'working_urls': len(working_urls),
            'broken_urls': len(broken_urls),
            'events_with_urls': len(event_urls),
            'broken_percentage': round(len(broken_urls) / len(all_urls) * 100, 1) if all_urls else 0
        },
        'broken_urls': broken_urls,
        'working_urls': {url: {'used_in': info['used_in']} for url, info in working_urls.items()},
        'events_with_broken_urls': {}
    }
    
    # Map broken URLs to events
    for url, info in broken_urls.items():
        for event_file in info['used_in']:
            if event_file not in report['events_with_broken_urls']:
                report['events_with_broken_urls'][event_file] = []
            report['events_with_broken_urls'][event_file].append({
                'url': url,
                'message': info['message'],
                'archive_suggestion': info['archive_url']
            })
    
    # Save report
    report_file = report_dir / f"link_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    # Also save a simplified version for quick reference
    simple_report_file = report_dir / "broken_links.json"
    with open(simple_report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'generated': report['generated'],
            'summary': report['summary'],
            'events_needing_fixes': list(report['events_with_broken_urls'].keys())
        }, f, indent=2)
    
    print(f"\n=== Link Check Summary ===")
    print(f"Total URLs checked: {len(all_urls)}")
    print(f"Working URLs: {len(working_urls)} ({100 - report['summary']['broken_percentage']:.1f}%)")
    print(f"Broken URLs: {len(broken_urls)} ({report['summary']['broken_percentage']:.1f}%)")
    print(f"Events with broken URLs: {len(report['events_with_broken_urls'])}")
    print(f"\nFull report saved to: {report_file}")
    print(f"Simple report saved to: {simple_report_file}")
    
    return report

if __name__ == "__main__":
    main()