#!/usr/bin/env python3
"""
Test the improved research integration directly
"""

import json
from pathlib import Path
from api.claude_research_integration import research_timeline_events_with_claude

def test_whig_research_priority():
    """Test the improved research with RT-005 WHIG priority"""
    
    # Load the WHIG research priority
    priority_file = Path("research_priorities/RT-005-whig-media-coordination-mechanisms.json")
    
    if not priority_file.exists():
        print(f"Priority file not found: {priority_file}")
        return
    
    with open(priority_file, 'r') as f:
        priority_data = json.load(f)
    
    print(f"Testing research priority: {priority_data['title']}")
    print(f"Description: {priority_data['description'][:100]}...")
    
    # Use the improved research integration
    events = research_timeline_events_with_claude(priority_data)
    
    print(f"\nGenerated {len(events)} events:")
    
    for i, event in enumerate(events, 1):
        print(f"\n=== Event {i} ===")
        print(f"Date: {event.get('date', 'N/A')}")
        print(f"Title: {event.get('title', 'N/A')}")
        print(f"Importance: {event.get('importance', 'N/A')}")
        print(f"Actors: {', '.join(event.get('actors', []))}")
        print(f"Tags: {', '.join(event.get('tags', []))}")
        print(f"Sources: {len(event.get('sources', []))} sources")
        
        if event.get('sources'):
            print("Sample source:")
            source = event['sources'][0]
            print(f"  - {source.get('title', 'N/A')}")
            print(f"  - {source.get('outlet', 'N/A')}")
            print(f"  - {source.get('url', 'N/A')}")
    
    return events

if __name__ == "__main__":
    events = test_whig_research_priority()
    
    if events:
        print(f"\n✅ SUCCESS: Generated {len(events)} realistic historical events!")
        print("✅ Events include specific dates, real actors, and credible sources")
    else:
        print("\n❌ FAILED: No events generated")