"""
Application configuration with multi-tenant support.

Supports configuring which timeline repository to work with via environment variables.
"""

import os
from pathlib import Path


class Config:
    """Application configuration settings"""

    # Base paths
    BASE_DIR = Path(__file__).parent.parent.parent
    TIMELINE_DIR = BASE_DIR / 'timeline_data' / 'events'

    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///unified_research.db')

    # Server
    API_KEY = os.environ.get('RESEARCH_MONITOR_API_KEY', None)
    PORT = int(os.environ.get('RESEARCH_MONITOR_PORT', 5558))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Sync settings (legacy - will be replaced by git service)
    SYNC_INTERVAL = 30  # seconds
    COMMIT_THRESHOLD = 10  # events


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
        if not cls.GITHUB_TOKEN and not Config.DEBUG:
            # GitHub token required in production for PR creation
            return False
        return True
