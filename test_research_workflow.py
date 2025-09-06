#!/usr/bin/env python3
"""
Test Research Workflow - Demonstrates the research API and automation capabilities
"""

import time
import json
from research_client import TimelineResearchClient, quick_search, analyze_actor

def main():
    """Demonstrate research workflow"""
    print("🔍 Timeline Research Workflow Demo")
    print("="*50)
    
    # Initialize client
    client = TimelineResearchClient()
    
    # Test 1: Basic search functionality
    print("\n1. Testing Basic Search")
    print("-" * 30)
    
    try:
        # Search for Bush administration events
        bush_events = client.search_events("Bush", limit=5)
        print(f"✅ Found {len(bush_events)} Bush-related events")
        
        if bush_events:
            latest = bush_events[0]
            print(f"   Latest: {latest.get('date')} - {latest.get('title', '')[:60]}...")
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return
    
    # Test 2: Actor analysis
    print("\n2. Testing Actor Analysis")
    print("-" * 30)
    
    try:
        # Analyze George W. Bush
        analysis = analyze_actor("George W. Bush")
        print(f"✅ George W. Bush analysis:")
        print(f"   Events: {analysis['total_events']}")
        print(f"   Active years: {analysis['active_years'][:5]}...")
        print(f"   Common tags: {analysis['common_tags'][:5]}")
        print(f"   Avg importance: {analysis['avg_importance']:.1f}")
    except Exception as e:
        print(f"❌ Actor analysis failed: {e}")
    
    # Test 3: Advanced search with filters
    print("\n3. Testing Advanced Filters")
    print("-" * 30)
    
    try:
        # High importance events from 2017
        high_impact = client.search_events(
            start_date="2017-01-01",
            end_date="2017-12-31", 
            min_importance=8
        )
        print(f"✅ Found {len(high_impact)} high-importance events from 2017")
        
        for event in high_impact[:3]:
            print(f"   • {event.get('date')}: {event.get('title', '')}")
    except Exception as e:
        print(f"❌ Filtered search failed: {e}")
    
    # Test 4: Research note workflow
    print("\n4. Testing Research Notes")
    print("-" * 30)
    
    try:
        # Add a research note
        note = client.add_research_note(
            query="Investigate connections between Heritage Foundation and Supreme Court appointments",
            priority=8,
            status="pending"
        )
        print(f"✅ Added research note: {note.get('note_id')}")
        
        # Get pending notes
        pending = client.get_research_notes(status="pending", limit=3)
        print(f"✅ Found {len(pending)} pending research notes")
    except Exception as e:
        print(f"❌ Research notes failed: {e}")
    
    # Test 5: Timeline period analysis  
    print("\n5. Testing Timeline Analysis")
    print("-" * 30)
    
    try:
        # Analyze 2020 events
        timeline_2020 = client.research_timeline("2020-01-01", "2020-12-31")
        print(f"✅ 2020 timeline analysis:")
        print(f"   Total events: {timeline_2020['total_events']}")
        print(f"   Key actors: {timeline_2020['all_actors'][:5]}")
        print(f"   Months covered: {len(timeline_2020['events_by_month'])}")
    except Exception as e:
        print(f"❌ Timeline analysis failed: {e}")
    
    # Test 6: Research suggestions
    print("\n6. Testing Research Suggestions")
    print("-" * 30)
    
    try:
        suggestions = client.suggest_research_priorities()
        print(f"✅ Generated {len(suggestions)} research suggestions")
        
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"   {i}. [{suggestion['type']}] Priority {suggestion['priority']}")
            print(f"      {suggestion['query']}")
            print(f"      Reason: {suggestion['reason']}")
    except Exception as e:
        print(f"❌ Research suggestions failed: {e}")
    
    # Test 7: Create a test event (commented out to avoid actual creation)
    print("\n7. Testing Event Creation (simulation)")
    print("-" * 30)
    
    print("✅ Event creation capability available")
    print("   Use client.create_event() to add new timeline entries")
    print("   Supports validation, database storage, and YAML export")
    
    # Test 8: Database statistics
    print("\n8. Database Statistics")
    print("-" * 30)
    
    try:
        stats = client.get_stats()
        print(f"✅ Database statistics:")
        print(f"   Total events: {stats.get('total_events', 0):,}")
        print(f"   Total actors: {stats.get('total_actors', 0):,}")
        print(f"   Total tags: {stats.get('total_tags', 0):,}")
        print(f"   Total sources: {stats.get('total_sources', 0):,}")
        print(f"   Research notes: {stats.get('research_notes', {})}")
        
        # Show recent years
        years = stats.get('events_by_year', {})
        recent_years = {k: v for k, v in years.items() if int(k) >= 2020}
        if recent_years:
            print(f"   Recent years: {recent_years}")
    except Exception as e:
        print(f"❌ Statistics failed: {e}")
    
    print("\n" + "="*50)
    print("🎉 Research workflow demo completed!")
    print("\nNext steps:")
    print("• Run the research server: python3 api/research_server.py")
    print("• Use the client library: from research_client import TimelineResearchClient")
    print("• Integrate with subagents for automated research")
    print("• Build custom analysis workflows")

if __name__ == "__main__":
    main()