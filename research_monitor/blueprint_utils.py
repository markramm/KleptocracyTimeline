"""
Shared utilities for Flask blueprints

Consolidates common helper functions used across all blueprint modules.
Eliminates code duplication and provides single source of truth for:
- Database access
- API authentication
- Activity logging
- Caching with invalidation

Usage in blueprints:
    from research_monitor.blueprint_utils import get_db, require_api_key, log_activity
"""

from flask import request, jsonify, current_app
from functools import wraps
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Database Access
# ============================================================================

def get_db():
    """
    Get database session from app_v2.

    Returns:
        SQLAlchemy Session object

    Usage:
        db = get_db()
        events = db.query(TimelineEvent).all()
    """
    from research_monitor import app_v2
    return app_v2.get_db()


# ============================================================================
# Authentication
# ============================================================================

def require_api_key(f):
    """
    Decorator to require API key authentication for endpoints.

    Checks X-API-Key header against configured API keys.
    Returns 401 Unauthorized if key is missing or invalid.

    Usage:
        @bp.route('/api/endpoint', methods=['POST'])
        @require_api_key
        def protected_endpoint():
            return {"status": "success"}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from research_monitor import app_v2

        # Get API key from header
        provided_key = request.headers.get('X-API-Key')

        # Get valid keys from config
        valid_keys = current_app.config.get('API_KEYS', ['test-key'])

        # Validate
        if not provided_key or provided_key not in valid_keys:
            logger.warning(f"Unauthorized API access attempt from {request.remote_addr}")
            return jsonify({
                "error": "Unauthorized",
                "message": "Valid API key required"
            }), 401

        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# Activity Logging
# ============================================================================

def log_activity(activity_type: str, details: str = None, metadata: dict = None):
    """
    Log activity to database for audit trail and monitoring.

    Args:
        activity_type: Type of activity (e.g., 'priority_reserved', 'event_validated')
        details: Human-readable description of the activity
        metadata: Additional structured data (JSON serializable)

    Usage:
        log_activity(
            'priority_reserved',
            f'Reserved priority {priority_id}',
            {'priority_id': priority_id, 'agent_id': agent_id}
        )
    """
    try:
        db = get_db()

        # Import here to avoid circular dependencies
        from research_monitor.models import ActivityLog

        log_entry = ActivityLog(
            activity_type=activity_type,
            details=details,
            metadata=metadata,
            timestamp=datetime.now(timezone.utc)
        )

        db.add(log_entry)
        db.commit()

        logger.info(f"Activity logged: {activity_type} - {details}")

    except Exception as e:
        logger.error(f"Failed to log activity: {e}")
        # Don't raise - activity logging should not break requests


# ============================================================================
# Caching
# ============================================================================

def cache_with_invalidation(timeout=300, key_prefix='view'):
    """
    Decorator for caching endpoint responses with invalidation support.

    Provides simple in-memory caching with TTL and manual invalidation.
    Not a replacement for Redis, but sufficient for development.

    Args:
        timeout: Cache timeout in seconds (default: 300 = 5 minutes)
        key_prefix: Prefix for cache keys (default: 'view')

    Usage:
        @bp.route('/api/data')
        @cache_with_invalidation(timeout=600, key_prefix='api_data')
        def get_data():
            return expensive_operation()
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if caching is enabled
            if not current_app.config.get('ENABLE_CACHE', True):
                return f(*args, **kwargs)

            # Generate cache key from endpoint and args
            cache_key = f"{key_prefix}_{request.endpoint}_{request.query_string.decode()}"

            # Try to get from cache
            cache = current_app.config.get('CACHE', {})
            cached_data = cache.get(cache_key)

            if cached_data:
                cached_value, cached_time = cached_data
                age = (datetime.now() - cached_time).total_seconds()

                if age < timeout:
                    logger.debug(f"Cache hit: {cache_key} (age: {age:.1f}s)")
                    return cached_value

            # Cache miss - execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = f(*args, **kwargs)

            # Store in cache
            cache[cache_key] = (result, datetime.now())

            return result

        return decorated_function
    return decorator


