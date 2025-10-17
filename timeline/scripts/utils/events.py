"""Event management utilities for timeline data."""

import yaml
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from datetime import datetime, date
from collections import Counter

class EventManager:
    """Centralized event management and loading."""
    
    def __init__(self, events_dir: str = "timeline_data/events"):
        """Initialize EventManager with events directory."""
        self.events_dir = Path(__file__).parent.parent.parent / events_dir
        self._events = None
        self._event_files = {}
    
    def load_all_events(self, force_reload: bool = False) -> List[Dict]:
        """
        Load and cache all events with consistent date handling.
        
        Args:
            force_reload: Force reload even if events are cached
            
        Returns:
            List of event dictionaries
        """
        if self._events is not None and not force_reload:
            return self._events
        
        self._events = []
        self._event_files = {}
        
        for yaml_file in sorted(self.events_dir.glob('*.yaml')):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    event = yaml.safe_load(f)
                    if event:
                        self._events.append(event)
                        self._event_files[event.get('id', yaml_file.stem)] = yaml_file
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")
        
        return self._events
    
    def get_sorted_events(self, reverse: bool = False) -> List[Dict]:
        """Get events sorted by date."""
        if self._events is None:
            self.load_all_events()
        
        return sorted(self._events, key=self._get_date_key, reverse=reverse)
    
    @staticmethod
    def _get_date_key(event: Dict) -> str:
        """
        Extract date key for sorting.
        
        Args:
            event: Event dictionary
            
        Returns:
            String date key for sorting
        """
        date_val = event.get('date', '')
        
        if isinstance(date_val, str):
            return date_val
        elif isinstance(date_val, (date, datetime)):
            return date_val.strftime('%Y-%m-%d')
        elif hasattr(date_val, 'strftime'):
            return date_val.strftime('%Y-%m-%d')
        else:
            return str(date_val)
    
    @staticmethod
    def normalize_date(date_val: Any) -> Optional[str]:
        """
        Normalize date value to string format.
        
        Args:
            date_val: Date value (string, date, or datetime)
            
        Returns:
            Normalized date string or None
        """
        if date_val is None:
            return None
        elif isinstance(date_val, str):
            return date_val
        elif isinstance(date_val, (date, datetime)):
            return date_val.strftime('%Y-%m-%d')
        elif hasattr(date_val, 'strftime'):
            return date_val.strftime('%Y-%m-%d')
        else:
            return str(date_val)
    
    def get_events_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Filter events by date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of events within date range
        """
        if self._events is None:
            self.load_all_events()
        
        filtered = []
        for event in self._events:
            event_date = self.normalize_date(event.get('date'))
            if event_date and start_date <= event_date <= end_date:
                filtered.append(event)
        
        return sorted(filtered, key=self._get_date_key)
    
    def get_events_by_tags(self, tags: List[str]) -> List[Dict]:
        """
        Filter events by tags.
        
        Args:
            tags: List of tags to filter by
            
        Returns:
            List of events containing any of the specified tags
        """
        if self._events is None:
            self.load_all_events()
        
        tag_set = set(tags)
        filtered = []
        
        for event in self._events:
            event_tags = set(event.get('tags', []))
            if event_tags & tag_set:  # Intersection
                filtered.append(event)
        
        return sorted(filtered, key=self._get_date_key)
    
    def get_events_by_actors(self, actors: List[str]) -> List[Dict]:
        """
        Filter events by actors.
        
        Args:
            actors: List of actors to filter by
            
        Returns:
            List of events containing any of the specified actors
        """
        if self._events is None:
            self.load_all_events()
        
        actor_set = set(actors)
        filtered = []
        
        for event in self._events:
            event_actors = set(event.get('actors', []))
            if event_actors & actor_set:
                filtered.append(event)
        
        return sorted(filtered, key=self._get_date_key)
    
    def calculate_statistics(self) -> Dict:
        """
        Calculate comprehensive statistics about events.
        
        Returns:
            Dictionary with statistics
        """
        if self._events is None:
            self.load_all_events()
        
        stats = {
            'total_events': len(self._events),
            'date_range': self._get_date_range(),
            'tag_counts': self._count_tags(),
            'actor_counts': self._count_actors(),
            'source_statistics': self._analyze_sources(),
            'importance_distribution': self._count_importance(),
            'status_distribution': self._count_status(),
            'capture_type_distribution': self._count_capture_types(),
            'events_by_year': self._count_by_year(),
        }
        
        return stats
    
    def _get_date_range(self) -> Dict[str, str]:
        """Get date range of events."""
        if not self._events:
            return {'start': None, 'end': None}
        
        sorted_events = self.get_sorted_events()
        return {
            'start': self.normalize_date(sorted_events[0].get('date')),
            'end': self.normalize_date(sorted_events[-1].get('date'))
        }
    
    def _count_tags(self) -> Counter:
        """Count tag frequencies."""
        tags = Counter()
        for event in self._events:
            for tag in event.get('tags', []):
                tags[tag] += 1
        return tags
    
    def _count_actors(self) -> Counter:
        """Count actor frequencies."""
        actors = Counter()
        for event in self._events:
            for actor in event.get('actors', []):
                actors[actor] += 1
        return actors
    
    def _analyze_sources(self) -> Dict:
        """Analyze source coverage."""
        total = len(self._events)
        no_sources = sum(1 for e in self._events if not e.get('sources'))
        single_source = sum(1 for e in self._events if len(e.get('sources', [])) == 1)
        multiple_sources = sum(1 for e in self._events if len(e.get('sources', [])) > 1)
        
        return {
            'no_sources': no_sources,
            'single_source': single_source,
            'multiple_sources': multiple_sources,
            'average_sources': sum(len(e.get('sources', [])) for e in self._events) / total if total else 0
        }
    
    def _count_importance(self) -> Counter:
        """Count importance levels."""
        return Counter(e.get('importance', 'unknown') for e in self._events)
    
    def _count_status(self) -> Counter:
        """Count status values."""
        return Counter(e.get('status', 'unknown') for e in self._events)
    
    def _count_capture_types(self) -> Counter:
        """Count capture types."""
        return Counter(e.get('capture_type', 'unknown') for e in self._events)
    
    def _count_by_year(self) -> Counter:
        """Count events by year."""
        years = Counter()
        for event in self._events:
            date_str = self.normalize_date(event.get('date'))
            if date_str:
                year = date_str[:4]
                years[year] += 1
        return years
    
    def find_events_missing_field(self, field_name: str) -> List[Dict]:
        """
        Find events missing a specific field.
        
        Args:
            field_name: Name of field to check
            
        Returns:
            List of events missing the field
        """
        if self._events is None:
            self.load_all_events()
        
        return [e for e in self._events if field_name not in e]
    
    def get_event_file_path(self, event_id: str) -> Optional[Path]:
        """
        Get file path for an event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Path to event file or None
        """
        if self._events is None:
            self.load_all_events()
        
        return self._event_files.get(event_id)