#!/usr/bin/env python3
"""Generate a single YAML file containing all timeline events."""

import yaml
from pathlib import Path
from datetime import datetime
import argparse

def load_events():
    """Load all events from individual YAML files."""
    events_dir = Path(__file__).parent.parent / 'timeline_data' / 'events'
    events = []
    
    for yaml_file in sorted(events_dir.glob('*.yaml')):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                event = yaml.safe_load(f)
                if event:
                    events.append(event)
        except Exception as e:
            print(f"Error loading {yaml_file}: {e}")
    
    # Sort by date
    def get_date_key(event):
        date_val = event.get('date', '')
        if isinstance(date_val, str):
            return date_val
        elif hasattr(date_val, 'strftime'):
            return date_val.strftime('%Y-%m-%d')
        else:
            return str(date_val)
    
    events.sort(key=get_date_key)
    return events

def generate_yaml_export(events, output_file):
    """Generate consolidated YAML file."""
    # Create metadata
    metadata = {
        'metadata': {
            'title': 'Kleptocracy Timeline - Complete Event Archive',
            'description': 'Comprehensive timeline tracking patterns of democratic degradation and kleptocratic capture',
            'generated': datetime.now().isoformat(),
            'event_count': len(events),
            'date_range': {
                'start': events[0].get('date') if events else None,
                'end': events[-1].get('date') if events else None
            },
            'source': 'https://github.com/yourusername/kleptocracy-timeline',
            'license': 'CC BY-SA 4.0',
            'format_version': '1.0'
        },
        'events': events
    }
    
    # Custom YAML representer for better formatting
    def str_presenter(dumper, data):
        if len(data.splitlines()) > 1:  # Multi-line string
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    
    yaml.add_representer(str, str_presenter)
    
    # Write YAML with nice formatting
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(
            metadata,
            f,
            default_flow_style=False,
            allow_unicode=True,
            width=100,
            sort_keys=False
        )
    
    return len(events)

def generate_minimal_yaml(events, output_file):
    """Generate a minimal YAML file with just essential fields."""
    minimal_events = []
    
    for event in events:
        minimal_event = {
            'date': event.get('date'),
            'title': event.get('title'),
            'summary': event.get('summary'),
            'importance': event.get('importance'),
            'tags': event.get('tags', []),
            'actors': event.get('actors', []),
            'id': event.get('id')
        }
        minimal_events.append(minimal_event)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(
            {'events': minimal_events},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )
    
    return len(minimal_events)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate YAML export of timeline events')
    parser.add_argument('--output', '-o', 
                       default='timeline_events.yaml',
                       help='Output YAML file path')
    parser.add_argument('--minimal', '-m',
                       action='store_true',
                       help='Generate minimal YAML with only essential fields')
    parser.add_argument('--viewer-dir',
                       default=None,
                       help='Copy files to viewer directory')
    
    args = parser.parse_args()
    
    print("Loading timeline events...")
    events = load_events()
    print(f"Loaded {len(events)} events")
    
    # Generate full YAML
    output_path = Path(args.output)
    if args.minimal:
        print(f"\nGenerating minimal YAML: {output_path}")
        count = generate_minimal_yaml(events, output_path)
        file_size = output_path.stat().st_size / 1024  # KB
        print(f"✓ Wrote {count} events to {output_path} ({file_size:.1f} KB)")
    else:
        print(f"\nGenerating full YAML: {output_path}")
        count = generate_yaml_export(events, output_path)
        file_size = output_path.stat().st_size / 1024  # KB
        print(f"✓ Wrote {count} events to {output_path} ({file_size:.1f} KB)")
    
    # Also generate minimal version
    if not args.minimal:
        minimal_path = output_path.with_stem(output_path.stem + '_minimal')
        print(f"\nGenerating minimal YAML: {minimal_path}")
        generate_minimal_yaml(events, minimal_path)
        minimal_size = minimal_path.stat().st_size / 1024
        print(f"✓ Created minimal version ({minimal_size:.1f} KB)")
    
    # Copy to viewer directory if specified
    if args.viewer_dir:
        viewer_path = Path(args.viewer_dir)
        if viewer_path.exists():
            public_dir = viewer_path / 'public'
            public_dir.mkdir(exist_ok=True)
            
            import shutil
            
            # Copy full YAML
            yaml_dest = public_dir / 'timeline_events.yaml'
            shutil.copy(output_path, yaml_dest)
            print(f"\n✓ Copied YAML to {yaml_dest}")
            
            # Copy minimal YAML
            if not args.minimal:
                minimal_dest = public_dir / 'timeline_events_minimal.yaml'
                shutil.copy(output_path.with_stem(output_path.stem + '_minimal'), minimal_dest)
                print(f"✓ Copied minimal YAML to {minimal_dest}")
    
    # Print statistics
    print("\n" + "=" * 50)
    print("YAML EXPORT COMPLETE")
    print("=" * 50)
    print(f"Total events: {len(events)}")
    print(f"Date range: {events[0].get('date')} to {events[-1].get('date')}")
    print(f"Output file: {output_path.absolute()}")
    print("\nThe YAML file can be used for:")
    print("  • Data migration and backup")
    print("  • API development")
    print("  • Research and analysis")
    print("  • Integration with other tools")

if __name__ == "__main__":
    main()