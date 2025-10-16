#!/usr/bin/env python3
"""
INTEGRATION VALIDATION WORKFLOW - Validator 4
Validates and prepares timeline events for kleptocracy timeline integration
"""

from research_api import ResearchAPI
import json
import sys
from datetime import datetime

def main():
    """Execute validation workflow for timeline event integration"""
    
    # Connect to Research Monitor API on port 5560
    print("=== INTEGRATION VALIDATION TASK - Validator 4 ===")
    print("Connecting to Research Monitor API...")
    
    api = ResearchAPI(base_url='http://localhost:5560', api_key='test')
    
    try:
        # Get current system statistics
        print("\n1. RETRIEVING SYSTEM STATISTICS...")
        stats = api.get_stats()
        print(f"Current system stats:")
        print(f"  - Total events: {stats.get('events', {}).get('total', 'N/A')}")
        print(f"  - Staged events: {stats.get('events', {}).get('staged', 'N/A')}")
        print(f"  - Pending priorities: {stats.get('priorities', {}).get('pending', 'N/A')}")
        print(f"  - Server status: {stats.get('status', 'Unknown')}")
        
        # Search for key categories of institutional capture events
        print("\n2. SEARCHING FOR INSTITUTIONAL CAPTURE EVENTS...")
        
        # Focus on media, intelligence and judicial events per task requirements
        print("\n2a. Media suppression and capture events:")
        media_events = api.search_events("media suppression", limit=50)
        print(f"  - Found {len(media_events)} media-related events")
        
        print("\n2b. Intelligence and surveillance events:")
        intelligence_events = api.search_events("surveillance", limit=50) 
        print(f"  - Found {len(intelligence_events)} intelligence-related events")
        
        print("\n2c. Supreme Court and judicial events:")
        judicial_events = api.search_events("Supreme Court", limit=50)
        print(f"  - Found {len(judicial_events)} judicial-related events")
        
        print("\n2d. Powell Memo institutional blueprint events:")
        powell_events = api.search_events("Powell Memo", limit=50)
        print(f"  - Found {len(powell_events)} Powell Memo-related events")
        
        # Additional searches for systematic corruption patterns
        print("\n2e. Corporate capture patterns:")
        corporate_events = api.search_events("regulatory capture", limit=30)
        print(f"  - Found {len(corporate_events)} regulatory capture events")
        
        print("\n2f. Intelligence privatization events:")
        private_intel_events = api.search_events("intelligence privatization", limit=30) 
        print(f"  - Found {len(private_intel_events)} intelligence privatization events")
        
        # Combine all events for comprehensive validation analysis
        all_events = []
        all_events.extend(media_events)
        all_events.extend(intelligence_events) 
        all_events.extend(judicial_events)
        all_events.extend(powell_events)
        all_events.extend(corporate_events)
        all_events.extend(private_intel_events)
        
        # Remove duplicates based on event ID
        unique_events = {}
        for event in all_events:
            event_id = event.get('id')
            if event_id and event_id not in unique_events:
                unique_events[event_id] = event
        
        final_events = list(unique_events.values())
        print(f"\n  TOTAL UNIQUE EVENTS FOR VALIDATION: {len(final_events)}")
        
        # Perform detailed validation analysis
        print("\n3. PERFORMING QUALITY VALIDATION...")
        validation_results = {
            'total_events': len(final_events),
            'accepted': 0,
            'flagged': 0,
            'rejected': 0,
            'validation_issues': [],
            'recommendations': [],
            'category_breakdown': {
                'media_capture': 0,
                'intelligence_surveillance': 0, 
                'judicial_capture': 0,
                'powell_implementation': 0,
                'regulatory_capture': 0,
                'systematic_corruption': 0
            }
        }
        
        print("Analyzing events for validation criteria...")
        
        for event in final_events:
            validation_status = validate_event_quality(event)
            
            if validation_status['status'] == 'accepted':
                validation_results['accepted'] += 1
            elif validation_status['status'] == 'flagged':
                validation_results['flagged'] += 1
                validation_results['validation_issues'].extend(validation_status.get('issues', []))
            else:  # rejected
                validation_results['rejected'] += 1
                validation_results['validation_issues'].extend(validation_status.get('issues', []))
            
            # Categorize events
            categorize_event(event, validation_results['category_breakdown'])
        
        # Generate validation report
        print("\n4. VALIDATION REPORT")
        print("=" * 50)
        print(f"Total Events Analyzed: {validation_results['total_events']}")
        print(f"✅ ACCEPTED: {validation_results['accepted']} ({validation_results['accepted']/validation_results['total_events']*100:.1f}%)")
        print(f"⚠️  FLAGGED: {validation_results['flagged']} ({validation_results['flagged']/validation_results['total_events']*100:.1f}%)")
        print(f"❌ REJECTED: {validation_results['rejected']} ({validation_results['rejected']/validation_results['total_events']*100:.1f}%)")
        
        print(f"\nCATEGORY BREAKDOWN:")
        for category, count in validation_results['category_breakdown'].items():
            print(f"  {category.replace('_', ' ').title()}: {count}")
        
        # Show top validation issues
        if validation_results['validation_issues']:
            print(f"\nTOP VALIDATION ISSUES:")
            issue_counts = {}
            for issue in validation_results['validation_issues']:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  - {issue} ({count} events)")
        
        # Generate recommendations
        generate_recommendations(validation_results, stats)
        
        print(f"\nRECOMMENDATIONS:")
        for rec in validation_results['recommendations']:
            print(f"  • {rec}")
        
        print(f"\n=== VALIDATION COMPLETE ===")
        print(f"Ready for integration: {validation_results['accepted']} events")
        print(f"Needs review: {validation_results['flagged']} events")  
        print(f"Should be excluded: {validation_results['rejected']} events")
        
        return validation_results
        
    except Exception as e:
        print(f"ERROR during validation: {str(e)}")
        return None

