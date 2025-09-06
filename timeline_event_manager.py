#!/usr/bin/env python3
"""
Timeline Event Manager - Python API for managing timeline events.
Designed for both human and agent use.
"""

import json
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Optional, Union
import re

class TimelineEventManager:
    """Manager class for timeline events."""
    
    def __init__(self, events_dir: str = "timeline_data/events"):
        """
        Initialize the event manager.
        
        Args:
            events_dir: Directory where events are stored
        """
        self.events_dir = Path(events_dir)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        
        # Valid values for validation
        self.valid_statuses = ['confirmed', 'reported', 'developing', 'disputed', 'alleged', 'speculative', 'predicted']
        self.common_tags = [
            'corruption', 'obstruction-of-justice', 'money-laundering', 
            'foreign-influence', 'classified-documents', 'election-fraud',
            'authoritarianism', 'disinformation', 'january-6', 
            'mueller-investigation', 'ukraine', 'russia', 'saudi-arabia',
            'emoluments', 'nepotism', 'pardons', 'regulatory-capture'
        ]
    
    @staticmethod
    def sanitize_id(text: str) -> str:
        """Convert text to valid ID format."""
        text = re.sub(r'[^\w\s-]', '', text.lower())
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')[:50]
    
    def generate_id(self, date_str: str, title: str) -> str:
        """Generate event ID from date and title."""
        title_part = self.sanitize_id(title)
        return f"{date_str}--{title_part}"
    
    def validate_date(self, date_input: Union[str, date, datetime]) -> str:
        """
        Validate and normalize date to YYYY-MM-DD string.
        
        Args:
            date_input: Date as string, date, or datetime object
            
        Returns:
            str: Date in YYYY-MM-DD format
            
        Raises:
            ValueError: If date format is invalid
        """
        if isinstance(date_input, datetime):
            return date_input.strftime('%Y-%m-%d')
        elif isinstance(date_input, date):
            return date_input.strftime('%Y-%m-%d')
        elif isinstance(date_input, str):
            # Validate string format
            try:
                datetime.strptime(date_input, '%Y-%m-%d')
                return date_input
            except ValueError:
                raise ValueError(f"Invalid date format: {date_input} (use YYYY-MM-DD)")
        else:
            raise ValueError(f"Invalid date type: {type(date_input)}")
    
    def create_source(
        self,
        title: str,
        url: str,
        outlet: str,
        source_date: Optional[Union[str, date, datetime]] = None
    ) -> Dict:
        """
        Create a properly formatted source dictionary.
        
        Args:
            title: Article/source title
            url: Source URL
            outlet: News outlet/publisher name
            source_date: Publication date (optional)
            
        Returns:
            Dict: Formatted source dictionary
        """
        source = {
            'title': title,
            'url': url,
            'outlet': outlet
        }
        
        if source_date:
            source['date'] = self.validate_date(source_date)
        
        return source
    
    def validate_event(self, event: Dict, check_id_format: bool = True) -> List[str]:
        """
        Validate event structure and return any errors.
        
        Args:
            event: Event dictionary to validate
            check_id_format: Whether to validate ID format matches date--title pattern
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        required = ['id', 'date', 'title', 'summary', 'importance', 'actors', 'tags', 'sources']
        for field in required:
            if field not in event:
                errors.append(f"Missing required field: {field}")
        
        # Validate ID format (must match YYYY-MM-DD--slug pattern)
        if check_id_format and 'id' in event:
            id_pattern = r'^\d{4}-\d{2}-\d{2}--[a-z0-9-]+$'
            if not re.match(id_pattern, event['id']):
                errors.append(f"ID format invalid: {event['id']} (must be YYYY-MM-DD--slug-format)")
            
            # Check if ID date matches event date
            if 'date' in event:
                id_date = event['id'][:10]  # Extract date part
                if id_date != str(event['date']):
                    errors.append(f"ID date mismatch: ID has {id_date} but event date is {event['date']}")
        
        # Validate date
        if 'date' in event:
            try:
                date_str = self.validate_date(event['date'])
                # Check future dates can't be confirmed
                if 'status' in event and event['status'] == 'confirmed':
                    event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    if event_date > datetime.now().date():
                        errors.append(f"Future event ({date_str}) cannot have status 'confirmed'")
            except ValueError as e:
                errors.append(str(e))
        
        # Validate importance
        if 'importance' in event:
            if not isinstance(event['importance'], int):
                errors.append(f"Importance must be an integer, got: {type(event['importance'])}")
            elif not 1 <= event['importance'] <= 10:
                errors.append(f"Importance must be 1-10, got: {event['importance']}")
        
        # Validate status
        if 'status' in event and event['status'] not in self.valid_statuses:
            errors.append(f"Invalid status: {event['status']} (must be one of: {', '.join(self.valid_statuses)})")
        
        # Validate lists
        for field in ['actors', 'tags']:
            if field in event and not isinstance(event[field], list):
                errors.append(f"{field} must be a list")
        
        # Validate sources
        if 'sources' in event:
            if not isinstance(event['sources'], list):
                errors.append("sources must be a list")
            elif not event['sources']:
                errors.append("At least one source is required")
            else:
                for i, source in enumerate(event['sources']):
                    if not isinstance(source, dict):
                        errors.append(f"Source {i+1} must be a dictionary")
                    else:
                        required_source_fields = ['title', 'url', 'outlet']
                        for field in required_source_fields:
                            if field not in source or not source[field]:
                                errors.append(f"Source {i+1} missing required field: {field}")
        
        return errors
    
    def create_event(
        self,
        date: Union[str, date, datetime],
        title: str,
        summary: str,
        importance: int,
        actors: List[str],
        tags: List[str],
        sources: List[Dict],
        status: str = 'confirmed',
        notes: Optional[str] = None,
        event_id: Optional[str] = None
    ) -> Dict:
        """
        Create a validated event dictionary.
        
        Args:
            date: Event date
            title: Event title (keep concise, <15 words)
            summary: Event description
            importance: Rating 1-10 (10=historic, 5=standard, 1=minor)
            actors: List of people/organizations involved
            tags: List of categorization tags
            sources: List of source dictionaries
            status: Event status (confirmed/reported/developing/disputed)
            notes: Optional additional notes
            event_id: Optional custom ID (auto-generated if not provided)
            
        Returns:
            Dict: Validated event dictionary
            
        Raises:
            ValueError: If validation fails
        """
        # Validate and normalize date
        date_str = self.validate_date(date)
        
        # Generate ID if not provided
        if not event_id:
            event_id = self.generate_id(date_str, title)
        
        # Build event
        event = {
            'id': event_id,
            'date': date_str,
            'importance': importance,
            'title': title,
            'summary': summary,
            'actors': actors,
            'tags': tags,
            'status': status,
            'sources': sources
        }
        
        if notes:
            event['notes'] = notes
        
        # Validate
        errors = self.validate_event(event)
        if errors:
            raise ValueError(f"Event validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return event
    
    def save_event(self, event: Dict, overwrite: bool = False) -> Path:
        """
        Save event to JSON file with automatic ID correction.
        
        Args:
            event: Event dictionary
            overwrite: Whether to overwrite existing files
            
        Returns:
            Path: Path to saved file
            
        Raises:
            FileExistsError: If file exists and overwrite=False
            ValueError: If event validation fails
        """
        # Auto-correct ID to match expected format
        if 'date' in event and 'title' in event:
            expected_id = self.generate_id(event['date'], event['title'])
            if 'id' not in event or event['id'] != expected_id:
                print(f"Auto-correcting ID: {event.get('id', 'none')} -> {expected_id}")
                event['id'] = expected_id
        
        # Validate first
        errors = self.validate_event(event)
        if errors:
            raise ValueError(f"Cannot save invalid event:\n" + "\n".join(f"  - {e}" for e in errors))
        
        filename = f"{event['id']}.json"
        filepath = self.events_dir / filename
        
        if filepath.exists() and not overwrite:
            raise FileExistsError(f"Event file already exists: {filepath}")
        
        # Ensure date is string (not date object)
        if hasattr(event.get('date'), 'isoformat'):
            event['date'] = event['date'].isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(event, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def validate_all_events(self) -> Dict[str, List[str]]:
        """
        Validate all events in the directory.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping filenames to validation errors
        """
        all_errors = {}
        
        for json_file in self.events_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    event = json.load(f)
                
                # Check if ID matches filename
                expected_id = json_file.stem
                if event.get('id') != expected_id:
                    all_errors[json_file.name] = [f"ID mismatch: expected '{expected_id}', got '{event.get('id')}'"]
                    continue
                
                # Run full validation
                errors = self.validate_event(event)
                if errors:
                    all_errors[json_file.name] = errors
                    
            except Exception as e:
                all_errors[json_file.name] = [f"Error loading file: {e}"]
        
        return all_errors
    
    def fix_all_ids(self, dry_run: bool = True) -> int:
        """
        Fix all ID/filename mismatches.
        
        Args:
            dry_run: If True, only report what would be fixed
            
        Returns:
            int: Number of files fixed
        """
        fixed_count = 0
        
        for json_file in self.events_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    event = json.load(f)
                
                expected_id = json_file.stem
                if event.get('id') != expected_id:
                    if dry_run:
                        print(f"Would fix {json_file.name}: '{event.get('id')}' -> '{expected_id}'")
                    else:
                        print(f"Fixing {json_file.name}: '{event.get('id')}' -> '{expected_id}'")
                        event['id'] = expected_id
                        with open(json_file, 'w') as f:
                            json.dump(event, f, indent=2, ensure_ascii=False)
                    fixed_count += 1
                    
            except Exception as e:
                print(f"Error processing {json_file.name}: {e}")
        
        return fixed_count
    
    def load_event(self, event_id: str) -> Dict:
        """
        Load an event by ID.
        
        Args:
            event_id: Event ID (with or without .json extension)
            
        Returns:
            Dict: Event dictionary
            
        Raises:
            FileNotFoundError: If event doesn't exist
        """
        if not event_id.endswith('.json'):
            event_id += '.json'
        
        filepath = self.events_dir / event_id
        
        if not filepath.exists():
            raise FileNotFoundError(f"Event not found: {filepath}")
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def list_events(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict]:
        """
        List all events, optionally filtered by date range.
        
        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            
        Returns:
            List[Dict]: List of event dictionaries
        """
        events = []
        
        for json_file in self.events_dir.glob('*.json'):
            with open(json_file, 'r') as f:
                event = json.load(f)
                
                # Apply date filters if provided
                if date_from and event.get('date') < date_from:
                    continue
                if date_to and event.get('date') > date_to:
                    continue
                
                events.append(event)
        
        # Sort by date
        events.sort(key=lambda e: e.get('date', ''))
        
        return events
    
    def search_events(
        self,
        query: str = '',
        tags: Optional[List[str]] = None,
        actors: Optional[List[str]] = None,
        importance_min: int = 1,
        importance_max: int = 10
    ) -> List[Dict]:
        """
        Search events with various filters.
        
        Args:
            query: Text to search in title and summary
            tags: Filter by tags (any match)
            actors: Filter by actors (any match)
            importance_min: Minimum importance
            importance_max: Maximum importance
            
        Returns:
            List[Dict]: Matching events
        """
        results = []
        query_lower = query.lower()
        
        for event in self.list_events():
            # Text search
            if query and query_lower not in event.get('title', '').lower() \
                     and query_lower not in event.get('summary', '').lower():
                continue
            
            # Tag filter
            if tags and not any(tag in event.get('tags', []) for tag in tags):
                continue
            
            # Actor filter
            if actors and not any(actor in event.get('actors', []) for actor in actors):
                continue
            
            # Importance filter
            importance = event.get('importance', 5)
            if importance < importance_min or importance > importance_max:
                continue
            
            results.append(event)
        
        return results


# Convenience functions for direct use
def quick_create_event(
    date: str,
    title: str,
    summary: str,
    source_title: str,
    source_url: str,
    source_outlet: str,
    importance: int = 5,
    actors: List[str] = None,
    tags: List[str] = None,
    save: bool = True
) -> Dict:
    """
    Quick function to create and optionally save an event with minimal parameters.
    
    Example:
        event = quick_create_event(
            date="2025-09-01",
            title="Something Happened",
            summary="Details of what happened",
            source_title="News Article",
            source_url="https://example.com",
            source_outlet="CNN",
            importance=7,
            tags=["corruption"]
        )
    """
    manager = TimelineEventManager()
    
    source = manager.create_source(source_title, source_url, source_outlet, date)
    
    event = manager.create_event(
        date=date,
        title=title,
        summary=summary,
        importance=importance,
        actors=actors or [],
        tags=tags or [],
        sources=[source]
    )
    
    if save:
        filepath = manager.save_event(event)
        print(f"✅ Event saved to: {filepath}")
    
    return event


if __name__ == "__main__":
    # Example usage
    manager = TimelineEventManager()
    
    # Create an event
    event = manager.create_event(
        date="2025-09-01",
        title="Example Event",
        summary="This is an example event for testing",
        importance=5,
        actors=["Person A", "Organization B"],
        tags=["test", "example"],
        sources=[
            manager.create_source(
                title="Test Article",
                url="https://example.com/article",
                outlet="Example News",
                source_date="2025-09-01"
            )
        ]
    )
    
    print("Created event:")
    print(json.dumps(event, indent=2, ensure_ascii=False))
    
    # Optionally save
    # filepath = manager.save_event(event)
    # print(f"Saved to: {filepath}")