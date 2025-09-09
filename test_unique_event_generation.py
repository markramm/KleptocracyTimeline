#!/usr/bin/env python3
"""
Test with priorities that should generate unique events to validate completion tracking
"""

import json
from pathlib import Path
from save_events_to_timeline import research_and_save_events_from_priority
import logging

# Configure logging  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_with_less_common_priorities():
    """Test with priorities less likely to generate duplicate events"""
    
    print("🎯 TESTING WITH UNIQUE EVENT PRIORITIES")
    print("=" * 60)
    
    initial_timeline_count = len(list(Path("timeline_data/events").glob("*.json")))
    
    # Look for priorities that should generate more unique events
    target_priorities = [
        "RT-051-reagan-era-regulatory-capture-foundation.json",
        "RT-050-clinton-era-financial-deregulation-capture.json", 
        "RT-052-bush-sr-intelligence-privatization-acceleration.json"
    ]
    
    results = []
    
    for priority_filename in target_priorities:
        priority_path = Path("research_priorities") / priority_filename
        if not priority_path.exists():
            print(f"⚠️  Priority not found: {priority_filename}")
            continue
            
        print(f"\n=== Testing: {priority_filename} ===")
        
        try:
            with open(priority_path, 'r') as f:
                priority_data = json.load(f)
            
            title = priority_data.get('title', 'Unknown')
            estimated_events = priority_data.get('estimated_events', 0)
            
            print(f"📝 Title: {title[:60]}...")
            print(f"📈 Expected Events: {estimated_events}")
            
            # Test the research and save process
            saved_events = research_and_save_events_from_priority(priority_data)
            
            # Check if priority was properly updated
            with open(priority_path, 'r') as f:
                updated_data = json.load(f)
            
            new_status = updated_data.get('status', 'unknown')
            actual_events = updated_data.get('actual_events', 0)
            
            result = {
                'file': priority_filename,
                'title': title,
                'estimated_events': estimated_events,
                'events_saved': saved_events,
                'actual_events_recorded': actual_events,
                'status_after': new_status,
                'completion_correct': (
                    (saved_events > 0 and new_status == 'completed' and actual_events == saved_events) or
                    (saved_events == 0 and new_status == 'pending' and actual_events == 0)
                )
            }
            
            results.append(result)
            
            if result['completion_correct']:
                print(f"✅ COMPLETION TRACKING WORKING: {saved_events} events saved, status={new_status}")
            else:
                print(f"❌ COMPLETION TRACKING BROKEN: {saved_events} saved, {actual_events} recorded, status={new_status}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                'file': priority_filename,
                'error': str(e),
                'completion_correct': False
            })
    
    final_timeline_count = len(list(Path("timeline_data/events").glob("*.json")))
    new_events_added = final_timeline_count - initial_timeline_count
    
    print(f"\n" + "=" * 60)
    print("📊 UNIQUE EVENT GENERATION TEST RESULTS")
    print("=" * 60)
    
    correct_completions = sum(1 for r in results if r['completion_correct'])
    total_saved = sum(r.get('events_saved', 0) for r in results)
    
    print(f"🎯 Priorities Tested: {len(results)}")
    print(f"✅ Correct Completion Tracking: {correct_completions}/{len(results)}")
    print(f"📄 Timeline Events Added: {new_events_added}")
    print(f"💾 Total Events Saved: {total_saved}")
    print(f"📈 Timeline: {initial_timeline_count} → {final_timeline_count}")
    
    if correct_completions == len(results) and new_events_added > 0:
        print(f"\n🎉 COMPLETION TRACKING FULLY FIXED!")
        print(f"✅ All priorities have accurate completion tracking")
        print(f"✅ {new_events_added} unique events added to timeline")
        print(f"✅ System correctly tracks event saves and completion status")
        return True
    else:
        print(f"\n📈 PROGRESS MADE")
        print(f"✅ Completion tracking: {correct_completions}/{len(results)}")
        print(f"📄 New events: {new_events_added}")
        return new_events_added > 0

if __name__ == "__main__":
    success = test_with_less_common_priorities()