def validate_event_quality(event):
    """
    Validate individual event quality based on schema compliance, 
    source credibility, and systematic corruption focus
    """
    issues = []
    status = 'accepted'  # Default to accepted
    
    # Required field validation
    required_fields = ['id', 'date', 'title', 'summary', 'importance']
    for field in required_fields:
        if not event.get(field):
            issues.append(f"Missing required field: {field}")
            status = 'rejected'
    
    # Date format validation  
    date_str = event.get('date', '')
    if date_str:
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            issues.append("Invalid date format - should be YYYY-MM-DD")
            status = 'flagged'
    
    # Importance score validation
    importance = event.get('importance')
    if importance is not None:
        if not isinstance(importance, int) or not (1 <= importance <= 10):
            issues.append("Importance must be integer 1-10")
            status = 'flagged'
    
    # Source credibility check
    sources = event.get('sources', [])
    if not sources:
        issues.append("No sources provided")
        status = 'flagged'
    else:
        credible_sources = check_source_credibility(sources)
        if not credible_sources:
            issues.append("No credible sources found")
            status = 'rejected'
    
    # Systematic corruption focus check
    if not is_systematic_corruption_focused(event):
        issues.append("Event focuses on isolated incident rather than systematic corruption")
        status = 'flagged'
    
    # Check for duplicate indicators in title/summary
    if has_duplicate_indicators(event):
        issues.append("Potential duplicate - similar content exists")
        status = 'rejected'
    
    return {
        'status': status,
        'issues': issues
    }

def check_source_credibility(sources):
    """Check if sources are from credible outlets"""
    credible_domains = [
        'gov', 'edu', 'nytimes.com', 'washingtonpost.com', 'reuters.com',
        'ap.org', 'bbc.com', 'npr.org', 'pbs.org', 'propublica.org',
        'theguardian.com', 'wsj.com', 'ft.com', 'bloomberg.com',
        'congress.gov', 'fbi.gov', 'justice.gov', 'sec.gov'
    ]
    
    for source in sources:
        if isinstance(source, dict):
            url = source.get('url', '')
        else:
            url = str(source)
            
        if url:
            for domain in credible_domains:
                if domain in url.lower():
                    return True
    return False

