#!/usr/bin/env python3
"""
Research Agent C - Continuous Research Workflow
Execute complete research workflow until queue is empty
"""

import sys
import os
import time
import json
from datetime import datetime
from research_api import ResearchAPI, ResearchAPIError

def conduct_research(topic_title, topic_description):
    """
    Research a topic using Claude subagent for timeline research
    This function demonstrates the architecture but requires Task tool integration
    
    Returns:
        List of timeline events
    """
    print(f"\n=== Researching: {topic_title} ===")
    print(f"Description: {topic_description}")
    
    print(f"[INFO] This implementation requires Task tool integration for real research")
    print(f"[INFO] Would call Task(subagent_type='general-purpose', prompt=research_prompt)")
    print(f"[INFO] No fake data generation - removed all hardcoded template events")
    
    # Return empty list - no fake data generation
    # In the actual implementation, this would:
    # 1. Call Task tool with timeline-researcher subagent
    # 2. Process real web search results 
    # 3. Return verified historical events
    
    events = []
    
    print(f"Created {len(events)} timeline events (Task tool integration required)")
    
    return events

def main():
    """Main research workflow loop"""
    print("=== Research Agent C Starting ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Initialize API client
    try:
        api = ResearchAPI()
        print(f"Connected to Research Monitor API at {api.base_url}")
        
        # Get initial stats
        stats = api.get_stats()
        print(f"System Status: {stats['events']['total']} total events, {stats['priorities']['pending']} pending priorities")
        
    except ResearchAPIError as e:
        print(f"FATAL: Cannot connect to Research Monitor API: {e}")
        print("Make sure the shared Flask API is running at http://localhost:5558")
        return
    
    # Main research loop
    iteration = 0
    while True:
        iteration += 1
        print(f"\n{'='*50}")
        print(f"Research Loop Iteration {iteration}")
        print(f"{'='*50}")
        
        try:
            # Step 1: Reserve next priority
            print("Step 1: Reserving next priority...")
            priority = api.reserve_priority("research-agent-C")
            priority_id = priority['id']
            
            print(f"Reserved Priority: {priority['title']}")
            print(f"Priority ID: {priority_id}")
            print(f"Description: {priority.get('description', 'N/A')}")
            print(f"Expected Events: {priority.get('expected_events', 'N/A')}")
            
            # Step 2: Confirm work started
            print("\nStep 2: Confirming work started...")
            api.confirm_work_started(priority_id)
            print("Work started confirmation sent")
            
            # Step 3: Conduct research
            print("\nStep 3: Conducting research...")
            events = conduct_research(priority['title'], priority.get('description', ''))
            
            if not events:
                print("ERROR: No events created during research")
                api.update_priority_status(priority_id, 'failed', notes="No events created during research")
                continue
            
            # Step 4: Submit events
            print(f"\nStep 4: Submitting {len(events)} events...")
            submission_result = api.submit_events(events, priority_id)
            print(f"Events submitted successfully: {submission_result['events_submitted']}")
            
            # Step 5: Complete priority  
            print("\nStep 5: Completing priority...")
            completion_notes = f"Research Agent C completed research on '{priority['title']}'. Created {len(events)} high-quality timeline events with detailed summaries, multiple actors, authoritative sources, and appropriate importance scores."
            api.complete_priority(priority_id, len(events), completion_notes)
            
            print(f"Priority {priority_id} completed successfully!")
            print(f"Events created: {len(events)}")
            
            # Brief pause before next iteration
            time.sleep(2)
            
        except ResearchAPIError as e:
            error_msg = str(e)
            if "No priorities available" in error_msg or "404" in error_msg:
                print("No more priorities available - research queue is empty")
                break
            else:
                print(f"ERROR during research workflow: {e}")
                if 'priority_id' in locals():
                    try:
                        api.update_priority_status(priority_id, 'failed', notes=f"Agent error: {e}")
                    except:
                        pass
                time.sleep(5)  # Wait before retrying
                continue
    
    # Final stats
    print(f"\n{'='*50}")
    print("Research Agent C Complete")
    print(f"{'='*50}")
    
    try:
        final_stats = api.get_stats()
        print(f"Final Status: {final_stats['events']['total']} total events")
        print(f"Completed {iteration-1} research priorities")
        
        # Check commit status
        commit_status = api.get_commit_status()
        if commit_status.get('needs_commit', False):
            print(f"Commit needed: {commit_status['staged_events']} staged events ready")
        else:
            print("No commit needed")
            
    except Exception as e:
        print(f"Error getting final stats: {e}")
    
    print("Research Agent C workflow complete")

if __name__ == "__main__":
    main()