#!/usr/bin/env python3
"""
Timeline Deduplication Tool
Identifies and handles duplicate timeline events, prioritizing enhancement over deletion
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import shutil

def find_potential_duplicates(timeline_dir):
    """Find potential duplicate events based on date and similarity"""
    events_by_date = defaultdict(list)
    
    for json_file in Path(timeline_dir).glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                event = json.load(f)
            
            date = event.get('date', '')
            title = event.get('title', '')
            events_by_date[date].append({
                'file': json_file,
                'id': event.get('id', ''),
                'title': title,
                'importance': event.get('importance', 0),
                'description': event.get('description', ''),
                'tags': event.get('tags', [])
            })
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
    
    # Find dates with multiple events
    duplicates = {}
    for date, events in events_by_date.items():
        if len(events) > 1:
            # Check for potential duplicates by comparing titles
            for i, event1 in enumerate(events):
                for j, event2 in enumerate(events[i+1:], i+1):
                    if are_similar_events(event1, event2):
                        if date not in duplicates:
                            duplicates[date] = []
                        duplicates[date].append((event1, event2))
    
    return duplicates

def are_similar_events(event1, event2):
    """Check if two events are likely duplicates"""
    title1 = event1['title'].lower()
    title2 = event2['title'].lower()
    
    # Check for key overlapping terms
    key_terms1 = set(title1.split())
    key_terms2 = set(title2.split())
    
    # If they share significant terms, likely duplicates
    overlap = len(key_terms1.intersection(key_terms2))
    min_terms = min(len(key_terms1), len(key_terms2))
    
    if min_terms > 0 and overlap / min_terms > 0.5:
        return True
    
    # Check for specific duplicate patterns
    if any(term in title1 and term in title2 for term in [
        'cambridge analytica', 'mueller', 'blackwater', 'nisour', 
        'barr', 'immunity', 'twitter files'
    ]):
        return True
    
    return False

def merge_events(event1_data, event2_data, keep_file, merge_file):
    """Merge two events, keeping the better one and enhancing it"""
    
    # Read both events
    with open(event1_data['file'], 'r') as f:
        event1 = json.load(f)
    with open(event2_data['file'], 'r') as f:
        event2 = json.load(f)
    
    # Determine which is better (higher importance, more comprehensive)
    if event1.get('importance', 0) >= event2.get('importance', 0):
        primary = event1
        secondary = event2
        primary_file = event1_data['file']
        secondary_file = event2_data['file']
    else:
        primary = event2
        secondary = event1
        primary_file = event2_data['file']
        secondary_file = event1_data['file']
    
    # Enhance primary with information from secondary
    enhanced = primary.copy()
    
    # Merge descriptions if secondary has additional info
    if len(secondary.get('description', '')) > len(primary.get('description', '')):
        enhanced['description'] = secondary['description']
    
    # Merge tags
    primary_tags = set(primary.get('tags', []))
    secondary_tags = set(secondary.get('tags', []))
    enhanced['tags'] = list(primary_tags.union(secondary_tags))
    
    # Merge sources
    primary_sources = primary.get('sources', [])
    secondary_sources = secondary.get('sources', [])
    enhanced_sources = primary_sources.copy()
    
    for sec_source in secondary_sources:
        # Check if source already exists
        exists = any(src.get('title') == sec_source.get('title') for src in enhanced_sources)
        if not exists:
            enhanced_sources.append(sec_source)
    
    enhanced['sources'] = enhanced_sources
    
    # Add merge note
    enhanced['_merge_note'] = f"Enhanced with information from duplicate event: {secondary.get('id', 'unknown')}"
    enhanced['_merge_timestamp'] = datetime.now().isoformat()
    
    # Write enhanced version
    with open(primary_file, 'w') as f:
        json.dump(enhanced, f, indent=2, ensure_ascii=False)
    
    # Move duplicate to backup
    backup_dir = Path('timeline_data/events/.duplicates_backup')
    backup_dir.mkdir(exist_ok=True)
    
    backup_file = backup_dir / secondary_file.name
    shutil.move(secondary_file, backup_file)
    
    return primary_file, backup_file

def main():
    timeline_dir = "timeline_data/events"
    
    print("🔍 Scanning for duplicate timeline events...")
    duplicates = find_potential_duplicates(timeline_dir)
    
    if not duplicates:
        print("✅ No duplicates found!")
        return
    
    print(f"📊 Found potential duplicates on {len(duplicates)} dates")
    
    merged_count = 0
    for date, duplicate_pairs in duplicates.items():
        print(f"\n📅 Date: {date}")
        for event1, event2 in duplicate_pairs:
            print(f"  🔄 Merging:")
            print(f"    • {event1['title'][:60]}... (importance: {event1['importance']})")
            print(f"    • {event2['title'][:60]}... (importance: {event2['importance']})")
            
            try:
                primary_file, backup_file = merge_events(event1, event2, event1['file'], event2['file'])
                print(f"    ✅ Merged into: {primary_file.name}")
                print(f"    🗄️  Backed up: {backup_file.name}")
                merged_count += 1
            except Exception as e:
                print(f"    ❌ Error merging: {e}")
    
    print(f"\n✅ Deduplication complete: {merged_count} duplicates merged")
    print(f"📁 Duplicates backed up to: timeline_data/events/.duplicates_backup/")

if __name__ == "__main__":
    main()