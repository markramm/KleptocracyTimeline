#!/usr/bin/env python3
"""
Update RAG vector store with latest timeline data.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_system import AdvancedRAGSystem

def update_index():
    """Update the RAG index with latest timeline data."""
    
    # Load the timeline data
    timeline_path = "../viewer/public/api/timeline.json"
    print(f"Loading timeline data from {timeline_path}")
    
    with open(timeline_path, 'r') as f:
        data = json.load(f)
    
    events = data.get('events', [])
    print(f"Found {len(events)} events")
    
    # Save events in the format RAG expects
    rag_data_path = "timeline_events.json"
    print(f"Saving events to {rag_data_path}")
    
    with open(rag_data_path, 'w') as f:
        json.dump(events, f, indent=2)
    
    # Initialize RAG system with the data
    print("Initializing RAG system and building vector store...")
    rag = AdvancedRAGSystem(rag_data_path)
    
    print(f"✓ Vector store updated with {len(rag.events)} events")
    print(f"✓ ChromaDB collection created at: ./chroma_db_advanced")
    
    # Quick test to verify Coristine events are in the data
    coristine_events = [e for e in rag.events if 'Coristine' in e.title or 'Coristine' in e.summary]
    print(f"\n✓ Found {len(coristine_events)} Coristine-related events in the index")
    if coristine_events:
        print("  Sample events:")
        for event in coristine_events[:3]:
            print(f"    - {event.date}: {event.title[:60]}...")

if __name__ == "__main__":
    update_index()