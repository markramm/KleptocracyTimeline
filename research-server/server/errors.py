"""
Custom exceptions for Research Monitor

Provides specific exception types for better error handling and debugging.
Replaces broad `except Exception:` handlers with targeted exception catching.
"""


class ResearchMonitorError(Exception):
    """Base exception for all Research Monitor errors."""
    pass


# Database Errors
class DatabaseError(ResearchMonitorError):
    """Database operation failed."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Failed to connect to database."""
    pass


class DatabaseQueryError(DatabaseError):
    """Database query failed."""
    pass


class DatabaseIntegrityError(DatabaseError):
    """Database integrity constraint violated."""
    pass


# Validation Errors
class ValidationError(ResearchMonitorError):
    """Data validation failed."""
    pass


class EventValidationError(ValidationError):
    """Timeline event validation failed."""
    pass


class PriorityValidationError(ValidationError):
    """Research priority validation failed."""
    pass


class SchemaValidationError(ValidationError):
    """JSON schema validation failed."""
    pass


# Filesystem Errors
class FilesystemError(ResearchMonitorError):
    """Filesystem operation failed."""
    pass


class FileReadError(FilesystemError):
    """Failed to read file."""
    pass


class FileWriteError(FilesystemError):
    """Failed to write file."""
    pass


class FileParseError(FilesystemError):
    """Failed to parse file content."""
    pass


class FileSyncError(FilesystemError):
    """Filesystem sync operation failed."""
    pass


# API Errors
class APIError(ResearchMonitorError):
    """API operation failed."""
    pass


class AuthenticationError(APIError):
    """API authentication failed."""
    pass


class RateLimitError(APIError):
    """API rate limit exceeded."""
    pass


class InvalidRequestError(APIError):
    """Invalid API request."""
    pass


# QA System Errors
class QAError(ResearchMonitorError):
    """QA system operation failed."""
    pass


class QAQueueError(QAError):
    """QA queue operation failed."""
    pass


class ValidationRunError(QAError):
    """Validation run operation failed."""
    pass


class EventReservationError(QAError):
    """Event reservation failed (already reserved or not found)."""
    pass


# Configuration Errors
class ConfigurationError(ResearchMonitorError):
    """Configuration is invalid or missing."""
    pass


class MissingConfigError(ConfigurationError):
    """Required configuration is missing."""
    pass


class InvalidConfigError(ConfigurationError):
    """Configuration value is invalid."""
    pass


# Server Errors
class ServerError(ResearchMonitorError):
    """Server operation failed."""
    pass


class ServerStartupError(ServerError):
    """Server failed to start."""
    pass


class ServerShutdownError(ServerError):
    """Server failed to shutdown gracefully."""
    pass


# Search Errors
class SearchError(ResearchMonitorError):
    """Search operation failed."""
    pass


class FTSError(SearchError):
    """Full-text search (FTS5) operation failed."""
    pass


class QueryParseError(SearchError):
    """Search query parsing failed."""
    pass


# External Service Errors
class ExternalServiceError(ResearchMonitorError):
    """External service call failed."""
    pass


class WebFetchError(ExternalServiceError):
    """Web fetch operation failed."""
    pass


class TimeoutError(ExternalServiceError):
    """Operation timed out."""
    pass


def wrap_database_errors(func):
    """Decorator to convert SQLAlchemy exceptions to DatabaseError types.

    Usage:
        @wrap_database_errors
        def query_events(db):
            return db.query(TimelineEvent).all()
    """
    from functools import wraps
    from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            raise DatabaseIntegrityError(f"Database integrity error: {e}") from e
        except OperationalError as e:
            raise DatabaseConnectionError(f"Database connection error: {e}") from e
        except SQLAlchemyError as e:
            raise DatabaseQueryError(f"Database query error: {e}") from e

    return wrapper


def wrap_filesystem_errors(func):
    """Decorator to convert filesystem exceptions to FilesystemError types.

    Usage:
        @wrap_filesystem_errors
        def read_event_file(path):
            with open(path) as f:
                return json.load(f)
    """
    from functools import wraps
    import json

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            raise FileReadError(f"File not found: {e}") from e
        except PermissionError as e:
            raise FileReadError(f"Permission denied: {e}") from e
        except json.JSONDecodeError as e:
            raise FileParseError(f"JSON parse error: {e}") from e
        except (IOError, OSError) as e:
            raise FilesystemError(f"Filesystem error: {e}") from e

    return wrapper


def wrap_validation_errors(func):
    """Decorator to convert validation exceptions to ValidationError types.

    Usage:
        @wrap_validation_errors
        def validate_event(event_data):
            # validation logic
            pass
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, TypeError, KeyError) as e:
            raise ValidationError(f"Validation error: {e}") from e

    return wrapper
