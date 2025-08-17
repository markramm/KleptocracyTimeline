#!/usr/bin/env python3
"""
Comprehensive Timeline QA System

This script performs deep validation of timeline events by:
1. Fetching and analyzing all source links
2. Verifying sources actually support the claimed event
3. Evaluating summary completeness (who, what, when, where, why)
4. Checking for missing critical information
5. Generating detailed QA reports with actionable recommendations
"""

import os
import sys
import yaml
import json
import requests
import hashlib
import time
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import re
from bs4 import BeautifulSoup

# Configuration
TIMELINE_DIR = Path(__file__).parent.parent.parent / "timeline_data" / "events"
CACHE_DIR = Path(__file__).parent.parent.parent / "timeline_data" / ".qa_cache"
REPORTS_DIR = Path(__file__).parent.parent.parent / "timeline_data" / "qa_reports"
ARCHIVE_DIR = Path(__file__).parent.parent.parent / "timeline_data" / "archive"

# Create directories
CACHE_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# QA Criteria
SUMMARY_MIN_LENGTH = 50  # Minimum characters for a summary
SUMMARY_KEY_ELEMENTS = {
    'who': ['who', 'person', 'individual', 'actor', 'organization', 'company', 'agency'],
    'what': ['what', 'action', 'event', 'decision', 'announcement', 'ruling'],
    'when': ['when', 'date', 'time', 'year', 'month'],
    'where': ['where', 'location', 'place', 'country', 'state', 'city'],
    'why': ['why', 'because', 'reason', 'cause', 'purpose', 'goal'],
    'impact': ['impact', 'result', 'consequence', 'effect', 'outcome', 'significance']
}

