"""
Service layer for business logic, separated from HTTP layer for testability
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import sqlite3
from contextlib import contextmanager

# Import our validation functions
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research_monitor.validation_functions import (
    validate_required_fields,
    calculate_validation_score,
    validate_date_format,
    validate_sources,
    validate_actors,
    validate_tags,
    validate_title,
    validate_summary,
    validate_status,
    validate_importance,
    suggest_fixes
)


class EventService:
    """Service for managing timeline events"""
    
    def __init__(self, timeline_dir: Path):
        self.timeline_dir = Path(timeline_dir)
        self.timeline_dir.mkdir(parents=True, exist_ok=True)
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events from filesystem"""
        events = []
        for event_file in self.timeline_dir.glob("*.json"):
            try:
                with open(event_file, 'r') as f:
                    event = json.load(f)
                    events.append(event)
            except (json.JSONDecodeError, IOError) as e:
                # Log error but continue
                print(f"Error reading {event_file}: {e}")
        return events
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific event by ID"""
        event_file = self.timeline_dir / f"{event_id}.json"
        if not event_file.exists():
            return None
        
        try:
            with open(event_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def create_event(self, event_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Create a new event
        
        Returns:
            Tuple of (success, result_dict)
        """
        # Generate ID if not provided
        if 'id' not in event_data:
            date = event_data.get('date', datetime.now().strftime('%Y-%m-%d'))
            title_slug = event_data.get('title', 'event')[:50].lower()
            title_slug = '-'.join(title_slug.split())
            event_data['id'] = f"{date}--{title_slug}"
        
        # Check if event already exists
        if self.get_event_by_id(event_data['id']):
            return False, {'error': 'Event already exists'}
        
        # Save event
        event_file = self.timeline_dir / f"{event_data['id']}.json"
        try:
            with open(event_file, 'w') as f:
                json.dump(event_data, f, indent=2)
            return True, {'id': event_data['id'], 'message': 'Event created successfully'}
        except IOError as e:
            return False, {'error': f'Failed to save event: {str(e)}'}
    
    def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Update an existing event"""
        event_file = self.timeline_dir / f"{event_id}.json"
        if not event_file.exists():
            return False, {'error': 'Event not found'}
        
        try:
            # Preserve ID
            event_data['id'] = event_id
            with open(event_file, 'w') as f:
                json.dump(event_data, f, indent=2)
            return True, {'message': 'Event updated successfully'}
        except IOError as e:
            return False, {'error': f'Failed to update event: {str(e)}'}
    
    def delete_event(self, event_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Delete an event"""
        event_file = self.timeline_dir / f"{event_id}.json"
        if not event_file.exists():
            return False, {'error': 'Event not found'}
        
        try:
            event_file.unlink()
            return True, {'message': 'Event deleted successfully'}
        except IOError as e:
            return False, {'error': f'Failed to delete event: {str(e)}'}
    
    def search_events(self, query: str, field: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search events by query string"""
        events = self.get_all_events()
        results = []
        
        query_lower = query.lower()
        for event in events:
            if field:
                # Search specific field
                if field in event:
                    field_value = str(event[field]).lower()
                    if query_lower in field_value:
                        results.append(event)
            else:
                # Search all text fields
                searchable = [
                    str(event.get('title', '')),
                    str(event.get('summary', '')),
                    ' '.join(event.get('tags', [])),
                    ' '.join(event.get('actors', []))
                ]
                if any(query_lower in text.lower() for text in searchable):
                    results.append(event)
        
        return results


class ValidationService:
    """Service for event validation"""
    
    def validate_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive event validation
        
        Returns:
            Dictionary with validation results
        """
        errors = []
        
        # Check required fields
        fields_present, missing = validate_required_fields(event)
        if not fields_present:
            errors.extend([f"Missing required field: {field}" for field in missing])
        
        # Validate each field if present
        if 'date' in event:
            valid, error = validate_date_format(event['date'])
            if not valid and error:
                errors.append(error)
        
        if 'title' in event:
            valid, title_errors = validate_title(event['title'])
            errors.extend(title_errors)
        
        if 'summary' in event:
            valid, summary_errors = validate_summary(event['summary'])
            errors.extend(summary_errors)
        
        if 'status' in event:
            valid, error = validate_status(event['status'])
            if not valid and error:
                errors.append(error)
        
        if 'actors' in event:
            valid, actor_errors = validate_actors(event['actors'])
            errors.extend(actor_errors)
        
        if 'sources' in event:
            valid, source_errors = validate_sources(event['sources'])
            errors.extend(source_errors)
        
        if 'tags' in event:
            valid, tag_errors = validate_tags(event['tags'])
            errors.extend(tag_errors)
        
        if 'importance' in event:
            valid, importance_errors = validate_importance(event['importance'])
            errors.extend(importance_errors)
        
        # Calculate validation score
        score = calculate_validation_score(event, errors)
        
        # Get fix suggestions
        suggestions = suggest_fixes(event, errors)
        
        return {
            'valid': len(errors) == 0,
            'score': score,
            'errors': errors,
            'suggestions': suggestions,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def validate_batch(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate multiple events"""
        results = []
        total_score = 0
        total_valid = 0
        
        for event in events:
            result = self.validate_event(event)
            results.append({
                'id': event.get('id', 'unknown'),
                'valid': result['valid'],
                'score': result['score'],
                'error_count': len(result['errors'])
            })
            total_score += result['score']
            if result['valid']:
                total_valid += 1
        
        return {
            'total_events': len(events),
            'valid_events': total_valid,
            'average_score': total_score / len(events) if events else 0,
            'results': results
        }


class FileService:
    """Service for file operations"""
    
    def read_json_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """Read JSON file safely"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def write_json_file(self, path: Path, data: Dict[str, Any]) -> bool:
        """Write JSON file safely"""
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except IOError:
            return False
    
    def list_files(self, directory: Path, pattern: str = "*") -> List[Path]:
        """List files matching pattern"""
        try:
            return list(Path(directory).glob(pattern))
        except (IOError, OSError):
            return []
    
    def ensure_directory(self, path: Path) -> bool:
        """Ensure directory exists"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except (IOError, OSError):
            return False


class DatabaseService:
    """Service for database operations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS validation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    validation_score REAL,
                    error_count INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        # Extract path from URL
        if self.database_url.startswith('sqlite:///'):
            db_path = self.database_url.replace('sqlite:///', '')
            if db_path == ':memory:':
                conn = sqlite3.connect(':memory:')
            else:
                conn = sqlite3.connect(db_path)
        else:
            conn = sqlite3.connect(':memory:')
        
        try:
            yield conn
        finally:
            conn.close()
    
    def log_validation(self, event_id: str, score: float, error_count: int):
        """Log validation result"""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO validation_history (event_id, validation_score, error_count) VALUES (?, ?, ?)',
                (event_id, score, error_count)
            )
            conn.commit()
    
    def log_activity(self, action: str, details: Optional[str] = None):
        """Log activity"""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO activity_log (action, details) VALUES (?, ?)',
                (action, details)
            )
            conn.commit()
    
    def get_validation_history(self, event_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get validation history"""
        with self.get_connection() as conn:
            if event_id:
                cursor = conn.execute(
                    'SELECT * FROM validation_history WHERE event_id = ? ORDER BY timestamp DESC',
                    (event_id,)
                )
            else:
                cursor = conn.execute(
                    'SELECT * FROM validation_history ORDER BY timestamp DESC LIMIT 100'
                )
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]