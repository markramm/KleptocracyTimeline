#!/usr/bin/env python3
"""
Robust YAML loader that handles all edge cases for RAG ingestion
Fixes issues with:
- Datetime objects
- Quotes in strings
- Special characters
- Malformed YAML
"""

import yaml
import json
import re
from pathlib import Path
from datetime import date, datetime
from typing import Any, Dict, List, Optional
import warnings

# Suppress YAML warnings
warnings.filterwarnings("ignore")

class RobustYAMLLoader:
    """Handles problematic YAML files with special characters and datetime objects"""
    
    @staticmethod
    def clean_yaml_content(content: str) -> str:
        """Pre-process YAML content to fix common issues"""
        
        # Fix quotes in summaries and titles that break YAML
        # Look for lines that start with summary: or title: and have unescaped quotes
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Check if this is a summary or title line with potential quote issues
            if re.match(r'^(summary|title|description):\s+', line):
                # Extract the key and value
                match = re.match(r'^(summary|title|description):\s+(.+)$', line)
                if match:
                    key = match.group(1)
                    value = match.group(2)
                    
                    # If value is not already quoted and contains quotes, wrap it
                    if not (value.startswith('"') and value.endswith('"')):
                        if '"' in value or "'" in value or ':' in value or '|' in value:
                            # Escape internal quotes and wrap
                            value = value.replace('\\', '\\\\').replace('"', '\\"')
                            value = f'"{value}"'
                            line = f'{key}: {value}'
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    @staticmethod
    def convert_dates(obj: Any) -> Any:
        """Recursively convert date/datetime objects to strings"""
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: RobustYAMLLoader.convert_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [RobustYAMLLoader.convert_dates(item) for item in obj]
        else:
            return obj
    
    @staticmethod
    def load_yaml_file(file_path: Path) -> Optional[Dict]:
        """Load a YAML file with robust error handling"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # First attempt: try to load as-is
            try:
                data = yaml.safe_load(content)
                if data:
                    return RobustYAMLLoader.convert_dates(data)
            except yaml.YAMLError:
                # If that fails, try cleaning the content
                cleaned_content = RobustYAMLLoader.clean_yaml_content(content)
                try:
                    data = yaml.safe_load(cleaned_content)
                    if data:
                        return RobustYAMLLoader.convert_dates(data)
                except yaml.YAMLError:
                    pass
            
            # Last resort: try with unsafe load (but convert results)
            try:
                data = yaml.unsafe_load(content)
                if data:
                    # Convert to JSON and back to ensure serializable
                    json_str = json.dumps(data, default=str)
                    return json.loads(json_str)
            except:
                pass
                
        except Exception as e:
            print(f"Error loading {file_path.name}: {e}")
        
        return None
    
    @staticmethod
    def validate_event(event: Dict) -> Dict:
        """Ensure event has all required fields"""
        
        # Required fields with defaults
        defaults = {
            'id': 'unknown',
            'date': 'Unknown',
            'title': 'Untitled Event',
            'summary': '',
            'actors': [],
            'tags': [],
            'importance': 5,
            'sources': []
        }
        
        # Ensure all required fields exist
        for field, default in defaults.items():
            if field not in event or event[field] is None:
                event[field] = default
        
        # Ensure date is a string
        if isinstance(event['date'], (date, datetime)):
            event['date'] = event['date'].isoformat()
        
        # Ensure lists are lists
        for field in ['actors', 'tags', 'sources']:
            if not isinstance(event[field], list):
                event[field] = []
        
        # Ensure importance is an int
        try:
            event['importance'] = int(event['importance'])
        except:
            event['importance'] = 5
        
        return event

def load_all_timeline_events():
    """Load all timeline events with robust error handling"""
    
    loader = RobustYAMLLoader()
    timeline_dir = Path(__file__).parent.parent / 'timeline_data' / 'events'
    
    events = []
    errors = []
    
    yaml_files = list(timeline_dir.glob('*.yaml'))
    print(f"Processing {len(yaml_files)} YAML files...")
    
    for i, file_path in enumerate(yaml_files, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(yaml_files)} files...")
        
        event = loader.load_yaml_file(file_path)
        
        if event:
            # Set ID from filename if missing
            if not event.get('id') or event['id'] == 'unknown':
                event['id'] = file_path.stem
            
            # Validate and clean the event
            event = loader.validate_event(event)
            events.append(event)
        else:
            errors.append(file_path.name)
    
    print(f"\nSuccessfully loaded: {len(events)} events")
    if errors:
        print(f"Failed to load: {len(errors)} files")
        print("Failed files (first 10):")
        for error in errors[:10]:
            print(f"  - {error}")
    
    return events, errors

def export_for_rag(events: List[Dict], output_path: str = 'timeline_events.json'):
    """Export events in format expected by RAG system"""
    
    rag_dir = Path(__file__).parent
    output_file = rag_dir / output_path
    
    # Ensure all events are JSON serializable
    clean_events = []
    for event in events:
        try:
            # Test serialization
            json_str = json.dumps(event, default=str)
            clean_event = json.loads(json_str)
            clean_events.append(clean_event)
        except Exception as e:
            print(f"Error serializing event {event.get('id', 'unknown')}: {e}")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(clean_events, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(clean_events)} events to {output_file}")
    return output_file

def main():
    """Main function to update RAG data with robust loading"""
    
    print("="*60)
    print("Robust YAML Loader for RAG Ingestion")
    print("="*60)
    
    # Load events
    print("\nLoading timeline events...")
    events, errors = load_all_timeline_events()
    
    if not events:
        print("ERROR: No events loaded!")
        return False
    
    # Export for RAG
    print("\nExporting for RAG system...")
    output_file = export_for_rag(events)
    
    # Verify the export
    print("\nVerifying export...")
    try:
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Successfully exported {len(data)} events")
        
        # Check for Epstein events
        epstein_count = sum(1 for event in data 
                          if 'epstein' in json.dumps(event).lower())
        print(f"  Including {epstein_count} Epstein-related events")
        
        return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)