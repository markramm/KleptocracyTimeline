"""
Timeline Sync Service - Coordinates import/export between database and git repository.

Replaces filesystem sync complexity with explicit operations.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from research_monitor.services.git_service import GitService


class TimelineSyncService:
    """
    Coordinates import/export between database and git repository.
    Replaces filesystem sync polling with explicit operations.
    """

    def __init__(self, git_service: GitService, events_dir: Optional[Path] = None):
        """
        Initialize TimelineSyncService.

        Args:
            git_service: GitService instance for git operations
            events_dir: Path to events directory (None = use git workspace)
        """
        self.git = git_service
        self.events_dir = events_dir or (git_service.workspace / 'timeline_data' / 'events')

    # === Import from Git ===

    def import_from_repo(self, force: bool = False) -> Dict[str, Any]:
        """
        Import events from git repository.

        Pulls latest changes and returns information about imported events.
        Does NOT write to database - returns event data for caller to process.

        Args:
            force: Force reimport even if no changes

        Returns:
            Dict with: {
                'pulled': bool,
                'new_commits': int,
                'files_changed': List[str],
                'events': List[Dict],  # Parsed event data
                'errors': List[str]
            }
        """
        result: Dict[str, Any] = {
            'pulled': False,
            'new_commits': 0,
            'files_changed': [],
            'events': [],
            'errors': []
        }

        # Pull latest from repo
        pull_result = self.git.pull_latest()

        if not pull_result['success']:
            result['errors'].append(f"Pull failed: {pull_result.get('error', 'Unknown error')}")
            return result

        result['pulled'] = True
        result['new_commits'] = pull_result['new_commits']
        result['files_changed'] = pull_result['files_changed']

        # Get event files that changed
        event_files = [f for f in pull_result['files_changed']
                      if f.startswith('timeline_data/events/') and f.endswith('.json')]

        # Load each changed event
        for filepath in event_files:
            full_path = self.git.workspace / filepath
            if full_path.exists():
                try:
                    event_data = self._load_event_file(full_path)
                    result['events'].append(event_data)
                except Exception as e:
                    result['errors'].append(f"Error loading {filepath}: {str(e)}")

        return result

    def _load_event_file(self, filepath: Path) -> Dict[str, Any]:
        """Load and parse event JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    # === Export to Git ===

    def prepare_export_files(self, events: List[Dict[str, Any]]) -> List[Path]:
        """
        Write events to workspace for commit.

        Args:
            events: List of event dictionaries to export

        Returns:
            List of file paths written
        """
        written_files = []

        # Ensure events directory exists
        self.events_dir.mkdir(parents=True, exist_ok=True)

        for event in events:
            event_id = event.get('id')
            if not event_id:
                continue

            filename = f"{event_id}.json"
            filepath = self.events_dir / filename

            try:
                # Write event to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(event, f, indent=2, ensure_ascii=False)

                # Track relative path for git commit
                relative_path = filepath.relative_to(self.git.workspace)
                written_files.append(relative_path)
            except Exception:
                # Skip files that can't be written
                continue

        return written_files

    # === Status ===

    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync status.

        Returns:
            Dict with sync information
        """
        git_status = self.git.get_status()

        # Count events in workspace
        events_count = 0
        if self.events_dir.exists():
            events_count = len(list(self.events_dir.glob('*.json')))

        return {
            'git_status': git_status,
            'events_in_workspace': events_count,
            'workspace_path': str(self.git.workspace),
            'events_dir': str(self.events_dir),
            'last_check': datetime.now(timezone.utc).isoformat()
        }

    def list_workspace_events(self) -> List[str]:
        """
        List all event IDs in workspace.

        Returns:
            List of event IDs (filenames without .json extension)
        """
        if not self.events_dir.exists():
            return []

        return [f.stem for f in self.events_dir.glob('*.json')]

    def get_workspace_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single event from workspace by ID.

        Args:
            event_id: Event ID to retrieve

        Returns:
            Event data dict or None if not found
        """
        filepath = self.events_dir / f"{event_id}.json"

        if not filepath.exists():
            return None

        try:
            return self._load_event_file(filepath)
        except Exception:
            return None

    def validate_workspace_events(self) -> Dict[str, Any]:
        """
        Validate all events in workspace.

        Returns:
            Dict with validation statistics
        """
        if not self.events_dir.exists():
            return {
                'valid': 0,
                'invalid': 0,
                'errors': [],
                'total': 0
            }

        valid = 0
        invalid = 0
        errors = []

        for filepath in self.events_dir.glob('*.json'):
            try:
                data = self._load_event_file(filepath)

                # Basic validation - check required fields
                if self._validate_event_basic(data):
                    valid += 1
                else:
                    invalid += 1
                    errors.append(f"{filepath.name}: Missing required fields")
            except json.JSONDecodeError as e:
                invalid += 1
                errors.append(f"{filepath.name}: JSON parse error - {str(e)}")
            except Exception as e:
                invalid += 1
                errors.append(f"{filepath.name}: {str(e)}")

        return {
            'valid': valid,
            'invalid': invalid,
            'errors': errors[:20],  # Limit error list
            'total': valid + invalid
        }

    def _validate_event_basic(self, event: Dict[str, Any]) -> bool:
        """Basic validation check for required fields."""
        required = ['id', 'date', 'title', 'summary']
        return all(field in event and event[field] for field in required)
