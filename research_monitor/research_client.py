#!/usr/bin/env python3
"""
Research Monitor v2 API Client
Extended Python client for Research Monitor v2 API endpoints
Builds on the original Timeline Research Client with full API coverage
"""

import argparse
import json
import logging
import os
import pprint
import requests
import sys
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime, date

logger = logging.getLogger(__name__)

class ResearchMonitorClient:
    """
    Python client for Research Monitor v2 API
    Covers all endpoints including timeline viewer functionality
    """
    
    def __init__(self, base_url: str = "http://localhost:5558", api_key: str = None):
        """
        Initialize client
        
        Args:
            base_url: Base URL for the API server
            api_key: API key for write operations
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        # Set default headers
        if api_key:
            self.session.headers['X-API-Key'] = api_key
        self.session.headers['Content-Type'] = 'application/json'
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {url} - {e}")
            raise
    
    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """GET request with JSON response"""
        response = self._request('GET', endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    def _post(self, endpoint: str, data: Dict = None) -> Dict:
        """POST request with JSON payload"""
        response = self._request('POST', endpoint, json=data)
        response.raise_for_status()
        return response.json()
    
    def _put(self, endpoint: str, data: Dict = None) -> Dict:
        """PUT request with JSON payload"""
        response = self._request('PUT', endpoint, json=data)
        response.raise_for_status()
        return response.json()
    
    def _delete(self, endpoint: str) -> Dict:
        """DELETE request"""
        response = self._request('DELETE', endpoint)
        response.raise_for_status()
        return response.json()
    
    # ==================== HEALTH & STATUS ====================
    
    def health_check(self) -> Dict:
        """Check API health"""
        return self._get('/api/server/health')
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        return self._get('/api/stats')
    
    # ==================== RESEARCH PRIORITIES ====================
    
    def get_next_priority(self) -> Dict:
        """Get next priority to research"""
        return self._get('/api/priorities/next')
    
    def get_priorities(self, status: str = None, limit: int = 50) -> Dict:
        """Get research priorities with optional filtering"""
        params = {'limit': limit}
        if status:
            params['status'] = status
        return self._get('/api/priorities', params=params)
    
    def get_priority(self, priority_id: str) -> Dict:
        """Get specific priority by ID"""
        return self._get(f'/api/priorities/{priority_id}')
    
    def update_priority_status(self, priority_id: str, status: str, 
                              actual_events: int = None, notes: str = None) -> Dict:
        """Update priority status"""
        data = {'status': status}
        if actual_events is not None:
            data['actual_events'] = actual_events
        if notes:
            data['notes'] = notes
        return self._put(f'/api/priorities/{priority_id}/status', data)
    
    def export_priorities(self) -> Dict:
        """Export valuable priorities"""
        return self._get('/api/priorities/export')
    
    # ==================== TIMELINE EVENTS ====================
    
    def search_events(self, query: str, limit: int = 50) -> Dict:
        """Search events by text query"""
        return self._get('/api/events/search', params={'q': query, 'limit': limit})
    
    def validate_event(self, event_data: Dict) -> Dict:
        """Validate event data"""
        return self._post('/api/events/validate', event_data)
    
    def stage_event(self, event_data: Dict) -> Dict:
        """Stage event for commit"""
        return self._post('/api/events/staged', event_data)
    
    def get_timeline_events(self, page: int = 1, limit: int = 50, 
                           min_importance: int = None, max_importance: int = None,
                           start_date: str = None, end_date: str = None,
                           actors: List[str] = None, tags: List[str] = None,
                           status: str = None) -> Dict:
        """Get timeline events with filtering and pagination"""
        params = {'page': page, 'limit': limit}
        
        if min_importance is not None:
            params['min_importance'] = min_importance
        if max_importance is not None:
            params['max_importance'] = max_importance
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if actors:
            params['actors'] = ','.join(actors)
        if tags:
            params['tags'] = ','.join(tags)
        if status:
            params['status'] = status
            
        return self._get('/api/timeline/events', params=params)
    
    def get_timeline_event(self, event_id: str) -> Dict:
        """Get specific timeline event by ID"""
        return self._get(f'/api/timeline/events/{event_id}')
    
    def get_events_by_date(self, date: str) -> Dict:
        """Get events for specific date"""
        return self._get(f'/api/timeline/events/date/{date}')
    
    # ==================== TIMELINE METADATA ====================
    
    def get_timeline_actors(self, min_events: int = 1, limit: int = None) -> Dict:
        """Get timeline actors"""
        params = {'min_events': min_events}
        if limit:
            params['limit'] = limit
        return self._get('/api/timeline/actors', params=params)
    
    def get_timeline_tags(self, min_events: int = 1, limit: int = None) -> Dict:
        """Get timeline tags"""
        params = {'min_events': min_events}
        if limit:
            params['limit'] = limit
        return self._get('/api/timeline/tags', params=params)
    
    def get_timeline_sources(self, limit: int = None) -> Dict:
        """Get timeline sources"""
        params = {}
        if limit:
            params['limit'] = limit
        return self._get('/api/timeline/sources', params=params)
    
    def get_timeline_date_range(self) -> Dict:
        """Get timeline date range"""
        return self._get('/api/timeline/date-range')
    
    # ==================== TIMELINE FILTERING ====================
    
    def filter_timeline(self, filters: Dict) -> Dict:
        """Filter timeline with complex criteria"""
        return self._get('/api/timeline/filter', params=filters)
    
    def search_timeline(self, search_criteria: Dict) -> Dict:
        """Advanced timeline search"""
        return self._post('/api/timeline/search', search_criteria)
    
    # ==================== VIEWER DATA ====================
    
    def get_timeline_data(self, limit: int = 1000) -> Dict:
        """Get timeline data optimized for visualization"""
        return self._get('/api/viewer/timeline-data', params={'limit': limit})
    
    def get_actor_network(self, min_connections: int = 3, limit: int = 100) -> Dict:
        """Get actor network for visualization"""
        params = {'min_connections': min_connections, 'limit': limit}
        return self._get('/api/viewer/actor-network', params=params)
    
    def get_tag_cloud(self, min_count: int = 2, limit: int = 50) -> Dict:
        """Get tag cloud data"""
        params = {'min_count': min_count, 'limit': limit}
        return self._get('/api/viewer/tag-cloud', params=params)
    
    # ==================== VIEWER STATISTICS ====================
    
    def get_overview_stats(self) -> Dict:
        """Get overview statistics"""
        return self._get('/api/viewer/stats/overview')
    
    def get_actor_stats(self, min_events: int = 5) -> Dict:
        """Get actor statistics"""
        return self._get('/api/viewer/stats/actors', params={'min_events': min_events})
    
    def get_importance_stats(self) -> Dict:
        """Get importance distribution statistics"""
        return self._get('/api/viewer/stats/importance')
    
    def get_timeline_stats(self) -> Dict:
        """Get timeline coverage statistics"""
        return self._get('/api/viewer/stats/timeline')
    
    def get_tag_stats(self, limit: int = 20) -> Dict:
        """Get tag usage statistics"""
        return self._get('/api/viewer/stats/tags', params={'limit': limit})
    
    def get_source_stats(self, limit: int = 20) -> Dict:
        """Get source statistics"""
        return self._get('/api/viewer/stats/sources', params={'limit': limit})
    
    # ==================== COMMIT ORCHESTRATION ====================
    
    def get_commit_status(self) -> Dict:
        """Check commit status"""
        return self._get('/api/commit/status')
    
    def reset_commit_counter(self) -> Dict:
        """Reset commit counter after committing"""
        return self._post('/api/commit/reset')
    
    # ==================== CACHE MANAGEMENT ====================
    
    def clear_cache(self) -> Dict:
        """Clear all caches"""
        return self._post('/api/cache/clear')
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return self._get('/api/cache/stats')
    
    # ==================== HIGH-LEVEL RESEARCH WORKFLOW METHODS ====================
    
    def analyze_actor(self, actor_name: str) -> Dict:
        """
        Analyze all events involving a specific actor
        
        Args:
            actor_name: Name of actor to analyze
            
        Returns:
            Analysis dictionary with events, timeline, tags, etc.
        """
        events = self.search_events(f'"{actor_name}"').get('events', [])
        
        if not events:
            return {'actor': actor_name, 'events': [], 'total': 0}
        
        # Analyze patterns
        tags = set()
        other_actors = set()
        years = set()
        importance_levels = []
        
        for event in events:
            event_content = event.get('json_content', event)
            tags.update(event_content.get('tags', []))
            other_actors.update(event_content.get('actors', []))
            if event_content.get('date'):
                years.add(event_content['date'][:4])
            if event_content.get('importance'):
                importance_levels.append(event_content['importance'])
        
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
                'start': min([e.get('date') for e in events if e.get('date')]) if events else None,
                'end': max([e.get('date') for e in events if e.get('date')]) if events else None
            }
        }
        
        return analysis
    
    def research_timeline_period(self, start_date: str, end_date: str) -> Dict:
        """
        Research events in a specific time period
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Timeline analysis dictionary
        """
        events_response = self.get_timeline_events(
            start_date=start_date, 
            end_date=end_date, 
            limit=1000
        )
        events = events_response.get('events', [])
        
        # Group by month
        by_month = {}
        all_actors = set()
        all_tags = set()
        
        for event in events:
            event_content = event.get('json_content', event)
            month = event.get('date', '')[:7]  # YYYY-MM
            if month not in by_month:
                by_month[month] = []
            by_month[month].append(event)
            
            all_actors.update(event_content.get('actors', []))
            all_tags.update(event_content.get('tags', []))
        
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
        high_importance_response = self.get_timeline_events(min_importance=8, limit=20)
        high_importance = high_importance_response.get('events', [])
        
        # Find actors with multiple high-importance events
        actor_counts = {}
        for event in high_importance:
            event_content = event.get('json_content', event)
            for actor in event_content.get('actors', []):
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
        
        # Suggest gap analysis using overview stats
        try:
            stats = self.get_overview_stats()
            events_by_year = stats.get('events_by_year', {})
            if events_by_year:
                avg_events = sum(events_by_year.values()) / len(events_by_year)
                for year, count in events_by_year.items():
                    if count < avg_events * 0.5 and int(year) >= 2000:  # Focus on recent years
                        suggestions.append({
                            'type': 'gap_analysis',
                            'target': year,
                            'priority': 7,
                            'reason': f'Only {count} events in {year}, below average of {avg_events:.1f}',
                            'query': f'Research significant events missing from {year} timeline'
                        })
        except Exception as e:
            logger.warning(f"Could not get stats for gap analysis: {e}")
        
        return suggestions[:10]  # Top 10 suggestions
    
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
            filters['actors'] = [actor]
        if tag:
            filters['tags'] = [tag]
        if date_range:
            filters['start_date'], filters['end_date'] = date_range
        
        response = self.get_timeline_events(**filters, limit=100)
        return response.get('events', [])
    
    def research_priority(self, priority_id: str, events_data: List[Dict]) -> Dict:
        """
        Complete research workflow for a priority
        
        Args:
            priority_id: Priority to research
            events_data: List of events to create
            
        Returns:
            Dict with results summary
        """
        results = {
            'priority_id': priority_id,
            'events_created': 0,
            'events_failed': 0,
            'errors': []
        }
        
        try:
            # Mark priority as in progress
            self.update_priority_status(priority_id, 'in_progress')
            
            # Create events
            for event_data in events_data:
                try:
                    # Add priority reference
                    event_data['priority_id'] = priority_id
                    
                    # Validate first
                    validation = self.validate_event(event_data)
                    if not validation.get('valid', False):
                        results['errors'].append(f"Invalid event {event_data.get('id')}: {validation.get('errors')}")
                        results['events_failed'] += 1
                        continue
                    
                    # Stage event
                    self.stage_event(event_data)
                    results['events_created'] += 1
                    
                except Exception as e:
                    results['errors'].append(f"Failed to create event {event_data.get('id')}: {str(e)}")
                    results['events_failed'] += 1
            
            # Update priority status
            status = 'completed' if results['events_failed'] == 0 else 'blocked'
            self.update_priority_status(
                priority_id, 
                status, 
                actual_events=results['events_created']
            )
            
            results['final_status'] = status
            
        except Exception as e:
            results['errors'].append(f"Research workflow failed: {str(e)}")
            
        return results
    
    def bulk_search(self, queries: List[str]) -> Dict:
        """
        Perform multiple searches in parallel
        
        Args:
            queries: List of search terms
            
        Returns:
            Dict mapping queries to results
        """
        results = {}
        for query in queries:
            try:
                results[query] = self.search_events(query)
            except Exception as e:
                results[query] = {'error': str(e)}
        return results
    
    def get_actor_timeline(self, actor_name: str) -> Dict:
        """
        Get complete timeline for specific actor
        
        Args:
            actor_name: Name of actor to trace
            
        Returns:
            Events involving this actor
        """
        return self.search_events(f'"{actor_name}"')
    
    def analyze_time_period(self, start_date: str, end_date: str) -> Dict:
        """
        Comprehensive analysis of time period
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Analysis results
        """
        events = self.get_timeline_events(
            start_date=start_date, 
            end_date=end_date,
            limit=1000
        )
        
        # Get statistics for this period
        overview = self.get_overview_stats()
        
        return {
            'period': f"{start_date} to {end_date}",
            'events': events,
            'total_events': events.get('total', 0),
            'overview_stats': overview
        }


# ==================== CONVENIENCE FUNCTIONS ====================

def create_client(base_url: str = None, api_key: str = None) -> ResearchMonitorClient:
    """Create API client with defaults from environment"""
    
    if not base_url:
        port = os.environ.get('RESEARCH_MONITOR_PORT', '5558')
        base_url = f"http://localhost:{port}"
    
    if not api_key:
        api_key = os.environ.get('RESEARCH_MONITOR_API_KEY')
    
    return ResearchMonitorClient(base_url, api_key)

def quick_search(query: str, **filters) -> List[Dict]:
    """Quick search function"""
    client = create_client()
    response = client.search_events(query, **filters) 
    return response.get('events', [])

def analyze_actor(actor_name: str) -> Dict:
    """Quick actor analysis"""
    client = create_client()
    return client.analyze_actor(actor_name)

def create_timeline_event(event_data: Dict) -> Dict:
    """Create timeline event"""
    client = create_client()
    return client.stage_event(event_data)


# ==================== CLI INTERFACE ====================

def main():
    """Command-line interface for testing client"""
    
    parser = argparse.ArgumentParser(description='Research Monitor API Client')
    parser.add_argument('--url', default='http://localhost:5558', help='API base URL')
    parser.add_argument('--key', help='API key')
    parser.add_argument('command', help='API command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    
    args = parser.parse_args()
    
    client = ResearchMonitorClient(args.url, args.key)
    
    try:
        if args.command == 'stats':
            result = client.get_stats()
        elif args.command == 'next-priority':
            result = client.get_next_priority()
        elif args.command == 'search':
            if not args.args:
                print("Search requires a query argument")
                return 1
            result = client.search_events(args.args[0])
        elif args.command == 'events':
            result = client.get_timeline_events()
        elif args.command == 'actors':
            result = client.get_timeline_actors()
        elif args.command == 'actor-network':
            result = client.get_actor_network()
        elif args.command == 'analyze-actor':
            if not args.args:
                print("analyze-actor requires an actor name argument")
                return 1
            result = client.analyze_actor(args.args[0])
        elif args.command == 'overview':
            result = client.get_overview_stats()
        else:
            print(f"Unknown command: {args.command}")
            print("Available commands: stats, next-priority, search, events, actors, actor-network, analyze-actor, overview")
            return 1
        
        pprint.pprint(result)
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())