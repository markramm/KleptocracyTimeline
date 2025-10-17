# Exception Handling Guide

**Version**: 1.0
**Date**: 2025-10-16
**Sprint**: Sprint 1, Task 3

## Overview

This guide documents the transition from broad exception handling to specific exception types in the Kleptocracy Timeline project.

## Problem: Broad Exception Handlers

The codebase previously contained broad exception handlers that masked bugs:

```python
# ❌ BAD: Catches everything, including bugs
try:
    result = do_something()
except Exception:
    return None  # What went wrong? Unknown!
```

**Problems with broad handlers:**
- Masks programming errors (AttributeError, NameError, etc.)
- Makes debugging difficult
- Hides unexpected failure modes
- Violates Python best practices

## Solution: Specific Exception Types

Use specific exception types that match the expected failure modes:

```python
# ✅ GOOD: Catches specific expected errors
try:
    result = load_json_file(path)
except FileNotFoundError:
    logger.warning(f"File not found: {path}")
    return None
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in {path}: {e}")
    return None
except PermissionError:
    logger.error(f"Permission denied: {path}")
    return None
```

## Custom Exception Classes

Location: `research_monitor/errors.py`

### Exception Hierarchy

```
ResearchMonitorError (base)
├── DatabaseError
│   ├── DatabaseConnectionError
│   ├── DatabaseQueryError
│   └── DatabaseIntegrityError
├── ValidationError
│   ├── EventValidationError
│   ├── PriorityValidationError
│   └── SchemaValidationError
├── FilesystemError
│   ├── FileReadError
│   ├── FileWriteError
│   ├── FileParseError
│   └── FileSyncError
├── APIError
│   ├── AuthenticationError
│   ├── RateLimitError
│   └── InvalidRequestError
├── QAError
│   ├── QAQueueError
│   ├── ValidationRunError
│   └── EventReservationError
├── ConfigurationError
│   ├── MissingConfigError
│   └── InvalidConfigError
├── ServerError
│   ├── ServerStartupError
│   └── ServerShutdownError
├── SearchError
│   ├── FTSError
│   └── QueryParseError
└── ExternalServiceError
    ├── WebFetchError
    └── TimeoutError
```

### Usage Examples

#### Database Operations

```python
from research_monitor.errors import DatabaseError, DatabaseQueryError
from sqlalchemy.exc import SQLAlchemyError

try:
    events = db.query(TimelineEvent).all()
except SQLAlchemyError as e:
    raise DatabaseQueryError(f"Failed to query events: {e}") from e
```

#### File Operations

```python
from research_monitor.errors import FileReadError, FileParseError
import json

try:
    with open(path) as f:
        return json.load(f)
except FileNotFoundError as e:
    raise FileReadError(f"Event file not found: {path}") from e
except json.JSONDecodeError as e:
    raise FileParseError(f"Invalid JSON in {path}: {e}") from e
```

#### Validation

```python
from research_monitor.errors import EventValidationError

def validate_event(event_data):
    if 'date' not in event_data:
        raise EventValidationError("Missing required field: date")
    if event_data['importance'] not in range(1, 11):
        raise EventValidationError("Importance must be between 1 and 10")
```

## Decorator Patterns

The `errors.py` module provides decorators for common exception patterns:

### Database Error Wrapping

```python
from research_monitor.errors import wrap_database_errors

@wrap_database_errors
def get_timeline_events(db):
    """Automatically converts SQLAlchemy errors to DatabaseError types"""
    return db.query(TimelineEvent).all()
```

### Filesystem Error Wrapping

```python
from research_monitor.errors import wrap_filesystem_errors

@wrap_filesystem_errors
def load_event_file(path):
    """Automatically converts filesystem errors to FilesystemError types"""
    with open(path) as f:
        return json.load(f)
```

### Validation Error Wrapping

```python
from research_monitor.errors import wrap_validation_errors

@wrap_validation_errors
def validate_event_data(data):
    """Automatically converts value errors to ValidationError types"""
    if not data.get('title'):
        raise ValueError("Title is required")
    return True
```

## Migration Pattern

### Step 1: Identify Broad Handler

```python
# Current code
try:
    result = risky_operation()
except Exception:
    return default_value
```

### Step 2: Determine Specific Exceptions

Ask: "What can actually go wrong here?"
- File operations → FileNotFoundError, PermissionError, IOError
- JSON parsing → json.JSONDecodeError
- Network calls → socket.error, TimeoutError, ConnectionError
- Database → SQLAlchemyError and subtypes

### Step 3: Replace with Specific Handlers

```python
# Migrated code
try:
    result = risky_operation()
except FileNotFoundError:
    logger.warning(f"File not found, using default")
    return default_value
except PermissionError as e:
    logger.error(f"Permission denied: {e}")
    return default_value
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON: {e}")
    return default_value
```

### Step 4: Add Logging

Always log the specific error:

```python
import logging
logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    return default_value
```

## Common Exception Patterns

### Pattern 1: File Operations

