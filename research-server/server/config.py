#!/usr/bin/env python3
"""
Research Monitor Configuration Management

Centralized configuration loading, validation, and defaults for the Research Monitor
Flask application. Loads configuration from environment variables with sensible defaults.

Environment Variables:
- RESEARCH_MONITOR_PORT: Server port (default: 5558)
- RESEARCH_MONITOR_SECRET: Flask secret key (default: auto-generated)
- RESEARCH_MONITOR_API_KEY: API authentication key (default: None)
- RESEARCH_DB_PATH: SQLite database path (default: ../unified_research.db)
- TIMELINE_EVENTS_PATH: Timeline events directory (default: ../timeline/data/events)
- RESEARCH_PRIORITIES_PATH: Research priorities directory (default: ../research_priorities)
- VALIDATION_LOGS_PATH: Validation logs directory (default: ../timeline/data/validation_logs)
- COMMIT_THRESHOLD: Events before commit signal (default: 10)
- CACHE_TYPE: Flask-Caching cache type (default: simple)
- CACHE_DEFAULT_TIMEOUT: Cache timeout in seconds (default: 300)
- CACHE_THRESHOLD: Maximum cached items (default: 1000)
"""

import os
from pathlib import Path
from typing import Optional
import secrets


# Legacy constants for backward compatibility
DEFAULT_RESEARCH_MONITOR_PORT = 5558
SERVER_PID_FILE = "/tmp/research_monitor.pid"
SERVER_LOG_FILE = "/tmp/research_monitor.log"


def get_research_monitor_port():
    """Get the Research Monitor port from environment or default (legacy function)"""
    return int(os.environ.get('RESEARCH_MONITOR_PORT', DEFAULT_RESEARCH_MONITOR_PORT))


def get_research_monitor_url():
    """Get the full URL for the Research Monitor server (legacy function)"""
    port = get_research_monitor_port()
    return f"http://localhost:{port}"


