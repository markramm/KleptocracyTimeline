#!/usr/bin/env python3
"""Analyze event sources and capture_lane fields."""

import yaml
from pathlib import Path

def analyze_events():
    """Analyze source counts and capture_lane presence."""
    events_dir = Path(__file__).parent.parent / 'timeline_data' / 'events'
    
    total_events = 0
    single_source = 0
    multiple_sources = 0
    no_sources = 0
    missing_capture_lane = 0
    
    for yaml_file in sorted(events_dir.glob('*.yaml')):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                event = yaml.safe_load(f)
                if event:
                    total_events += 1
                    
                    # Check sources
                    sources = event.get('sources', [])
                    if not sources:
                        no_sources += 1
                    elif len(sources) == 1:
                        single_source += 1
                    else:
                        multiple_sources += 1
                    
                    # Check capture_lane
                    if 'capture_lane' not in event:
                        missing_capture_lane += 1
                        
        except Exception as e:
            print(f"Error loading {yaml_file}: {e}")
    
    print(f"Total events: {total_events}")
    print(f"\nSource Analysis:")
    print(f"  • Single source: {single_source} ({single_source*100/total_events:.1f}%)")
    print(f"  • Multiple sources: {multiple_sources} ({multiple_sources*100/total_events:.1f}%)")
    print(f"  • No sources: {no_sources} ({no_sources*100/total_events:.1f}%)")
    print(f"\nCapture Lane Analysis:")
    print(f"  • Missing capture_lane: {missing_capture_lane} ({missing_capture_lane*100/total_events:.1f}%)")
    print(f"  • Has capture_lane: {total_events - missing_capture_lane} ({(total_events-missing_capture_lane)*100/total_events:.1f}%)")

if __name__ == "__main__":
    analyze_events()