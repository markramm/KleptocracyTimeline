#!/usr/bin/env python3
"""
Update RAG search index from timeline YAML files
Handles datetime objects and YAML parsing edge cases
"""

import yaml
import json
import sys
from pathlib import Path
from datetime import date, datetime
from typing import Any, Dict, List
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

def convert_dates(obj: Any) -> Any:
    """Recursively convert date/datetime objects to strings"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates(item) for item in obj]
    else:
        return obj

def load_timeline_events() -> List[Dict]:
    """Load all timeline events from YAML files"""
    timeline_dir = Path(__file__).parent.parent.parent / 'data' / 'events'
    events = []
    errors = []
    
    yaml_files = list(timeline_dir.glob('*.yaml'))
    print(f"Processing {len(yaml_files)} timeline events...")
    
    for i, file_path in enumerate(yaml_files, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(yaml_files)} files...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                event = yaml.safe_load(f)
                if event:
                    # Convert dates
                    event = convert_dates(event)
                    
                    # Ensure required fields
                    event.setdefault('id', file_path.stem)
                    event.setdefault('date', 'Unknown')
                    event.setdefault('title', 'Untitled')
                    event.setdefault('summary', '')
                    event.setdefault('actors', [])
                    event.setdefault('tags', [])
                    event.setdefault('importance', 5)
                    event.setdefault('sources', [])
                    
                    events.append(event)
        except Exception as e:
            errors.append(f"{file_path.name}: {e}")
    
    if errors:
        print(f"\nWarning: {len(errors)} files had issues")
        for error in errors[:5]:
            print(f"  - {error}")
    
    return events

def export_to_rag(events: List[Dict]) -> None:
    """Export events to RAG system JSON format"""
    rag_dir = Path(__file__).parent.parent.parent / 'rag'
    rag_dir.mkdir(exist_ok=True)
    
    output_file = rag_dir / 'timeline_events.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ Exported {len(events)} events to {output_file}")
    
    # Quick stats
    epstein_count = sum(1 for e in events if 'epstein' in str(e).lower())
    print(f"  Including {epstein_count} Epstein-related events")

def main():
    """Main function"""
    print("="*60)
    print("RAG Index Update Tool")
    print("="*60 + "\n")
    
    events = load_timeline_events()
    
    if not events:
        print("❌ No events loaded!")
        sys.exit(1)
    
    export_to_rag(events)
    print("\n✅ RAG index successfully updated!")

if __name__ == "__main__":
    main()