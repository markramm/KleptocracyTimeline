#!/usr/bin/env python3
"""
Batch verify and fix timeline events using known good sources.
Matches broken URLs with extracted sources database.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from difflib import SequenceMatcher

def load_known_sources() -> Dict:
    """Load the extracted sources database."""
    sources_file = Path.cwd() / "timeline_data" / "qa_reports" / "extracted_sources.json"
    if sources_file.exists():
        with open(sources_file, 'r') as f:
            return json.load(f)
    return {'categorized_urls': {}, 'all_urls': []}

def load_broken_links() -> Dict:
    """Load the broken links report."""
    broken_file = Path.cwd() / "timeline_data" / "qa_reports" / "broken_links.json"
    if broken_file.exists():
        with open(broken_file, 'r') as f:
            return json.load(f)
    return {'events_needing_fixes': []}

def find_matching_source(broken_url: str, event_data: dict, known_sources: List[str]) -> Optional[str]:
    """Find a matching source from known good sources."""
    # Extract key terms from the broken URL and event
    url_terms = extract_key_terms(broken_url)
    event_terms = extract_event_terms(event_data)
    all_terms = url_terms + event_terms
    
    best_match = None
    best_score = 0
    
    for source in known_sources:
        score = calculate_relevance_score(source, all_terms, event_data)
        if score > best_score and score > 0.3:  # Minimum threshold
            best_score = score
            best_match = source
    
    return best_match

def extract_key_terms(url: str) -> List[str]:
    """Extract key terms from a URL."""
    # Remove protocol and common parts
    url = re.sub(r'https?://', '', url)
    url = re.sub(r'www\.', '', url)
    
    # Split on delimiters
    terms = re.split(r'[/\-_.?&=]', url)
    
    # Filter out common words and short terms
    stop_words = {'com', 'org', 'net', 'html', 'php', 'asp', 'htm', 'the', 'and', 'or', 'of', 'to', 'in'}
    terms = [t.lower() for t in terms if len(t) > 2 and t.lower() not in stop_words]
    
    return terms

def extract_event_terms(event_data: dict) -> List[str]:
    """Extract key terms from event data."""
    terms = []
    
    # Extract from title
    if 'title' in event_data:
        title_terms = re.findall(r'\b[A-Za-z]+\b', event_data['title'])
        terms.extend([t.lower() for t in title_terms if len(t) > 3])
    
    # Extract from tags
    if 'tags' in event_data:
        terms.extend([str(tag).lower() for tag in event_data['tags']])
    
    # Extract key names and organizations
    if 'actors' in event_data:
        for actor in event_data['actors']:
            actor_terms = re.findall(r'\b[A-Za-z]+\b', str(actor))
            terms.extend([t.lower() for t in actor_terms if len(t) > 2])
    
    # Extract year from date
    if 'date' in event_data:
        date_str = str(event_data['date'])
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            terms.append(year_match.group(1))
    
    return list(set(terms))

def calculate_relevance_score(source_url: str, search_terms: List[str], event_data: dict) -> float:
    """Calculate relevance score between a source URL and search terms."""
    source_lower = source_url.lower()
    score = 0.0
    
    # Check for term matches
    for term in search_terms:
        if term in source_lower:
            score += 0.1
    
    # Bonus for date match
    if 'date' in event_data:
        date_str = str(event_data['date'])[:10]
        if date_str in source_url:
            score += 0.3
    
    # Bonus for domain relevance
    if any(gov in source_lower for gov in ['.gov', 'congress', 'senate', 'house', 'whitehouse']):
        if any(tag in str(event_data.get('tags', [])).lower() for tag in ['legislation', 'executive', 'government']):
            score += 0.2
    
    if any(court in source_lower for court in ['supremecourt', 'scotus', 'justia', 'courtlistener']):
        if any(tag in str(event_data.get('tags', [])).lower() for tag in ['judicial', 'scotus', 'court']):
            score += 0.2
    
    return score

def update_event_with_matches(event_file: Path, matches: Dict[str, str]) -> bool:
    """Update an event file with matched URLs."""
    try:
        with open(event_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return False
        
        updated = False
        
        # Update citations
        if 'citations' in data:
            for i, citation in enumerate(data['citations']):
                if isinstance(citation, str) and citation in matches:
                    data['citations'][i] = {
                        'url': matches[citation],
                        'archived': f"https://web.archive.org/web/*/{matches[citation]}"
                    }
                    updated = True
                elif isinstance(citation, dict) and 'url' in citation:
                    if citation['url'] in matches:
                        citation['url'] = matches[citation['url']]
                        if 'archived' not in citation:
                            citation['archived'] = f"https://web.archive.org/web/*/{citation['url']}"
                        updated = True
        
        if updated:
            with open(event_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        
        return updated
        
    except Exception as e:
        print(f"Error updating {event_file.name}: {e}")
        return False

def main():
    """Main function to batch verify and fix events."""
    timeline_dir = Path.cwd() / "timeline_data" / "events"
    report_dir = Path.cwd() / "timeline_data" / "qa_reports"
    
    print("Loading known sources and broken links...")
    known_sources = load_known_sources()
    broken_links = load_broken_links()
    
    all_known_urls = known_sources.get('all_urls', [])
    categorized_urls = known_sources.get('categorized_urls', {})
    events_needing_fixes = broken_links.get('events_needing_fixes', [])
    
    print(f"Found {len(all_known_urls)} known good sources")
    print(f"Found {len(events_needing_fixes)} events needing fixes")
    
    if not all_known_urls:
        print("\nNo known sources found. Run extract_pdf_citations.py first.")
        return
    
    # Process events with broken links
    auto_fixed = []
    needs_manual = []
    
    for event_filename in events_needing_fixes[:50]:  # Process first 50
        event_file = timeline_dir / event_filename
        if not event_file.exists():
            continue
        
        try:
            with open(event_file, 'r', encoding='utf-8') as f:
                event_data = yaml.safe_load(f)
            
            if not event_data:
                continue
            
            # Try to find matches for broken URLs
            url_matches = {}
            
            # Get all URLs from the event
            event_urls = []
            for citation in event_data.get('citations', []):
                if isinstance(citation, str):
                    event_urls.append(citation)
                elif isinstance(citation, dict) and 'url' in citation:
                    event_urls.append(citation['url'])
            
            # Try to match each URL
            for url in event_urls:
                # First try exact domain match
                domain = re.search(r'(?:https?://)?([^/]+)', url)
                if domain:
                    domain_str = domain.group(1)
                    
                    # Look for same domain in known sources
                    for known_url in all_known_urls:
                        if domain_str in known_url:
                            url_matches[url] = known_url
                            break
                
                # If no exact match, try fuzzy matching
                if url not in url_matches:
                    match = find_matching_source(url, event_data, all_known_urls)
                    if match:
                        url_matches[url] = match
            
            if url_matches:
                # Update the event with matches
                if update_event_with_matches(event_file, url_matches):
                    auto_fixed.append({
                        'file': event_filename,
                        'fixes': len(url_matches),
                        'matches': {k: v[:80] for k, v in url_matches.items()}
                    })
                    print(f"  Auto-fixed {len(url_matches)} URLs in {event_filename}")
            else:
                needs_manual.append({
                    'file': event_filename,
                    'reason': 'No matching sources found',
                    'broken_urls': event_urls[:3]  # First 3 for reference
                })
        
        except Exception as e:
            print(f"  Error processing {event_filename}: {e}")
            needs_manual.append({
                'file': event_filename,
                'reason': f'Processing error: {str(e)[:50]}'
            })
    
    # Generate report
    report = {
        'auto_fixed_count': len(auto_fixed),
        'needs_manual_count': len(needs_manual),
        'auto_fixed': auto_fixed,
        'needs_manual_review': needs_manual
    }
    
    # Save report
    report_file = report_dir / "batch_verify_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n=== Batch Verify Summary ===")
    print(f"Events auto-fixed: {len(auto_fixed)}")
    print(f"Events needing manual review: {len(needs_manual)}")
    print(f"\nReport saved to: {report_file}")
    
    if needs_manual:
        print("\nSample events needing manual review:")
        for item in needs_manual[:5]:
            print(f"  - {item['file']}: {item.get('reason', 'Unknown')}")

if __name__ == "__main__":
    main()