def invalidate_cache(key_pattern: str = None):
    """
    Invalidate cached responses matching pattern.

    Args:
        key_pattern: Pattern to match cache keys (None = clear all)

    Usage:
        # Clear specific cache
        invalidate_cache('api_data')

        # Clear all cache
        invalidate_cache()
    """
    cache = current_app.config.get('CACHE', {})

    if key_pattern is None:
        # Clear all
        cache.clear()
        logger.info("All cache cleared")
    else:
        # Clear matching keys
        keys_to_delete = [k for k in cache.keys() if key_pattern in k]
        for key in keys_to_delete:
            del cache[key]
        logger.info(f"Cleared {len(keys_to_delete)} cache entries matching '{key_pattern}'")


# ============================================================================
# Response Helpers
# ============================================================================

def success_response(data=None, message=None, **kwargs):
    """
    Generate standardized success response.

    Args:
        data: Response data (dict, list, etc.)
        message: Optional success message
        **kwargs: Additional fields to include in response

    Returns:
        Flask JSON response with 200 status

    Usage:
        return success_response(
            data={'events': events},
            message='Events retrieved successfully',
            count=len(events)
        )
    """
    response = {
        'success': True,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    if message:
        response['message'] = message

    if data is not None:
        response['data'] = data

    # Add any additional fields
    response.update(kwargs)

    return jsonify(response), 200


def error_response(message, status_code=400, error_type=None, **kwargs):
    """
    Generate standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        error_type: Type of error (e.g., 'ValidationError')
        **kwargs: Additional error details

    Returns:
        Flask JSON response with appropriate status code

    Usage:
        return error_response(
            'Event not found',
            status_code=404,
            error_type='NotFoundError',
            event_id=event_id
        )
    """
    response = {
        'success': False,
        'error': {
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    }

    if error_type:
        response['error']['type'] = error_type

    # Add any additional error details
    if kwargs:
        response['error']['details'] = kwargs

    logger.warning(f"Error response: {status_code} - {message}")

    return jsonify(response), status_code


# ============================================================================
# Pagination Helpers
# ============================================================================

def paginate_query(query, page=1, per_page=50, max_per_page=1000):
    """
    Paginate SQLAlchemy query with validation.

    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page
        max_per_page: Maximum allowed items per page

    Returns:
        dict with paginated results and metadata

    Usage:
        query = db.query(TimelineEvent).filter(...)
        result = paginate_query(query, page=2, per_page=20)
        return jsonify(result)
    """
    # Validate and clamp parameters
    page = max(1, int(page))
    per_page = min(max(1, int(per_page)), max_per_page)

    # Get total count
    total = query.count()

    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # Execute query
    items = query.limit(per_page).offset(offset).all()

    return {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }


# ============================================================================
# Request Helpers
# ============================================================================

def get_request_json(required_fields=None):
    """
    Get and validate JSON from request body.

    Args:
        required_fields: List of required field names

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If JSON is invalid or required fields are missing

    Usage:
        data = get_request_json(required_fields=['event_id', 'status'])
    """
    if not request.is_json:
        raise ValueError("Request must be JSON")

    data = request.get_json()

    if not data:
        raise ValueError("Request body is empty")

    if required_fields:
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

    return data


def get_query_params(defaults=None):
    """
    Get query parameters with defaults and type conversion.

    Args:
        defaults: Dict of parameter names and default values

    Returns:
        Dict of query parameters with proper types

    Usage:
        params = get_query_params({
            'page': 1,
            'limit': 50,
            'include_validated': False
        })
    """
    if defaults is None:
        defaults = {}

    params = {}

    for key, default_value in defaults.items():
        value = request.args.get(key)

        if value is None:
            params[key] = default_value
        else:
            # Type conversion based on default value type
            if isinstance(default_value, bool):
                params[key] = value.lower() in ('true', '1', 'yes')
            elif isinstance(default_value, int):
                params[key] = int(value)
            elif isinstance(default_value, float):
                params[key] = float(value)
            else:
                params[key] = value

    return params
