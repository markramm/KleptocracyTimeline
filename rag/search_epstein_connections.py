#!/usr/bin/env python3
"""
Search for Epstein connections in the timeline
Simple and robust implementation
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set

def load_events():
    """Load timeline events from JSON"""
    file_path = Path(__file__).parent / 'timeline_events.json'
    with open(file_path, 'r') as f:
        return json.load(f)

def find_epstein_connections(events: List[Dict]) -> Dict:
    """Find all Epstein-related events and connections"""
    
    epstein_events = []
    actors_to_events = defaultdict(list)
    tags_to_events = defaultdict(list)
    
    for event in events:
        # Check if Epstein is mentioned anywhere in the event
        event_str = json.dumps(event).lower()
        if 'epstein' in event_str:
            epstein_events.append(event)
            
            # Track actors
            for actor in event.get('actors', []):
                if 'epstein' not in actor.lower():
                    actors_to_events[actor].append({
                        'date': event.get('date', 'Unknown'),
                        'title': event.get('title', 'Unknown'),
                        'summary': event.get('summary', '')[:200]
                    })
            
            # Track tags
            for tag in event.get('tags', []):
                tags_to_events[tag].append({
                    'date': event.get('date', 'Unknown'),
                    'title': event.get('title', 'Unknown')
                })
    
    return {
        'total_events': len(epstein_events),
        'events': epstein_events,
        'actors': dict(actors_to_events),
        'tags': dict(tags_to_events)
    }

def search_actor_connections(events: List[Dict], target_actors: List[str]) -> Dict:
    """Search for connections between Epstein and specific actors"""
    
    connections = {}
    
    for actor_name in target_actors:
        actor_events = []
        
        for event in events:
            event_str = json.dumps(event).lower()
            actor_lower = actor_name.lower()
            
            # Check if both Epstein and the target actor are mentioned
            if 'epstein' in event_str and actor_lower in event_str:
                actor_events.append({
                    'date': event.get('date', 'Unknown'),
                    'title': event.get('title', 'Unknown'),
                    'summary': event.get('summary', '')[:200],
                    'actors': event.get('actors', [])
                })
        
        if actor_events:
            connections[actor_name] = actor_events
    
    return connections

def main():
    """Main analysis function"""
    print("="*80)
    print("EPSTEIN NETWORK ANALYSIS")
    print("="*80)
    
    # Load events
    events = load_events()
    print(f"\nTotal timeline events: {len(events)}")
    
    # Find Epstein connections
    epstein_data = find_epstein_connections(events)
    print(f"Epstein-related events: {epstein_data['total_events']}")
    
    # Show connected actors
    print("\n" + "="*80)
    print("KEY ACTORS IN EPSTEIN NETWORK:")
    print("="*80)
    
    # Sort actors by number of connections
    sorted_actors = sorted(
        epstein_data['actors'].items(), 
        key=lambda x: len(x[1]), 
        reverse=True
    )
    
    for actor, actor_events in sorted_actors[:20]:
        print(f"\n{actor}: {len(actor_events)} event(s)")
        for event in actor_events[:2]:
            print(f"  • {event['date']}: {event['title'][:70]}")
    
    # Search for specific high-profile connections
    print("\n" + "="*80)
    print("SEARCHING FOR HIGH-PROFILE CONNECTIONS:")
    print("="*80)
    
    target_actors = [
        'Trump', 'Donald Trump', 'Clinton', 'Bill Clinton',
        'Prince Andrew', 'Alan Dershowitz', 'Bill Gates',
        'Les Wexner', 'Ghislaine Maxwell', 'Bill Barr',
        'Alex Acosta', 'Alexander Acosta', 'Deutsche Bank',
        'Jean-Luc Brunel', 'Peter Thiel', 'Elon Musk',
        'Leon Black', 'Glenn Dubin', 'Eva Andersson-Dubin'
    ]
    
    connections = search_actor_connections(events, target_actors)
    
    for actor, actor_events in connections.items():
        if actor_events:
            print(f"\n{actor}: {len(actor_events)} connection(s)")
            for event in actor_events[:2]:
                print(f"  • {event['date']}: {event['title'][:70]}")
    
    # Show most common tags
    print("\n" + "="*80)
    print("COMMON THEMES IN EPSTEIN EVENTS:")
    print("="*80)
    
    sorted_tags = sorted(
        epstein_data['tags'].items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    for tag, tag_events in sorted_tags[:15]:
        print(f"  • {tag}: {len(tag_events)} events")
    
    # Timeline analysis
    print("\n" + "="*80)
    print("TIMELINE DISTRIBUTION:")
    print("="*80)
    
    year_counts = defaultdict(int)
    for event in epstein_data['events']:
        date = event.get('date', 'Unknown')
        if date != 'Unknown' and len(date) >= 4:
            year = date[:4]
            year_counts[year] += 1
    
    for year in sorted(year_counts.keys()):
        print(f"  {year}: {'█' * year_counts[year]} ({year_counts[year]})")

if __name__ == "__main__":
    main()