def is_systematic_corruption_focused(event):
    """Check if event focuses on systematic corruption patterns"""
    systematic_keywords = [
        'capture', 'systematic', 'coordinated', 'network', 'infrastructure',
        'institutional', 'revolving door', 'regulatory capture', 'oligarch',
        'kleptocracy', 'authoritarian', 'powell memo', 'heritage foundation',
        'federalist society', 'corporate state', 'privatization'
    ]
    
    text = f"{event.get('title', '')} {event.get('summary', '')}".lower()
    
    for keyword in systematic_keywords:
        if keyword in text:
            return True
    return False

def has_duplicate_indicators(event):
    """Check for potential duplicate indicators"""
    # This is a simplified check - in practice would compare against existing timeline
    title = event.get('title', '').lower()
    summary = event.get('summary', '').lower()
    
    # Check for common duplicate patterns
    duplicate_indicators = [
        'duplicate', 'repeat', 'already covered', 'same as',
        'identical to', 'previously reported'
    ]
    
    text = f"{title} {summary}"
    for indicator in duplicate_indicators:
        if indicator in text:
            return True
    return False

def categorize_event(event, category_breakdown):
    """Categorize event into institutional capture categories"""
    title = event.get('title', '').lower()
    summary = event.get('summary', '').lower()
    tags = [tag.lower() for tag in event.get('tags', [])]
    
    text = f"{title} {summary} {' '.join(tags)}"
    
    # Media capture patterns
    if any(term in text for term in ['media', 'news', 'journalism', 'broadcast', 'sinclair', 'fox news', 'clear channel']):
        category_breakdown['media_capture'] += 1
    
    # Intelligence/surveillance patterns  
    elif any(term in text for term in ['surveillance', 'nsa', 'cia', 'intelligence', 'fisa', 'spying', 'privacy']):
        category_breakdown['intelligence_surveillance'] += 1
    
    # Judicial capture patterns
    elif any(term in text for term in ['supreme court', 'federal court', 'judge', 'judicial', 'federalist society', 'leonard leo']):
        category_breakdown['judicial_capture'] += 1
    
    # Powell Memo implementation
    elif any(term in text for term in ['powell memo', 'lewis powell', 'business roundtable', 'heritage foundation']):
        category_breakdown['powell_implementation'] += 1
    
    # Regulatory capture
    elif any(term in text for term in ['regulatory capture', 'revolving door', 'sec', 'fda', 'epa', 'regulation']):
        category_breakdown['regulatory_capture'] += 1
    
    # General systematic corruption
    else:
        category_breakdown['systematic_corruption'] += 1

def generate_recommendations(validation_results, stats):
    """Generate actionable recommendations based on validation results"""
    recommendations = []
    
    total = validation_results['total_events']
    flagged_pct = validation_results['flagged'] / total * 100 if total > 0 else 0
    rejected_pct = validation_results['rejected'] / total * 100 if total > 0 else 0
    
    if rejected_pct > 20:
        recommendations.append("High rejection rate suggests need for better initial filtering")
    
    if flagged_pct > 30:
        recommendations.append("Many events need additional sourcing or validation")
    
    # Category-specific recommendations
    categories = validation_results['category_breakdown']
    if categories['media_capture'] < 10:
        recommendations.append("Expand media capture event collection - underrepresented")
    
    if categories['intelligence_surveillance'] < 15:
        recommendations.append("Intelligence privatization timeline needs more events")
    
    if categories['judicial_capture'] < 10:
        recommendations.append("Judicial capture events are sparse - focus on Federalist Society")
    
    if categories['powell_implementation'] < 5:
        recommendations.append("Powell Memo implementation timeline needs development")
    
    # Technical recommendations
    recommendations.append("Implement automated duplicate detection before staging")
    recommendations.append("Require at least one .gov or .edu source for acceptance")
    recommendations.append("Focus collection on systematic patterns over isolated incidents")
    
    validation_results['recommendations'] = recommendations

if __name__ == "__main__":
    main()