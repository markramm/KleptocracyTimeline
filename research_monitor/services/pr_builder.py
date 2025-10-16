"""
PR Builder Service - Creates GitHub Pull Requests for validated events.

Replaces manual git commands and orchestration with programmatic PR creation.
"""

import requests
from typing import Dict, Any, List, Optional, cast
from datetime import datetime, timezone

from research_monitor.services.git_service import GitService
from research_monitor.services.timeline_sync import TimelineSyncService


class PRBuilderService:
    """
    Creates GitHub Pull Requests for validated events.
    Replaces: Manual git commands and orchestration
    """

    def __init__(self, git_service: GitService, sync_service: TimelineSyncService):
        """
        Initialize PRBuilderService.

        Args:
            git_service: GitService instance for git operations
            sync_service: TimelineSyncService for file preparation
        """
        self.git = git_service
        self.sync = sync_service
        self.github_token = git_service.github_token

    def create_pr(self,
                  events: List[Dict[str, Any]],
                  title: Optional[str] = None,
                  description: Optional[str] = None,
                  branch_prefix: str = 'research-batch') -> Dict[str, Any]:
        """
        Create Pull Request with validated events.

        Args:
            events: Events to include in PR
            title: PR title (auto-generated if None)
            description: PR description (auto-generated if None)
            branch_prefix: Prefix for branch name

        Returns:
            Dict with: {
                'success': bool,
                'pr_url': str,
                'pr_number': int,
                'branch': str,
                'events_count': int,
                'commit_hash': str
            }
        """
        if not events:
            return {
                'success': False,
                'error': 'No events to export'
            }

        try:
            # 1. Create branch
            branch_name = self._generate_branch_name(len(events), branch_prefix)
            if not self.git.create_branch(branch_name):
                return {
                    'success': False,
                    'error': f'Failed to create branch: {branch_name}'
                }

            # 2. Write events to files
            files = self.sync.prepare_export_files(events)
            if not files:
                return {
                    'success': False,
                    'error': 'No files written'
                }

            # 3. Commit changes
            commit_msg = self._generate_commit_message(events)
            commit_hash = self.git.commit_changes(commit_msg, files)
            if not commit_hash:
                return {
                    'success': False,
                    'error': 'Commit failed'
                }

            # 4. Push branch
            if not self.git.push_branch(branch_name):
                return {
                    'success': False,
                    'error': f'Failed to push branch: {branch_name}'
                }

            # 5. Create PR via GitHub API
            pr_title = title or self._generate_pr_title(events)
            pr_description = description or self._generate_pr_description(events)

            pr_data = self._create_github_pr(
                branch=branch_name,
                title=pr_title,
                description=pr_description
            )

            if not pr_data:
                return {
                    'success': False,
                    'error': 'Failed to create PR via GitHub API'
                }

            return {
                'success': True,
                'pr_url': pr_data['html_url'],
                'pr_number': pr_data['number'],
                'branch': branch_name,
                'events_count': len(events),
                'commit_hash': commit_hash
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _create_github_pr(self, branch: str, title: str, description: str) -> Optional[Dict[str, Any]]:
        """
        Create PR using GitHub API.

        Args:
            branch: Head branch name
            title: PR title
            description: PR body

        Returns:
            PR data from GitHub API or None if failed
        """
        if not self.github_token:
            return None

        # Extract owner/repo from git URL
        repo_path = self._get_repo_path()
        if not repo_path:
            return None

        url = f"https://api.github.com/repos/{repo_path}/pulls"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        data = {
            'title': title,
            'body': description,
            'head': branch,
            'base': self.git.branch
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.RequestException:
            return None

    def _get_repo_path(self) -> Optional[str]:
        """
        Extract owner/repo from git URL.

        Returns:
            String like 'owner/repo' or None
        """
        url = self.git.repo_url

        # Handle https://github.com/owner/repo.git
        if 'github.com' in url:
            parts = url.rstrip('/').rstrip('.git').split('/')
            if len(parts) >= 2:
                return f"{parts[-2]}/{parts[-1]}"

        return None

    def _generate_branch_name(self, event_count: int, prefix: str) -> str:
        """Generate branch name for PR."""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
        return f"{prefix}-{event_count}-events-{timestamp}"

    def _generate_commit_message(self, events: List[Dict[str, Any]]) -> str:
        """Generate commit message for events."""
        count = len(events)
        date_range = self._get_date_range(events)

        lines = [
            f"Add {count} researched timeline event{'s' if count > 1 else ''}",
            "",
            f"Date range: {date_range}",
            f"Events: {count}",
            ""
        ]

        # List first 5 events
        for event in events[:5]:
            event_id = event.get('id', 'unknown')
            title = event.get('title', 'No title')[:60]
            lines.append(f"- {event_id}: {title}")

        if len(events) > 5:
            lines.append(f"- ... and {len(events) - 5} more events")

        return "\n".join(lines)

    def _generate_pr_title(self, events: List[Dict[str, Any]]) -> str:
        """Auto-generate PR title from events."""
        count = len(events)
        date_range = self._get_date_range(events)
        return f"Add {count} researched events ({date_range})"

    def _generate_pr_description(self, events: List[Dict[str, Any]]) -> str:
        """Auto-generate PR description with event summary."""
        lines = [
            "## Research Batch Summary",
            "",
            f"**Events**: {len(events)}",
            f"**Date Range**: {self._get_date_range(events)}",
            ""
        ]

        # Calculate statistics
        avg_importance = self._avg_importance(events)
        total_sources = sum(len(e.get('sources', [])) for e in events)

        lines.extend([
            "### Statistics",
            f"- Average Importance: {avg_importance:.1f}/10",
            f"- Total Sources: {total_sources}",
            f"- Sources per Event: {total_sources / len(events):.1f}",
            ""
        ])

        # List events
        lines.extend([
            "### Events Added",
            ""
        ])

        for event in sorted(events, key=lambda e: e.get('date', '')):
            event_date = event.get('date', 'Unknown date')
            title = event.get('title', 'No title')
            importance = event.get('importance', '?')
            lines.append(f"- `{event_date}` - {title} (importance: {importance}/10)")

        lines.extend([
            "",
            "### Quality Assurance",
            "- All events validated by QA system",
            "- Required fields verified",
            "- Source quality checked",
            "",
            "🤖 Generated by Timeline Research Tools"
        ])

        return "\n".join(lines)

    def _get_date_range(self, events: List[Dict[str, Any]]) -> str:
        """Get date range string for events."""
        dates: List[str] = [str(e.get('date')) for e in events if e.get('date')]
        if not dates:
            return "Unknown"

        dates.sort()
        if len(dates) == 1:
            return dates[0]
        elif dates[0] == dates[-1]:
            return dates[0]
        else:
            return f"{dates[0]} to {dates[-1]}"

    def _avg_importance(self, events: List[Dict[str, Any]]) -> float:
        """Calculate average importance score."""
        importances: List[float] = [float(e.get('importance', 0)) for e in events if e.get('importance')]
        if not importances:
            return 0.0
        return sum(importances) / len(importances)

    def validate_github_config(self) -> Dict[str, Any]:
        """
        Validate GitHub configuration.

        Returns:
            Dict with validation results
        """
        issues = []

        if not self.github_token:
            issues.append("GitHub token not configured (GITHUB_TOKEN environment variable)")

        repo_path = self._get_repo_path()
        if not repo_path:
            issues.append(f"Invalid repository URL: {self.git.repo_url}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'repo_path': repo_path,
            'has_token': bool(self.github_token)
        }