class Config:
    """Research Monitor configuration with environment variable loading and validation"""

    def __init__(self):
        """Load and validate configuration from environment variables"""
        # Server configuration
        self.port = self._get_int('RESEARCH_MONITOR_PORT', 5558)
        self.secret_key = self._get_str('RESEARCH_MONITOR_SECRET', secrets.token_hex(32))
        self.api_key = self._get_str('RESEARCH_MONITOR_API_KEY', None)

        # Database configuration
        self.db_path = self._get_str('RESEARCH_DB_PATH', '../unified_research.db')

        # Path configuration (updated for new directory structure)
        self.events_path = self._get_path('TIMELINE_EVENTS_PATH', '../../timeline/data/events')
        self.priorities_path = self._get_path('RESEARCH_PRIORITIES_PATH', '../data/research_priorities')
        self.validation_logs_path = self._get_path('VALIDATION_LOGS_PATH', '../../timeline/data/validation_logs')

        # Commit orchestration
        self.commit_threshold = self._get_int('COMMIT_THRESHOLD', 10)

        # Cache configuration
        self.cache_type = self._get_str('CACHE_TYPE', 'simple')
        self.cache_default_timeout = self._get_int('CACHE_DEFAULT_TIMEOUT', 300)
        self.cache_threshold = self._get_int('CACHE_THRESHOLD', 1000)

        # Validate configuration
        self._validate()

    def _get_str(self, env_var: str, default: Optional[str]) -> Optional[str]:
        """Get string from environment variable with default"""
        return os.environ.get(env_var, default)

    def _get_int(self, env_var: str, default: int) -> int:
        """Get integer from environment variable with default and validation"""
        value = os.environ.get(env_var)
        if value is None:
            return default

        try:
            return int(value)
        except ValueError:
            raise ValueError(
                f"Invalid integer value for {env_var}: {value}. "
                f"Using default: {default}"
            )

    def _get_path(self, env_var: str, default: str) -> Path:
        """Get Path from environment variable with default"""
        value = os.environ.get(env_var, default)
        return Path(value)

    def _validate(self):
        """Validate configuration values"""
        # Validate port range
        if not (1024 <= self.port <= 65535):
            raise ValueError(
                f"Port {self.port} is outside valid range (1024-65535). "
                f"Set RESEARCH_MONITOR_PORT environment variable."
            )

        # Validate commit threshold
        if self.commit_threshold < 1:
            raise ValueError(
                f"Commit threshold {self.commit_threshold} must be >= 1. "
                f"Set COMMIT_THRESHOLD environment variable."
            )

        # Validate cache settings
        if self.cache_default_timeout < 0:
            raise ValueError(
                f"Cache timeout {self.cache_default_timeout} must be >= 0. "
                f"Set CACHE_DEFAULT_TIMEOUT environment variable."
            )

        if self.cache_threshold < 1:
            raise ValueError(
                f"Cache threshold {self.cache_threshold} must be >= 1. "
                f"Set CACHE_THRESHOLD environment variable."
            )

    def to_flask_config(self) -> dict:
        """
        Convert Config to Flask app.config dictionary

        Returns:
            dict: Configuration dictionary suitable for Flask app.config.update()
        """
        return {
            'SECRET_KEY': self.secret_key,
            'API_KEY': self.api_key,
            'DB_PATH': self.db_path,
            'EVENTS_PATH': self.events_path,
            'PRIORITIES_PATH': self.priorities_path,
            'VALIDATION_LOGS_PATH': self.validation_logs_path,
            'COMMIT_THRESHOLD': self.commit_threshold,
            'CACHE_TYPE': self.cache_type,
            'CACHE_DEFAULT_TIMEOUT': self.cache_default_timeout,
            'CACHE_THRESHOLD': self.cache_threshold,
        }

    def __repr__(self) -> str:
        """String representation of Config (safe - no secrets)"""
        return (
            f"Config("
            f"port={self.port}, "
            f"db_path={self.db_path}, "
            f"events_path={self.events_path}, "
            f"priorities_path={self.priorities_path}, "
            f"validation_logs_path={self.validation_logs_path}, "
            f"commit_threshold={self.commit_threshold}, "
            f"cache_type={self.cache_type}, "
            f"cache_timeout={self.cache_default_timeout}, "
            f"api_key={'***' if self.api_key else 'None'}"
            f")"
        )

    def summary(self) -> str:
        """
        Human-readable configuration summary

        Returns:
            str: Multi-line configuration summary
        """
        return f"""
Research Monitor Configuration:

Server:
  Port: {self.port}
  API Key: {'Configured' if self.api_key else 'Not configured (warning)'}

Database:
  Path: {self.db_path}

Filesystem Paths:
  Events: {self.events_path}
  Priorities: {self.priorities_path}
  Validation Logs: {self.validation_logs_path}

Commit Orchestration:
  Threshold: {self.commit_threshold} events

Cache:
  Type: {self.cache_type}
  Default Timeout: {self.cache_default_timeout}s
  Max Items: {self.cache_threshold}
"""


# Singleton instance for application-wide use
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get or create singleton Config instance

    Returns:
        Config: Application configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reset_config():
    """Reset singleton config instance (useful for testing)"""
    global _config_instance
    _config_instance = None


class GitConfig:
    """Git service configuration for multi-tenant timeline repository management"""

    # Timeline Repository Configuration
    TIMELINE_REPO_URL = os.environ.get(
        'TIMELINE_REPO_URL',
        'https://github.com/user/kleptocracy-timeline'  # Default placeholder
    )
    TIMELINE_BRANCH = os.environ.get('TIMELINE_BRANCH', 'main')
    TIMELINE_WORKSPACE = Path(os.environ.get(
        'TIMELINE_WORKSPACE',
        '/tmp/timeline-workspace'
    ))

    # GitHub Integration
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # Required for PR creation
    GITHUB_API_URL = 'https://api.github.com'

    # Sync Settings
    AUTO_PULL_ON_START = os.environ.get('AUTO_PULL_ON_START', 'true').lower() == 'true'
    PR_AUTO_BRANCH_PREFIX = os.environ.get('PR_BRANCH_PREFIX', 'research-batch')

    # Multi-tenant Support
    WORKSPACE_ISOLATION = True  # Each repo gets own workspace

    @classmethod
    def get_repo_name(cls) -> str:
        """Extract repository name from URL"""
        if not cls.TIMELINE_REPO_URL:
            return 'unknown'
        # Extract last part of URL (e.g., 'kleptocracy-timeline' from full URL)
        return cls.TIMELINE_REPO_URL.rstrip('/').split('/')[-1]

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        if not cls.TIMELINE_REPO_URL:
            return False
        # NOTE: Validation against Config.DEBUG removed since we're using different Config class
        # In production, GitHub token should be set for PR creation
        return True