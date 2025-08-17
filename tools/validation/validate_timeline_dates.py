#!/usr/bin/env python3
"""
Validate timeline dates and verification status.

This script checks for:
1. Future dates with confirmed status
2. Proper date formats
3. Verification requirements
"""

import os
import yaml
from datetime import datetime, date
from pathlib import Path
import json
import sys

def load_timeline_file(filepath):
    """Load a timeline YAML file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def validate_timeline_dates(timeline_dir="timeline_data/events"):
    """Validate all timeline files for date and verification issues."""
    
    issues = {
        'future_confirmed': [],
        'invalid_dates': [],
        'unverified_confirmed': [],
        'missing_status': []
    }
    
    today = date.today()
    timeline_path = Path(timeline_dir)
    
    for yaml_file in timeline_path.glob("*.yaml"):
        if yaml_file.name.startswith('.'):
            continue
            
        try:
            data = load_timeline_file(yaml_file)
            
            # Check for missing status
            if 'status' not in data:
                issues['missing_status'].append({
                    'file': yaml_file.name,
                    'title': data.get('title', 'Unknown')
                })
                continue
            
            # Parse date
            event_date = data.get('date')
            if not event_date:
                issues['invalid_dates'].append({
                    'file': yaml_file.name,
                    'error': 'Missing date field'
                })
                continue
                
            # Convert to date object
            if isinstance(event_date, str):
                try:
                    event_date = datetime.fromisoformat(event_date).date()
                except:
                    issues['invalid_dates'].append({
                        'file': yaml_file.name,
                        'error': f'Invalid date format: {event_date}'
                    })
                    continue
            elif hasattr(event_date, 'date'):
                event_date = event_date.date()
            elif not isinstance(event_date, date):
                event_date = date(event_date.year, event_date.month, event_date.day)
            
            # Check for future dates with confirmed status
            if event_date > today and data.get('status') == 'confirmed':
                issues['future_confirmed'].append({
                    'file': yaml_file.name,
                    'date': str(event_date),
                    'title': data.get('title', 'Unknown'),
                    'status': data.get('status')
                })
            
            # Check for confirmed status without proper verification
            if data.get('status') == 'confirmed':
                sources = data.get('sources', [])
                if not sources:
                    issues['unverified_confirmed'].append({
                        'file': yaml_file.name,
                        'title': data.get('title', 'Unknown'),
                        'reason': 'No sources provided'
                    })
                # Note: Actual content verification would require fetching and analyzing sources
                
        except Exception as e:
            issues['invalid_dates'].append({
                'file': yaml_file.name,
                'error': str(e)
            })
    
    return issues

def print_report(issues):
    """Print validation report."""
    
    print("Timeline Validation Report")
    print("=" * 60)
    print(f"Generated: {datetime.now().isoformat()}")
    print()
    
    # Future confirmed events
    if issues['future_confirmed']:
        print(f"❌ CRITICAL: {len(issues['future_confirmed'])} future events marked as confirmed:")
        for item in issues['future_confirmed']:
            print(f"  - {item['file']}: {item['date']} - {item['title']}")
        print()
    
    # Invalid dates
    if issues['invalid_dates']:
        print(f"⚠️  WARNING: {len(issues['invalid_dates'])} files with invalid dates:")
        for item in issues['invalid_dates']:
            print(f"  - {item['file']}: {item['error']}")
        print()
    
    # Unverified confirmed
    if issues['unverified_confirmed']:
        print(f"⚠️  WARNING: {len(issues['unverified_confirmed'])} confirmed events without proper verification:")
        for item in issues['unverified_confirmed'][:5]:  # Show first 5
            print(f"  - {item['file']}: {item['reason']}")
        if len(issues['unverified_confirmed']) > 5:
            print(f"  ... and {len(issues['unverified_confirmed']) - 5} more")
        print()
    
    # Missing status
    if issues['missing_status']:
        print(f"ℹ️  INFO: {len(issues['missing_status'])} files missing status field:")
        for item in issues['missing_status'][:5]:  # Show first 5
            print(f"  - {item['file']}")
        if len(issues['missing_status']) > 5:
            print(f"  ... and {len(issues['missing_status']) - 5} more")
        print()
    
    # Summary
    total_issues = sum(len(v) for v in issues.values())
    if total_issues == 0:
        print("✅ All timeline dates and statuses are valid!")
    else:
        print(f"Total issues found: {total_issues}")
        
    return total_issues

def main():
    """Main function."""
    issues = validate_timeline_dates()
    
    # Save report
    report_dir = Path("timeline_data/reports")
    report_dir.mkdir(exist_ok=True)
    
    report_file = report_dir / f"date_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(issues, f, indent=2, default=str)
    
    print_report(issues)
    print(f"\nDetailed report saved to: {report_file}")
    
    # Exit with error if critical issues found
    if issues['future_confirmed']:
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    main()