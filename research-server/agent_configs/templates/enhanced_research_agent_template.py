#!/usr/bin/env python3
"""
Enhanced Research Agent Template - Timeline Events with Complete Fields
Based on project contribution guidelines in timeline_data/events/README.md
Focus: Creating events with all required fields (actors, sources, tags)

IMPORTANT: Uses the agentic Research CLI for all API interactions
"""

import sys
import argparse
import subprocess
import json
import time
import random
import os

# Agent identification
AGENT_ID = f"enhanced-research-agent-{random.randint(1000, 9999)}"

class ResearchCLI:
    """CLI wrapper for Research API calls"""
    
    def __init__(self, cli_path="./research_cli.py"):
        self.cli_path = cli_path
        
    def _run_command(self, command_args):
        """Run CLI command and return JSON result"""
        try:
            result = subprocess.run(
                ["python3", self.cli_path] + command_args,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {"success": False, "error": {"message": result.stderr}}
            
            return json.loads(result.stdout)
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}
    
    def get_stats(self):
        """Get system statistics"""
        return self._run_command(["get-stats"])
    
    def get_next_priority(self):
        """Get next research priority"""
        return self._run_command(["get-next-priority"])
    
    def update_priority(self, priority_id, status, notes=None, actual_events=None):
        """Update priority status"""
        args = ["update-priority", "--id", priority_id, "--status", status]
        if notes:
            args.extend(["--notes", notes])
        if actual_events is not None:
            args.extend(["--actual-events", str(actual_events)])
        return self._run_command(args)
    
    def create_event(self, event_data):
        """Create new timeline event"""
        return self._run_command(["create-event", "--json", json.dumps(event_data)])
    
    def search_events(self, query, limit=50):
        """Search timeline events"""
        return self._run_command(["search-events", "--query", query, "--limit", str(limit)])

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Enhanced Research Agent')
    parser.add_argument('--max-iterations',
                       type=int,
                       default=3,
                       help='Maximum research iterations')
    parser.add_argument('--cli-path',
                       default='./research_cli.py',
                       help='Path to research CLI tool')
    return parser.parse_args()

def create_enhanced_event_template():
    """
    Create enhanced timeline event template matching contribution guidelines
    All events must include actors, sources, and tags as per README requirements
    """
    return {
        "date": "",  # YYYY-MM-DD format
        "title": "",  # Brief, factual headline
        "summary": "",  # Detailed description of the event
        "status": "confirmed",  # confirmed, alleged, reported, speculative, developing, disputed, predicted
        "actors": [],  # Key people/organizations involved (REQUIRED)
        "sources": [],  # Source citations with title, url, date, outlet (REQUIRED)
        "tags": [],  # Categorization tags (REQUIRED)
        "timeline_tags": [],  # Timeline-specific categorization (optional)
        "connections": [],  # IDs of related events (optional)
        "importance": 8  # 1-10 scale
    }

def research_priority_with_enhanced_fields(priority_data):
    """
    Research a priority and create events with all required fields
    
    CRITICAL: This function must perform REAL research - never use placeholder or fake data
    
    Required Research Steps:
    1. Search for verifiable historical events related to the priority
    2. Verify dates, actors, and facts through multiple sources
    3. Find official documentation, news reports, government records
    4. Cross-reference information for accuracy
    5. Only include confirmed, documented information
    
    Returns list of complete timeline events matching contribution guidelines
    """
    
    # This template demonstrates the architecture but requires Task tool integration
    # Real implementation must use Claude subagent via Task tool for actual research
    # NO fake data generation - all hardcoded events removed
    
    print(f"[INFO] Template function - Task tool integration required for real research")
    print(f"[INFO] Would call Task(subagent_type='general-purpose', prompt=research_prompt)")
    print(f"[INFO] Research topic: {priority_data.get('title', 'Unknown')}")
    print(f"[INFO] No fake data generation - returning empty list")
    
    # Return empty list - Task tool integration required for real events
    return []
    
    # All hardcoded sample events removed
    # Real implementation requires Task tool integration with Claude subagent

