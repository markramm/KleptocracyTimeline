"""Export utilities for timeline data."""

import csv
import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from abc import ABC, abstractmethod

class BaseExporter(ABC):
    """Base class for all exporters."""
    
    def __init__(self, events: List[Dict]):
        """
        Initialize exporter with events.
        
        Args:
            events: List of event dictionaries
        """
        self.events = events
    
    @abstractmethod
    def export(self, output_file: Path) -> int:
        """
        Export events to file.
        
        Args:
            output_file: Path to output file
            
        Returns:
            Number of events exported
        """
        pass
    
    def _ensure_serializable(self, obj: Any) -> Any:
        """
        Ensure object is serializable.
        
        Args:
            obj: Object to convert
            
        Returns:
            Serializable version of object
        """
        if isinstance(obj, (date, datetime)):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, dict):
            return {k: self._ensure_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._ensure_serializable(item) for item in obj]
        elif hasattr(obj, 'strftime'):
            return obj.strftime('%Y-%m-%d')
        return obj

class CSVExporter(BaseExporter):
    """Export events to CSV format."""
    
    def export(self, output_file: Path) -> int:
        """Export events to CSV file."""
        if not self.events:
            return 0
        
        # Define standard fieldnames
        fieldnames = [
            'date', 'year', 'month', 'day', 'title', 'summary', 'description',
            'importance', 'status', 'location', 'actors', 'tags', 'patterns',
            'capture_type', 'capture_lane', 'source_urls', 'source_outlets',
            'notes', 'id'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for event in self.events:
                row = self._prepare_csv_row(event)
                writer.writerow(row)
        
        return len(self.events)
    
    def _prepare_csv_row(self, event: Dict) -> Dict:
        """Prepare event for CSV export."""
        row = {}
        
        # Handle date fields
        date_val = event.get('date', '')
        if isinstance(date_val, str):
            date_str = date_val
        elif hasattr(date_val, 'strftime'):
            date_str = date_val.strftime('%Y-%m-%d')
        else:
            date_str = str(date_val)
        
        row['date'] = date_str
        
        # Extract year, month, day
        if len(date_str) >= 10:
            row['year'] = date_str[:4]
            row['month'] = date_str[5:7]
            row['day'] = date_str[8:10]
        else:
            row['year'] = row['month'] = row['day'] = ''
        
        # Basic fields
        row['title'] = event.get('title', '')
        row['summary'] = event.get('summary', '')
        row['description'] = event.get('description', '')
        row['importance'] = event.get('importance', '')
        row['status'] = event.get('status', '')
        row['location'] = event.get('location', '')
        row['capture_type'] = event.get('capture_type', '')
        row['capture_lane'] = event.get('capture_lane', '')
        row['notes'] = event.get('notes', '')
        row['id'] = event.get('id', '')
        
        # Handle list fields
        row['actors'] = '; '.join(event.get('actors', []))
        row['tags'] = '; '.join(event.get('tags', []))
        row['patterns'] = '; '.join(event.get('patterns', []))
        
        # Handle sources
        sources = event.get('sources', [])
        urls = []
        outlets = []
        
        for source in sources[:3]:  # Limit to first 3 sources
            if isinstance(source, dict):
                if 'url' in source:
                    urls.append(source['url'])
                if 'outlet' in source:
                    outlets.append(source['outlet'])
            elif isinstance(source, str):
                urls.append(source)
        
        row['source_urls'] = '; '.join(urls)
        row['source_outlets'] = '; '.join(outlets)
        
        return row

class JSONExporter(BaseExporter):
    """Export events to JSON format."""
    
    def export(self, output_file: Path, pretty: bool = True) -> int:
        """Export events to JSON file."""
        # Ensure all events are serializable
        serializable_events = [self._ensure_serializable(event) for event in self.events]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(serializable_events, f, indent=2, ensure_ascii=False)
            else:
                json.dump(serializable_events, f, ensure_ascii=False)
        
        return len(self.events)

class YAMLExporter(BaseExporter):
    """Export events to YAML format."""
    
    def __init__(self, events: List[Dict], include_metadata: bool = True):
        """
        Initialize YAML exporter.
        
        Args:
            events: List of event dictionaries
            include_metadata: Whether to include metadata in export
        """
        super().__init__(events)
        self.include_metadata = include_metadata
    
    def export(self, output_file: Path) -> int:
        """Export events to YAML file."""
        # Prepare data
        if self.include_metadata:
            data = self._create_metadata_wrapper()
        else:
            data = {'events': self.events}
        
        # Custom YAML representer for better formatting
        def str_presenter(dumper, data):
            if len(data.splitlines()) > 1:  # Multi-line string
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)
        
        yaml.add_representer(str, str_presenter)
        
        # Write YAML
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                width=100,
                sort_keys=False
            )
        
        return len(self.events)
    
    def _create_metadata_wrapper(self) -> Dict:
        """Create metadata wrapper for YAML export."""
        date_range = self._get_date_range()
        
        return {
            'metadata': {
                'title': 'Kleptocracy Timeline - Complete Event Archive',
                'description': 'Comprehensive timeline tracking patterns of democratic degradation and kleptocratic capture',
                'generated': datetime.now().isoformat(),
                'event_count': len(self.events),
                'date_range': date_range,
                'source': 'https://github.com/yourusername/kleptocracy-timeline',
                'license': 'CC BY-SA 4.0',
                'format_version': '1.0'
            },
            'events': self.events
        }
    
    def _get_date_range(self) -> Dict[str, Optional[str]]:
        """Get date range of events."""
        if not self.events:
            return {'start': None, 'end': None}
        
        # Sort events by date
        sorted_events = sorted(self.events, key=lambda e: str(e.get('date', '')))
        
        return {
            'start': self._ensure_serializable(sorted_events[0].get('date')),
            'end': self._ensure_serializable(sorted_events[-1].get('date'))
        }

class MinimalYAMLExporter(YAMLExporter):
    """Export minimal YAML with only essential fields."""
    
    def __init__(self, events: List[Dict]):
        """Initialize minimal YAML exporter."""
        super().__init__(events, include_metadata=False)
    
    def export(self, output_file: Path) -> int:
        """Export minimal YAML file."""
        # Extract only essential fields
        minimal_events = []
        
        for event in self.events:
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
        
        # Write minimal YAML
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(
                {'events': minimal_events},
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
        
        return len(minimal_events)

class ExporterFactory:
    """Factory for creating exporters."""
    
    @staticmethod
    def create_exporter(format: str, events: List[Dict]) -> BaseExporter:
        """
        Create an exporter for the specified format.
        
        Args:
            format: Export format (csv, json, yaml, yaml-minimal)
            events: Events to export
            
        Returns:
            Appropriate exporter instance
            
        Raises:
            ValueError: If format is not supported
        """
        exporters = {
            'csv': CSVExporter,
            'json': JSONExporter,
            'yaml': YAMLExporter,
            'yaml-minimal': MinimalYAMLExporter
        }
        
        if format not in exporters:
            raise ValueError(f"Unsupported export format: {format}")
        
        return exporters[format](events)