#!/usr/bin/env python3
"""
Test concurrent research with actual timeline event saving
"""

import json
import time
from pathlib import Path
from save_events_to_timeline import research_and_save_events_from_priority
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_single_priority(priority_file: Path) -> dict:
    """Process a single research priority and save events"""
    try:
        with open(priority_file, 'r') as f:
            priority_data = json.load(f)
        
        title = priority_data.get('title', 'Unknown')
        logger.info(f"Processing: {title[:60]}...")
        
        # Generate and save events
        saved_count = research_and_save_events_from_priority(priority_data)
        
        return {
            'priority_file': priority_file.name,
            'title': title,
            'events_saved': saved_count,
            'success': saved_count > 0
        }
        
    except Exception as e:
        logger.error(f"Error processing {priority_file.name}: {str(e)}")
        return {
            'priority_file': priority_file.name,
            'title': 'Error',
            'events_saved': 0,
            'success': False,
            'error': str(e)
        }

def test_concurrent_research_with_saving():
    """Test concurrent research processing with timeline event saving"""
    
    print("🚀 CONCURRENT RESEARCH WITH TIMELINE SAVING TEST")
    print("=" * 60)
    
    # Count initial timeline events
    initial_count = len(list(Path("timeline_data/events").glob("*.json")))
    print(f"📊 Initial timeline events: {initial_count}")
    
    # Find research priorities (exclude PDF and pattern analysis)
    priority_files = []
    for priority_file in Path("research_priorities").glob("*.json"):
        if "PDF" not in priority_file.name and "PATTERN" not in priority_file.name:
            priority_files.append(priority_file)
    
    # Test with first 8 priorities for concurrent processing
    test_priorities = priority_files[:8]
    print(f"📁 Selected {len(test_priorities)} research priorities for concurrent processing")
    
    # Record start time
    start_time = time.time()
    
    # Process priorities concurrently
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_priority = {executor.submit(process_single_priority, priority): priority 
                             for priority in test_priorities}
        
        for future in as_completed(future_to_priority):
            priority = future_to_priority[future]
            try:
                result = future.result()
                results.append(result)
                
                if result['success']:
                    print(f"✅ {result['priority_file']}: {result['events_saved']} events saved")
                else:
                    print(f"⚠️  {result['priority_file']}: No events saved")
                    
            except Exception as e:
                print(f"❌ {priority.name}: Error - {str(e)}")
                results.append({
                    'priority_file': priority.name,
                    'title': 'Exception',
                    'events_saved': 0,
                    'success': False,
                    'error': str(e)
                })
    
    # Calculate results
    end_time = time.time()
    duration = end_time - start_time
    
    # Count final timeline events
    final_count = len(list(Path("timeline_data/events").glob("*.json")))
    new_events = final_count - initial_count
    
    successful_priorities = sum(1 for r in results if r['success'])
    total_events_saved = sum(r['events_saved'] for r in results)
    
    print("\n" + "=" * 60)
    print("📊 CONCURRENT RESEARCH WITH SAVING RESULTS")
    print("=" * 60)
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"📁 Priorities Processed: {len(test_priorities)}")
    print(f"✅ Successful Priorities: {successful_priorities}")
    print(f"💾 Total Events Saved: {total_events_saved}")
    print(f"📄 Timeline Events Before: {initial_count}")
    print(f"📄 Timeline Events After: {final_count}")
    print(f"📈 New Events Added: {new_events}")
    
    # Show detailed results
    print(f"\n📋 DETAILED PRIORITY RESULTS:")
    for result in sorted(results, key=lambda x: x['events_saved'], reverse=True):
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['priority_file'][:40]}: {result['events_saved']} events")
    
    if new_events > 0:
        print(f"\n🎉 CONCURRENT RESEARCH SUCCESS!")
        print(f"✅ Processed {len(test_priorities)} priorities concurrently in {duration:.1f} seconds")
        print(f"✅ Added {new_events} new timeline events to the database")
        print(f"✅ Timeline now contains {final_count} total events")
        print(f"✅ System demonstrates concurrent research with persistent event storage")
        return True
    else:
        print(f"\n⚠️  LIMITED SUCCESS - NO NEW EVENTS SAVED")
        print(f"Events generated but may have been duplicates or failed to save")
        return False

if __name__ == "__main__":
    success = test_concurrent_research_with_saving()