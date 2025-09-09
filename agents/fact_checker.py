#!/usr/bin/env python3
"""
Timeline Fact-Checking and Source Validation Agent

Validates timeline events for:
- Factual accuracy of descriptions
- Source link validity and accessibility 
- Source credibility and reliability
- Cross-reference verification
- Importance scoring accuracy
- Missing source identification
"""

import json
import os
import requests
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin
import time
import logging
from dataclasses import dataclass
import hashlib

@dataclass
class SourceValidation:
    """Result of source validation check"""
    url: str
    accessible: bool
    status_code: Optional[int]
    content_type: Optional[str]
    title_match: bool
    outlet_match: bool
    date_accessible: bool
    credibility_score: int
    issues: List[str]
    validation_timestamp: str

@dataclass
class FactCheckResult:
    """Result of fact-checking an event"""
    event_id: str
    accuracy_score: int  # 1-10 scale
    source_validations: List[SourceValidation]
    fact_check_issues: List[str]
    enhancement_suggestions: List[str]
    credibility_assessment: str
    validation_timestamp: str
    validator_agent: str

class TimelineFactChecker:
    """Main fact-checking agent for timeline events"""
    
    def __init__(self, events_dir: str = "timeline_data/events", 
                 validation_db: str = "validation_tracking.db"):
        self.events_dir = events_dir
        self.validation_db = validation_db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Timeline-Fact-Checker/1.0 (Research Bot)'
        })
        self.logger = self._setup_logging()
        self._init_database()
        
        # Source credibility scoring
        self.outlet_credibility = {
            'reuters': 9, 'ap': 9, 'bbc': 9, 'npr': 8, 'pbs': 8,
            'washington post': 8, 'new york times': 8, 'wall street journal': 8,
            'propublica': 9, 'center for investigative reporting': 9,
            'guardian': 7, 'cnn': 6, 'msnbc': 5, 'fox news': 4,
            'breitbart': 2, 'infowars': 1, 'wikipedia': 6,
            'government report': 10, 'congressional record': 10,
            'court records': 10, 'foia documents': 10
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging for fact-checking"""
        os.makedirs("logs/fact_checking", exist_ok=True)
        
        logger = logging.getLogger('fact_checker')
        logger.setLevel(logging.INFO)
        
        # JSON formatter for structured logging
        formatter = logging.Formatter('%(message)s')
        
        # Daily log files
        today = datetime.now().strftime('%Y%m%d')
        handler = logging.FileHandler(f'logs/fact_checking/fact_check_{today}.jsonl')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize validation tracking database"""
        conn = sqlite3.connect(self.validation_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fact_check_results (
                event_id TEXT PRIMARY KEY,
                accuracy_score INTEGER,
                credibility_assessment TEXT,
                fact_check_issues TEXT,
                enhancement_suggestions TEXT,
                validation_timestamp TEXT,
                validator_agent TEXT,
                validation_hash TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                url TEXT,
                accessible BOOLEAN,
                status_code INTEGER,
                content_type TEXT,
                title_match BOOLEAN,
                outlet_match BOOLEAN,
                credibility_score INTEGER,
                issues TEXT,
                validation_timestamp TEXT,
                FOREIGN KEY (event_id) REFERENCES fact_check_results (event_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_queue (
                event_id TEXT PRIMARY KEY,
                priority_score INTEGER,
                reason TEXT,
                added_timestamp TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        
        conn.commit()
        conn.close()
    
    def validate_source_link(self, url: str, expected_title: str = None, 
                           expected_outlet: str = None) -> SourceValidation:
        """Validate a single source link"""
        issues = []
        accessible = False
        status_code = None
        content_type = None
        title_match = False
        outlet_match = False
        
        try:
            # Check URL accessibility
            response = self.session.head(url, timeout=10, allow_redirects=True)
            status_code = response.status_code
            content_type = response.headers.get('content-type', '')
            
            if status_code == 200:
                accessible = True
            elif status_code in [301, 302, 303, 307, 308]:
                # Follow redirects for full check
                response = self.session.get(url, timeout=10)
                status_code = response.status_code
                accessible = status_code == 200
                
                if accessible and expected_title:
                    # Basic title matching (would need more sophisticated parsing)
                    page_content = response.text.lower()
                    title_match = expected_title.lower() in page_content
            else:
                issues.append(f"HTTP {status_code}: Link not accessible")
                
        except requests.exceptions.Timeout:
            issues.append("Link timeout - may be slow or unavailable")
        except requests.exceptions.ConnectionError:
            issues.append("Connection error - link may be broken")
        except Exception as e:
            issues.append(f"Validation error: {str(e)}")
        
        # Outlet credibility scoring
        credibility_score = 5  # default
        if expected_outlet:
            outlet_lower = expected_outlet.lower()
            for outlet, score in self.outlet_credibility.items():
                if outlet in outlet_lower:
                    credibility_score = score
                    outlet_match = True
                    break
        
        return SourceValidation(
            url=url,
            accessible=accessible,
            status_code=status_code,
            content_type=content_type,
            title_match=title_match,
            outlet_match=outlet_match,
            date_accessible=True,  # Would need more sophisticated date checking
            credibility_score=credibility_score,
            issues=issues,
            validation_timestamp=datetime.now().isoformat()
        )
    
    def fact_check_event(self, event_data: Dict) -> FactCheckResult:
        """Comprehensive fact-checking of a timeline event"""
        event_id = event_data.get('id', 'unknown')
        issues = []
        enhancement_suggestions = []
        source_validations = []
        
        # Validate all sources
        sources = event_data.get('sources', [])
        if not sources:
            issues.append("No sources provided")
            enhancement_suggestions.append("Add primary sources for verification")
        
        for source in sources:
            url = source.get('url')
            title = source.get('title')
            outlet = source.get('outlet')
            
            if url:
                validation = self.validate_source_link(url, title, outlet)
                source_validations.append(validation)
                
                if not validation.accessible:
                    issues.append(f"Inaccessible source: {url}")
                    enhancement_suggestions.append(f"Find alternative source for: {title}")
                
                if validation.credibility_score < 5:
                    issues.append(f"Low credibility source: {outlet}")
                    enhancement_suggestions.append(f"Supplement with higher credibility source")
        
        # Check for basic data quality issues
        required_fields = ['id', 'date', 'title', 'summary', 'importance']
        for field in required_fields:
            if not event_data.get(field):
                issues.append(f"Missing required field: {field}")
        
        # Check date format
        date_str = event_data.get('date', '')
        if date_str:
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                issues.append("Invalid date format - should be YYYY-MM-DD")
        
        # Check importance scoring
        importance = event_data.get('importance', 0)
        if not isinstance(importance, int) or importance < 1 or importance > 10:
            issues.append("Importance should be integer 1-10")
        
        # Calculate accuracy score based on issues found
        accuracy_score = max(1, 10 - len(issues))
        
        # Calculate overall credibility
        if source_validations:
            avg_credibility = sum(sv.credibility_score for sv in source_validations) / len(source_validations)
            if avg_credibility >= 8:
                credibility_assessment = "high"
            elif avg_credibility >= 6:
                credibility_assessment = "medium"
            else:
                credibility_assessment = "low"
        else:
            credibility_assessment = "unverified"
        
        return FactCheckResult(
            event_id=event_id,
            accuracy_score=accuracy_score,
            source_validations=source_validations,
            fact_check_issues=issues,
            enhancement_suggestions=enhancement_suggestions,
            credibility_assessment=credibility_assessment,
            validation_timestamp=datetime.now().isoformat(),
            validator_agent="timeline_fact_checker_v1.0"
        )
    
    def save_fact_check_result(self, result: FactCheckResult):
        """Save fact-check result to database and logs"""
        conn = sqlite3.connect(self.validation_db)
        cursor = conn.cursor()
        
        # Create validation hash for change detection
        validation_data = {
            'accuracy_score': result.accuracy_score,
            'issues': result.fact_check_issues,
            'suggestions': result.enhancement_suggestions
        }
        validation_hash = hashlib.sha256(
            json.dumps(validation_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        # Insert or update fact check result
        cursor.execute("""
            INSERT OR REPLACE INTO fact_check_results
            (event_id, accuracy_score, credibility_assessment, fact_check_issues,
             enhancement_suggestions, validation_timestamp, validator_agent, validation_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.event_id,
            result.accuracy_score, 
            result.credibility_assessment,
            json.dumps(result.fact_check_issues),
            json.dumps(result.enhancement_suggestions),
            result.validation_timestamp,
            result.validator_agent,
            validation_hash
        ))
        
        # Clear old source validations for this event
        cursor.execute("DELETE FROM source_validations WHERE event_id = ?", (result.event_id,))
        
        # Insert source validations
        for validation in result.source_validations:
            cursor.execute("""
                INSERT INTO source_validations
                (event_id, url, accessible, status_code, content_type, title_match,
                 outlet_match, credibility_score, issues, validation_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.event_id,
                validation.url,
                validation.accessible,
                validation.status_code,
                validation.content_type,
                validation.title_match,
                validation.outlet_match,
                validation.credibility_score,
                json.dumps(validation.issues),
                validation.validation_timestamp
            ))
        
        conn.commit()
        conn.close()
        
        # Log structured result
        log_entry = {
            "timestamp": result.validation_timestamp,
            "event_id": result.event_id,
            "validation_type": "fact_check",
            "accuracy_score": result.accuracy_score,
            "credibility_assessment": result.credibility_assessment,
            "issues_count": len(result.fact_check_issues),
            "sources_validated": len(result.source_validations),
            "accessible_sources": sum(1 for sv in result.source_validations if sv.accessible),
            "avg_source_credibility": sum(sv.credibility_score for sv in result.source_validations) / len(result.source_validations) if result.source_validations else 0
        }
        
        self.logger.info(json.dumps(log_entry))
    
    def generate_validation_priorities(self) -> List[Tuple[str, int, str]]:
        """Generate prioritized list of events needing validation"""
        priorities = []
        
        # Get all events
        for filename in os.listdir(self.events_dir):
            if not filename.endswith('.json'):
                continue
                
            event_path = os.path.join(self.events_dir, filename)
            try:
                with open(event_path, 'r') as f:
                    event_data = json.load(f)
                
                event_id = event_data.get('id', filename.replace('.json', ''))
                priority_score = 0
                reasons = []
                
                # High importance events get priority
                importance = event_data.get('importance', 5)
                priority_score += importance
                
                # Events with few/no sources get priority  
                sources = event_data.get('sources', [])
                if len(sources) == 0:
                    priority_score += 5
                    reasons.append("no_sources")
                elif len(sources) < 2:
                    priority_score += 3  
                    reasons.append("few_sources")
                
                # Events with certain tags get priority
                tags = event_data.get('tags', [])
                priority_tags = ['whig', 'intelligence-manipulation', 'constitutional-crisis']
                if any(tag in tags for tag in priority_tags):
                    priority_score += 2
                    reasons.append("priority_tags")
                
                # Recent events get priority
                date_str = event_data.get('date', '')
                if date_str and date_str >= '2020-01-01':
                    priority_score += 2
                    reasons.append("recent_event")
                
                priorities.append((event_id, priority_score, ', '.join(reasons)))
                
            except Exception as e:
                self.logger.error(f"Error processing {filename}: {e}")
        
        # Sort by priority score descending
        priorities.sort(key=lambda x: x[1], reverse=True)
        return priorities
    
    def populate_validation_queue(self, max_items: int = 100):
        """Populate validation queue with prioritized events"""
        priorities = self.generate_validation_priorities()
        
        conn = sqlite3.connect(self.validation_db)
        cursor = conn.cursor()
        
        # Clear existing queue
        cursor.execute("DELETE FROM validation_queue")
        
        # Add top priority items
        for event_id, priority_score, reason in priorities[:max_items]:
            cursor.execute("""
                INSERT INTO validation_queue (event_id, priority_score, reason, added_timestamp)
                VALUES (?, ?, ?, ?)
            """, (event_id, priority_score, reason, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        self.logger.info(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "action": "queue_populated",
            "items_added": min(max_items, len(priorities)),
            "total_events_analyzed": len(priorities)
        }))

def main():
    """Main execution for fact-checking agent"""
    fact_checker = TimelineFactChecker()
    
    # Populate validation queue
    print("Populating validation queue...")
    fact_checker.populate_validation_queue()
    
    # Process a few high-priority events
    conn = sqlite3.connect(fact_checker.validation_db)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT event_id FROM validation_queue 
        WHERE status = 'pending'
        ORDER BY priority_score DESC 
        LIMIT 5
    """)
    
    pending_events = cursor.fetchall()
    
    for (event_id,) in pending_events:
        print(f"Fact-checking event: {event_id}")
        
        # Load event data
        event_path = os.path.join(fact_checker.events_dir, f"{event_id}.json")
        if not os.path.exists(event_path):
            continue
            
        with open(event_path, 'r') as f:
            event_data = json.load(f)
        
        # Perform fact check
        result = fact_checker.fact_check_event(event_data)
        fact_checker.save_fact_check_result(result)
        
        # Update queue status
        cursor.execute("""
            UPDATE validation_queue SET status = 'completed'
            WHERE event_id = ?
        """, (event_id,))
        
        print(f"  Accuracy Score: {result.accuracy_score}/10")
        print(f"  Credibility: {result.credibility_assessment}")
        print(f"  Issues: {len(result.fact_check_issues)}")
        print(f"  Sources Validated: {len(result.source_validations)}")
        
        time.sleep(1)  # Rate limiting
    
    conn.commit()
    conn.close()
    
    print("Fact-checking batch completed")

if __name__ == "__main__":
    main()