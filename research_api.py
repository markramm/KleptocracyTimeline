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
        Submit researched timeline events using batch endpoint with validation
        
        Args:
            events: List of timeline event objects
            priority_id: Associated priority ID
            
        Returns:
            Batch submission result with detailed validation feedback
        """
        # Use the new batch endpoint for better validation and error handling
        return self.submit_events_batch(events, priority_id)
    
    def submit_events_batch(self, events: List[Dict], priority_id: str, auto_fix: bool = True) -> Dict:
        """
        Submit multiple events using the batch endpoint with validation
        
        Args:
            events: List of timeline event objects
            priority_id: Associated priority ID
            auto_fix: Whether to automatically fix validation errors before submission
            
        Returns:
            Detailed batch result with per-event validation status
        """
        # Auto-fix validation errors if requested
        if auto_fix:
            try:
                from enhanced_event_validator import validate_and_fix_events
                validation_result = validate_and_fix_events(events)
                
                if validation_result['summary']['fixes_applied'] > 0:
                    print(f"✅ Auto-fixed {validation_result['summary']['fixes_applied']} validation issues")
                    events = validation_result['fixed_events']
                    
                if validation_result['summary']['total_errors'] > 0:
                    print(f"⚠️  {validation_result['summary']['total_errors']} validation errors detected")
                    
            except ImportError:
                print("⚠️  Enhanced validator not available, proceeding without auto-fix")
        
        # Prepare batch request
        batch_data = {
            'events': events,
            'priority_id': priority_id
        }
        
        # Submit to batch endpoint
        result = self._make_request('POST', 'events/batch', batch_data)
        
        return result
    
    def submit_events_legacy(self, events: List[Dict], priority_id: str) -> Dict:
        """
        Submit researched timeline events one by one (legacy method)
        
        Args:
            events: List of timeline event objects
            priority_id: Associated priority ID
            
        Returns:
            Submission confirmation with staging info
        """
        import uuid
        import hashlib
        results = []
        
        for i, event in enumerate(events):
            # Make a copy to avoid modifying the original
            formatted_event = event.copy()
            
            # Generate ID if not provided
            if 'id' not in formatted_event:
                # Create ID using date and title slug to prevent duplicates
                title_slug = formatted_event.get('title', 'event').lower().replace(' ', '-').replace('--', '-')[:50]
                # Remove any trailing hyphens and clean up multiple consecutive hyphens
                title_slug = '-'.join(filter(None, title_slug.split('-')))
                
                formatted_event['id'] = f"{formatted_event.get('date', '2000-01-01')}--{title_slug}"
            
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
    
    def validate_event(self, event: Dict, auto_fix: bool = False) -> Dict:
        """
        Validate event format before submission with optional auto-fix
        
        Args:
            event: Timeline event object
            auto_fix: Whether to return a fixed version of the event
            
        Returns:
            Validation result with errors/warnings and optionally fixed event
        """
        if auto_fix:
            try:
                from enhanced_event_validator import TimelineEventValidator
                validator = TimelineEventValidator()
                return validator.validate_event(event)
            except ImportError:
                print("⚠️  Enhanced validator not available, using basic validation")
                
        return self._make_request('POST', 'events/validate', event)
    
    def validate_events_batch(self, events: List[Dict], auto_fix: bool = True) -> Dict:
        """
        Validate multiple events with comprehensive error reporting
        
        Args:
            events: List of timeline event objects
            auto_fix: Whether to automatically fix validation errors
            
        Returns:
            Comprehensive validation report with fixed events if requested
        """
        try:
            from enhanced_event_validator import validate_and_fix_events
            return validate_and_fix_events(events)
        except ImportError:
            # Fallback to individual validation
            results = []
            for i, event in enumerate(events):
                result = self.validate_event(event)
                result['index'] = i
                results.append(result)
                
            return {
                'summary': {
                    'total_events': len(events),
                    'valid_events': sum(1 for r in results if r.get('valid', False)),
                    'total_errors': sum(len(r.get('errors', [])) for r in results)
                },
                'results': results
            }
    
    def fix_and_retry_events(self, failed_results: List[Dict], events: List[Dict], priority_id: str) -> Dict:
        """
        Helper method for agents to fix validation errors and retry submission
        
        Args:
            failed_results: Results from batch submission showing failed events
            events: Original events list
            priority_id: Priority ID
            
        Returns:
            Results of retry attempt with fixes applied
        """
        fixed_events = []
        
        for result in failed_results:
            if result['status'] == 'failed':
                index = result['index']
                original_event = events[index].copy()
                errors = result['errors']
                
                # Apply automatic fixes where possible
                for error in errors:
                    if 'Missing required field: actors' in error:
                        original_event['actors'] = ['Unknown Actor']
                    elif 'Missing required field: sources' in error:
                        original_event['sources'] = [{'title': 'Source needed', 'url': 'https://example.com', 'outlet': 'TBD'}]
                    elif 'Missing required field: tags' in error:
                        original_event['tags'] = ['needs_tags']
                    elif 'Missing required field: importance' in error:
                        original_event['importance'] = 5
                    elif 'Date must be YYYY-MM-DD format' in error:
                        # Try to fix common date format issues
                        date = original_event.get('date', '')
                        if '/' in date:
                            parts = date.split('/')
                            if len(parts) == 3:
                                original_event['date'] = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                
                fixed_events.append(original_event)
        
        if fixed_events:
            return self.submit_events_batch(fixed_events, priority_id)
        else:
            return {'status': 'no_fixes_applied', 'message': 'No automatic fixes could be applied'}
    
    def submit_events_with_retry(self, events: List[Dict], priority_id: str, max_retries: int = 1) -> Dict:
        """
        Submit events with automatic retry and fixing of validation errors
        
        Args:
            events: List of timeline event objects
            priority_id: Associated priority ID
            max_retries: Maximum number of retry attempts
            
        Returns:
            Final submission result with all retry attempts
        """
        # Initial submission attempt
        result = self.submit_events_batch(events, priority_id)
        
        # Check for failures and retry if needed
        retries = 0
        while retries < max_retries and result.get('failed_events', 0) > 0:
            failed_results = [r for r in result.get('results', []) if r['status'] == 'failed']
            
            if failed_results:
                retry_result = self.fix_and_retry_events(failed_results, events, priority_id)
                
                # Update result with retry information
                result['retry_attempts'] = retries + 1
                result['retry_result'] = retry_result
                
                if retry_result.get('successful_events', 0) > 0:
                    result['successful_events'] += retry_result['successful_events']
                    result['failed_events'] -= retry_result['successful_events']
            
            retries += 1
        
        return result
    
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
    
    def reset_commit_counter(self) -> Dict:
        """
        Reset the commit counter (called by orchestrator after git commit)
        
        Returns:
            Reset confirmation
        """
        return self._make_request('POST', 'commit/reset')
    
    # ===== SERVER MANAGEMENT =====
    
    def health_check(self) -> Dict:
        """
        Check server health and database connectivity
        
        Returns:
            Health status information
        """
        return self._make_request('GET', 'server/health')
    
    def shutdown_server(self) -> Dict:
        """
        Gracefully shutdown the Research Monitor server
        
        Returns:
            Shutdown confirmation
        """
        return self._make_request('POST', 'server/shutdown')
    
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