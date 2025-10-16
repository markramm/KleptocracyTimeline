#!/usr/bin/env python3
"""
Sync Priority Status - Fix research priority status tracking
"""

import json
import os
import glob
from pathlib import Path
from collections import defaultdict

def sync_priority_status():
    """Sync priority status based on completed timeline events"""
    
    # Step 1: Find all timeline events with priority_id references
    events_dir = Path("/Users/markr/kleptocracy-timeline/timeline_data/events")
    priorities_dir = Path("/Users/markr/kleptocracy-timeline/research_priorities")
    
    completed_priority_ids = set()
    priority_event_counts = defaultdict(int)
    
    print("🔍 Scanning timeline events for priority references...")
    
    # Scan all timeline events for priority_id references
    for event_file in events_dir.glob("*.json"):
        try:
            with open(event_file, 'r') as f:
                event = json.load(f)
                if 'priority_id' in event:
                    priority_id = event['priority_id']
                    completed_priority_ids.add(priority_id)
                    priority_event_counts[priority_id] += 1
        except Exception as e:
            print(f"Error reading {event_file}: {e}")
    
    print(f"✅ Found {len(completed_priority_ids)} unique priorities with completed events")
    print(f"📊 Total events with priority references: {sum(priority_event_counts.values())}")
    
    # Step 2: Update priority JSON files to mark as completed
    priorities_updated = 0
    priorities_found = 0
    
    print("\n🔄 Updating priority status files...")
    
    for priority_file in priorities_dir.glob("**/*.json"):
        try:
            with open(priority_file, 'r') as f:
                priority = json.load(f)
            
            priority_id = priority.get('id', '')
            priorities_found += 1
            
            # Check if this priority has completed events
            if priority_id in completed_priority_ids:
                # Update status to completed
                old_status = priority.get('status', 'pending')
                priority['status'] = 'completed'
                priority['events_created'] = priority_event_counts[priority_id]
                priority['completion_date'] = '2025-01-15'  # Today's session
                
                # Write back the updated priority
                with open(priority_file, 'w') as f:
                    json.dump(priority, f, indent=2)
                
                priorities_updated += 1
                print(f"✅ Updated {priority_id}: {old_status} → completed ({priority_event_counts[priority_id]} events)")
        
        except Exception as e:
            print(f"Error updating {priority_file}: {e}")
    
    # Step 3: Summary
    print(f"\n📊 Summary:")
    print(f"   Total priority files found: {priorities_found}")
    print(f"   Priorities with completed events: {len(completed_priority_ids)}")
    print(f"   Priority files updated: {priorities_updated}")
    print(f"   Remaining pending: {priorities_found - priorities_updated}")
    
    # Step 4: Show some examples of completed priorities
    print(f"\n📋 Sample completed priorities:")
    for priority_id in list(completed_priority_ids)[:10]:
        events = priority_event_counts[priority_id]
        print(f"   {priority_id}: {events} events")
    
    return priorities_updated, priorities_found - priorities_updated

if __name__ == "__main__":
    print("=== Research Priority Status Sync ===")
    updated, remaining = sync_priority_status()
    print(f"\n🎯 Status: {updated} priorities marked completed, {remaining} remaining pending")