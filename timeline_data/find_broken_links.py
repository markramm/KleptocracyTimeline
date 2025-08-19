#!/usr/bin/env python3
"""
Find broken links in timeline events
"""

import os
import yaml
import re
from collections import defaultdict

def check_archive_url_format(url):
    """Check if archive.org URL is properly formatted"""
    if not url or not isinstance(url, str):
        return None
    
    if 'archive.org' in url or 'archive.is' in url:
        # Check for common issues
        if 'archive.org/save/' in url:
            return "Uses /save/ instead of /web/"
        if not re.match(r'https://web\.archive\.org/web/\d{14}/', url):
            if 'web.archive.org' in url:
                return "Incorrect archive.org format"
    return None

def find_issues():
    events_dir = 'events'
    issues = defaultdict(list)
    
    for filename in sorted(os.listdir(events_dir)):
        if not filename.endswith('.yaml'):
            continue
            
        filepath = os.path.join(events_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if not data:
                continue
                
            # Check for events before 2024
            date = data.get('date', '')
            if date and date < '2024':
                
                # Check sources
                sources = data.get('sources', [])
                for source in sources:
                    if isinstance(source, dict):
                        url = source.get('url', '')
                        
                        # Check for broken patterns
                        if 'whitehouse.gov/presidential-actions' in url:
                            issues['broken_whitehouse'].append((filename, url))
                        elif 'twitter.com' in url and 'x.com' not in url:
                            issues['twitter_not_x'].append((filename, url))
                        elif url == 'Research Document':
                            issues['research_placeholder'].append((filename, url))
                        
                        # Check archive URLs
                        archive_url = source.get('archive_url', '')
                        issue = check_archive_url_format(archive_url)
                        if issue:
                            issues['archive_format'].append((filename, archive_url, issue))
                            
        except Exception as e:
            issues['parse_errors'].append((filename, str(e)))
    
    return issues

def main():
    print("Finding broken links and issues in timeline events...")
    print("=" * 60)
    
    issues = find_issues()
    
    if issues['broken_whitehouse']:
        print(f"\n❌ Broken whitehouse.gov links ({len(issues['broken_whitehouse'])} found):")
        for filename, url in issues['broken_whitehouse'][:5]:
            print(f"  {filename}: {url[:80]}...")
            
    if issues['twitter_not_x']:
        print(f"\n❌ Old twitter.com links ({len(issues['twitter_not_x'])} found):")
        for filename, url in issues['twitter_not_x'][:5]:
            print(f"  {filename}: {url[:80]}...")
            
    if issues['archive_format']:
        print(f"\n❌ Incorrect archive.org format ({len(issues['archive_format'])} found):")
        for filename, url, issue in issues['archive_format'][:5]:
            print(f"  {filename}: {issue}")
            print(f"    {url[:80]}...")
            
    if issues['research_placeholder']:
        print(f"\n⚠️  Research Document placeholders ({len(issues['research_placeholder'])} found):")
        for filename, _ in issues['research_placeholder'][:5]:
            print(f"  {filename}")
            
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    total_issues = sum(len(v) for v in issues.values())
    print(f"  Total issues found: {total_issues}")
    for issue_type, items in issues.items():
        if items:
            print(f"  - {issue_type}: {len(items)}")

if __name__ == "__main__":
    main()