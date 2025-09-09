#!/usr/bin/env python3
"""
Test comprehensive research integration with actual event saving to timeline
"""

import json
from pathlib import Path
from save_events_to_timeline import research_and_save_events_from_priority
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_research_and_save_pipeline():
    """Test the full research-to-timeline pipeline"""
    
    print("🚀 COMPREHENSIVE RESEARCH AND TIMELINE SAVING TEST")
    print("=" * 65)
    
    # Count initial timeline events
    initial_count = len(list(Path("timeline_data/events").glob("*.json")))
    print(f"📊 Initial timeline events: {initial_count}")
    
    # Select test research priorities
    test_priorities = [
        "RT-016-corporate-state-fusion-infrastructure.json",
        "RT-008-corporate-media-executive-complicity.json",
        "RT-005-whig-media-coordination-mechanisms.json"
    ]
    
    total_saved = 0
    
    for priority_file in test_priorities:
        print(f"\n=== Processing: {priority_file} ===")
        
        priority_path = Path("research_priorities") / priority_file
        
        if not priority_path.exists():
            print(f"⚠️  Priority file not found: {priority_file}")
            continue
        
        try:
            with open(priority_path, 'r') as f:
                priority_data = json.load(f)
            
            title = priority_data.get('title', 'Unknown')
            print(f"📝 Title: {title[:60]}...")
            
            # Generate and save events
            saved_count = research_and_save_events_from_priority(priority_data)
            total_saved += saved_count
            
            if saved_count > 0:
                print(f"✅ Generated and saved {saved_count} timeline events")
            else:
                print(f"⚠️  No events saved for this priority")
                
        except Exception as e:
            print(f"❌ Error processing {priority_file}: {str(e)}")
    
    # Count final timeline events
    final_count = len(list(Path("timeline_data/events").glob("*.json")))
    new_events = final_count - initial_count
    
    print("\n" + "=" * 65)
    print("📊 RESEARCH AND TIMELINE SAVING RESULTS")
    print("=" * 65)
    print(f"📄 Initial Events: {initial_count}")
    print(f"📄 Final Events: {final_count}")
    print(f"📈 New Events Added: {new_events}")
    print(f"💾 Events Saved Successfully: {total_saved}")
    
    if new_events > 0:
        print(f"\n✅ SUCCESS: Research pipeline working!")
        print(f"✅ Generated {total_saved} events and saved {new_events} to timeline")
        print(f"✅ Timeline now contains {final_count} total events")
        
        # Show some recently added events
        print(f"\n📋 RECENTLY ADDED EVENTS:")
        recent_events = sorted(Path("timeline_data/events").glob("*.json"), 
                             key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        
        for event_file in recent_events:
            try:
                with open(event_file, 'r') as f:
                    event_data = json.load(f)
                date = event_data.get('date', 'N/A')
                title = event_data.get('title', 'N/A')[:50]
                print(f"   📅 {date}: {title}...")
            except:
                print(f"   📁 {event_file.name}")
                
        return True
    else:
        print(f"\n⚠️  NO NEW EVENTS SAVED TO TIMELINE")
        print(f"Events may have been generated but not persisted to disk")
        return False

if __name__ == "__main__":
    success = test_research_and_save_pipeline()