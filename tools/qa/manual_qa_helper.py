#!/usr/bin/env python3
"""
Manual QA Helper - Lists events for systematic manual verification
"""

import yaml
from pathlib import Path
from datetime import datetime, date
import json

TIMELINE_DIR = Path(__file__).parent.parent.parent / "timeline_data" / "events"
QA_PROGRESS_FILE = Path(__file__).parent / "qa_progress.json"

def load_progress():
    """Load QA progress from file"""
    if QA_PROGRESS_FILE.exists():
        with open(QA_PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    """Save QA progress to file"""
    with open(QA_PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def list_events_for_qa():
    """List all events that need QA"""
    event_files = sorted(TIMELINE_DIR.glob("*.yaml"))
    progress = load_progress()
    
    print(f"Timeline Events for Manual QA")
    print(f"Total: {len(event_files)} events")
    print("=" * 60)
    
    completed = [f for f in event_files if progress.get(str(f.name), {}).get('checked', False)]
    pending = [f for f in event_files if not progress.get(str(f.name), {}).get('checked', False)]
    
    print(f"Completed: {len(completed)}")
    print(f"Pending: {len(pending)}")
    print("\n" + "=" * 60)
    
    if pending:
        print(f"\nNext {min(10, len(pending))} events to check:")
        print("-" * 60)
        
        for i, file_path in enumerate(pending[:10], 1):
            try:
                with open(file_path, 'r') as f:
                    event = yaml.safe_load(f)
                
                print(f"\n{i}. {file_path.name}")
                print(f"   Title: {event.get('title', 'Unknown')}")
                print(f"   Date: {event.get('date', 'Unknown')}")
                print(f"   Status: {event.get('status', 'unknown')}")
                
                # Get sources
                sources = []
                if 'sources' in event:
                    for s in event['sources']:
                        if isinstance(s, dict):
                            sources.append(s.get('url', str(s)))
                        else:
                            sources.append(str(s))
                
                if 'citations' in event:
                    for c in event['citations']:
                        if isinstance(c, dict):
                            url = c.get('url')
                            if url and url not in sources:
                                sources.append(url)
                        elif str(c) not in sources:
                            sources.append(str(c))
                
                print(f"   Sources: {len(sources)}")
                for j, source in enumerate(sources, 1):
                    print(f"     {j}. {source[:80]}...")
                
            except Exception as e:
                print(f"   ERROR: {e}")
    
    return pending

if __name__ == "__main__":
    list_events_for_qa()