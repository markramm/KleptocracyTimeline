#!/usr/bin/env python3
"""Find and analyze duplicate events in the timeline."""

import yaml
import re
from pathlib import Path
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from collections import defaultdict
import json

def load_events():
    """Load all events from YAML files."""
    events_dir = Path(__file__).parent.parent / 'timeline_data' / 'events'
    events = []
    
    for yaml_file in sorted(events_dir.glob('*.yaml')):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                event = yaml.safe_load(f)
                if event:
                    event['_filename'] = yaml_file.name
                    events.append(event)
        except Exception as e:
            print(f"Error loading {yaml_file}: {e}")
    
    return events

def normalize_text(text):
    """Normalize text for comparison."""
    if not text:
        return ""
    # Convert to lowercase, remove extra spaces, remove punctuation
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def calculate_similarity(text1, text2):
    """Calculate similarity between two texts."""
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    return SequenceMatcher(None, norm1, norm2).ratio()

def extract_key_terms(text):
    """Extract key terms from text for comparison."""
    if not text:
        return set()
    
    # Important terms to look for
    important_terms = {
        'trump', 'musk', 'crypto', 'bitcoin', 'inspector', 'general',
        'fired', 'resignation', 'investigation', 'million', 'billion',
        'pardon', 'executive', 'order', 'court', 'lawsuit', 'settlement'
    }
    
    normalized = normalize_text(text)
    words = set(normalized.split())
    
    # Extract numbers (like amounts)
    numbers = set(re.findall(r'\d+', text))
    
    # Find important terms
    found_terms = words.intersection(important_terms)
    
    return found_terms.union(numbers)

def find_duplicates_by_title(events, threshold=0.85):
    """Find events with similar titles."""
    duplicates = []
    
    for i, event1 in enumerate(events):
        for j, event2 in enumerate(events[i+1:], i+1):
            title_sim = calculate_similarity(event1.get('title', ''), event2.get('title', ''))
            
            if title_sim >= threshold:
                duplicates.append({
                    'event1': event1,
                    'event2': event2,
                    'similarity': title_sim,
                    'type': 'title_match'
                })
    
    return duplicates

def find_duplicates_by_date_and_actors(events):
    """Find events on same date with overlapping actors."""
    date_actor_map = defaultdict(list)
    
    # Group events by date
    for event in events:
        date = str(event.get('date', ''))
        if date:
            date_actor_map[date].append(event)
    
    duplicates = []
    
    # Check events on same date
    for date, date_events in date_actor_map.items():
        if len(date_events) > 1:
            for i, event1 in enumerate(date_events):
                actors1 = set(event1.get('actors', []))
                for event2 in date_events[i+1:]:
                    actors2 = set(event2.get('actors', []))
                    
                    # Check for actor overlap
                    if actors1 and actors2 and actors1.intersection(actors2):
                        # Also check if titles or summaries are similar
                        title_sim = calculate_similarity(
                            event1.get('title', ''), 
                            event2.get('title', '')
                        )
                        summary_sim = calculate_similarity(
                            event1.get('summary', ''), 
                            event2.get('summary', '')
                        )
                        
                        if title_sim > 0.5 or summary_sim > 0.6:
                            duplicates.append({
                                'event1': event1,
                                'event2': event2,
                                'similarity': max(title_sim, summary_sim),
                                'type': 'date_actor_match',
                                'shared_actors': list(actors1.intersection(actors2))
                            })
    
    return duplicates

def find_near_duplicates(events, days_threshold=3):
    """Find events within a few days with similar content."""
    duplicates = []
    
    for i, event1 in enumerate(events):
        date1 = event1.get('date')
        if not date1:
            continue
            
        # Convert to date object if string
        if isinstance(date1, str):
            try:
                date1 = datetime.strptime(date1, '%Y-%m-%d').date()
            except:
                continue
        
        for j, event2 in enumerate(events[i+1:], i+1):
            date2 = event2.get('date')
            if not date2:
                continue
                
            # Convert to date object if string
            if isinstance(date2, str):
                try:
                    date2 = datetime.strptime(date2, '%Y-%m-%d').date()
                except:
                    continue
            
            # Check if dates are within threshold
            if abs((date2 - date1).days) <= days_threshold:
                # Check content similarity
                title_sim = calculate_similarity(
                    event1.get('title', ''), 
                    event2.get('title', '')
                )
                
                # Extract key terms
                terms1 = extract_key_terms(event1.get('title', '') + ' ' + event1.get('summary', ''))
                terms2 = extract_key_terms(event2.get('title', '') + ' ' + event2.get('summary', ''))
                
                # Calculate term overlap
                if terms1 and terms2:
                    overlap = len(terms1.intersection(terms2)) / min(len(terms1), len(terms2))
                    
                    if title_sim > 0.6 or overlap > 0.7:
                        duplicates.append({
                            'event1': event1,
                            'event2': event2,
                            'similarity': max(title_sim, overlap),
                            'type': 'near_date_match',
                            'days_apart': abs((date2 - date1).days),
                            'shared_terms': list(terms1.intersection(terms2))
                        })
    
    return duplicates

