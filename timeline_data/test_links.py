#!/usr/bin/env python3
"""
Quick link testing script to check URL accessibility for timeline events.
"""

import os
import yaml
import requests
import time
from datetime import datetime
from urllib.parse import urlparse

def test_links():
    """Test all URLs in YAML files"""
    events_dir = "events"
    
    if not os.path.exists(events_dir):
        print("Events directory not found!")
        return
    
    print("Testing links in timeline events...")
    print("=" * 60)
    
    total_urls = 0
    working_urls = 0
    failed_urls = 0
    
    yaml_files = [f for f in os.listdir(events_dir) if f.endswith('.yaml')]
    yaml_files.sort()
    
    print(f"Found {len(yaml_files)} YAML files to check")
    print("=" * 60)
    
    for filename in yaml_files:
        filepath = os.path.join(events_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if 'sources' not in data:
                continue
                
            sources = data['sources']
            if not isinstance(sources, list):
                continue
            
            for source in sources:
                if not isinstance(source, dict) or 'url' not in source:
                    continue
                
                url = source['url']
                if not url or url.startswith('http') == False:
                    continue
                
                total_urls += 1
                
                try:
                    # Quick test with short timeout
                    response = requests.head(url, timeout=10, allow_redirects=True,
                                           headers={'User-Agent': 'Mozilla/5.0 (compatible; LinkChecker)'})
                    
                    if response.status_code < 400:
                        working_urls += 1
                        status = "✅"
                    else:
                        failed_urls += 1
                        status = f"❌ {response.status_code}"
                        print(f"{filename}: {url} - {status}")
                        
                except requests.exceptions.RequestException as e:
                    failed_urls += 1
                    status = f"❌ {str(e)[:50]}"
                    print(f"{filename}: {url} - {status}")
                
                # Small delay to be respectful
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    print("=" * 60)
    print("LINK TESTING SUMMARY:")
    print(f"  Total URLs tested: {total_urls}")
    print(f"  ✅ Working: {working_urls} ({working_urls/total_urls*100:.1f}%)")
    print(f"  ❌ Failed: {failed_urls} ({failed_urls/total_urls*100:.1f}%)")
    print("=" * 60)
    
    # Save summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_urls": total_urls,
        "working_urls": working_urls, 
        "failed_urls": failed_urls,
        "success_rate": f"{working_urls/total_urls*100:.1f}%"
    }
    
    with open("link_test_summary.json", 'w') as f:
        import json
        json.dump(summary, f, indent=2)
    
    print("Summary saved to link_test_summary.json")

if __name__ == "__main__":
    test_links()