#!/usr/bin/env python3
"""
Interactive tool to create new timeline events with proper schema validation.
Ensures all events are created with correct structure and valid data.
"""

import yaml
import sys
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional
import re

# Event template with all required and optional fields
EVENT_TEMPLATE = {
    'id': '',
    'date': '',
    'importance': 5,
    'title': '',
    'summary': '',
    'actors': [],
    'tags': [],
    'status': 'confirmed',
    'sources': []
}

# Valid status values
VALID_STATUSES = ['confirmed', 'reported', 'developing', 'disputed']

# Common tags for quick selection
COMMON_TAGS = [
    'corruption', 'obstruction-of-justice', 'money-laundering', 'foreign-influence',
    'classified-documents', 'election-fraud', 'authoritarianism', 'disinformation',
    'january-6', 'mueller-investigation', 'ukraine', 'russia', 'saudi-arabia',
    'emoluments', 'nepotism', 'pardons', 'regulatory-capture', 'environmental',
    'covid-19', 'immigration', 'tax-fraud', 'campaign-finance', 'perjury'
]

def sanitize_id(text: str) -> str:
    """Convert text to valid ID format."""
    # Remove special characters and convert to lowercase
    text = re.sub(r'[^\w\s-]', '', text.lower())
    # Replace spaces with hyphens
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def get_date_input() -> str:
    """Get and validate date input."""
    while True:
        date_str = input("Enter date (YYYY-MM-DD) or 'today': ").strip()
        
        if date_str.lower() == 'today':
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Validate date format
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD")

def get_importance() -> int:
    """Get importance rating."""
    print("\nImportance scale:")
    print("  10: Historic/unprecedented events")
    print("  9:  Major national impact")
    print("  8:  Significant corruption/abuse")
    print("  7:  Important pattern evidence")
    print("  6:  Notable but limited scope")
    print("  5:  Standard political events")
    print("  1-4: Minor/contextual events")
    
    while True:
        try:
            importance = int(input("\nImportance (1-10) [5]: ").strip() or "5")
            if 1 <= importance <= 10:
                return importance
            print("❌ Please enter a number between 1 and 10")
        except ValueError:
            print("❌ Please enter a valid number")

def get_list_input(prompt: str, suggestions: List[str] = None) -> List[str]:
    """Get a list of items from user input."""
    items = []
    
    if suggestions:
        print(f"\nCommon options: {', '.join(suggestions[:10])}")
        print("(Enter items one per line, empty line to finish)")
    
    print(prompt)
    while True:
        item = input("  > ").strip()
        if not item:
            break
        items.append(item)
    
    return items

def get_sources() -> List[Dict]:
    """Get source information."""
    sources = []
    print("\nAdd sources (at least 1 required, 3+ recommended)")
    print("Enter empty title to finish")
    
    while True:
        print(f"\nSource {len(sources) + 1}:")
        title = input("  Title: ").strip()
        if not title:
            if len(sources) == 0:
                print("❌ At least one source is required")
                continue
            break
        
        url = input("  URL: ").strip()
        outlet = input("  Outlet: ").strip()
        date_str = input("  Date (YYYY-MM-DD) or 'today': ").strip()
        
        if date_str.lower() == 'today':
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        sources.append({
            'title': title,
            'url': url,
            'outlet': outlet,
            'date': date_str
        })
    
    return sources

def create_event_interactive():
    """Create an event through interactive prompts."""
    print("\n🆕 Create New Timeline Event")
    print("=" * 40)
    
    event = EVENT_TEMPLATE.copy()
    
    # Get date first (needed for ID)
    event['date'] = get_date_input()
    
    # Get title
    event['title'] = input("\nEnter title (concise, <15 words): ").strip()
    
    # Generate ID from date and title
    id_base = sanitize_id(event['title'][:50])
    event['id'] = f"{event['date']}--{id_base}"
    print(f"Generated ID: {event['id']}")
    
    # Get summary
    print("\nEnter summary (press Enter twice to finish):")
    summary_lines = []
    while True:
        line = input()
        if not line and summary_lines:
            break
        summary_lines.append(line)
    event['summary'] = ' '.join(summary_lines).strip()
    
    # Get importance
    event['importance'] = get_importance()
    
    # Get actors
    event['actors'] = get_list_input("\nEnter actors/people involved (empty to finish):")
    
    # Get tags
    print("\nSelect tags:")
    event['tags'] = get_list_input("Enter tags (empty to finish):", COMMON_TAGS)
    
    # Get status
    print(f"\nStatus options: {', '.join(VALID_STATUSES)}")
    status = input(f"Status [{event['status']}]: ").strip()
    if status in VALID_STATUSES:
        event['status'] = status
    
    # Get sources
    event['sources'] = get_sources()
    
    # Optional notes
    notes = input("\nOptional notes (or empty): ").strip()
    if notes:
        event['notes'] = notes
    
    return event

def save_event(event: Dict, events_dir: str = "timeline_data/events"):
    """Save event to YAML file."""
    events_path = Path(events_dir)
    events_path.mkdir(parents=True, exist_ok=True)
    
    filename = f"{event['id']}.yaml"
    filepath = events_path / filename
    
    # Check if file already exists
    if filepath.exists():
        overwrite = input(f"\n⚠️  File {filename} already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("❌ Event not saved")
            return None
    
    # Save to YAML
    with open(filepath, 'w') as f:
        yaml.dump(event, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    return filepath

def validate_event(event: Dict) -> List[str]:
    """Validate event structure and return any errors."""
    errors = []
    
    # Required fields
    required = ['id', 'date', 'title', 'summary', 'importance', 'actors', 'tags', 'sources']
    for field in required:
        if field not in event or not event[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate date format
    try:
        datetime.strptime(event['date'], '%Y-%m-%d')
    except:
        errors.append(f"Invalid date format: {event['date']}")
    
    # Validate importance
    if not isinstance(event['importance'], int) or not 1 <= event['importance'] <= 10:
        errors.append(f"Importance must be 1-10: {event['importance']}")
    
    # Validate status
    if event.get('status') and event['status'] not in VALID_STATUSES:
        errors.append(f"Invalid status: {event['status']}")
    
    # Validate sources
    if not event.get('sources'):
        errors.append("At least one source is required")
    
    return errors

def main():
    """Main entry point."""
    print("📚 Timeline Event Creator")
    print("Create properly formatted events for the Kleptocracy Timeline")
    
    # Create event
    event = create_event_interactive()
    
    # Show preview
    print("\n" + "=" * 40)
    print("📋 Event Preview:")
    print(yaml.dump(event, default_flow_style=False, allow_unicode=True))
    
    # Validate
    errors = validate_event(event)
    if errors:
        print("❌ Validation errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix these issues and try again")
        return 1
    
    print("✅ Event validation passed!")
    
    # Confirm save
    save_confirm = input("\nSave this event? (y/n): ")
    if save_confirm.lower() != 'y':
        print("❌ Event not saved")
        return 0
    
    # Save event
    filepath = save_event(event)
    if filepath:
        print(f"✅ Event saved to: {filepath}")
        print("\nNext steps:")
        print("1. Run: ./validate_new_events.sh")
        print("2. Run: python3 api/generate_static_api.py")
        print("3. Update RAG: cd rag && python3 update_rag_index.py")
        print("4. Commit your changes")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())