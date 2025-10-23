#!/usr/bin/env python3
"""
Git Syncer - Replaces FilesystemSyncer with git-based sync

Syncs timeline events from git repository on demand:
- On startup
- On manual trigger (POST /api/sync)
- No background polling thread

Markdown only - all events are Hugo-style .md files with YAML frontmatter
"""

import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from services.git_service import GitService
from parsers.factory import EventParserFactory
from models import TimelineEvent, ActivityLog
from utils.event_normalizer import EventNormalizer

logger = logging.getLogger(__name__)


class GitSyncer:
    """
    Git-based event syncer - replaces FilesystemSyncer

    Key differences from FilesystemSyncer:
    - Syncs from git repository (not local filesystem)
    - On-demand sync (no 30-second polling)
    - Markdown only (no JSON support)
    - Git aware (pulls latest changes)
    """

    def __init__(self, app, session_factory, git_service: Optional[GitService] = None):
        """
        Initialize GitSyncer

        Args:
            app: Flask app instance (for config)
            session_factory: SQLAlchemy session factory
            git_service: GitService instance (creates default if None)
        """
        self.app = app
        self.Session = session_factory
        self.git_service = git_service or GitService()
        self.parser_factory = EventParserFactory()
        self.normalizer = EventNormalizer()

    def sync_from_git(self, pull_first: bool = True) -> Dict[str, Any]:
        """
        Sync events from git repository to database

        Args:
            pull_first: If True, git pull before syncing (default: True)

        Returns:
            Dict with sync statistics:
            {
                'success': bool,
                'events_synced': int,
                'events_added': int,
                'events_updated': int,
                'events_unchanged': int,
                'errors': List[str],
                'git_pull': dict
            }
        """
        stats = {
            'success': False,
            'events_synced': 0,
            'events_added': 0,
            'events_updated': 0,
            'events_unchanged': 0,
            'errors': [],
            'git_pull': None
        }

        db = self.Session()
        try:
            # Ensure repository is cloned/updated
            if pull_first:
                logger.info("Git sync: Pulling latest changes...")
                pull_result = self.git_service.clone_or_update()
                stats['git_pull'] = pull_result

                if not pull_result.get('success'):
                    error_msg = f"Git operation failed: {pull_result.get('error', 'Unknown error')}"
                    stats['errors'].append(error_msg)
                    logger.error(error_msg)
                    return stats

                action = pull_result.get('action', 'unknown')
                if action == 'clone':
                    logger.info(f"Cloned repository to {pull_result.get('workspace')}")
                elif action == 'pull':
                    new_commits = pull_result.get('new_commits', 0)
                    logger.info(f"Pulled {new_commits} new commits")

            # Get events directory from git workspace
            events_path = self.git_service.workspace / 'timeline' / 'data' / 'events'

            if not events_path.exists():
                error_msg = f"Events directory not found: {events_path}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)
                return stats

            # Sync all markdown events
            logger.info(f"Syncing events from {events_path}")

            for event_file in events_path.glob('*.md'):
                try:
                    # Skip README and other non-event files
                    if event_file.name.upper() in ('README.MD', 'INDEX.MD', '_INDEX.MD'):
                        logger.debug(f"Skipping {event_file.name}")
                        continue

                    result = self._sync_event_file(db, event_file)

                    if result == 'added':
                        stats['events_added'] += 1
                    elif result == 'updated':
                        stats['events_updated'] += 1
                    elif result == 'unchanged':
                        stats['events_unchanged'] += 1

                    stats['events_synced'] += 1

                except Exception as e:
                    error_msg = f"Error syncing {event_file.name}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)

            # Commit database changes
            db.commit()

            # Log activity
            activity = ActivityLog(
                action='git_sync',
                agent='system',
                details={
                    'events_added': stats['events_added'],
                    'events_updated': stats['events_updated'],
                    'events_unchanged': stats['events_unchanged'],
                    'total': stats['events_synced']
                }
            )
            db.add(activity)
            db.commit()

            stats['success'] = True
            logger.info(
                f"Git sync complete: +{stats['events_added']} "
                f"~{stats['events_updated']} "
                f"={stats['events_unchanged']} "
                f"(total: {stats['events_synced']})"
            )

        except Exception as e:
            error_msg = f"Git sync error: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            db.rollback()
        finally:
            db.close()

        return stats

    def _sync_event_file(self, db: Session, event_file: Path) -> str:
        """
        Sync single event file to database

        Args:
            db: Database session
            event_file: Path to event markdown file

        Returns:
            'added', 'updated', or 'unchanged'
        """
        # Calculate file hash for change detection
        with open(event_file, 'rb') as f:
            file_content = f.read()
            file_hash = hashlib.md5(file_content).hexdigest()

        # Extract event ID from filename (without .md extension)
        event_id = event_file.stem

        # Check if exists in database
        existing = db.query(TimelineEvent).filter_by(id=event_id).first()

        # If exists and hash unchanged, skip
        if existing and existing.file_hash == file_hash:
            logger.debug(f"Unchanged: {event_id}")
            return 'unchanged'

        # Parse event (Markdown with YAML frontmatter)
        try:
            data = self.parser_factory.parse_event(event_file)
        except ValueError as e:
            raise ValueError(f"Parse error in {event_file.name}: {e}")

        # Normalize event data for consistent formatting
        normalized_data = self.normalizer.normalize(data)

        # Create or update event
        if not existing:
            event = TimelineEvent(id=event_id)
            result = 'added'
            logger.info(f"Adding new event: {event_id}")
        else:
            event = existing
            result = 'updated'
            logger.info(f"Updating event: {event_id}")

        # Update fields (same structure as FilesystemSyncer)
        event.json_content = normalized_data
        event.date = normalized_data.get('date', '')
        event.title = normalized_data.get('title', '')
        event.summary = normalized_data.get('summary', '')
        event.importance = normalized_data.get('importance', 5)
        event.status = normalized_data.get('status', 'confirmed')
        event.file_path = str(event_file)
        event.file_hash = file_hash
        event.last_synced = datetime.now()

        if not existing:
            db.add(event)

        return result

    def get_git_status(self) -> Dict[str, Any]:
        """
        Get current git repository status

        Returns:
            Dict with git status information
        """
        try:
            return self.git_service.get_status()
        except Exception as e:
            logger.error(f"Error getting git status: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def clone_or_update_repo(self) -> Dict[str, Any]:
        """
        Ensure git repository is cloned and up to date

        Returns:
            Dict with operation result
        """
        try:
            return self.git_service.clone_or_update()
        except Exception as e:
            logger.error(f"Error cloning/updating repo: {e}")
            return {
                'success': False,
                'error': str(e)
            }
