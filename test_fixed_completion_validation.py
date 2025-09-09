#!/usr/bin/env python3
"""
Test the fixed completion validation system
"""

import json
from pathlib import Path
from save_events_to_timeline import research_and_save_events_from_priority
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fixed_completion_validation():
    """Test that completion validation now works correctly"""
    
    print("🔧 TESTING FIXED COMPLETION VALIDATION SYSTEM")
    print("=" * 65)
    
    # Count initial states
    initial_timeline_count = len(list(Path("timeline_data/events").glob("*.json")))
    
    # Find some pending priorities to test
    test_priorities = []
    for priority_file in Path("research_priorities").glob("*.json"):
        if "PATTERN" not in priority_file.name:  # Skip pattern analysis
            try:
                with open(priority_file, 'r') as f:
                    data = json.load(f)
                if data.get('status') == 'pending' and data.get('estimated_events', 0) > 0:
                    test_priorities.append((priority_file, data))
                    if len(test_priorities) >= 5:  # Test with 5 priorities
                        break
            except:
                continue
    
    print(f"📊 Initial Timeline Events: {initial_timeline_count}")
    print(f"🎯 Testing with {len(test_priorities)} pending priorities")
    
    results = []
    
    for priority_file, priority_data in test_priorities:
        print(f"\n=== Testing: {priority_file.name} ===")
        
        title = priority_data.get('title', 'Unknown')[:60]
        estimated_events = priority_data.get('estimated_events', 0)
        
        print(f"📝 Title: {title}...")
        print(f"📈 Expected Events: {estimated_events}")
        
        # Test the research and save process
        try:
            saved_events = research_and_save_events_from_priority(priority_data)
            
            # Check if priority was properly updated
            with open(priority_file, 'r') as f:
                updated_data = json.load(f)
            
            new_status = updated_data.get('status', 'unknown')
            actual_events = updated_data.get('actual_events', 0)
            
            result = {
                'file': priority_file.name,
                'title': title,
                'estimated_events': estimated_events,
                'events_saved': saved_events,
                'actual_events_recorded': actual_events,
                'status_after': new_status,
                'completion_valid': (new_status == 'completed' and actual_events > 0) or (new_status == 'pending' and actual_events == 0)
            }
            
            results.append(result)
            
            if result['completion_valid']:
                print(f"✅ Completion tracking CORRECT: status={new_status}, events={actual_events}")
            else:
                print(f"❌ Completion tracking BROKEN: status={new_status}, events={actual_events}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                'file': priority_file.name,
                'title': title,
                'estimated_events': estimated_events,
                'events_saved': 0,
                'actual_events_recorded': 0,
                'status_after': 'error',
                'completion_valid': False,
                'error': str(e)
            })
    
    # Final analysis
    final_timeline_count = len(list(Path("timeline_data/events").glob("*.json")))
    new_events_added = final_timeline_count - initial_timeline_count
    
    valid_completions = sum(1 for r in results if r['completion_valid'])
    total_events_saved = sum(r['events_saved'] for r in results)
    
    print("\n" + "=" * 65)
    print("📊 FIXED COMPLETION VALIDATION TEST RESULTS")
    print("=" * 65)
    
    print(f"🎯 Priorities Tested: {len(results)}")
    print(f"✅ Valid Completion Tracking: {valid_completions}/{len(results)}")
    print(f"📄 Timeline Events Added: {new_events_added}")
    print(f"💾 Total Events Saved: {total_events_saved}")
    print(f"📈 Timeline Growth: {initial_timeline_count} → {final_timeline_count}")
    
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        status_icon = "✅" if result['completion_valid'] else "❌"
        print(f"   {status_icon} {result['file'][:40]}")
        print(f"      Events: {result['events_saved']} saved, {result['actual_events_recorded']} recorded")
        print(f"      Status: {result['status_after']}")
    
    # Validation check
    success_rate = valid_completions / len(results) if results else 0
    
    if success_rate >= 0.8 and new_events_added > 0:
        print(f"\n🎉 COMPLETION VALIDATION FIX SUCCESSFUL!")
        print(f"✅ {success_rate:.1%} of priorities have correct completion tracking")
        print(f"✅ {new_events_added} new timeline events properly added and tracked")
        print(f"✅ System now accurately tracks when events are actually saved")
        return True
    else:
        print(f"\n⚠️  COMPLETION VALIDATION NEEDS MORE WORK")
        print(f"📊 Success rate: {success_rate:.1%} (need ≥80%)")
        print(f"📈 Timeline growth: {new_events_added} events")
        return False

if __name__ == "__main__":
    success = test_fixed_completion_validation()