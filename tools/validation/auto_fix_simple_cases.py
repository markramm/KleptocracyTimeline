#!/usr/bin/env python3
"""
Automatically fix simple URL issues in timeline events.
Handles common patterns like http->https, domain changes, etc.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import re

# Domain migration mappings
DOMAIN_MIGRATIONS = {
    'twitter.com': 'x.com',
    'www.twitter.com': 'www.x.com',
    'mobile.twitter.com': 'x.com',
}

# Known working URL patterns to replace broken ones
URL_REPLACEMENTS = {
    # Supreme Court cases
    r'supremecourt\.gov/opinions/\d+pdf': 'supremecourt.gov/opinions/boundvolumes',
    r'supremecourt\.gov/DocketPDF': 'supremecourt.gov/docket/docketfiles',
    
    # Government sites
    r'whitehouse\.gov/briefing-room/.*-\d{4}/\d{2}/': 'whitehouse.gov/briefing-room/statements-releases/',
    
    # Archive.org patterns
    r'web\.archive\.org/web/\d+/': 'web.archive.org/web/*/',
}

def fix_protocol(url: str) -> str:
    """Fix http -> https for known secure domains."""
    secure_domains = [
        'nytimes.com', 'washingtonpost.com', 'cnn.com', 'npr.org',
        'bbc.com', 'reuters.com', 'apnews.com', 'bloomberg.com',
        'wsj.com', 'theguardian.com', 'nbcnews.com', 'foxnews.com',
        'politico.com', 'axios.com', 'thehill.com', '.gov',
        'wikipedia.org', 'archive.org', 'justia.com', 'scotusblog.com'
    ]
    
    if url.startswith('http://'):
        for domain in secure_domains:
            if domain in url:
                return url.replace('http://', 'https://', 1)
    return url

def fix_domain_migration(url: str) -> str:
    """Fix known domain migrations."""
    for old_domain, new_domain in DOMAIN_MIGRATIONS.items():
        if old_domain in url:
            return url.replace(old_domain, new_domain)
    return url

def fix_archive_url(url: str) -> str:
    """Fix common archive.org URL issues."""
    # Fix missing wildcards
    if 'web.archive.org/web/' in url and '/*/' not in url:
        # Extract the original URL
        match = re.search(r'web\.archive\.org/web/\d+/(.*)', url)
        if match:
            original_url = match.group(1)
            return f"https://web.archive.org/web/*/{original_url}"
    return url

def normalize_url(url: str) -> str:
    """Normalize URL formatting."""
    # Remove trailing slashes
    url = url.rstrip('/')
    
    # Fix double slashes (except after protocol)
    url = re.sub(r'([^:])/+', r'\1/', url)
    
    # Ensure protocol
    if not url.startswith(('http://', 'https://', 'ftp://')):
        if any(domain in url for domain in ['.com', '.org', '.net', '.gov', '.edu']):
            url = 'https://' + url
    
    return url

def fix_date_in_filename(filename: str, event_data: dict) -> Tuple[str, bool]:
    """Check if filename date matches event date."""
    if 'date' not in event_data:
        return filename, False
    
    event_date = str(event_data['date'])
    # Extract date from filename
    filename_match = re.match(r'^(\d{4}-\d{2}-\d{2})', filename)
    if filename_match:
        filename_date = filename_match.group(1)
        if filename_date != event_date[:10]:
            # Date mismatch - suggest new filename
            new_filename = filename.replace(filename_date, event_date[:10])
            return new_filename, True
    
    return filename, False

def fix_event_urls(event_data: dict) -> Tuple[dict, List[str]]:
    """Fix URLs in an event and return updated data with changes."""
    changes = []
    
    # Fix citations
    if 'citations' in event_data:
        for i, citation in enumerate(event_data['citations']):
            if isinstance(citation, str):
                original = citation
                fixed = fix_protocol(citation)
                fixed = fix_domain_migration(fixed)
                fixed = fix_archive_url(fixed)
                fixed = normalize_url(fixed)
                
                if fixed != original:
                    event_data['citations'][i] = fixed
                    changes.append(f"Fixed URL: {original[:50]}... -> {fixed[:50]}...")
            
            elif isinstance(citation, dict):
                if 'url' in citation:
                    original = citation['url']
                    fixed = fix_protocol(original)
                    fixed = fix_domain_migration(fixed)
                    fixed = normalize_url(fixed)
                    
                    if fixed != original:
                        citation['url'] = fixed
                        changes.append(f"Fixed URL: {original[:50]}... -> {fixed[:50]}...")
                
                if 'archived' in citation:
                    original = citation['archived']
                    fixed = fix_archive_url(original)
                    fixed = normalize_url(fixed)
                    
                    if fixed != original:
                        citation['archived'] = fixed
                        changes.append(f"Fixed archive URL: {original[:50]}... -> {fixed[:50]}...")
    
    # Fix sources (legacy field)
    if 'sources' in event_data:
        for i, source in enumerate(event_data['sources']):
            if isinstance(source, str):
                original = source
                fixed = fix_protocol(source)
                fixed = fix_domain_migration(fixed)
                fixed = normalize_url(fixed)
                
                if fixed != original:
                    event_data['sources'][i] = fixed
                    changes.append(f"Fixed source URL: {original[:50]}... -> {fixed[:50]}...")
            
            elif isinstance(source, dict) and 'url' in source:
                original = source['url']
                fixed = fix_protocol(original)
                fixed = fix_domain_migration(fixed)
                fixed = normalize_url(fixed)
                
                if fixed != original:
                    source['url'] = fixed
                    changes.append(f"Fixed source URL: {original[:50]}... -> {fixed[:50]}...")
    
    return event_data, changes

def main():
    """Main function to auto-fix simple URL issues."""
    timeline_dir = Path.cwd() / "timeline_data" / "events"
    report_dir = Path.cwd() / "timeline_data" / "qa_reports"
    
    if not timeline_dir.exists():
        print(f"Timeline directory not found: {timeline_dir}")
        return
    
    print("Scanning for simple URL fixes...")
    
    total_fixes = 0
    fixed_files = []
    rename_suggestions = []
    
    for yaml_file in sorted(timeline_dir.glob("*.yaml")):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                continue
            
            # Check for date mismatches
            new_filename, needs_rename = fix_date_in_filename(yaml_file.name, data)
            if needs_rename:
                rename_suggestions.append({
                    'current': yaml_file.name,
                    'suggested': new_filename,
                    'reason': 'Date mismatch between filename and event date'
                })
            
            # Fix URLs
            original_data = json.dumps(data, sort_keys=True)
            fixed_data, changes = fix_event_urls(data)
            
            if changes:
                # Save the fixed file
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump(fixed_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
                
                fixed_files.append({
                    'file': yaml_file.name,
                    'changes': changes
                })
                total_fixes += len(changes)
                print(f"  Fixed {len(changes)} URLs in {yaml_file.name}")
        
        except Exception as e:
            print(f"  Error processing {yaml_file.name}: {e}")
    
    # Generate report
    report = {
        'total_files_fixed': len(fixed_files),
        'total_url_fixes': total_fixes,
        'files_fixed': fixed_files,
        'rename_suggestions': rename_suggestions
    }
    
    # Save report
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "auto_fixes_report.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n=== Auto-Fix Summary ===")
    print(f"Files fixed: {len(fixed_files)}")
    print(f"Total URL fixes: {total_fixes}")
    print(f"Files needing rename: {len(rename_suggestions)}")
    
    if rename_suggestions:
        print("\nFiles that should be renamed:")
        for suggestion in rename_suggestions[:5]:
            print(f"  {suggestion['current']} -> {suggestion['suggested']}")
        if len(rename_suggestions) > 5:
            print(f"  ... and {len(rename_suggestions) - 5} more")
    
    print(f"\nReport saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    main()