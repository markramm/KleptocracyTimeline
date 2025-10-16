#!/usr/bin/env python3
"""
Test Research API Workflow - Demonstrate proper queue integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_api import ResearchAPI

def test_api_workflow():
    """Test the full research workflow using the API queue system"""
    
    # Initialize API client
    api = ResearchAPI()
    
    print("=== Research API Workflow Test ===")
    print(f"Connected to: {api.base_url}")
    
    # Step 1: Check system status
    stats = api.get_stats()
    print(f"\n📊 System Status:")
    print(f"   Events in timeline: {stats['events']['total']}")
    print(f"   Pending priorities: {stats['priorities']['pending']}")
    
    # Step 2: Preview next priority (without reserving)
    next_info = api.get_next_priority_info()
    if next_info:
        print(f"\n🎯 Next Priority: {next_info['title']}")
        print(f"   Description: {next_info['description'][:100]}...")
        print(f"   Expected events: {next_info.get('expected_events', 'N/A')}")
    else:
        print("\n❌ No pending priorities available")
        return
    
    # Step 3: Reserve priority for this agent
    agent_id = "claude-api-test-agent"
    print(f"\n🔒 Reserving priority for agent: {agent_id}")
    
    try:
        priority = api.reserve_priority(agent_id)
        print(f"   ✅ Reserved priority: {priority['id']}")
        print(f"   Title: {priority['title']}")
        
        # Step 4: Confirm work started
        api.confirm_work_started(priority['id'])
        print(f"   ✅ Work started confirmed")
        
        # Step 5: Create some sample events (simulating research results)
        print(f"\n📝 Creating sample timeline events...")
        
        # Sample event 1
        event1 = {
            "date": "2024-01-15",
            "title": "Test API Integration Event",
            "summary": "This is a test event created through the Research API to demonstrate proper queue integration and status tracking.",
            "importance": 6,
            "actors": ["Research API", "Claude Code"],
            "tags": ["api-test", "integration-test"],
            "sources": [
                {
                    "title": "Research API Documentation",
                    "url": "https://example.com/api-docs",
                    "outlet": "Internal Documentation",
                    "date": "2024-01-15"
                }
            ],
            "status": "confirmed"
        }
        
        # Submit events
        result = api.submit_events([event1], priority['id'])
        print(f"   ✅ Submitted {result['events_submitted']} events")
        
        # Step 6: Complete the priority
        completion_notes = f"Completed via API workflow test. Created {result['events_submitted']} high-quality timeline events."
        api.complete_priority(priority['id'], result['events_submitted'], completion_notes)
        print(f"   ✅ Priority marked as completed")
        
        # Step 7: Check updated system status
        updated_stats = api.get_stats()
        print(f"\n📊 Updated System Status:")
        print(f"   Events in timeline: {updated_stats['events']['total']}")
        print(f"   Pending priorities: {updated_stats['priorities']['pending']}")
        print(f"   Change in events: +{updated_stats['events']['total'] - stats['events']['total']}")
        print(f"   Change in priorities: {updated_stats['priorities']['pending'] - stats['priorities']['pending']}")
        
        print(f"\n✅ API Workflow Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error in workflow: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_api_workflow()
    sys.exit(0 if success else 1)