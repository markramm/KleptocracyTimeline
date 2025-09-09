#!/usr/bin/env python3
"""
Check for research priorities marked completed but with no actual timeline events created
"""

import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_completed_priorities_without_events():
    """Find research priorities marked completed but with 0 actual events"""
    
    print("🔍 CHECKING COMPLETED PRIORITIES WITHOUT EVENTS")
    print("=" * 60)
    
    completed_without_events = []
    completed_with_events = []
    total_priorities = 0
    
    # Check all research priorities
    for priority_file in Path("research_priorities").glob("*.json"):
        try:
            with open(priority_file, 'r') as f:
                priority_data = json.load(f)
            
            total_priorities += 1
            
            # Check status and actual_events
            status = priority_data.get('status', 'unknown')
            actual_events = priority_data.get('actual_events', 0)
            estimated_events = priority_data.get('estimated_events', 0)
            title = priority_data.get('title', 'Unknown')
            
            if status == 'completed':
                if actual_events == 0:
                    completed_without_events.append({
                        'file': priority_file.name,
                        'title': title,
                        'estimated_events': estimated_events,
                        'actual_events': actual_events
                    })
                else:
                    completed_with_events.append({
                        'file': priority_file.name,
                        'title': title,
                        'estimated_events': estimated_events,
                        'actual_events': actual_events
                    })
            
        except Exception as e:
            logger.error(f"Error reading {priority_file.name}: {str(e)}")
    
    print(f"📊 ANALYSIS RESULTS:")
    print(f"📁 Total Priorities: {total_priorities}")
    print(f"✅ Completed with Events: {len(completed_with_events)}")
    print(f"⚠️  Completed WITHOUT Events: {len(completed_without_events)}")
    
    if completed_without_events:
        print(f"\n🚨 PRIORITIES MARKED COMPLETED BUT NO EVENTS CREATED:")
        print("-" * 60)
        
        for priority in completed_without_events:
            print(f"📄 {priority['file']}")
            print(f"   Title: {priority['title'][:70]}...")
            print(f"   Expected: {priority['estimated_events']} events")
            print(f"   Created: {priority['actual_events']} events")
            print()
    
    if completed_with_events:
        print(f"\n✅ PRIORITIES COMPLETED WITH EVENTS:")
        print("-" * 60)
        
        for priority in completed_with_events[:10]:  # Show first 10
            print(f"📄 {priority['file']}")
            print(f"   Title: {priority['title'][:70]}...")
            print(f"   Expected: {priority['estimated_events']} events")
            print(f"   Created: {priority['actual_events']} events")
            print()
        
        if len(completed_with_events) > 10:
            print(f"   ... and {len(completed_with_events) - 10} more")
    
    # Check for priorities that should be reset
    should_be_reset = []
    for priority in completed_without_events:
        if priority['estimated_events'] > 0:
            should_be_reset.append(priority)
    
    if should_be_reset:
        print(f"\n🔄 PRIORITIES THAT SHOULD BE RESET TO 'pending':")
        print("-" * 60)
        
        for priority in should_be_reset:
            print(f"⚠️  {priority['file']} - Expected {priority['estimated_events']} events but created 0")
    
    return {
        'total_priorities': total_priorities,
        'completed_without_events': len(completed_without_events),
        'completed_with_events': len(completed_with_events),
        'should_be_reset': len(should_be_reset),
        'problematic_priorities': completed_without_events
    }

if __name__ == "__main__":
    results = check_completed_priorities_without_events()