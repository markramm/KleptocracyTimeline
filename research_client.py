#!/usr/bin/env python3
"""
Timeline Research Client - Python interface for the research API
Enables easy programmatic access for research automation and analysis
"""

import requests
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, date
import yaml
from pathlib import Path

class TimelineResearchClient:
    """Client for interacting with the Timeline Research API"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5174"):
        """Initialize client with API base URL"""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request and return JSON response"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
                raise Exception(f"API Error {response.status_code}: {error_data.get('error', 'Unknown error')}")
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
        return self._request('GET', '/api/search', params=params)
    
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
        result = self._request('GET', '/api/actors')
        return result.get('actors', [])
    
    def get_tags(self) -> List[str]:
        """Get all unique tags"""  
        result = self._request('GET', '/api/tags')
        return result.get('tags', [])
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        return self._request('GET', '/api/stats')
    
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
        return self._request('POST', '/api/events', json=event_data, params=params)
    
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