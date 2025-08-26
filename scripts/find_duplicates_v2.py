#!/usr/bin/env python3
"""Find and analyze duplicate events using centralized utilities."""

import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from collections import defaultdict
from pathlib import Path

from utils.events import EventManager
from utils.cli import create_base_parser, add_output_arguments, add_verbosity_arguments

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
    important_patterns = [
        r'\b\d{4}\b',  # Years
        r'\$[\d,]+(?:\.\d+)?(?:[BMK])?',  # Money amounts
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b',
        r'\b(?:Trump|Biden|Putin|Musk|Thiel)\b',  # Key names
        r'\b(?:Russia|Ukraine|China|Israel)\b',  # Key countries
    ]
    
    terms = set()
    text_lower = text.lower()
    
    for pattern in important_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        terms.update(m.lower() for m in matches)
    
    # Also add general words
    words = normalize_text(text).split()
    terms.update(w for w in words if len(w) > 3)
    
    return terms

def find_duplicates_by_title(events, threshold=0.85):
    """Find potential duplicates based on title similarity."""
    duplicates = []
    
    for i, event1 in enumerate(events):
        for j, event2 in enumerate(events[i+1:], i+1):
            title1 = event1.get('title', '')
            title2 = event2.get('title', '')
            
            if title1 and title2:
                similarity = calculate_similarity(title1, title2)
                if similarity >= threshold:
                    duplicates.append({
                        'type': 'title_similarity',
                        'similarity': similarity,
                        'event1': event1,
                        'event2': event2
                    })
    
    return duplicates

def find_duplicates_by_date_and_actors(events):
    """Find events with same date and overlapping actors."""
    date_actor_map = defaultdict(list)
    
    for event in events:
        date = event.get('date')
        actors = set(event.get('actors', []))
        
        if date and actors:
            date_str = str(date)
            date_actor_map[date_str].append((event, actors))
    
    duplicates = []
    for date_str, event_list in date_actor_map.items():
        if len(event_list) > 1:
            for i, (event1, actors1) in enumerate(event_list):
                for event2, actors2 in event_list[i+1:]:
                    if actors1 & actors2:  # Intersection
                        duplicates.append({
                            'type': 'date_actor_overlap',
                            'date': date_str,
                            'common_actors': list(actors1 & actors2),
                            'event1': event1,
                            'event2': event2
                        })
    
    return duplicates

def find_near_duplicates(events, date_window_days=3, title_threshold=0.7):
    """Find events with similar titles within a date window."""
    duplicates = []
    
    # Sort by date for efficient comparison
    sorted_events = sorted(events, key=lambda e: str(e.get('date', '')))
    
    for i, event1 in enumerate(sorted_events):
        date1 = event1.get('date')
        if not date1:
            continue
            
        # Parse date
        if isinstance(date1, str):
            try:
                date1_obj = datetime.strptime(date1[:10], '%Y-%m-%d')
            except:
                continue
        else:
            date1_obj = date1
        
        # Check nearby events
        for event2 in sorted_events[i+1:]:
            date2 = event2.get('date')
            if not date2:
                continue
                
            if isinstance(date2, str):
                try:
                    date2_obj = datetime.strptime(date2[:10], '%Y-%m-%d')
                except:
                    continue
            else:
                date2_obj = date2
            
            # Check if within date window
            if abs((date2_obj - date1_obj).days) > date_window_days:
                break  # Events are sorted, so we can stop
            
            # Check title similarity
            title1 = event1.get('title', '')
            title2 = event2.get('title', '')
            
            if title1 and title2:
                similarity = calculate_similarity(title1, title2)
                if similarity >= title_threshold:
                    duplicates.append({
                        'type': 'near_date_similar_title',
                        'date_diff_days': abs((date2_obj - date1_obj).days),
                        'title_similarity': similarity,
                        'event1': event1,
                        'event2': event2
                    })
    
    return duplicates

def analyze_duplicate_group(duplicates):
    """Analyze a group of potential duplicates."""
    if not duplicates:
        return None
    
    # Group duplicates by event pairs
    pair_map = defaultdict(list)
    
    for dup in duplicates:
        # Create a unique key for the event pair
        id1 = dup['event1'].get('id', dup['event1'].get('_filename', ''))
        id2 = dup['event2'].get('id', dup['event2'].get('_filename', ''))
        pair_key = tuple(sorted([id1, id2]))
        pair_map[pair_key].append(dup)
    
    return pair_map