```python
try:
    with open(filepath, 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    # File doesn't exist - might be expected
    return None
except PermissionError as e:
    # Permissions issue - unexpected
    raise FileReadError(f"Cannot read {filepath}: {e}") from e
except json.JSONDecodeError as e:
    # Corrupt file - needs investigation
    raise FileParseError(f"Invalid JSON in {filepath}: {e}") from e
```

### Pattern 2: Database Operations

```python
from sqlalchemy.exc import IntegrityError, OperationalError

try:
    db.add(new_record)
    db.commit()
except IntegrityError as e:
    # Duplicate or constraint violation - might be expected
    db.rollback()
    raise DatabaseIntegrityError(f"Integrity error: {e}") from e
except OperationalError as e:
    # Database connection issue - unexpected
    db.rollback()
    raise DatabaseConnectionError(f"Database error: {e}") from e
```

### Pattern 3: Network Operations

```python
import socket
import requests

try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.Timeout:
    raise TimeoutError(f"Request to {url} timed out")
except requests.ConnectionError as e:
    raise ExternalServiceError(f"Connection failed: {e}") from e
except requests.HTTPError as e:
    if e.response.status_code == 404:
        return None  # Not found is often expected
    raise ExternalServiceError(f"HTTP error: {e}") from e
```

### Pattern 4: Validation

```python
def validate_event(event_data: dict):
    """Validate event data with specific error messages"""
    try:
        # Required fields
        if 'id' not in event_data:
            raise EventValidationError("Missing required field: id")
        if 'date' not in event_data:
            raise EventValidationError("Missing required field: date")

        # Type validation
        if not isinstance(event_data.get('importance'), int):
            raise EventValidationError("Importance must be an integer")

        # Range validation
        if not (1 <= event_data['importance'] <= 10):
            raise EventValidationError("Importance must be between 1 and 10")

    except (KeyError, TypeError, ValueError) as e:
        # Convert standard Python exceptions to our custom types
        raise EventValidationError(f"Validation failed: {e}") from e
```

## When to Use Broad Handlers (Rarely!)

There are a few cases where `except Exception:` might be acceptable:

### 1. Top-Level Error Handlers

```python
# In API endpoints - catch everything to return proper error response
@app.route('/api/endpoint')
def endpoint():
    try:
        result = process_request()
        return jsonify(result)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except DatabaseError as e:
        logger.error(f"Database error: {e}", exc_info=True)
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        # Last resort - log and return generic error
        logger.exception(f"Unexpected error in endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500
```

### 2. Cleanup Code

```python
try:
    perform_operation()
finally:
    try:
        cleanup_resources()
    except Exception as e:
        # Don't want cleanup to hide original exception
        logger.warning(f"Cleanup failed: {e}")
```

### 3. Defensive Code in Libraries

```python
# When you truly don't know what exceptions to expect
def safe_callback(callback, *args, **kwargs):
    try:
        return callback(*args, **kwargs)
    except Exception as e:
        logger.error(f"Callback failed: {e}", exc_info=True)
        return None
```

## Testing Exception Handling

Always test your exception handling:

```python
def test_file_not_found():
    """Test that missing files are handled gracefully"""
    with pytest.raises(FileReadError):
        load_event_file("/nonexistent/path.json")

def test_invalid_json():
    """Test that corrupt JSON is handled"""
    with pytest.raises(FileParseError):
        load_event_file("corrupt.json")
```

## Progress Tracking

### Sprint 1 (Completed)

**Research Monitor Directory** (8 broad handlers):
- ✅ `server_manager.py`: Fixed 4 handlers
  - `_is_process_running()`: catch psutil.Error, AttributeError
  - `_is_port_in_use()`: catch OSError, AttributeError
  - `_get_process_info()`: catch psutil exceptions
  - `_kill_processes_on_port()`: catch psutil.Error, AttributeError, PermissionError
- ✅ `services/timeline_sync.py`: Fixed 2 handlers
  - File writing: catch IOError, OSError, json.JSONEncodeError
  - File loading: catch IOError, OSError, json.JSONDecodeError
- ⏭️ `test_app_v2.py`: 2 handlers kept (intentional test failures)

**Created Infrastructure**:
- ✅ `research_monitor/errors.py`: Custom exception classes
- ✅ `docs/EXCEPTION_HANDLING_GUIDE.md`: This guide

### Remaining Work (Future Sprints)

**Project-wide** (~46 remaining):
- Scripts directory: ~20 broad handlers
- AI analysis tools: ~10 broad handlers
- Research monitor utilities: ~6 broad handlers
- Other Python files: ~10 broad handlers

## Resources

- [Python Exception Handling Best Practices](https://docs.python.org/3/tutorial/errors.html)
- [PEP 3134 - Exception Chaining](https://www.python.org/dev/peps/pep-3134/)
- [Google Python Style Guide - Exceptions](https://google.github.io/styleguide/pyguide.html#24-exceptions)

## Related Documentation

- `research_monitor/errors.py` - Custom exception definitions
- `specs/PROJECT_EVALUATION.md` - Project evaluation (Sprint 1)
- `specs/ARCHITECTURAL_CLEANUP.md` - Cleanup priorities