class SourceFetcher:
    """Fetches and caches source content"""
    
    def __init__(self, use_cache=True):
        self.use_cache = use_cache
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; TimelineQA/1.0; +https://github.com/kleptocracy-timeline)'
        })
    
    def get_cache_path(self, url: str) -> Path:
        """Generate cache file path for URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return CACHE_DIR / f"{url_hash}.json"
    
    def fetch_url(self, url: str) -> Dict[str, Any]:
        """Fetch URL content with caching"""
        cache_path = self.get_cache_path(url)
        
        # Check cache
        if self.use_cache and cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cached = json.load(f)
                    # Cache expires after 7 days
                    if time.time() - cached['timestamp'] < 7 * 24 * 3600:
                        return cached
            except:
                pass
        
        # Fetch fresh content
        result = {
            'url': url,
            'timestamp': time.time(),
            'status_code': None,
            'error': None,
            'title': None,
            'content': None,
            'excerpt': None
        }
        
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            result['status_code'] = response.status_code
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title
                title_tag = soup.find('title')
                if title_tag:
                    result['title'] = title_tag.text.strip()
                
                # Extract main content (try various selectors)
                content = ""
                for selector in ['article', 'main', '[role="main"]', '.content', '#content']:
                    elem = soup.select_one(selector)
                    if elem:
                        content = elem.get_text(separator=' ', strip=True)
                        break
                
                if not content:
                    # Fallback to body text
                    content = soup.get_text(separator=' ', strip=True)
                
                # Clean and truncate content
                content = ' '.join(content.split())[:5000]  # First 5000 chars
                result['content'] = content
                
                # Extract excerpt (first meaningful paragraph)
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 100:
                        result['excerpt'] = text[:500]
                        break
                        
        except requests.exceptions.RequestException as e:
            result['error'] = str(e)
        except Exception as e:
            result['error'] = f"Parse error: {str(e)}"
        
        # Cache result
        if self.use_cache:
            with open(cache_path, 'w') as f:
                json.dump(result, f, indent=2)
        
        return result

class ContentAnalyzer:
    """Analyzes whether source content supports the event"""
    
    def __init__(self):
        self.fetcher = SourceFetcher()
    
    def extract_key_terms(self, event: Dict) -> List[str]:
        """Extract key terms from event for verification"""
        terms = []
        
        # Add key actors
        if 'actors' in event:
            actors = event['actors']
            if isinstance(actors, list):
                terms.extend(actors)
            elif isinstance(actors, str):
                terms.append(actors)
        
        # Extract key terms from title
        title = event.get('title', '')
        # Remove common words and extract significant terms
        title_words = title.split()
        for word in title_words:
            if len(word) > 4 and word.lower() not in ['about', 'after', 'before', 'during', 'through']:
                terms.append(word)
        
        # Add location if present
        if 'location' in event:
            terms.append(event['location'])
        
        return terms
    
    def verify_source_relevance(self, source_content: Dict, event: Dict) -> Dict[str, Any]:
        """Verify if source content actually supports the event"""
        result = {
            'url': source_content['url'],
            'accessible': source_content['status_code'] == 200,
            'error': source_content.get('error'),
            'relevance_score': 0,
            'key_terms_found': [],
            'key_terms_missing': [],
            'supports_event': False,
            'issues': []
        }
        
        if not result['accessible']:
            result['issues'].append(f"Source not accessible: {source_content.get('error', 'HTTP ' + str(source_content.get('status_code', 'Unknown')))}")
            return result
        
        content = (source_content.get('content', '') + ' ' + 
                  source_content.get('title', '')).lower()
        
        if not content:
            result['issues'].append("No content extracted from source")
            return result
        
        # Check for key terms
        key_terms = self.extract_key_terms(event)
        terms_found = 0
        
        for term in key_terms:
            if term.lower() in content:
                result['key_terms_found'].append(term)
                terms_found += 1
            else:
                result['key_terms_missing'].append(term)
        
        # Calculate relevance score
        if key_terms:
            result['relevance_score'] = terms_found / len(key_terms)
        
        # Check date relevance
        event_date = event.get('date')
        if event_date:
            date_str = str(event_date)
            year = date_str[:4]
            if year in content:
                result['relevance_score'] += 0.2
        
        # Determine if source supports event
        if result['relevance_score'] >= 0.3:  # At least 30% of key terms found
            result['supports_event'] = True
        else:
            result['issues'].append(f"Low relevance score ({result['relevance_score']:.2f}): Missing key terms: {', '.join(result['key_terms_missing'][:3])}")
        
        return result

class SummaryEvaluator:
    """Evaluates the completeness and quality of event summaries"""
    
    def evaluate_summary(self, event: Dict) -> Dict[str, Any]:
        """Evaluate summary completeness"""
        summary = event.get('summary', '')
        result = {
            'has_summary': bool(summary),
            'length': len(summary),
            'completeness_score': 0,
            'missing_elements': [],
            'issues': []
        }
        
        if not summary:
            result['issues'].append("No summary provided")
            result['missing_elements'] = list(SUMMARY_KEY_ELEMENTS.keys())
            return result
        
        if len(summary) < SUMMARY_MIN_LENGTH:
            result['issues'].append(f"Summary too short ({len(summary)} chars, minimum {SUMMARY_MIN_LENGTH})")
        
        # Check for key elements
        summary_lower = summary.lower()
        elements_found = {}
        
        for element, keywords in SUMMARY_KEY_ELEMENTS.items():
            found = False
            for keyword in keywords:
                if keyword in summary_lower:
                    found = True
                    break
            elements_found[element] = found
            if not found:
                result['missing_elements'].append(element)
        
        # Calculate completeness score
        result['completeness_score'] = sum(elements_found.values()) / len(SUMMARY_KEY_ELEMENTS)
        
        # Specific checks
        if 'who' in result['missing_elements']:
            # Check if actors are specified elsewhere
            if event.get('actors'):
                result['missing_elements'].remove('who')
                result['completeness_score'] = sum(1 for e in SUMMARY_KEY_ELEMENTS if e not in result['missing_elements']) / len(SUMMARY_KEY_ELEMENTS)
        
        if 'when' in result['missing_elements']:
            # Date is in filename, so this might be OK
            if event.get('date'):
                result['missing_elements'].remove('when')
                result['completeness_score'] = sum(1 for e in SUMMARY_KEY_ELEMENTS if e not in result['missing_elements']) / len(SUMMARY_KEY_ELEMENTS)
        
        # Generate specific recommendations
        if result['completeness_score'] < 0.7:
            missing_str = ', '.join(result['missing_elements'])
            result['issues'].append(f"Summary missing key elements: {missing_str}")
        
        return result

class TimelineQA:
    """Main QA orchestrator"""
    
    def __init__(self, parallel=True, max_workers=5):
        self.content_analyzer = ContentAnalyzer()
        self.summary_evaluator = SummaryEvaluator()
        self.parallel = parallel
        self.max_workers = max_workers
    
    def load_event(self, file_path: Path) -> Optional[Dict]:
        """Load a timeline event from YAML"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def qa_single_event(self, file_path: Path) -> Dict[str, Any]:
        """Perform QA on a single event"""
        event = self.load_event(file_path)
        if not event:
            return {
                'file': file_path.name,
                'error': 'Failed to load event',
                'passed': False
            }
        
        result = {
            'file': file_path.name,
            'id': event.get('id', file_path.stem),
            'title': event.get('title', 'Unknown'),
            'date': str(event.get('date', 'Unknown')),
            'status': event.get('status', 'unknown'),
            'passed': True,
            'issues': [],
            'warnings': [],
            'sources_analysis': [],
            'summary_analysis': None,
            'overall_score': 0
        }
        
        # Evaluate summary
        summary_eval = self.summary_evaluator.evaluate_summary(event)
        result['summary_analysis'] = summary_eval
        if summary_eval['issues']:
            result['issues'].extend(summary_eval['issues'])
            result['passed'] = False
        
        # Get sources/citations
        sources = []
        if 'sources' in event:
            for source in event['sources']:
                if isinstance(source, dict):
                    url = source.get('url')
                elif isinstance(source, str):
                    url = source
                else:
                    continue
                if url:
                    sources.append(url)
        
        if 'citations' in event:
            for citation in event['citations']:
                if isinstance(citation, dict):
                    url = citation.get('url')
                elif isinstance(citation, str):
                    url = citation
                else:
                    continue
                if url and url not in sources:
                    sources.append(url)
        
        if not sources:
            result['issues'].append("No sources or citations provided")
            result['passed'] = False
        else:
            # Analyze each source
            sources_support_event = False
            for url in sources:
                print(f"  Checking source: {url[:50]}...")
                source_content = self.content_analyzer.fetcher.fetch_url(url)
                source_analysis = self.content_analyzer.verify_source_relevance(source_content, event)
                result['sources_analysis'].append(source_analysis)
                
                if source_analysis['supports_event']:
                    sources_support_event = True
                elif source_analysis['accessible']:
                    result['warnings'].append(f"Source may not support event: {url[:50]}...")
            
            if not sources_support_event:
                result['issues'].append("No sources clearly support the described event")
                result['passed'] = False
        
        # Calculate overall score
        source_score = 0
        if result['sources_analysis']:
            accessible_sources = [s for s in result['sources_analysis'] if s['accessible']]
            if accessible_sources:
                source_score = sum(s['relevance_score'] for s in accessible_sources) / len(accessible_sources)
        
        summary_score = summary_eval['completeness_score'] if summary_eval else 0
        result['overall_score'] = (source_score + summary_score) / 2
        
        # Additional checks based on status
        if result['status'] == 'confirmed':
            if not sources:
                result['issues'].append("Confirmed status requires sources")
                result['passed'] = False
            
            # Check if event is in the future
            try:
                event_date = event.get('date')
                if isinstance(event_date, str):
                    event_date = datetime.fromisoformat(event_date).date()
                elif hasattr(event_date, 'date'):
                    event_date = event_date.date()
                
                if event_date > date.today():
                    result['issues'].append("Future event cannot have 'confirmed' status")
                    result['passed'] = False
            except:
                pass
        
        return result
    
    def qa_all_events(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Run QA on all timeline events"""
        event_files = sorted(TIMELINE_DIR.glob("*.yaml"))
        if limit:
            event_files = event_files[:limit]
        
        print(f"Running QA on {len(event_files)} timeline events...")
        print("=" * 60)
        
        results = []
        failed_events = []
        warning_events = []
        
        if self.parallel:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {executor.submit(self.qa_single_event, f): f for f in event_files}
                
                for i, future in enumerate(as_completed(future_to_file), 1):
                    file_path = future_to_file[future]
                    print(f"[{i}/{len(event_files)}] Processing {file_path.name}")
                    
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if not result['passed']:
                            failed_events.append(result)
                        elif result.get('warnings'):
                            warning_events.append(result)
                            
                    except Exception as e:
                        print(f"  ERROR: {e}")
                        results.append({
                            'file': file_path.name,
                            'error': str(e),
                            'passed': False
                        })
        else:
            for i, file_path in enumerate(event_files, 1):
                print(f"[{i}/{len(event_files)}] Processing {file_path.name}")
                result = self.qa_single_event(file_path)
                results.append(result)
                
                if not result['passed']:
                    failed_events.append(result)
                elif result.get('warnings'):
                    warning_events.append(result)
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_events': len(results),
            'passed': len([r for r in results if r['passed']]),
            'failed': len(failed_events),
            'warnings': len(warning_events),
            'average_score': sum(r.get('overall_score', 0) for r in results) / len(results) if results else 0,
            'common_issues': self.analyze_common_issues(results),
            'failed_events': failed_events,
            'warning_events': warning_events,
            'all_results': results
        }
        
        return report
    
    def analyze_common_issues(self, results: List[Dict]) -> Dict[str, int]:
        """Analyze common issues across all events"""
        issue_counts = {}
        
        for result in results:
            for issue in result.get('issues', []):
                # Categorize issues
                if 'summary' in issue.lower():
                    category = 'Summary issues'
                elif 'source' in issue.lower():
                    category = 'Source issues'
                elif 'status' in issue.lower():
                    category = 'Status issues'
                else:
                    category = 'Other issues'
                
                issue_counts[category] = issue_counts.get(category, 0) + 1
        
        return issue_counts
    
    def save_report(self, report: Dict, format: str = 'json') -> Path:
        """Save QA report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'json':
            report_path = REPORTS_DIR / f"qa_report_{timestamp}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        
        elif format == 'markdown':
            report_path = REPORTS_DIR / f"qa_report_{timestamp}.md"
            with open(report_path, 'w') as f:
                f.write(self.format_markdown_report(report))
        
        else:
            raise ValueError(f"Unknown format: {format}")
        
        return report_path
    
    def format_markdown_report(self, report: Dict) -> str:
        """Format report as markdown"""
        md = []
        md.append("# Timeline QA Report")
        md.append(f"\nGenerated: {report['timestamp']}")
        md.append(f"\n## Summary")
        md.append(f"- **Total Events**: {report['total_events']}")
        md.append(f"- **Passed**: {report['passed']} ({report['passed']/report['total_events']*100:.1f}%)")
        md.append(f"- **Failed**: {report['failed']} ({report['failed']/report['total_events']*100:.1f}%)")
        md.append(f"- **Warnings**: {report['warnings']}")
        md.append(f"- **Average Score**: {report['average_score']:.2f}/1.0")
        
        if report['common_issues']:
            md.append(f"\n## Common Issues")
            for issue, count in sorted(report['common_issues'].items(), key=lambda x: x[1], reverse=True):
                md.append(f"- {issue}: {count} events")
        
        if report['failed_events']:
            md.append(f"\n## Failed Events ({len(report['failed_events'])})")
            for event in report['failed_events'][:20]:  # Show first 20
                md.append(f"\n### {event['file']}")
                md.append(f"**{event['title']}** ({event['date']})")
                if event.get('issues'):
                    md.append("Issues:")
                    for issue in event['issues']:
                        md.append(f"- {issue}")
                if event.get('sources_analysis'):
                    accessible = sum(1 for s in event['sources_analysis'] if s['accessible'])
                    supporting = sum(1 for s in event['sources_analysis'] if s['supports_event'])
                    md.append(f"Sources: {accessible} accessible, {supporting} supporting")
        
        if report['warning_events']:
            md.append(f"\n## Events with Warnings ({len(report['warning_events'])})")
            for event in report['warning_events'][:10]:  # Show first 10
                md.append(f"\n### {event['file']}")
                md.append(f"**{event['title']}**")
                if event.get('warnings'):
                    for warning in event['warnings']:
                        md.append(f"- ⚠️ {warning}")
        
        md.append(f"\n## Recommendations")
        md.append("1. **Immediate Actions**:")
        md.append("   - Fix events with no sources or citations")
        md.append("   - Update summaries to include who, what, when, where, why, and impact")
        md.append("   - Verify future events are marked as 'predicted' not 'confirmed'")
        md.append("\n2. **Source Verification**:")
        md.append("   - Review events where sources don't clearly support claims")
        md.append("   - Add archive.org links for sources that may disappear")
        md.append("   - Ensure at least 2 independent sources for 'confirmed' events")
        md.append("\n3. **Summary Improvements**:")
        md.append("   - Expand summaries under 50 characters")
        md.append("   - Include impact/significance for each event")
        md.append("   - Add specific names, organizations, and locations")
        
        return '\n'.join(md)

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Timeline QA System')
    parser.add_argument('--limit', type=int, help='Limit number of events to check')
    parser.add_argument('--no-cache', action='store_true', help='Disable cache, fetch fresh content')
    parser.add_argument('--sequential', action='store_true', help='Run sequentially instead of parallel')
    parser.add_argument('--format', choices=['json', 'markdown', 'both'], default='both', help='Report format')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers')
    
    args = parser.parse_args()
    
    # Configure
    if args.no_cache:
        SourceFetcher.use_cache = False
    
    # Run QA
    qa = TimelineQA(parallel=not args.sequential, max_workers=args.workers)
    report = qa.qa_all_events(limit=args.limit)
    
    # Save reports
    if args.format in ['json', 'both']:
        json_path = qa.save_report(report, 'json')
        print(f"\nJSON report saved to: {json_path}")
    
    if args.format in ['markdown', 'both']:
        md_path = qa.save_report(report, 'markdown')
        print(f"Markdown report saved to: {md_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("QA SUMMARY")
    print("=" * 60)
    print(f"Total Events: {report['total_events']}")
    print(f"Passed: {report['passed']} ({report['passed']/report['total_events']*100:.1f}%)")
    print(f"Failed: {report['failed']} ({report['failed']/report['total_events']*100:.1f}%)")
    print(f"Warnings: {report['warnings']}")
    print(f"Average Score: {report['average_score']:.2f}/1.0")
    
    if report['common_issues']:
        print("\nMost Common Issues:")
        for issue, count in sorted(report['common_issues'].items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"  - {issue}: {count} events")
    
    # Exit with error if too many failures
    failure_rate = report['failed'] / report['total_events'] if report['total_events'] > 0 else 0
    if failure_rate > 0.2:  # More than 20% failure rate
        print(f"\n⚠️  High failure rate ({failure_rate*100:.1f}%) - Manual review required")
        sys.exit(1)
    else:
        print(f"\n✅ QA Complete - {report['passed']} events passed validation")

if __name__ == "__main__":
    main()