def analyze_duplicate_group(duplicates):
    """Analyze groups of related duplicates."""
    # Build graph of related events
    related = defaultdict(set)
    
    for dup in duplicates:
        file1 = dup['event1']['_filename']
        file2 = dup['event2']['_filename']
        related[file1].add(file2)
        related[file2].add(file1)
    
    # Find connected components (groups of related events)
    visited = set()
    groups = []
    
    for filename in related:
        if filename not in visited:
            group = set()
            stack = [filename]
            
            while stack:
                current = stack.pop()
                if current not in visited:
                    visited.add(current)
                    group.add(current)
                    stack.extend(related[current] - visited)
            
            if len(group) > 1:
                groups.append(group)
    
    return groups

def generate_report(all_duplicates, events_by_file):
    """Generate detailed duplicate report."""
    print("=" * 80)
    print("DUPLICATE EVENTS ANALYSIS REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total events analyzed: {len(events_by_file)}")
    print(f"Potential duplicates found: {len(all_duplicates)}")
    print()
    
    # Group by type
    by_type = defaultdict(list)
    for dup in all_duplicates:
        by_type[dup['type']].append(dup)
    
    # Report by type
    for dup_type, dups in by_type.items():
        print(f"\n{dup_type.upper().replace('_', ' ')} ({len(dups)} pairs)")
        print("-" * 60)
        
        # Sort by similarity
        dups.sort(key=lambda x: x['similarity'], reverse=True)
        
        for i, dup in enumerate(dups[:10], 1):  # Show top 10 per category
            event1 = dup['event1']
            event2 = dup['event2']
            
            print(f"\n{i}. Similarity: {dup['similarity']:.1%}")
            print(f"   Event 1: {event1.get('date')} - {event1.get('title', '')[:70]}")
            print(f"   File: {event1['_filename']}")
            print(f"   Event 2: {event2.get('date')} - {event2.get('title', '')[:70]}")
            print(f"   File: {event2['_filename']}")
            
            if 'shared_actors' in dup:
                print(f"   Shared actors: {', '.join(dup['shared_actors'][:5])}")
            if 'shared_terms' in dup:
                print(f"   Shared terms: {', '.join(map(str, list(dup['shared_terms'])[:8]))}")
            if 'days_apart' in dup:
                print(f"   Days apart: {dup['days_apart']}")
    
    # Analyze groups
    groups = analyze_duplicate_group(all_duplicates)
    if groups:
        print("\n" + "=" * 60)
        print("DUPLICATE GROUPS (events that may be the same story)")
        print("-" * 60)
        
        for i, group in enumerate(groups[:10], 1):
            print(f"\nGroup {i} ({len(group)} related events):")
            for filename in sorted(group)[:5]:  # Show first 5 in group
                event = events_by_file[filename]
                print(f"  • {event.get('date')} - {event.get('title', '')[:60]}...")
                print(f"    {filename}")
    
    return {
        'total_events': len(events_by_file),
        'duplicate_pairs': len(all_duplicates),
        'duplicate_groups': len(groups),
        'types': {k: len(v) for k, v in by_type.items()}
    }

def save_duplicates_json(duplicates, output_file='duplicates.json'):
    """Save duplicates to JSON for further processing."""
    # Convert to serializable format
    output = []
    for dup in duplicates:
        output.append({
            'file1': dup['event1']['_filename'],
            'title1': dup['event1'].get('title', ''),
            'date1': str(dup['event1'].get('date', '')),
            'file2': dup['event2']['_filename'],
            'title2': dup['event2'].get('title', ''),
            'date2': str(dup['event2'].get('date', '')),
            'similarity': dup['similarity'],
            'type': dup['type']
        })
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Duplicate list saved to {output_file}")

def main():
    """Main function."""
    print("Loading events...")
    events = load_events()
    print(f"Loaded {len(events)} events")
    
    # Create lookup by filename
    events_by_file = {e['_filename']: e for e in events}
    
    print("\nSearching for duplicates...")
    
    # Find different types of duplicates
    print("  • Checking title similarity...")
    title_dups = find_duplicates_by_title(events, threshold=0.85)
    
    print("  • Checking same date with same actors...")
    date_actor_dups = find_duplicates_by_date_and_actors(events)
    
    print("  • Checking near-date events...")
    near_dups = find_near_duplicates(events, days_threshold=3)
    
    # Combine all duplicates (remove redundant pairs)
    seen_pairs = set()
    all_duplicates = []
    
    for dup_list in [title_dups, date_actor_dups, near_dups]:
        for dup in dup_list:
            pair = tuple(sorted([dup['event1']['_filename'], dup['event2']['_filename']]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                all_duplicates.append(dup)
    
    # Generate report
    stats = generate_report(all_duplicates, events_by_file)
    
    # Save to JSON
    save_duplicates_json(all_duplicates)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total duplicate pairs found: {stats['duplicate_pairs']}")
    print(f"Duplicate groups identified: {stats['duplicate_groups']}")
    print("\nNext steps:")
    print("1. Review duplicates.json for the full list")
    print("2. Manually verify which events are true duplicates")
    print("3. Run merge_duplicates.py to combine confirmed duplicates")
    
    return all_duplicates

if __name__ == "__main__":
    main()