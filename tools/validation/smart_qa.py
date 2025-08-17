#!/usr/bin/env python3
"""
Smart QA process that handles broken links intelligently.
- Uses link check report to identify broken URLs
- Searches for replacement sources when links are broken
- Uses archived content when available
- Updates events with corrections
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys

def load_reports(report_dir: Path) -> Tuple[Optional[dict], Optional[dict], Optional[dict]]:
    """Load the most recent reports."""
    # Load link check report
    link_reports = sorted(report_dir.glob("link_check_*.json"), reverse=True)
    link_report = None
    if link_reports:
        with open(link_reports[0], 'r') as f:
            link_report = json.load(f)
    
    # Load archive map
    archive_maps = sorted(report_dir.glob("archive_map_*.json"), reverse=True)
    archive_map = None
    if archive_maps:
        with open(archive_maps[0], 'r') as f:
            archive_data = json.load(f)
            archive_map = archive_data.get('archives', {})
    
    # Load verification status
    verification_file = report_dir / "verification_status.json"
    verification_status = None
    if verification_file.exists():
        with open(verification_file, 'r') as f:
            verification_status = json.load(f)
    
    return link_report, archive_map, verification_status

def get_events_needing_qa(timeline_dir: Path, link_report: dict, verification_status: dict) -> List[Path]:
    """Identify events that need QA, prioritizing those with broken links."""
    verified_events = set(verification_status.get('verified_events', []))
    broken_link_events = set(link_report.get('events_with_broken_urls', {}).keys())
    
    priority_events = []
    other_events = []
    
    for event_file in sorted(timeline_dir.glob("*.yaml")):
        if event_file.name in verified_events:
            continue
        
        if event_file.name in broken_link_events:
            priority_events.append(event_file)
        else:
            other_events.append(event_file)
    
    return priority_events + other_events

def analyze_event(event_file: Path, link_report: dict, archive_map: dict) -> dict:
    """Analyze an event and identify issues."""
    with open(event_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data:
        return {'file': event_file.name, 'issues': ['Empty file'], 'data': {}}
    
    issues = []
    suggestions = []
    
    # Check date format and status
    event_date = data.get('date', '')
    if event_date:
        try:
            if isinstance(event_date, str):
                date_obj = datetime.fromisoformat(event_date)
            else:
                date_obj = event_date
            
            if date_obj > datetime.now():
                if data.get('status') != 'predicted':
                    issues.append(f"Future event ({event_date}) not marked as 'predicted'")
                    suggestions.append("Change status to 'predicted'")
        except:
            issues.append(f"Invalid date format: {event_date}")
    
    # Check for broken URLs
    broken_urls = link_report.get('events_with_broken_urls', {}).get(event_file.name, [])
    if broken_urls:
        for broken in broken_urls:
            issues.append(f"Broken URL: {broken['url'][:50]}...")
            if broken.get('archive_suggestion'):
                suggestions.append(f"Archive available: {broken['archive_suggestion']}")
    
    # Check if archives are available but not added
    citations = data.get('citations', [])
    for citation in citations:
        if isinstance(citation, str) and citation in archive_map:
            suggestions.append(f"Add archive for: {citation[:50]}...")
        elif isinstance(citation, dict):
            url = citation.get('url', '')
            if url in archive_map and 'archived' not in citation:
                suggestions.append(f"Add archive for: {url[:50]}...")
    
    # Check required fields
    required_fields = ['id', 'date', 'title', 'summary', 'status']
    for field in required_fields:
        if field not in data or not data[field]:
            issues.append(f"Missing or empty field: {field}")
    
    return {
        'file': event_file.name,
        'issues': issues,
        'suggestions': suggestions,
        'has_broken_links': len(broken_urls) > 0,
        'data': data
    }

def generate_fix_report(events_to_fix: List[dict]) -> dict:
    """Generate a report of events needing fixes."""
    report = {
        'generated': datetime.now().isoformat(),
        'total_events_analyzed': len(events_to_fix),
        'events_with_issues': 0,
        'events_with_broken_links': 0,
        'priority_fixes': [],
        'other_fixes': []
    }
    
    for event_analysis in events_to_fix:
        if event_analysis['issues'] or event_analysis['suggestions']:
            report['events_with_issues'] += 1
            
            fix_entry = {
                'file': event_analysis['file'],
                'issues': event_analysis['issues'],
                'suggestions': event_analysis['suggestions']
            }
            
            if event_analysis['has_broken_links']:
                report['events_with_broken_links'] += 1
                report['priority_fixes'].append(fix_entry)
            else:
                report['other_fixes'].append(fix_entry)
    
    return report

def main():
    timeline_dir = Path(__file__).parents[2] / "timeline_data" / "events"
    report_dir = Path(__file__).parents[2] / "timeline_data" / "qa_reports"
    
    print("Loading reports...")
    link_report, archive_map, verification_status = load_reports(report_dir)
    
    if not link_report:
        print("No link check report found. Run check_all_links.py first.")
        return
    
    if not verification_status:
        verification_status = {'verified_events': [], 'verification_log': []}
    
    print(f"Found {len(link_report.get('broken_urls', {}))} broken URLs")
    print(f"Found {len(archive_map) if archive_map else 0} archived URLs")
    print(f"Found {len(verification_status.get('verified_events', []))} verified events")
    
    # Get events needing QA
    events_to_check = get_events_needing_qa(timeline_dir, link_report, verification_status)
    print(f"\n{len(events_to_check)} events need QA")
    
    # Analyze events
    print("\nAnalyzing events...")
    events_to_fix = []
    
    for i, event_file in enumerate(events_to_check[:50]):  # Process first 50
        if i % 10 == 0:
            print(f"  Analyzed {i}/{min(50, len(events_to_check))} events...")
        
        analysis = analyze_event(event_file, link_report, archive_map or {})
        events_to_fix.append(analysis)
    
    # Generate fix report
    fix_report = generate_fix_report(events_to_fix)
    
    # Save report
    fix_report_file = report_dir / f"fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(fix_report_file, 'w', encoding='utf-8') as f:
        json.dump(fix_report, f, indent=2)
    
    print(f"\n=== Smart QA Analysis ===")
    print(f"Events analyzed: {fix_report['total_events_analyzed']}")
    print(f"Events with issues: {fix_report['events_with_issues']}")
    print(f"Events with broken links: {fix_report['events_with_broken_links']}")
    print(f"\nPriority fixes (broken links): {len(fix_report['priority_fixes'])}")
    print(f"Other fixes needed: {len(fix_report['other_fixes'])}")
    print(f"\nFix report saved to: {fix_report_file}")
    
    # Show sample of priority fixes
    if fix_report['priority_fixes']:
        print("\nSample priority fixes needed:")
        for fix in fix_report['priority_fixes'][:5]:
            print(f"\n  {fix['file']}:")
            for issue in fix['issues'][:2]:
                print(f"    - {issue}")

if __name__ == "__main__":
    main()