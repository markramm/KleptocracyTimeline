#!/usr/bin/env python3
"""
Timeline Research Client - Python interface for the research API
Enables easy programmatic access for research automation and analysis
"""

import requests
import json
import sys
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from pathlib import Path

# Import standardized config
sys.path.append(str(Path(__file__).parent / "research_monitor"))
try:
    from config import get_research_monitor_url
except ImportError:
    # Fallback if config not available
    def get_research_monitor_url():
        return "http://127.0.0.1:5558"

class TimelineResearchClient:
    """Client for interacting with the Timeline Research API"""
    
    def __init__(self, base_url: str = None, api_key: str = "test-key"):
        """Initialize client with API base URL and API key"""
        if base_url is None:
            base_url = get_research_monitor_url()
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-Key': api_key
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request and return JSON response"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
                # Try to get the most descriptive error message
                error_msg = (error_data.get('message') or 
                           error_data.get('error') or 
                           ', '.join(error_data.get('errors', [])) or
                           'Unknown error')
                raise Exception(f"API Error {response.status_code}: {error_msg}")
            except json.JSONDecodeError:
                raise Exception(f"HTTP Error {response.status_code}: {response.text}")
        
        return response.json()
    
    # Search and Query Methods
    
    def search(self, query: str = '', **filters) -> Dict:
        """
        Search timeline events with full-text search and filters
        
        Args:
            query: Full-text search query
            **filters: Additional filters (start_date, end_date, actor, tag, etc.)
        
        Returns:
            Dictionary with events list and metadata
        """
        params = {'q': query}
        params.update(filters)
        return self._request('GET', '/api/events/search', params=params)
    
    def search_events(self, query: str = '', **filters) -> List[Dict]:
        """
        Search timeline events and return just the events list
        
        Args:
            query: Full-text search query  
            **filters: Additional filters
            
        Returns:
            List of event dictionaries
        """
        result = self.search(query, **filters)
        return result.get('events', [])
    
    def get_event(self, event_id: str) -> Optional[Dict]:
        """
        Get single event by ID with connections
        
        Args:
            event_id: Event ID to retrieve
            
        Returns:
            Event dictionary or None if not found
        """
        try:
            return self._request('GET', f'/api/event/{event_id}')
        except Exception as e:
            if '404' in str(e):
                return None
            raise
    
    def get_actors(self) -> List[str]:
        """Get all unique actors"""
        result = self._request('GET', '/api/timeline/actors')
        return result.get('actors', [])
    
    def get_tags(self) -> List[str]:
        """Get all unique tags"""  
        result = self._request('GET', '/api/timeline/tags')
        return result.get('tags', [])
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        return self._request('GET', '/api/stats')
    
    # New Research Enhancement Methods
    
    def get_events_missing_sources(self, min_sources: int = 2, limit: int = 50) -> List[Dict]:
        """
        Find events with missing or insufficient sources
        
        Args:
            min_sources: Minimum number of sources required (default 2)
            limit: Maximum number of events to return
            
        Returns:
            List of events with insufficient sources
        """
        params = {'min_sources': min_sources, 'limit': limit}
        result = self._request('GET', '/api/events/missing-sources', params=params)
        return result.get('events', [])
    
    def get_validation_queue(self, limit: int = 50) -> List[Dict]:
        """
        Get events prioritized for validation by importance and source quality
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of events prioritized for validation
        """
        params = {'limit': limit}
        result = self._request('GET', '/api/events/validation-queue', params=params)
        return result.get('events', [])
    
    def get_broken_links(self, limit: int = 50) -> List[Dict]:
        """
        Find events with potentially broken or inaccessible source links
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of events with suspicious source URLs
        """
        params = {'limit': limit}
        result = self._request('GET', '/api/events/broken-links', params=params)
        return result.get('events', [])
    
    def get_research_candidates(self, min_importance: int = 7, limit: int = 50) -> List[Dict]:
        """
        Get high-importance events with insufficient sources - ideal for research
        
        Args:
            min_importance: Minimum importance level (default 7)
            limit: Maximum number of events to return
            
        Returns:
            List of high-priority research candidates
        """
        params = {'min_importance': min_importance, 'limit': limit}
        result = self._request('GET', '/api/events/research-candidates', params=params)
        return result.get('events', [])
    
    def get_actor_timeline(self, actor: str, start_year: int = None, end_year: int = None) -> Dict:
        """
        Get chronological timeline of all events for a specific actor
        
        Args:
            actor: Actor name to get timeline for
            start_year: Optional start year filter
            end_year: Optional end year filter
            
        Returns:
            Timeline data grouped by years with analysis
        """
        params = {}
        if start_year:
            params['start_year'] = start_year
        if end_year:
            params['end_year'] = end_year
        
        return self._request('GET', f'/api/timeline/actor/{actor}/timeline', params=params)
    
    # QA Queue Methods
    
    def get_qa_queue(self, limit: int = 50, offset: int = 0, 
                     min_importance: int = 1, include_validated: bool = False) -> Dict:
        """Get prioritized queue of events needing QA"""
        params = {
            'limit': limit,
            'offset': offset,
            'min_importance': min_importance,
            'include_validated': str(include_validated).lower()
        }
        return self._request('GET', '/api/qa/queue', params=params)
    
    def get_next_qa_event(self, min_importance: int = 7) -> Dict:
        """Get the next highest priority event for QA"""
        params = {'min_importance': min_importance}
        return self._request('GET', '/api/qa/next', params=params)
    
    def get_qa_stats(self) -> Dict:
        """Get comprehensive QA statistics"""
        return self._request('GET', '/api/qa/stats')
    
    def mark_event_validated(self, event_id: str, quality_score: float, 
                           validation_notes: str = "", created_by: str = "qa-agent") -> Dict:
        """Mark an event as validated with quality score"""
        data = {
            'quality_score': quality_score,
            'validation_notes': validation_notes,
            'created_by': created_by
        }
        return self._request('POST', f'/api/qa/validate/{event_id}', json=data)
    
    def enhance_event_with_qa(self, event_id: str, enhanced_event_file: str, quality_score: float,
                             validation_notes: str = "", created_by: str = "qa-agent") -> Dict:
        """Enhance an event with improved content and record QA metadata"""
        import json
        
        # Load the enhanced event from file
        try:
            with open(enhanced_event_file, 'r', encoding='utf-8') as f:
                enhanced_event = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load enhanced event file: {e}")
        
        data = {
            'enhanced_event': enhanced_event,
            'quality_score': quality_score,
            'validation_notes': validation_notes,
            'created_by': created_by
        }
        return self._request('POST', f'/api/qa/enhance/{event_id}', json=data)
    
    def mark_event_in_progress(self, event_id: str, created_by: str = "qa-agent", 
                              agent_id: str = None) -> Dict:
        """Mark an event as in_progress to prevent duplicate processing"""
        data = {
            'created_by': created_by,
            'agent_id': agent_id or created_by
        }
        return self._request('POST', f'/api/qa/start/{event_id}', json=data)
    
    def mark_event_rejected(self, event_id: str, rejection_reason: str, 
                           created_by: str = "qa-agent") -> Dict:
        """Mark an event as rejected with detailed reasoning"""
        data = {
            'rejection_reason': rejection_reason,
            'created_by': created_by
        }
        return self._request('POST', f'/api/qa/reject/{event_id}', json=data)
    
    def get_qa_candidates_by_issue(self, issue_type: str, limit: int = 20) -> Dict:
        """Get events with specific QA issues"""
        params = {'limit': limit}
        return self._request('GET', f'/api/qa/issues/{issue_type}', params=params)
    
    def calculate_qa_score(self, event_data: Dict, metadata: Dict = None) -> Dict:
        """Calculate QA priority score for event data"""
        data = {'event': event_data}
        if metadata:
            data['metadata'] = metadata
        return self._request('POST', '/api/qa/score', json=data)
    
    def initialize_validation_audit_trail(self, created_by: str = "client-init", dry_run: bool = False) -> Dict:
        """Initialize metadata records for all events to create complete validation audit trail"""
        data = {'created_by': created_by, 'dry_run': dry_run}
        return self._request('POST', '/api/qa/validation/initialize', json=data)
    
    def reset_validation_audit_trail(self, created_by: str = "client-reset", dry_run: bool = False) -> Dict:
        """Reset all validation records to pending status for complete re-validation"""
        data = {'created_by': created_by, 'dry_run': dry_run}
        return self._request('POST', '/api/qa/validation/reset', json=data)
    
    # Documentation and Help Methods
    
    def help(self, topic: str = None) -> str:
        """
        Get comprehensive help documentation for the research client
        
        Args:
            topic: Optional specific topic to get help for
            
        Returns:
            Help documentation as string
        """
        if topic:
            return self._get_topic_help(topic.lower())
        
        return self._get_general_help()
    
    def _get_general_help(self) -> str:
        """Generate general help documentation"""
        return """
🔍 Timeline Research Client - Comprehensive API Documentation

BASIC USAGE:
    from research_client import TimelineResearchClient
    client = TimelineResearchClient()

AVAILABLE METHODS:
    
📊 BASIC QUERIES:
    client.search(query, **filters)           # Full-text search with filters
    client.search_events(query, **filters)    # Search returning just events list
    client.get_event(event_id)                # Get single event by ID
    client.get_stats()                        # Database statistics
    client.get_actors()                       # List all actors
    client.get_tags()                         # List all tags

🎯 RESEARCH & VALIDATION (NEW):
    client.get_events_missing_sources(min_sources=2, limit=50)
    client.get_validation_queue(limit=50)
    client.get_broken_links(limit=50)
    client.get_research_candidates(min_importance=7, limit=50)
    client.get_actor_timeline(actor, start_year=None, end_year=None)

📝 EVENT MANAGEMENT:
    client.create_event(event_data, save_yaml=False)
    client.update_event(event_id, event_data, save_yaml=False)

🔬 RESEARCH WORKFLOW:
    client.add_research_note(query, results='', priority=5, status='pending')
    client.get_research_notes(status=None, limit=50)
    client.add_connection(event_id_1, event_id_2, connection_type='related')

🔧 UTILITIES:
    client.reload_data()                      # Force reload from filesystem
    client.suggest_research_priorities()     # Get research suggestions
    client.help(topic=None)                  # This help system

📖 DETAILED HELP:
    client.help('search')        # Search and query help
    client.help('validation')    # Validation workflow help
    client.help('events')        # Event management help
    client.help('research')      # Research workflow help
    client.help('examples')      # Code examples
    client.help('endpoints')     # All API endpoints

💡 QUICK START EXAMPLES:
    # Search for events
    events = client.search_events("Trump crypto")
    
    # Get validation queue
    to_validate = client.get_validation_queue(limit=10)
    
    # Analyze actor timeline
    timeline = client.get_actor_timeline("Trump")
    print(f"Found {timeline['total_events']} events")
    
    # Find research candidates
    candidates = client.get_research_candidates(min_importance=8)

For detailed examples: client.help('examples')
"""

    def _get_topic_help(self, topic: str) -> str:
        """Get help for specific topics"""
        
        topics = {
            'search': """
🔍 SEARCH AND QUERY METHODS:

client.search(query='', **filters)
    Full-text search with metadata. Returns complete response with metadata.
    Filters: start_date, end_date, actor, tag, importance_min, importance_max
    
    Example:
    result = client.search("Trump", importance_min=8, start_date="2020-01-01")
    events = result['events']
    total = result['total']

client.search_events(query='', **filters)  
    Same as search() but returns just the events list.
    
    Example:
    events = client.search_events("surveillance FISA", limit=10)

client.get_event(event_id)
    Get single event with full details and connections.
    
    Example:
    event = client.get_event("2016-06-09--trump-tower-russian-meeting")

client.get_actors() / client.get_tags()
    Get all unique actors or tags in the database.
    
    Example:
    actors = client.get_actors()
    tags = client.get_tags()
""",

            'validation': """
🎯 VALIDATION AND QUALITY CONTROL METHODS:

client.get_events_missing_sources(min_sources=2, limit=50)
    Find events with insufficient sources for validation.
    
    Example:
    missing = client.get_events_missing_sources(min_sources=3, limit=20)
    for event in missing:
        print(f"Event {event['id']} needs {3 - len(event.get('sources', []))} more sources")

client.get_validation_queue(limit=50)
    Get events prioritized for validation by importance and source quality.
    
    Example:
    queue = client.get_validation_queue(limit=10)
    for event in queue:
        print(f"High priority: {event['title']} (importance: {event['importance']})")

client.get_broken_links(limit=50)
    Find events with potentially broken or placeholder source links.
    
    Example:
    broken = client.get_broken_links(limit=25)
    for event in broken:
        sources = event.get('sources', [])
        print(f"Check sources for: {event['title']}")

client.get_research_candidates(min_importance=7, limit=50)
    Get high-importance events with insufficient sources - ideal for research.
    
    Example:
    candidates = client.get_research_candidates(min_importance=8, limit=15)
    for event in candidates:
        importance = event['importance']
        source_count = len(event.get('sources', []))
        print(f"Research needed: {event['title']} (imp:{importance}, sources:{source_count})")
""",

            'timeline': """
📈 TIMELINE AND ACTOR ANALYSIS:

client.get_actor_timeline(actor, start_year=None, end_year=None)
    Get comprehensive timeline for specific actor with year grouping.
    
    Example:
    timeline = client.get_actor_timeline("Trump")
    print(f"Total events: {timeline['total_events']}")
    print(f"Years covered: {len(timeline['events_by_year'])}")
    
    # Access events by year
    events_2016 = timeline['events_by_year']['2016']
    print(f"2016 events: {len(events_2016)}")
    
    # Get date range
    earliest = timeline['date_range']['earliest']
    latest = timeline['date_range']['latest']
    
    # Filter by years
    recent = client.get_actor_timeline("Trump", start_year=2020, end_year=2025)

client.analyze_actor(actor_name)
    Comprehensive actor analysis with patterns and statistics.
    
    Example:
    analysis = client.analyze_actor("Peter Thiel")
    print(f"Active years: {analysis['active_years']}")
    print(f"Common tags: {analysis['common_tags']}")
    print(f"Co-actors: {analysis['frequent_co_actors']}")
    print(f"Average importance: {analysis['avg_importance']}")
""",

            'events': """
📝 EVENT MANAGEMENT METHODS:

client.create_event(event_data, save_yaml=False)
    Create new timeline event.
    
    Example:
    event_data = {
        'id': '2025-01-20--example-event',
        'date': '2025-01-20',
        'title': 'Example Event',
        'summary': 'Detailed description...',
        'importance': 7,
        'actors': ['Actor 1', 'Actor 2'],
        'tags': ['tag1', 'tag2'],
        'sources': [
            {'title': 'Source Title', 'url': 'https://example.com', 'outlet': 'News Site'}
        ]
    }
    result = client.create_event(event_data, save_yaml=True)

client.update_event(event_id, event_data, save_yaml=False)
    Update existing event.
    
    Example:
    updated_data = {
        'importance': 9,  # Upgrade importance
        'summary': 'Updated summary with new information...'
    }
    result = client.update_event('2025-01-20--example-event', updated_data)

Event ID Format: YYYY-MM-DD--descriptive-slug-here
- Use actual event date, not today's date
- Keep slugs descriptive and searchable
- Use lowercase with hyphens
""",

            'research': """
🔬 RESEARCH WORKFLOW METHODS:

client.add_research_note(query, results='', priority=5, status='pending')
    Add research note for workflow tracking.
    
    Example:
    note = client.add_research_note(
        query="Investigate Trump's 2019 financial disclosures",
        priority=8,
        status='in_progress'
    )

client.get_research_notes(status=None, limit=50)
    Get research notes with optional status filter.
    
    Example:
    pending_notes = client.get_research_notes(status='pending', limit=20)
    for note in pending_notes:
        print(f"TODO: {note['query']} (priority: {note['priority']})")

client.add_connection(event_id_1, event_id_2, connection_type='related', strength=1.0)
    Add connection between two events.
    
    Example:
    connection = client.add_connection(
        '2016-06-09--trump-tower-russian-meeting',
        '2016-11-08--trump-election-victory',
        connection_type='leads_to',
        strength=0.8,
        notes='Meeting preceded election victory'
    )

client.suggest_research_priorities()
    Get AI-generated research suggestions based on event patterns.
    
    Example:
    suggestions = client.suggest_research_priorities()
    for suggestion in suggestions:
        print(f"Priority {suggestion['priority']}: {suggestion['query']}")
        print(f"Reason: {suggestion['reason']}")
""",

            'examples': """
💡 COMPREHENSIVE CODE EXAMPLES:

# 1. Find high-importance events needing research
candidates = client.get_research_candidates(min_importance=8, limit=10)
for event in candidates:
    source_count = len(event.get('sources', []))
    print(f"RESEARCH NEEDED: {event['title']}")
    print(f"   Importance: {event['importance']}, Sources: {source_count}")
    print(f"   Date: {event['date']}")
    print()

# 2. Validation workflow
validation_queue = client.get_validation_queue(limit=20)
for event in validation_queue:
    sources = event.get('sources', [])
    broken_indicators = ['example.com', 'TBD', 'internal-research']
    
    needs_validation = any(indicator in str(sources) for indicator in broken_indicators)
    if needs_validation:
        print(f"VALIDATE: {event['title']}")
        print(f"   Sources need verification: {sources}")

# 3. Actor deep dive with timeline analysis
timeline = client.get_actor_timeline("Peter Thiel")
print(f"=== PETER THIEL TIMELINE ===")
print(f"Total events: {timeline['total_events']}")
print(f"Date range: {timeline['date_range']['earliest']} to {timeline['date_range']['latest']}")

# Show events by year
for year, events in timeline['events_by_year'].items():
    print(f"{year}: {len(events)} events")
    for event in events[:2]:  # Show first 2 events per year
        print(f"   • {event['date']}: {event['title'][:50]}...")

# 4. Search and analysis workflow
# Search for specific pattern
crypto_events = client.search_events("crypto bitcoin", importance_min=6)
print(f"Found {len(crypto_events)} crypto-related events")

# Analyze common actors in results
actors = set()
for event in crypto_events:
    actors.update(event.get('actors', []))

print(f"Key crypto actors: {list(actors)[:10]}")

# 5. Research priority workflow
priorities = client.suggest_research_priorities()
print(f"=== RESEARCH PRIORITIES ===")
for i, priority in enumerate(priorities[:5]):
    print(f"{i+1}. {priority['query']} (Priority: {priority['priority']})")
    print(f"   Reason: {priority['reason']}")

# 6. Missing sources detection and enhancement
missing = client.get_events_missing_sources(min_sources=2, limit=15)
print(f"=== EVENTS NEEDING SOURCES ===")
for event in missing:
    current_sources = len(event.get('sources', []))
    print(f"{event['title']} - has {current_sources} sources, needs {2-current_sources} more")
""",

            'endpoints': """
🌐 ALL AVAILABLE API ENDPOINTS:

SEARCH & QUERY:
    GET /api/events/search                    # Search events with full-text and filters
    GET /api/timeline/actors                  # Get all unique actors  
    GET /api/timeline/tags                    # Get all unique tags
    GET /api/event/{id}                       # Get single event by ID
    GET /api/stats                           # Database statistics

VALIDATION & QUALITY:
    GET /api/events/missing-sources          # Events with insufficient sources
    GET /api/events/validation-queue         # Prioritized validation queue
    GET /api/events/broken-links            # Events with suspicious source URLs
    GET /api/events/research-candidates     # High-importance, low-source events

TIMELINE ANALYSIS:  
    GET /api/timeline/actor/{actor}/timeline # Comprehensive actor timelines
    GET /api/timeline/filter                # Filter events by criteria

EVENT MANAGEMENT:
    POST /api/events/staged                 # Create new event (staged)
    PUT /api/events/{id}                    # Update existing event
    DELETE /api/events/{id}                 # Delete event

RESEARCH WORKFLOW:
    GET /api/priorities/next                # Get next research priority
    PUT /api/priorities/{id}/status         # Update priority status
    GET /api/priorities/export              # Export all priorities

SYSTEM:
    GET /api/commit/status                  # Check commit status
    POST /api/commit/reset                  # Reset commit counter
    GET /api/reload                         # Reload data from filesystem

All endpoints return JSON. Most support limit, offset, and filtering parameters.
Authentication: Some endpoints require X-API-Key header.
"""
        }
        
        return topics.get(topic, f"❌ Unknown help topic: {topic}\\n\\nAvailable topics: {', '.join(topics.keys())}")

    # Event Management Methods
    
    def create_event(self, event_data: Dict, save_yaml: bool = False) -> Dict:
        """
        Create new timeline event
        
        Args:
            event_data: Event data dictionary
            save_yaml: Whether to save to YAML file
            
        Returns:
            Response with created event
        """
        params = {'save_yaml': 'true'} if save_yaml else {}
        return self._request('POST', '/api/events/staged', json=event_data, params=params)
    
    def update_event(self, event_id: str, event_data: Dict, save_yaml: bool = False) -> Dict:
        """
        Update existing timeline event
        
        Args:
            event_id: Event ID to update
            event_data: Updated event data
            save_yaml: Whether to update YAML file
            
        Returns:
            Response with updated event
        """
        params = {'save_yaml': 'true'} if save_yaml else {}
        return self._request('PUT', f'/api/events/{event_id}', json=event_data, params=params)
    
    def validate_event(self, event_data: Dict) -> Dict:
        """
        Validate event data without creating it
        
        Args:
            event_data: Event data to validate
            
        Returns:
            Validation result with any errors or suggestions
        """
        return self._request('POST', '/api/events/validate', json=event_data)
    
    # Research Priority Methods
    
    def get_next_priority(self) -> Dict:
        """
        Get next research priority from the queue
        
        Returns:
            Priority dictionary with id, title, description, etc.
        """
        return self._request('GET', '/api/priorities/next')
    
    def update_priority(self, priority_id: str, status: str, notes: str = None, 
                       actual_events: int = None) -> Dict:
        """
        Update priority status and progress
        
        Args:
            priority_id: Priority ID to update
            status: New status (pending, in_progress, completed)
            notes: Optional progress notes
            actual_events: Number of events actually created
            
        Returns:
            Updated priority data
        """
        data = {'status': status}
        if notes:
            data['notes'] = notes
        if actual_events is not None:
            data['actual_events'] = actual_events
        
        return self._request('PUT', f'/api/priorities/{priority_id}/status', json=data)
    
    def get_commit_status(self) -> Dict:
        """Get commit status with QA validation metadata"""
        return self._request('GET', '/api/commit/status')
    
    def reset_commit_counter(self) -> Dict:
        """Reset commit counter after performing git commit"""
        return self._request('POST', '/api/commit/reset')
    
    def get_qa_commit_message(self) -> Dict:
        """Get suggested commit message with QA validation metadata"""
        status = self.get_commit_status()
        if status.get('commit_needed') and 'suggested_commit_message' in status:
            return {
                'title': status['suggested_commit_message']['title'],
                'body': f"""
{status['suggested_commit_message']['qa_summary']}
{status['suggested_commit_message']['validation_rate']}

Recent QA Activity:
- {status['qa_validation']['recent_validations_24h']} validations in last 24h
- {status['qa_validation']['total_events_with_metadata']} total events tracked

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
""".strip(),
                'qa_metadata': status['qa_validation']
            }
        else:
            return {'error': 'No commit needed or QA metadata unavailable'}

    # Research Workflow Methods
    
    def add_research_note(self, query: str, results: str = '', priority: int = 5, 
                         status: str = 'pending') -> Dict:
        """
        Add research note for workflow tracking
        
        Args:
            query: Research query or question
            results: Research results or findings
            priority: Priority level (1-10)
            status: Note status (pending, in_progress, completed)
            
        Returns:
            Response with note ID
        """
        data = {
            'query': query,
            'results': results,
            'priority': priority,
            'status': status
        }
        return self._request('POST', '/api/research/notes', json=data)
    
    def get_research_notes(self, status: str = None, limit: int = 50) -> List[Dict]:
        """
        Get research notes with optional status filter
        
        Args:
            status: Filter by status (pending, in_progress, completed)
            limit: Maximum number of notes to return
            
        Returns:
            List of research note dictionaries
        """
        params = {'limit': limit}
        if status:
            params['status'] = status
        
        result = self._request('GET', '/api/research/notes', params=params)
        return result.get('notes', [])
    
    def add_connection(self, event_id_1: str, event_id_2: str, 
                      connection_type: str = 'related', strength: float = 1.0,
                      notes: str = '') -> Dict:
        """
        Add connection between two events
        
        Args:
            event_id_1: First event ID
            event_id_2: Second event ID
            connection_type: Type of connection (related, causes, enables, etc.)
            strength: Connection strength (0.0-1.0)
            notes: Additional notes about the connection
            
        Returns:
            Response with connection ID
        """
        data = {
            'event_id_1': event_id_1,
            'event_id_2': event_id_2,
            'connection_type': connection_type,
            'strength': strength,
            'notes': notes
        }
        return self._request('POST', '/api/research/connections', json=data)
    
    def reload_data(self) -> Dict:
        """Force reload data from YAML files"""
        return self._request('GET', '/api/reload')
    
    # Convenience Methods for Research Workflow
    
    def find_connections(self, actor: str = None, tag: str = None, 
                        date_range: tuple = None) -> List[Dict]:
        """
        Find events that might be connected based on common attributes
        
        Args:
            actor: Actor to search for
            tag: Tag to search for
            date_range: Tuple of (start_date, end_date)
            
        Returns:
            List of events with potential connections
        """
        filters = {}
        if actor:
            filters['actor'] = actor
        if tag:
            filters['tag'] = tag
        if date_range:
            filters['start_date'], filters['end_date'] = date_range
        
        return self.search_events(**filters)
    
    def analyze_actor(self, actor_name: str) -> Dict:
        """
        Analyze all events involving a specific actor
        
        Args:
            actor_name: Name of actor to analyze
            
        Returns:
            Analysis dictionary with events, timeline, tags, etc.
        """
        events = self.search_events(actor=actor_name)
        
        if not events:
            return {'actor': actor_name, 'events': [], 'total': 0}
        
        # Analyze patterns
        tags = set()
        other_actors = set()
        years = set()
        importance_levels = []
        
        for event in events:
            tags.update(event.get('tags', []))
            other_actors.update(event.get('actors', []))
            if event.get('date'):
                years.add(event['date'][:4])
            if event.get('importance'):
                importance_levels.append(event['importance'])
        
        # Remove the target actor from other_actors
        other_actors.discard(actor_name)
        
        analysis = {
            'actor': actor_name,
            'events': events,
            'total_events': len(events),
            'active_years': sorted(list(years)),
            'common_tags': sorted(list(tags)),
            'frequent_co_actors': sorted(list(other_actors)),
            'avg_importance': sum(importance_levels) / len(importance_levels) if importance_levels else 0,
            'max_importance': max(importance_levels) if importance_levels else 0,
            'date_range': {
                'start': min([e['date'] for e in events if e.get('date')]) if events else None,
                'end': max([e['date'] for e in events if e.get('date')]) if events else None
            }
        }
        
        return analysis
    
    def research_timeline(self, start_date: str, end_date: str) -> Dict:
        """
        Research events in a specific time period
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Timeline analysis dictionary
        """
        events = self.search_events(start_date=start_date, end_date=end_date)
        
        # Group by month
        by_month = {}
        all_actors = set()
        all_tags = set()
        
        for event in events:
            month = event['date'][:7]  # YYYY-MM
            if month not in by_month:
                by_month[month] = []
            by_month[month].append(event)
            
            all_actors.update(event.get('actors', []))
            all_tags.update(event.get('tags', []))
        
        return {
            'period': f"{start_date} to {end_date}",
            'total_events': len(events),
            'events_by_month': by_month,
            'all_actors': sorted(list(all_actors)),
            'all_tags': sorted(list(all_tags)),
            'events': events
        }
    
    def suggest_research_priorities(self) -> List[Dict]:
        """
        Suggest research priorities based on event patterns
        
        Returns:
            List of research suggestions with priorities
        """
        # Get recent high-importance events
        high_importance = self.search_events(min_importance=8, limit=20)
        
        # Find actors with multiple high-importance events
        actor_counts = {}
        for event in high_importance:
            for actor in event.get('actors', []):
                actor_counts[actor] = actor_counts.get(actor, 0) + 1
        
        suggestions = []
        
        # Suggest actor deep-dives
        for actor, count in sorted(actor_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= 3:
                suggestions.append({
                    'type': 'actor_analysis',
                    'target': actor,
                    'priority': min(count * 2, 10),
                    'reason': f'Actor appears in {count} high-importance events',
                    'query': f'Research comprehensive timeline for {actor}'
                })
        
        # Suggest gap analysis for years with few events
        stats = self.get_stats()
        years_data = stats.get('events_by_year', {})
        if years_data:
            avg_events = sum(years_data.values()) / len(years_data)
            for year, count in years_data.items():
                if count < avg_events * 0.5 and int(year) >= 2000:  # Focus on recent years
                    suggestions.append({
                        'type': 'gap_analysis',
                        'target': year,
                        'priority': 7,
                        'reason': f'Only {count} events in {year}, below average of {avg_events:.1f}',
                        'query': f'Research significant events missing from {year} timeline'
                    })
        
        return suggestions[:10]  # Top 10 suggestions

    # Validation Runs System Methods
    
    def list_validation_runs(self, status: str = None, run_type: str = None, 
                           limit: int = 20, offset: int = 0) -> Dict:
        """List validation runs with optional filtering"""
        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status
        if run_type:
            params['type'] = run_type
        return self._request('GET', '/api/validation-runs', params=params)
    
    def create_validation_run(self, run_type: str, **kwargs) -> Dict:
        """Create a new validation run"""
        data = {'run_type': run_type}
        data.update(kwargs)
        return self._request('POST', '/api/validation-runs', json=data)
    
    def get_validation_run(self, run_id: int) -> Dict:
        """Get detailed information about a validation run"""
        return self._request('GET', f'/api/validation-runs/{run_id}')
    
    def get_next_validation_event(self, run_id: int, validator_id: str = None) -> Dict:
        """Get next event to validate from a validation run"""
        params = {}
        if validator_id:
            params['validator_id'] = validator_id
        return self._request('GET', f'/api/validation-runs/{run_id}/next', params=params)
    
    def complete_validation_run_event(self, run_id: int, run_event_id: int, 
                                    status: str = 'validated', notes: str = '') -> Dict:
        """Complete a validation run event with flexible status handling"""
        data = {'status': status, 'notes': notes}
        return self._request('POST', f'/api/validation-runs/{run_id}/events/{run_event_id}/complete', json=data)
    
    def requeue_needs_work_events(self, run_id: int) -> Dict:
        """Requeue events marked as 'needs_work' back to pending status"""
        return self._request('POST', f'/api/validation-runs/{run_id}/requeue-needs-work')
    
    def create_validation_log(self, event_id: str, validator_type: str, status: str, notes: str, **kwargs) -> Dict:
        """Create a validation log entry"""
        data = {
            'event_id': event_id,
            'validator_type': validator_type,
            'status': status,
            'notes': notes
        }
        data.update(kwargs)
        return self._request('POST', '/api/validation-logs', json=data)
    
    def list_validation_logs(self, event_id: str = None, validation_run_id: int = None,
                           validator_type: str = None, status: str = None,
                           limit: int = 50, offset: int = 0) -> Dict:
        """List validation logs with optional filtering"""
        params = {'limit': limit, 'offset': offset}
        if event_id:
            params['event_id'] = event_id
        if validation_run_id:
            params['validation_run_id'] = validation_run_id
        if validator_type:
            params['validator_type'] = validator_type
        if status:
            params['status'] = status
        return self._request('GET', '/api/validation-logs', params=params)
    
    def list_event_update_failures(self, event_id: str = None, failure_type: str = None,
                                  validator_id: str = None, resolved: str = None,
                                  limit: int = 25, offset: int = 0) -> Dict:
        """List event update failures with optional filtering"""
        params = {'limit': limit, 'offset': offset}
        if event_id:
            params['event_id'] = event_id
        if failure_type:
            params['failure_type'] = failure_type
        if validator_id:
            params['validator_id'] = validator_id
        if resolved:
            params['resolved'] = resolved
        return self._request('GET', '/api/event-update-failures', params=params)
    
    def get_event_update_failure_stats(self) -> Dict:
        """Get statistics about event update failures"""
        return self._request('GET', '/api/event-update-failures/stats')

# Convenience functions for direct use
def quick_search(query: str, **filters) -> List[Dict]:
    """Quick search function"""
    client = TimelineResearchClient()
    return client.search_events(query, **filters)

def analyze_actor(actor_name: str) -> Dict:
    """Quick actor analysis"""
    client = TimelineResearchClient()
    return client.analyze_actor(actor_name)

def create_timeline_event(date: str, title: str, summary: str, 
                         importance: int, actors: List[str], tags: List[str],
                         sources: List[Dict], save_yaml: bool = True) -> Dict:
    """Create timeline event with minimal parameters"""
    client = TimelineResearchClient()
    
    event_data = {
        'date': date,
        'title': title,
        'summary': summary,
        'importance': importance,
        'actors': actors,
        'tags': tags,
        'sources': sources
    }
    
    return client.create_event(event_data, save_yaml=save_yaml)

if __name__ == "__main__":
    # Example usage
    client = TimelineResearchClient()
    
    print("🔍 Timeline Research Client")
    print("="*40)
    
    # Get stats
    stats = client.get_stats()
    print(f"📊 Database has {stats.get('total_events', 0)} events")
    
    # Example search
    results = client.search_events("Trump impeachment", limit=3)
    print(f"🔎 Found {len(results)} events matching 'Trump impeachment'")
    
    for event in results[:2]:
        print(f"   • {event.get('date', 'No date')}: {event.get('title', 'No title')}")
    
    # Example actor analysis
    if results:
        actors = set()
        for event in results:
            actors.update(event.get('actors', []))
        
        if actors:
            actor = list(actors)[0]
            analysis = client.analyze_actor(actor)
            print(f"👤 {actor} appears in {analysis['total_events']} events")
    
    # Research suggestions
    suggestions = client.suggest_research_priorities()
    print(f"💡 Top research suggestion: {suggestions[0]['query']}" if suggestions else "💡 No suggestions")