def main():
    """
    Enhanced Research Agent - Creates timeline events with complete field compliance
    """
    # Parse command line arguments
    args = parse_arguments()
    
    print(f"=== Enhanced Research Agent - {AGENT_ID} ===")
    print("Focus: Creating timeline events with all required fields")
    print(f"Using Research CLI: {args.cli_path}")
    
    try:
        # Initialize CLI wrapper
        cli = ResearchCLI(args.cli_path)
        
        # Test connection to server via CLI
        stats_result = cli.get_stats()
        if not stats_result.get('success'):
            print(f"[ERROR] Cannot connect to Research Monitor API via CLI")
            print(f"[ERROR] CLI response: {stats_result.get('error', {}).get('message', 'Unknown error')}")
            print(f"[ERROR] Make sure Research Monitor v2 is running on port 5558")
            return False
        
        stats = stats_result.get('data', {})
        print(f"[INFO] Connected to Research Monitor API via CLI")
        print(f"[INFO] Total events in system: {stats.get('events', {}).get('total', 0)}")
        print(f"[INFO] Pending priorities: {stats.get('priorities', {}).get('pending', 0)}")
        
        # Continuous processing loop
        max_iterations = args.max_iterations
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n[INFO] Processing iteration {iteration}/{max_iterations}")
            
            try:
                # Get next priority
                priority_result = cli.get_next_priority()
                if not priority_result.get('success'):
                    print(f"[INFO] No priorities available - waiting...")
                    time.sleep(30)
                    continue
                
                priority = priority_result.get('data', {})
                priority_id = priority.get('id')
                title = priority.get('title')
                
                print(f"[INFO] Got priority: {priority_id}")
                print(f"[INFO] Title: {title}")
                
                # Update status to in_progress
                update_result = cli.update_priority(priority_id, "in_progress", f"Started by {AGENT_ID}")
                if not update_result.get('success'):
                    print(f"[ERROR] Failed to update priority status: {update_result}")
                    continue
                print(f"[INFO] Work started confirmed")
                
                # Research and create enhanced events
                events = research_priority_with_enhanced_fields(priority)
                print(f"[INFO] Created {len(events)} enhanced events")
                
                # Validate all events have required fields
                for i, event in enumerate(events):
                    if not event.get('actors'):
                        print(f"[WARNING] Event {i+1} missing actors field")
                    if not event.get('sources'):
                        print(f"[WARNING] Event {i+1} missing sources field") 
                    if not event.get('tags'):
                        print(f"[WARNING] Event {i+1} missing tags field")
                
                # Submit events via CLI
                events_submitted = 0
                for event in events:
                    # Add event ID for timeline
                    event_id = f"{event['date']}--{event['title'].lower().replace(' ', '-').replace(':', '').replace(',', '')[:50]}"
                    event['id'] = event_id
                    
                    create_result = cli.create_event(event)
                    if create_result.get('success'):
                        events_submitted += 1
                        print(f"[INFO] Submitted event: {event_id}")
                    else:
                        print(f"[ERROR] Failed to submit event: {create_result}")
                
                # Complete the priority
                complete_result = cli.update_priority(
                    priority_id, 
                    "completed",
                    f"Enhanced events created with all required fields by {AGENT_ID}",
                    events_submitted
                )
                
                if complete_result.get('success'):
                    print(f"[INFO] Priority {priority_id} completed successfully")
                else:
                    print(f"[ERROR] Failed to complete priority: {complete_result}")
                    
            except Exception as e:
                print(f"[ERROR] Error processing priority: {e}")
                continue
                
        print(f"\n=== Enhanced Research Agent {AGENT_ID} Completed ===")
        print(f"Processed {iteration} priorities with enhanced field compliance")
        
    except Exception as e:
        print(f"[ERROR] Agent initialization failed: {e}")
        return False

if __name__ == "__main__":
    main()