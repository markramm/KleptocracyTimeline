"""
Event Validation Module - Strict format enforcement and validation
"""

from datetime import datetime, timezone
import re
from typing import Dict, List, Any, Tuple
import json

class EventValidator:
    """Comprehensive event validation with detailed error reporting"""
    
    # Valid status values
    VALID_STATUSES = ['confirmed', 'alleged', 'reported', 'speculative', 'developing', 'disputed', 'predicted']
    
    # Required fields
    REQUIRED_FIELDS = ['date', 'title', 'summary', 'actors', 'sources', 'tags']
    
    # Date format regex
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    @classmethod
    def validate_event(cls, event: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate a timeline event against all requirements
        
        Returns:
            Tuple of (is_valid, errors_list, validation_metadata)
        """
        errors = []
        metadata = {
            'validation_timestamp': datetime.now(timezone.utc).isoformat(),
            'fields_checked': [],
            'validation_score': 0.0
        }
        
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            metadata['fields_checked'].append(field)
            if field not in event:
                errors.append(f"Missing required field: {field}")
            elif not event[field]:
                errors.append(f"Empty required field: {field}")
        
        # Validate date format
        if 'date' in event and event['date']:
            if not cls.DATE_PATTERN.match(event['date']):
                errors.append(f"Invalid date format '{event['date']}' - must be YYYY-MM-DD")
            else:
                try:
                    datetime.strptime(event['date'], '%Y-%m-%d')
                except ValueError as e:
                    errors.append(f"Invalid date value: {e}")
        
        # Validate title
        if 'title' in event:
            if not event['title'] or len(event['title']) < 10:
                errors.append("Title must be at least 10 characters long")
            if len(event['title']) > 200:
                errors.append("Title must be less than 200 characters")
        
        # Validate summary
        if 'summary' in event:
            if not event['summary'] or len(event['summary']) < 50:
                errors.append("Summary must be at least 50 characters long")
        
        # Validate status
        if 'status' in event:
            if event['status'] not in cls.VALID_STATUSES:
                errors.append(f"Invalid status '{event['status']}' - must be one of: {', '.join(cls.VALID_STATUSES)}")
        
        # Validate actors
        if 'actors' in event:
            actors_errors = cls._validate_actors(event['actors'])
            errors.extend(actors_errors)
        
        # Validate sources
        if 'sources' in event:
            sources_errors = cls._validate_sources(event['sources'])
            errors.extend(sources_errors)
        
        # Validate tags
        if 'tags' in event:
            tags_errors = cls._validate_tags(event['tags'])
            errors.extend(tags_errors)
        
        # Validate importance
        if 'importance' in event:
            if not isinstance(event['importance'], int):
                errors.append("Importance must be an integer")
            elif event['importance'] < 1 or event['importance'] > 10:
                errors.append("Importance must be between 1 and 10")
        
        # Calculate validation score
        metadata['validation_score'] = cls._calculate_validation_score(event, errors)
        metadata['total_errors'] = len(errors)
        metadata['is_valid'] = len(errors) == 0
        
        return len(errors) == 0, errors, metadata
    
    @classmethod
    def _validate_actors(cls, actors: Any) -> List[str]:
        """Validate actors field"""
        errors = []
        
        if not isinstance(actors, list):
            errors.append("Actors must be a list")
            return errors
        
        if len(actors) == 0:
            errors.append("Actors list cannot be empty")
        elif len(actors) < 2:
            errors.append("At least 2 actors should be specified for context")
        
        for i, actor in enumerate(actors):
            if not isinstance(actor, str):
                errors.append(f"Actor {i+1} must be a string")
            elif len(actor.strip()) < 2:
                errors.append(f"Actor {i+1} name too short")
        
        return errors
    
    @classmethod
    def _validate_sources(cls, sources: Any) -> List[str]:
        """Validate sources field with strict format requirements"""
        errors = []
        
        if not isinstance(sources, list):
            errors.append("Sources must be a list")
            return errors
        
        if len(sources) == 0:
            errors.append("Sources list cannot be empty")
        elif len(sources) < 2:
            errors.append("At least 2 sources recommended for verification")
        
        for i, source in enumerate(sources):
            if isinstance(source, str):
                # Legacy format - just a URL
                errors.append(f"Source {i+1} using deprecated format - must be object with title, url, date, outlet")
            elif isinstance(source, dict):
                # Check required source fields
                if 'title' not in source or not source['title']:
                    errors.append(f"Source {i+1} missing required field: title")
                if 'url' not in source or not source['url']:
                    errors.append(f"Source {i+1} missing required field: url")
                
                # Validate URL format
                if 'url' in source and source['url']:
                    if not source['url'].startswith(('http://', 'https://')):
                        errors.append(f"Source {i+1} URL must start with http:// or https://")
                
                # Check recommended fields
                if 'date' not in source:
                    errors.append(f"Source {i+1} missing recommended field: date")
                elif source['date'] and not cls.DATE_PATTERN.match(source['date']):
                    errors.append(f"Source {i+1} invalid date format - must be YYYY-MM-DD")
                
                if 'outlet' not in source:
                    errors.append(f"Source {i+1} missing recommended field: outlet")
            else:
                errors.append(f"Source {i+1} must be a dictionary with title, url, date, outlet")
        
        return errors
    
    @classmethod
    def _validate_tags(cls, tags: Any) -> List[str]:
        """Validate tags field"""
        errors = []
        
        if not isinstance(tags, list):
            errors.append("Tags must be a list")
            return errors
        
        if len(tags) == 0:
            errors.append("Tags list cannot be empty")
        elif len(tags) < 3:
            errors.append("At least 3 tags recommended for categorization")
        
        for i, tag in enumerate(tags):
            if not isinstance(tag, str):
                errors.append(f"Tag {i+1} must be a string")
            elif len(tag.strip()) < 2:
                errors.append(f"Tag {i+1} too short")
            elif ' ' in tag and '-' not in tag:
                errors.append(f"Tag {i+1} should use hyphens instead of spaces")
        
        return errors
    
    @classmethod
    def _calculate_validation_score(cls, event: Dict[str, Any], errors: List[str]) -> float:
        """Calculate a validation score from 0.0 to 1.0"""
        score = 0.0
        total_checks = 15
        
        # Basic field presence (5 points)
        for field in ['date', 'title', 'summary', 'status', 'importance']:
            if field in event and event[field]:
                score += 1
        
        # Required lists present and non-empty (3 points)
        if event.get('actors') and len(event['actors']) > 0:
            score += 1
        if event.get('sources') and len(event['sources']) > 0:
            score += 1
        if event.get('tags') and len(event['tags']) > 0:
            score += 1
        
        # Quality checks (4 points)
        if event.get('actors') and len(event.get('actors', [])) >= 3:
            score += 1
        if event.get('sources') and len(event.get('sources', [])) >= 2:
            score += 1
        if event.get('tags') and len(event.get('tags', [])) >= 3:
            score += 1
        if event.get('summary') and len(event.get('summary', '')) >= 100:
            score += 1
        
        # Source format quality (3 points)
        if event.get('sources'):
            valid_sources = 0
            for source in event['sources'][:3]:  # Check first 3
                if isinstance(source, dict) and source.get('title') and source.get('url'):
                    valid_sources += 1
            score += valid_sources
        
        # Apply penalty for errors
        error_penalty = min(len(errors) * 0.05, 0.5)  # Max 50% penalty
        score = max(0, score - error_penalty * total_checks)
        
        return min(1.0, score / total_checks)
    
    @classmethod
    def suggest_fixes(cls, event: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
        """Suggest fixes for common validation errors"""
        suggestions = {
            'fixable_errors': [],
            'requires_research': [],
            'format_fixes': []
        }
        
        for error in errors:
            if "missing required field" in error.lower():
                field = error.split(':')[-1].strip()
                suggestions['requires_research'].append(f"Research and add {field}")
            
            elif "deprecated format" in error:
                suggestions['format_fixes'].append("Convert source URLs to full citation objects")
            
            elif "at least" in error.lower():
                suggestions['requires_research'].append(error)
            
            elif "hyphens instead of spaces" in error:
                suggestions['fixable_errors'].append("Replace spaces with hyphens in tags")
            
            elif "too short" in error:
                suggestions['requires_research'].append(f"Expand {error.split()[0]} with more detail")
        
        return suggestions