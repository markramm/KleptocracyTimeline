#!/usr/bin/env python3
"""
Research Monitor API Client - Lightweight Python wrapper for Research Monitor API
Designed to reduce token overhead in agent prompts while providing robust error handling
"""

import requests
import os
import json
import time
from typing import Dict, List, Optional, Union
from datetime import datetime

class ResearchAPIError(Exception):
    """Custom exception for Research API errors"""
    pass

class ResearchAPI:
    """
    Lightweight client for Research Monitor API
    
    Usage:
        api = ResearchAPI()
        priority = api.reserve_priority("agent-1")
        api.submit_events([event_data], priority['id'])
        api.complete_priority(priority['id'], events_created=1)
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize API client
        
        Args:
            base_url: Research Monitor URL (defaults to RESEARCH_MONITOR_URL env var or localhost:5558)
            api_key: API key for authentication (defaults to RESEARCH_MONITOR_API_KEY env var or 'test')
        """
        self.base_url = base_url or os.getenv('RESEARCH_MONITOR_URL', 'http://localhost:5558')
        self.api_key = api_key or os.getenv('RESEARCH_MONITOR_API_KEY', 'test')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        })
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=data or {})
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            else:
                raise ResearchAPIError(f"Unsupported HTTP method: {method}")
            
            if response.status_code >= 400:
                error_msg = f"API Error {response.status_code}: {response.text}"
                raise ResearchAPIError(error_msg)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise ResearchAPIError(f"Request failed: {str(e)}")
        except json.JSONDecodeError:
            raise ResearchAPIError(f"Invalid JSON response: {response.text}")
    
    # ===== PRIORITY MANAGEMENT =====
    
    def reserve_priority(self, agent_id: str) -> Dict:
        """
        Atomically reserve the next highest priority research task
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Priority object with id, title, description, etc.
            
        Raises:
            ResearchAPIError: If no priorities available or reservation fails
        """
        return self._make_request('POST', 'priorities/next', {'agent_id': agent_id})
    
    def get_next_priority_info(self) -> Dict:
        """
        Get info about next priority without reserving it (inspection only)
        
        Returns:
            Priority info or empty dict if no priorities
        """
        try:
            return self._make_request('GET', 'priorities/next')
        except ResearchAPIError:
            return {}
    
    def confirm_work_started(self, priority_id: str) -> Dict:
        """
        Confirm that agent has started work on reserved priority
        
        Args:
            priority_id: ID of reserved priority
            
        Returns:
            Confirmation response
        """
        return self._make_request('PUT', f'priorities/{priority_id}/start')
    
    def update_priority_status(self, priority_id: str, status: str, 
                              actual_events: Optional[int] = None, 
                              notes: Optional[str] = None) -> Dict:
        """
        Update priority status
        
        Args:
            priority_id: Priority ID
            status: New status (reserved, in_progress, completed, failed)
            actual_events: Number of events created (for completed status)
            notes: Research notes or completion summary
            
        Returns:
            Update confirmation
        """
        data = {'status': status}
        if actual_events is not None:
            data['actual_events'] = actual_events
        if notes:
            data['notes'] = notes
            
        return self._make_request('PUT', f'priorities/{priority_id}/status', data)
    
    def complete_priority(self, priority_id: str, events_created: int, 
                         notes: Optional[str] = None) -> Dict:
        """
        Mark priority as completed
        
        Args:
            priority_id: Priority ID
            events_created: Number of timeline events created
            notes: Optional completion notes
            
        Returns:
            Completion confirmation
        """
        return self.update_priority_status(
            priority_id, 
            'completed', 
            actual_events=events_created, 
            notes=notes
        )
    
    # ===== EVENT MANAGEMENT =====
    
    def submit_events(self, events: List[Dict], priority_id: str) -> Dict:
        """
        Submit researched timeline events
        
        Args:
            events: List of timeline event objects
            priority_id: Associated priority ID
            
        Returns:
            Submission confirmation with staging info
        """
        results = []
        
        for event in events:
            # Make a copy to avoid modifying the original
            formatted_event = event.copy()
            
            # Generate ID if not provided
            if 'id' not in formatted_event:
                timestamp = str(int(time.time()))
                title_slug = formatted_event.get('title', 'event').lower().replace(' ', '-').replace('--', '-')
                formatted_event['id'] = f"{formatted_event.get('date', '2000-01-01')}--{title_slug}-{timestamp}"
            
            # Add priority_id to the event
            formatted_event['priority_id'] = priority_id
            
            # Submit individual event
            result = self._make_request('POST', 'events/staged', formatted_event)
            results.append(result)
        
        return {
            'status': 'success',
            'events_submitted': len(events),
            'results': results
        }
    
    def search_events(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search timeline events
        
        Args:
            query: Search query string
            limit: Maximum results to return
            
        Returns:
            List of matching events
        """
        response = self._make_request('GET', 'events/search', {'q': query, 'limit': limit})
        return response.get('events', [])
    
    def validate_event(self, event: Dict) -> Dict:
        """
        Validate event format before submission
        
        Args:
            event: Timeline event object
            
        Returns:
            Validation result with errors/warnings
        """
        return self._make_request('POST', 'events/validate', event)
    
    # ===== SYSTEM INFO =====
    
    def get_stats(self) -> Dict:
        """
        Get system statistics
        
        Returns:
            Stats including event counts, priority status, session info
        """
        return self._make_request('GET', 'stats')
    
    def get_commit_status(self) -> Dict:
        """
        Check if commit is needed
        
        Returns:
            Commit status info
        """
        return self._make_request('GET', 'commit/status')
    
    # ===== CONVENIENCE METHODS =====
    
    def create_simple_event(self, date: str, title: str, summary: str, 
                           actors: List[str] = None, sources: List[str] = None,
                           importance: int = 5, tags: List[str] = None) -> Dict:
        """
        Create a simple timeline event with minimal required fields
        
        Args:
            date: Event date in YYYY-MM-DD format
            title: Event title
            summary: Event summary
            actors: List of people/organizations involved
            sources: List of source URLs
            importance: Importance score 1-10
            tags: List of tags
            
        Returns:
            Formatted event object ready for submission
        """
        event = {
            'date': date,
            'title': title,
            'summary': summary,
            'importance': importance,
            'status': 'confirmed'
        }
        
        if actors:
            event['actors'] = actors
        if sources:
            event['sources'] = sources
        if tags:
            event['tags'] = tags
            
        return event
    
    def research_workflow(self, agent_id: str) -> Dict:
        """
        Complete research workflow: reserve -> research -> submit -> complete
        
        Args:
            agent_id: Unique agent identifier
            
        Returns:
            Dict with workflow results and any errors
        """
        results = {
            'agent_id': agent_id,
            'priority_id': None,
            'events_created': 0,
            'success': False,
            'error': None
        }
        
        try:
            # Step 1: Reserve priority
            priority = self.reserve_priority(agent_id)
            results['priority_id'] = priority['id']
            results['priority_title'] = priority['title']
            
            # Step 2: Confirm work started
            self.confirm_work_started(priority['id'])
            
            # Return workflow context for agent to continue
            results['workflow_ready'] = True
            results['next_step'] = "Research topic and call api.submit_events(), then api.complete_priority()"
            
            return results
            
        except ResearchAPIError as e:
            results['error'] = str(e)
            return results


# ===== UTILITY FUNCTIONS =====

def quick_stats() -> Dict:
    """Quick system stats check"""
    api = ResearchAPI()
    return api.get_stats()

def next_priority() -> Dict:
    """Quick check of next priority"""
    api = ResearchAPI()
    return api.get_next_priority_info()

# ===== EXAMPLE USAGE =====

if __name__ == "__main__":
    # Example usage
    api = ResearchAPI()
    
    print("=== Research Monitor API Client ===")
    print(f"Connected to: {api.base_url}")
    
    # Get system stats
    stats = api.get_stats()
    print(f"Events: {stats['events']['total']}")
    print(f"Pending Priorities: {stats['priorities']['pending']}")
    
    # Check next priority
    priority_info = api.get_next_priority_info()
    if priority_info:
        print(f"Next Priority: {priority_info['title']}")
    else:
        print("No pending priorities")