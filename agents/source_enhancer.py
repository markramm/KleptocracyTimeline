#!/usr/bin/env python3
"""
Source Enhancement Agent for Timeline Events

Enhances timeline events by:
- Finding additional high-quality sources
- Verifying claims through cross-referencing
- Identifying primary source documents
- Suggesting government records, FOIA documents
- Finding scholarly sources and fact-checks
- Identifying key witnesses and testimonies
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time
import logging
from dataclasses import dataclass
import sqlite3
import re

@dataclass
class SourceSuggestion:
    """A suggested additional source"""
    title: str
    url: str
    outlet: str
    source_type: str  # 'government-record', 'news', 'scholarly', 'fact-check', 'witness-testimony'
    credibility_score: int
    relevance_score: int
    reason: str
    date_published: Optional[str] = None

class SourceEnhancer:
    """Agent to find and suggest additional sources for timeline events"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self._init_database()
        
        # High-priority source types and patterns
        self.priority_sources = {
            'government-record': {
                'domains': ['govinfo.gov', 'congress.gov', 'archives.gov', 'foia.gov', 
                          'justice.gov', 'cia.gov', 'nsa.gov', 'fbi.gov'],
                'patterns': [r'senate report', r'house report', r'inspector general', 
                           r'government accountability office', r'congressional testimony'],
                'credibility': 10
            },
            'court-record': {
                'domains': ['supremecourt.gov', 'uscourts.gov', 'courtlistener.com'],
                'patterns': [r'court decision', r'judicial ruling', r'indictment', 
                           r'court filing', r'legal brief'],
                'credibility': 10
            },
            'scholarly': {
                'domains': ['jstor.org', 'scholar.google.com', 'academia.edu', 'researchgate.net'],
                'patterns': [r'peer.?reviewed', r'academic study', r'research paper', 
                           r'university press'],
                'credibility': 8
            },
            'investigative-journalism': {
                'outlets': ['ProPublica', 'Center for Investigative Reporting', 
                          'International Consortium of Investigative Journalists',
                          'Washington Post Investigative', 'New York Times Investigative'],
                'patterns': [r'investigation reveals', r'documents obtained', r'whistleblower'],
                'credibility': 9
            },
            'fact-check': {
                'outlets': ['PolitiFact', 'FactCheck.org', 'Snopes', 'Washington Post Fact Checker'],
                'patterns': [r'fact.?check', r'verification', r'debunked', r'confirmed'],
                'credibility': 8
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for source enhancement"""
        os.makedirs("logs/source_enhancement", exist_ok=True)
        
        logger = logging.getLogger('source_enhancer')
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(message)s')
        today = datetime.now().strftime('%Y%m%d')
        handler = logging.FileHandler(f'logs/source_enhancement/enhancement_{today}.jsonl')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize database for tracking source suggestions"""
        conn = sqlite3.connect('source_enhancement.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                title TEXT,
                url TEXT,
                outlet TEXT,
                source_type TEXT,
                credibility_score INTEGER,
                relevance_score INTEGER,
                reason TEXT,
                date_published TEXT,
                suggested_timestamp TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enhancement_sessions (
                event_id TEXT PRIMARY KEY,
                original_sources_count INTEGER,
                suggestions_generated INTEGER,
                high_priority_suggestions INTEGER,
                enhancement_timestamp TEXT,
                enhancement_agent TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def analyze_source_gaps(self, event_data: Dict) -> List[str]:
        """Analyze what types of sources are missing from an event"""
        gaps = []
        sources = event_data.get('sources', [])
        
        if not sources:
            return ['all_sources_missing']
        
        # Check for primary source types
        source_types = set()
        outlets = set()
        
        for source in sources:
            outlet = source.get('outlet', '').lower()
            url = source.get('url', '').lower()
            title = source.get('title', '').lower()
            
            outlets.add(outlet)
            
            # Categorize existing sources
            if any(domain in url for domain in self.priority_sources['government-record']['domains']):
                source_types.add('government-record')
            elif any(domain in url for domain in self.priority_sources['court-record']['domains']):
                source_types.add('court-record')
            elif any(domain in url for domain in self.priority_sources['scholarly']['domains']):
                source_types.add('scholarly')
            elif outlet in [o.lower() for o in self.priority_sources['investigative-journalism']['outlets']]:
                source_types.add('investigative-journalism')
            elif outlet in [o.lower() for o in self.priority_sources['fact-check']['outlets']]:
                source_types.add('fact-check')
            else:
                source_types.add('news')
        
        # Identify gaps based on event characteristics
        tags = event_data.get('tags', [])
        importance = event_data.get('importance', 5)
        
        # High-importance events should have government records
        if importance >= 8 and 'government-record' not in source_types:
            gaps.append('missing_government_records')
        
        # Intelligence-related events should have official reports
        if any(tag in tags for tag in ['nsa', 'cia', 'intelligence', 'surveillance']):
            if 'government-record' not in source_types:
                gaps.append('missing_intelligence_records')
        
        # Legal/constitutional issues should have court records
        if any(tag in tags for tag in ['constitutional-crisis', 'supreme-court', 'judicial']):
            if 'court-record' not in source_types:
                gaps.append('missing_court_records')
        
        # Controversial claims should have fact-checks
        if importance >= 7 and 'fact-check' not in source_types:
            gaps.append('missing_fact_checks')
        
        # Single-source events are high risk
        if len(sources) == 1:
            gaps.append('single_source_risk')
        
        # Low credibility sources need enhancement
        if len([s for s in sources if self._assess_source_credibility(s) < 6]) > 0:
            gaps.append('low_credibility_sources')
        
        return gaps
    
    def _assess_source_credibility(self, source: Dict) -> int:
        """Assess credibility of a source"""
        outlet = source.get('outlet', '').lower()
        
        # Check against known credibility ratings
        for credible_outlet, score in [
            ('reuters', 9), ('associated press', 9), ('bbc', 9),
            ('washington post', 8), ('new york times', 8), ('npr', 8),
            ('propublica', 9), ('wall street journal', 8)
        ]:
            if credible_outlet in outlet:
                return score
        
        # Government sources
        url = source.get('url', '').lower()
        if any(domain in url for domain in ['gov', 'congress.gov', 'supremecourt.gov']):
            return 10
        
        return 5  # Default medium credibility
    
    def generate_search_queries(self, event_data: Dict, gaps: List[str]) -> List[Tuple[str, str]]:
        """Generate targeted search queries to fill source gaps"""
        queries = []
        
        title = event_data.get('title', '')
        date = event_data.get('date', '')
        actors = event_data.get('actors', [])
        tags = event_data.get('tags', [])
        
        # Extract key terms
        key_terms = []
        
        # Add main actors
        if actors:
            key_terms.extend(actors[:3])  # Top 3 actors
        
        # Add significant terms from title
        title_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', title)
        key_terms.extend(title_terms[:3])
        
        # Generate queries based on gaps
        base_query = ' '.join(key_terms[:4]) if key_terms else title[:50]
        
        for gap in gaps:
            if gap == 'missing_government_records':
                queries.append((f'{base_query} "government report"', 'government-record'))
                queries.append((f'{base_query} "congressional testimony"', 'government-record'))
                queries.append((f'{base_query} "inspector general"', 'government-record'))
            
            elif gap == 'missing_intelligence_records':
                queries.append((f'{base_query} "CIA" "declassified"', 'government-record'))
                queries.append((f'{base_query} "NSA" "documents"', 'government-record'))
                queries.append((f'{base_query} "FOIA"', 'government-record'))
            
            elif gap == 'missing_court_records':
                queries.append((f'{base_query} "court ruling"', 'court-record'))
                queries.append((f'{base_query} "judicial decision"', 'court-record'))
                
            elif gap == 'missing_fact_checks':
                queries.append((f'{base_query} "fact check"', 'fact-check'))
                queries.append((f'{base_query} "verification"', 'fact-check'))
            
            elif gap == 'single_source_risk':
                queries.append((f'{base_query} "investigation"', 'investigative-journalism'))
                queries.append((f'{base_query} "documents reveal"', 'investigative-journalism'))
        
        # Always look for additional investigative sources for high-importance events
        if event_data.get('importance', 5) >= 7:
            queries.append((f'{base_query} "ProPublica"', 'investigative-journalism'))
            queries.append((f'{base_query} "investigation reveals"', 'investigative-journalism'))
        
        return queries[:8]  # Limit to 8 queries to manage API usage
    
    def search_for_sources(self, query: str, source_type: str) -> List[SourceSuggestion]:
        """Search for sources using the query (placeholder for actual search implementation)"""
        # This would integrate with search APIs like:
        # - Google Custom Search API
        # - DuckDuckGo API  
        # - NewsAPI
        # - Government data APIs
        
        suggestions = []
        
        # For now, return structured placeholder suggestions that demonstrate the concept
        if source_type == 'government-record':
            suggestions.append(SourceSuggestion(
                title=f"Government Report Related to: {query[:30]}...",
                url="https://govinfo.gov/placeholder",
                outlet="Government Publishing Office",
                source_type="government-record",
                credibility_score=10,
                relevance_score=8,
                reason="Official government documentation needed for verification"
            ))
        
        elif source_type == 'investigative-journalism':
            suggestions.append(SourceSuggestion(
                title=f"Investigative Report: {query[:30]}...",
                url="https://propublica.org/placeholder",
                outlet="ProPublica",
                source_type="investigative-journalism", 
                credibility_score=9,
                relevance_score=7,
                reason="Independent investigative verification needed"
            ))
        
        return suggestions
    
    def enhance_event_sources(self, event_data: Dict) -> List[SourceSuggestion]:
        """Generate comprehensive source enhancement suggestions for an event"""
        event_id = event_data.get('id', 'unknown')
        
        # Analyze what sources are missing
        gaps = self.analyze_source_gaps(event_data)
        
        if not gaps:
            return []
        
        # Generate targeted search queries
        queries = self.generate_search_queries(event_data, gaps)
        
        all_suggestions = []
        
        # Execute searches (in real implementation)
        for query, source_type in queries:
            suggestions = self.search_for_sources(query, source_type)
            all_suggestions.extend(suggestions)
            
            # Rate limiting
            time.sleep(0.5)
        
        # Deduplicate and rank suggestions
        unique_suggestions = []
        seen_urls = set()
        
        for suggestion in all_suggestions:
            if suggestion.url not in seen_urls:
                seen_urls.add(suggestion.url)
                unique_suggestions.append(suggestion)
        
        # Sort by credibility and relevance
        unique_suggestions.sort(
            key=lambda x: (x.credibility_score, x.relevance_score), 
            reverse=True
        )
        
        return unique_suggestions[:10]  # Top 10 suggestions
    
    def save_enhancement_results(self, event_id: str, suggestions: List[SourceSuggestion]):
        """Save enhancement results to database"""
        conn = sqlite3.connect('source_enhancement.db')
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        # Save session info
        cursor.execute("""
            INSERT OR REPLACE INTO enhancement_sessions
            (event_id, suggestions_generated, high_priority_suggestions, enhancement_timestamp, enhancement_agent)
            VALUES (?, ?, ?, ?, ?)
        """, (
            event_id,
            len(suggestions),
            len([s for s in suggestions if s.credibility_score >= 9]),
            timestamp,
            "source_enhancer_v1.0"
        ))
        
        # Clear old suggestions
        cursor.execute("DELETE FROM source_suggestions WHERE event_id = ?", (event_id,))
        
        # Save suggestions
        for suggestion in suggestions:
            cursor.execute("""
                INSERT INTO source_suggestions
                (event_id, title, url, outlet, source_type, credibility_score, relevance_score, 
                 reason, date_published, suggested_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id, suggestion.title, suggestion.url, suggestion.outlet,
                suggestion.source_type, suggestion.credibility_score, suggestion.relevance_score,
                suggestion.reason, suggestion.date_published, timestamp
            ))
        
        conn.commit()
        conn.close()
        
        # Log results
        log_entry = {
            "timestamp": timestamp,
            "event_id": event_id,
            "action": "source_enhancement",
            "suggestions_generated": len(suggestions),
            "high_priority_suggestions": len([s for s in suggestions if s.credibility_score >= 9]),
            "source_types": list(set(s.source_type for s in suggestions))
        }
        
        self.logger.info(json.dumps(log_entry))

def main():
    """Main execution for source enhancement agent"""
    enhancer = SourceEnhancer()
    
    # Test with a sample event
    sample_event = {
        "id": "test-event",
        "title": "Bush Administration Intelligence Manipulation",
        "date": "2002-08-01", 
        "importance": 9,
        "actors": ["George W. Bush", "Dick Cheney", "Karl Rove"],
        "tags": ["whig", "intelligence-manipulation", "iraq-war"],
        "sources": [
            {
                "title": "News Article",
                "url": "https://example.com/article",
                "outlet": "Generic News"
            }
        ]
    }
    
    print("Analyzing source gaps...")
    gaps = enhancer.analyze_source_gaps(sample_event)
    print(f"Identified gaps: {gaps}")
    
    print("Generating source enhancement suggestions...")
    suggestions = enhancer.enhance_event_sources(sample_event)
    
    print(f"\nGenerated {len(suggestions)} source suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion.title}")
        print(f"   Source: {suggestion.outlet}")
        print(f"   Type: {suggestion.source_type}")
        print(f"   Credibility: {suggestion.credibility_score}/10")
        print(f"   Reason: {suggestion.reason}")
        print()
    
    enhancer.save_enhancement_results("test-event", suggestions)
    print("Enhancement results saved")

if __name__ == "__main__":
    main()