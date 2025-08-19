"""
Validation utilities for timeline events
"""

import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


def validate_date(date_str: str, allow_future: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate a date string.
    
    Args:
        date_str: Date string to validate (YYYY-MM-DD format)
        allow_future: Whether to allow future dates
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_str:
        return False, "Date is required"
    
    # Handle date objects
    if isinstance(date_str, (date, datetime)):
        date_obj = date_str if isinstance(date_str, date) else date_str.date()
    else:
        # Parse string date
        try:
            date_obj = datetime.strptime(str(date_str), '%Y-%m-%d').date()
        except ValueError:
            return False, f"Invalid date format: {date_str} (expected YYYY-MM-DD)"
    
    # Check if date is in the future
    if not allow_future and date_obj > date.today():
        return False, f"Date is in the future: {date_obj}"
    
    # Check reasonable range (1900-2100)
    if date_obj.year < 1900 or date_obj.year > 2100:
        return False, f"Date year out of range (1900-2100): {date_obj.year}"
    
    return True, None


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"
    
    # Special case for placeholder text
    if url == "Research Document":
        return True, None
    
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, f"Invalid URL format: {url}"
        
        if result.scheme not in ['http', 'https']:
            return False, f"URL must use http or https: {url}"
        
        return True, None
    except Exception as e:
        return False, f"Invalid URL: {url} ({e})"


def validate_sources(sources: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate event sources.
    
    Args:
        sources: List of source dictionaries
        
    Returns:
        Tuple of (all_valid, list_of_errors)
    """
    errors = []
    
    if not sources:
        errors.append("At least one source is required")
        return False, errors
    
    if not isinstance(sources, list):
        errors.append("Sources must be a list")
        return False, errors
    
    for i, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"Source {i+1}: Must be a dictionary")
            continue
        
        # Validate URL
        if 'url' not in source:
            errors.append(f"Source {i+1}: Missing URL")
        else:
            valid, error = validate_url(source['url'])
            if not valid:
                errors.append(f"Source {i+1}: {error}")
        
        # Validate title
        if 'title' not in source:
            errors.append(f"Source {i+1}: Missing title")
        elif not source['title'] or not source['title'].strip():
            errors.append(f"Source {i+1}: Title cannot be empty")
    
    return len(errors) == 0, errors


def validate_event_schema(event: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate an event against the schema requirements.
    
    Args:
        event: Event dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    required_fields = ['id', 'date', 'title', 'summary', 'sources', 'status']
    
    # Check required fields
    for field in required_fields:
        if field not in event:
            errors.append(f"Missing required field: {field}")
    
    # Validate ID
    if 'id' in event:
        event_id = event['id']
        if not event_id or not isinstance(event_id, str):
            errors.append("ID must be a non-empty string")
        elif not re.match(r'^[a-z0-9-]+$', event_id):
            errors.append(f"ID must contain only lowercase letters, numbers, and hyphens: {event_id}")
    
    # Validate date
    if 'date' in event:
        valid, error = validate_date(event['date'], allow_future=event.get('status') == 'predicted')
        if not valid:
            errors.append(error)
    
    # Validate title
    if 'title' in event:
        if not event['title'] or not event['title'].strip():
            errors.append("Title cannot be empty")
        elif len(event['title']) > 200:
            errors.append(f"Title too long ({len(event['title'])} chars, max 200)")
    
    # Validate summary
    if 'summary' in event:
        if not event['summary'] or not event['summary'].strip():
            errors.append("Summary cannot be empty")
        elif len(event['summary']) < 10:
            errors.append("Summary too short (min 10 characters)")
    
    # Validate status
    if 'status' in event:
        valid_statuses = ['confirmed', 'pending', 'predicted', 'disputed']
        if event['status'] not in valid_statuses:
            errors.append(f"Invalid status: {event['status']} (must be one of: {', '.join(valid_statuses)})")
    
    # Validate sources
    if 'sources' in event:
        valid, source_errors = validate_sources(event['sources'])
        errors.extend(source_errors)
    
    # Validate tags
    if 'tags' in event:
        if not isinstance(event['tags'], list):
            errors.append("Tags must be a list")
        else:
            for tag in event['tags']:
                if not isinstance(tag, str):
                    errors.append(f"Tag must be a string: {tag}")
                elif not tag.strip():
                    errors.append("Tag cannot be empty")
    
    # Validate actors
    if 'actors' in event:
        if not isinstance(event['actors'], list):
            errors.append("Actors must be a list")
        else:
            for actor in event['actors']:
                if not isinstance(actor, str):
                    errors.append(f"Actor must be a string: {actor}")
                elif not actor.strip():
                    errors.append("Actor cannot be empty")
    
    return len(errors) == 0, errors


def get_validation_errors(event: Dict[str, Any]) -> List[str]:
    """
    Get all validation errors for an event.
    
    Args:
        event: Event dictionary to validate
        
    Returns:
        List of error messages
    """
    _, errors = validate_event_schema(event)
    return errors


def validate_filename(filepath: str, event_id: str, event_date: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that filename matches expected format.
    
    Args:
        filepath: Path to the event file
        event_id: Event ID from the data
        event_date: Event date from the data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    from pathlib import Path
    
    filename = Path(filepath).stem
    expected_format = event_id  # The ID should match the filename exactly
    
    if filename != expected_format:
        return False, f"Filename '{filename}' doesn't match event ID '{expected_format}'"
    
    return True, None