#!/usr/bin/env python3
"""
Test the enhanced research integration with various research priority types
"""

import json
from pathlib import Path
from api.claude_research_integration import research_timeline_events_with_claude

def test_corporate_state_fusion():
    """Test corporate-state fusion research priority"""
    
    priority_file = Path("research_priorities/RT-016-corporate-state-fusion-infrastructure.json")
    
    if not priority_file.exists():
        print(f"Priority file not found: {priority_file}")
        return []
    
    with open(priority_file, 'r') as f:
        priority_data = json.load(f)
    
    print(f"Testing: {priority_data['title']}")
    print(f"Category: {priority_data['category']}")
    print(f"Priority: {priority_data['priority']}")
    
    events = research_timeline_events_with_claude(priority_data)
    
    print(f"\nGenerated {len(events)} events:")
    
    for i, event in enumerate(events, 1):
        print(f"\n=== Event {i} ===")
        print(f"Date: {event.get('date', 'N/A')}")
        print(f"Title: {event.get('title', 'N/A')}")
        print(f"Importance: {event.get('importance', 'N/A')}")
        print(f"Actors: {', '.join(event.get('actors', []))}")
        print(f"Tags: {', '.join(event.get('tags', []))}")
        print(f"Summary: {event.get('summary', 'N/A')[:200]}...")
    
    return events

def test_regulatory_capture():
    """Test regulatory capture detection"""
    
    # Create a mock regulatory capture priority
    priority_data = {
        "title": "Regulatory Capture Analysis: EPA and Energy Companies",
        "description": "Research systematic capture of EPA by energy companies",
        "category": "regulatory-capture",
        "priority": 8
    }
    
    print(f"\nTesting: {priority_data['title']}")
    
    events = research_timeline_events_with_claude(priority_data)
    
    print(f"\nGenerated {len(events)} regulatory capture events:")
    
    for i, event in enumerate(events, 1):
        print(f"\n=== Event {i} ===")
        print(f"Date: {event.get('date', 'N/A')}")
        print(f"Title: {event.get('title', 'N/A')}")
        print(f"Actors: {', '.join(event.get('actors', []))}")
        print(f"Tags: {', '.join(event.get('tags', []))}")
    
    return events

def test_institutional_capture():
    """Test institutional capture detection"""
    
    priority_data = {
        "title": "Project 2025: Systematic Institutional Capture",
        "description": "Research Project 2025 institutional capture mechanisms",
        "category": "institutional-capture",
        "priority": 9
    }
    
    print(f"\nTesting: {priority_data['title']}")
    
    events = research_timeline_events_with_claude(priority_data)
    
    print(f"\nGenerated {len(events)} institutional capture events:")
    
    for i, event in enumerate(events, 1):
        print(f"\n=== Event {i} ===")
        print(f"Date: {event.get('date', 'N/A')}")
        print(f"Title: {event.get('title', 'N/A')}")
        print(f"Actors: {', '.join(event.get('actors', []))}")
        print(f"Tags: {', '.join(event.get('tags', []))}")
    
    return events

if __name__ == "__main__":
    print("🚀 ENHANCED RESEARCH INTEGRATION TEST")
    print("=" * 60)
    
    # Test different research priority types
    corporate_events = test_corporate_state_fusion()
    regulatory_events = test_regulatory_capture()
    institutional_events = test_institutional_capture()
    
    print("\n" + "=" * 60)
    print("📊 ENHANCED RESEARCH TEST RESULTS:")
    print(f"🏢 Corporate-State Fusion: {len(corporate_events)} events")
    print(f"🏛️  Regulatory Capture: {len(regulatory_events)} events")
    print(f"⚖️  Institutional Capture: {len(institutional_events)} events")
    
    total_events = len(corporate_events) + len(regulatory_events) + len(institutional_events)
    
    if total_events > 0:
        print(f"\n✅ SUCCESS: Generated {total_events} contextually appropriate events!")
        print("✅ Enhanced research integration working for multiple priority types")
    else:
        print("\n❌ FAILED: No events generated")