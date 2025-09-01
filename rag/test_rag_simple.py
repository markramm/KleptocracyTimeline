#!/usr/bin/env python3
"""Simple RAG test to verify functionality."""

import json
from pathlib import Path

def test_rag():
    """Test basic RAG functionality."""
    
    # Load the data
    data_file = Path('timeline_events.json')
    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return False
    
    with open(data_file, 'r') as f:
        events = json.load(f)
    
    print(f"✅ Loaded {len(events)} events")
    
    # Simple keyword search
    query = "Epstein"
    matches = []
    
    for event in events:
        if query.lower() in str(event).lower():
            matches.append(event)
    
    print(f"✅ Found {len(matches)} matches for '{query}'")
    
    # Show first 3 matches
    for i, event in enumerate(matches[:3], 1):
        print(f"\n{i}. {event.get('date', 'NO DATE')}: {event.get('title', 'NO TITLE')[:60]}...")
        if 'summary' in event:
            print(f"   {event['summary'][:100]}...")
    
    # Test specific searches
    test_queries = [
        "money laundering",
        "Deutsche Bank", 
        "Putin",
        "2019-07-06"  # Epstein arrest date
    ]
    
    print("\n" + "="*60)
    print("Testing specific queries:")
    
    for q in test_queries:
        count = sum(1 for e in events if q.lower() in str(e).lower())
        print(f"  '{q}': {count} matches")
    
    return True

if __name__ == "__main__":
    print("Testing RAG System")
    print("="*60)
    
    success = test_rag()
    
    if success:
        print("\n✅ RAG data is accessible and searchable")
    else:
        print("\n❌ RAG system has issues")