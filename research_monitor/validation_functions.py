"""
Pure validation functions extracted from EventValidator for better testability
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

# Valid status values
# Core statuses for event certainty
VALID_STATUSES = [
    # Primary statuses (original)
    'confirmed', 'alleged', 'speculative', 'developing',
    # Additional verification statuses (from actual timeline events)
    'validated', 'reported', 'investigated', 'disputed',
    'contested', 'predicted', 'verified', 'enhanced',
    # Workflow statuses (from QA system)
    'needs_work', 'unverified'
]

# Required fields
REQUIRED_FIELDS = ['date', 'title', 'summary', 'actors', 'sources', 'tags']

# Date format regex
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def validate_date_format(date_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate date string format
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_str:
        return False, "Date is empty"
    
    if not DATE_PATTERN.match(date_str):
        return False, f"Invalid date format '{date_str}' - must be YYYY-MM-DD"
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True, None
    except ValueError as e:
        return False, f"Invalid date value: {e}"


def validate_title(title: str) -> Tuple[bool, List[str]]:
    """
    Validate event title
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not title or len(title) < 10:
        errors.append("Title must be at least 10 characters long")
    if len(title) > 200:
        errors.append("Title must be less than 200 characters")
    
    return len(errors) == 0, errors


def validate_summary(summary: str) -> Tuple[bool, List[str]]:
    """
    Validate event summary
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not summary or len(summary) < 50:
        errors.append("Summary must be at least 50 characters long")
    
    return len(errors) == 0, errors


def validate_status(status: str) -> Tuple[bool, Optional[str]]:
    """
    Validate event status
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if status not in VALID_STATUSES:
        return False, f"Invalid status '{status}' - must be one of: {', '.join(VALID_STATUSES)}"
    return True, None


def validate_actors(actors: Any) -> Tuple[bool, List[str]]:
    """
    Validate actors field
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(actors, list):
        errors.append("Actors must be a list")
        return False, errors
    
    if len(actors) == 0:
        errors.append("Actors list cannot be empty")
    elif len(actors) < 2:
        errors.append("At least 2 actors should be specified for context")
    
    for i, actor in enumerate(actors):
        if not isinstance(actor, str):
            errors.append(f"Actor {i+1} must be a string")
        elif len(actor.strip()) < 2:
            errors.append(f"Actor {i+1} name too short")
    
    return len(errors) == 0, errors


def validate_single_source(source: Any, index: int) -> List[str]:
    """
    Validate a single source entry
    
    Returns:
        List of errors for this source
    """
    errors = []
    
    if isinstance(source, str):
        # Legacy format - just a URL
        errors.append(f"Source {index} using deprecated format - must be object with title, url, date, outlet")
    elif isinstance(source, dict):
        # Check required source fields
        if 'title' not in source or not source['title']:
            errors.append(f"Source {index} missing required field: title")
        if 'url' not in source or not source['url']:
            errors.append(f"Source {index} missing required field: url")
        
        # Validate URL format
        if 'url' in source and source['url']:
            if not source['url'].startswith(('http://', 'https://')):
                errors.append(f"Source {index} URL must start with http:// or https://")
        
        # Check recommended fields
        if 'date' not in source:
            errors.append(f"Source {index} missing recommended field: date")
        elif source['date']:
            is_valid, date_error = validate_date_format(source['date'])
            if not is_valid:
                errors.append(f"Source {index} {date_error}")
        
        if 'outlet' not in source:
            errors.append(f"Source {index} missing recommended field: outlet")
    else:
        errors.append(f"Source {index} must be a dictionary with title, url, date, outlet")
    
    return errors


def validate_sources(sources: Any) -> Tuple[bool, List[str]]:
    """
    Validate sources field with strict format requirements
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(sources, list):
        errors.append("Sources must be a list")
        return False, errors
    
    if len(sources) == 0:
        errors.append("Sources list cannot be empty")
    elif len(sources) < 2:
        errors.append("At least 2 sources recommended for verification")
    
    for i, source in enumerate(sources, 1):
        source_errors = validate_single_source(source, i)
        errors.extend(source_errors)
    
    return len(errors) == 0, errors


def validate_tags(tags: Any) -> Tuple[bool, List[str]]:
    """
    Validate tags field
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(tags, list):
        errors.append("Tags must be a list")
        return False, errors
    
    if len(tags) == 0:
        errors.append("Tags list cannot be empty")
    elif len(tags) < 3:
        errors.append("At least 3 tags recommended for categorization")
    
    for i, tag in enumerate(tags, 1):
        if not isinstance(tag, str):
            errors.append(f"Tag {i} must be a string")
        elif len(tag.strip()) < 2:
            errors.append(f"Tag {i} too short")
        elif ' ' in tag and '-' not in tag:
            errors.append(f"Tag {i} should use hyphens instead of spaces")
    
    return len(errors) == 0, errors


def validate_importance(importance: Any) -> Tuple[bool, List[str]]:
    """
    Validate importance field
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(importance, int):
        errors.append("Importance must be an integer")
    elif importance < 1 or importance > 10:
        errors.append("Importance must be between 1 and 10")
    
    return len(errors) == 0, errors


def calculate_validation_score(event: Dict[str, Any], errors: List[str]) -> float:
    """
    Calculate a validation score from 0.0 to 1.0
    
    Args:
        event: The event dictionary
        errors: List of validation errors
    
    Returns:
        Score between 0.0 and 1.0
    """
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


def validate_required_fields(event: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check that all required fields are present
    
    Returns:
        Tuple of (all_present, list_of_missing_fields)
    """
    missing = []
    
    for field in REQUIRED_FIELDS:
        if field not in event:
            missing.append(field)
        elif not event[field]:
            missing.append(f"{field} (empty)")
    
    return len(missing) == 0, missing


def suggest_fixes(event: Dict[str, Any], errors: List[str]) -> Dict[str, List[str]]:
    """
    Suggest fixes for common validation errors
    
    Returns:
        Dictionary with categorized suggestions
    """
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