def print_duplicate_report(duplicates, verbose=False):
    """Print a formatted report of duplicates."""
    if not duplicates:
        print("No potential duplicates found.")
        return
    
    pair_map = analyze_duplicate_group(duplicates)
    
    print(f"\n{'='*80}")
    print(f"DUPLICATE ANALYSIS REPORT")
    print(f"{'='*80}")
    print(f"Found {len(pair_map)} potential duplicate pairs")
    print(f"Total duplicate instances: {len(duplicates)}")
    
    # Group by type
    by_type = defaultdict(list)
    for dup in duplicates:
        by_type[dup['type']].append(dup)
    
    print(f"\nBy detection method:")
    for dup_type, dups in by_type.items():
        print(f"  • {dup_type}: {len(dups)} instances")
    
    if verbose:
        print(f"\n{'='*80}")
        print("DETAILED DUPLICATE PAIRS")
        print(f"{'='*80}")
        
        for i, (pair_key, dup_list) in enumerate(pair_map.items(), 1):
            print(f"\n{'-'*40}")
            print(f"Pair {i}:")
            
            # Get the events
            event1 = dup_list[0]['event1']
            event2 = dup_list[0]['event2']
            
            print(f"\nEvent 1:")
            print(f"  File: {event1.get('_filename', 'unknown')}")
            print(f"  Date: {event1.get('date')}")
            print(f"  Title: {event1.get('title')}")
            
            print(f"\nEvent 2:")
            print(f"  File: {event2.get('_filename', 'unknown')}")
            print(f"  Date: {event2.get('date')}")
            print(f"  Title: {event2.get('title')}")
            
            print(f"\nDetection reasons:")
            for dup in dup_list:
                if dup['type'] == 'title_similarity':
                    print(f"  • Title similarity: {dup['similarity']:.1%}")
                elif dup['type'] == 'date_actor_overlap':
                    print(f"  • Same date with common actors: {', '.join(dup['common_actors'])}")
                elif dup['type'] == 'near_date_similar_title':
                    print(f"  • Near dates ({dup['date_diff_days']} days) with similar titles ({dup['title_similarity']:.1%})")

def save_duplicates_json(duplicates, output_file):
    """Save duplicates to JSON file."""
    import json
    
    # Prepare data for JSON serialization
    output_data = []
    pair_map = analyze_duplicate_group(duplicates)
    
    for pair_key, dup_list in pair_map.items():
        event1 = dup_list[0]['event1']
        event2 = dup_list[0]['event2']
        
        pair_data = {
            'event1': {
                'filename': event1.get('_filename', ''),
                'date': str(event1.get('date', '')),
                'title': event1.get('title', ''),
                'id': event1.get('id', '')
            },
            'event2': {
                'filename': event2.get('_filename', ''),
                'date': str(event2.get('date', '')),
                'title': event2.get('title', ''),
                'id': event2.get('id', '')
            },
            'detection_methods': []
        }
        
        for dup in dup_list:
            method = {'type': dup['type']}
            if 'similarity' in dup:
                method['similarity'] = dup['similarity']
            if 'title_similarity' in dup:
                method['title_similarity'] = dup['title_similarity']
            if 'date_diff_days' in dup:
                method['date_diff_days'] = dup['date_diff_days']
            if 'common_actors' in dup:
                method['common_actors'] = dup['common_actors']
            
            pair_data['detection_methods'].append(method)
        
        output_data.append(pair_data)
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nSaved duplicate analysis to: {output_file}")

def main():
    """Main function."""
    parser = create_base_parser(
        'Find and analyze duplicate events in the timeline'
    )
    add_output_arguments(parser, default_output='duplicates.json')
    
    parser.add_argument('--title-threshold', type=float, default=0.85,
                       help='Similarity threshold for title matching (0-1)')
    parser.add_argument('--date-window', type=int, default=3,
                       help='Date window in days for near-duplicate detection')
    parser.add_argument('--method', choices=['all', 'title', 'date-actor', 'near'],
                       default='all', help='Detection method to use')
    
    args = parser.parse_args()
    
    # Load events
    print("Loading timeline events...")
    manager = EventManager()
    events = manager.load_all_events()
    
    # Add filename tracking
    for event in events:
        event_id = event.get('id', '')
        file_path = manager.get_event_file_path(event_id)
        if file_path:
            event['_filename'] = file_path.name
    
    print(f"Loaded {len(events)} events")
    
    # Find duplicates
    all_duplicates = []
    
    if args.method in ['all', 'title']:
        print(f"\nSearching for title duplicates (threshold: {args.title_threshold:.0%})...")
        title_dups = find_duplicates_by_title(events, args.title_threshold)
        all_duplicates.extend(title_dups)
        print(f"  Found {len(title_dups)} potential title duplicates")
    
    if args.method in ['all', 'date-actor']:
        print("\nSearching for same-date events with common actors...")
        date_actor_dups = find_duplicates_by_date_and_actors(events)
        all_duplicates.extend(date_actor_dups)
        print(f"  Found {len(date_actor_dups)} date-actor overlaps")
    
    if args.method in ['all', 'near']:
        print(f"\nSearching for near-date duplicates (window: {args.date_window} days)...")
        near_dups = find_near_duplicates(events, args.date_window, args.title_threshold * 0.8)
        all_duplicates.extend(near_dups)
        print(f"  Found {len(near_dups)} near-date duplicates")
    
    # Print report
    print_duplicate_report(all_duplicates, verbose=args.verbose)
    
    # Save if output specified
    if args.output and all_duplicates:
        save_duplicates_json(all_duplicates, args.output)

if __name__ == "__main__":
    main()