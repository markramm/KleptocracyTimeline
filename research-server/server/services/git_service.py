"""
Git Service - Core Git operations for timeline repository management.

Provides repository-agnostic Git operations supporting multi-tenant architecture.
"""

import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, cast
from datetime import datetime, timezone

from server.config import GitConfig


class GitService:
    """
    Core Git operations for timeline repository management.
    Repository-agnostic, supports any timeline repo.
    """

    def __init__(self, config: Optional[GitConfig] = None):
        """
        Initialize GitService.

        Args:
            config: GitConfig instance (uses default if None)
        """
        self.config = config or GitConfig()
        self.repo_url = self.config.TIMELINE_REPO_URL
        self.branch = self.config.TIMELINE_BRANCH
        self.workspace = self._get_workspace()
        self.github_token = self.config.GITHUB_TOKEN

    # === Core Operations ===

    def clone_or_update(self) -> Dict[str, Any]:
        """
        Clone repository if not present, otherwise pull latest.

        Returns:
            Dict with success status and details
        """
        if self.workspace.exists() and (self.workspace / '.git').exists():
            return self.pull_latest()
        else:
            return self._clone_repo()

    def _clone_repo(self) -> Dict[str, Any]:
        """Clone the repository."""
        try:
            self.workspace.parent.mkdir(parents=True, exist_ok=True)

            cmd = ['git', 'clone', '--branch', self.branch, self.repo_url, str(self.workspace)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return {
                'success': True,
                'action': 'clone',
                'message': f'Cloned {self.repo_url} (branch: {self.branch})',
                'workspace': str(self.workspace)
            }
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'action': 'clone',
                'error': e.stderr,
                'workspace': str(self.workspace)
            }

    def pull_latest(self) -> Dict[str, Any]:
        """
        Pull latest changes from configured branch.

        Returns:
            Dict with success, new_commits, files_changed, conflicts
        """
        if not self._is_git_repo():
            return {
                'success': False,
                'error': 'Not a git repository',
                'workspace': str(self.workspace)
            }

        try:
            # Get current commit before pull
            before_commit = self._get_current_commit()

            # Pull latest changes
            cmd = ['git', '-C', str(self.workspace), 'pull', 'origin', self.branch]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Get commit after pull
            after_commit = self._get_current_commit()

            # Check for conflicts
            conflicts = self._check_conflicts()

            # Count new commits
            new_commits = 0
            if before_commit and after_commit and before_commit != after_commit:
                new_commits = self._count_commits_between(before_commit, after_commit)

            # Get changed files
            files_changed = []
            if before_commit and after_commit and before_commit != after_commit:
                files_changed = self._get_changed_files_between(before_commit, after_commit)

            return {
                'success': True,
                'new_commits': new_commits,
                'files_changed': files_changed,
                'conflicts': conflicts,
                'before_commit': before_commit,
                'after_commit': after_commit
            }
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': e.stderr,
                'workspace': str(self.workspace)
            }

    def create_branch(self, branch_name: str) -> bool:
        """
        Create new branch from current HEAD.

        Args:
            branch_name: Name of branch to create

        Returns:
            True if successful, False otherwise
        """
        if not self._is_git_repo():
            return False

        try:
            cmd = ['git', '-C', str(self.workspace), 'checkout', '-b', branch_name]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def commit_changes(self, message: str, files: List[Path]) -> Optional[str]:
        """
        Commit specified files.

        Args:
            message: Commit message
            files: List of file paths to commit (relative to workspace)

        Returns:
            Commit hash if successful, None otherwise
        """
        if not self._is_git_repo():
            return None

        try:
            # Add files
            for file_path in files:
                cmd = ['git', '-C', str(self.workspace), 'add', str(file_path)]
                subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Commit
            cmd = ['git', '-C', str(self.workspace), 'commit', '-m', message]
            subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Get commit hash
            return self._get_current_commit()
        except subprocess.CalledProcessError:
            return None

    def push_branch(self, branch_name: str) -> bool:
        """
        Push branch to remote.

        Args:
            branch_name: Name of branch to push

        Returns:
            True if successful, False otherwise
        """
        if not self._is_git_repo():
            return False

        try:
            cmd = ['git', '-C', str(self.workspace), 'push', '-u', 'origin', branch_name]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    # === Repository Information ===

    def get_status(self) -> Dict[str, Any]:
        """
        Get current repository status.

        Returns:
            Dict with repo_url, current_branch, last_sync, commits_behind, local_changes
        """
        if not self._is_git_repo():
            return {
                'exists': False,
                'repo_url': self.repo_url,
                'workspace': str(self.workspace)
            }

        try:
            current_branch = self._get_current_branch()
            commits_behind = self._get_commits_behind()
            local_changes = self._count_local_changes()

            return {
                'exists': True,
                'repo_url': self.repo_url,
                'current_branch': current_branch,
                'target_branch': self.branch,
                'commits_behind': commits_behind,
                'local_changes': local_changes,
                'workspace': str(self.workspace),
                'last_sync': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'exists': True,
                'error': str(e),
                'workspace': str(self.workspace)
            }

    def get_changed_files(self, since_commit: Optional[str] = None) -> List[str]:
        """
        Get list of changed files since commit.

        Args:
            since_commit: Commit hash to compare from (None = all uncommitted changes)

        Returns:
            List of changed file paths
        """
        if not self._is_git_repo():
            return []

        try:
            if since_commit:
                cmd = ['git', '-C', str(self.workspace), 'diff', '--name-only', since_commit]
            else:
                cmd = ['git', '-C', str(self.workspace), 'status', '--short']

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if since_commit:
                return result.stdout.strip().split('\n') if result.stdout.strip() else []
            else:
                # Parse status output (format: "XY filename")
                lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                return [line.split(maxsplit=1)[1] if len(line.split(maxsplit=1)) > 1 else line for line in lines if line]
        except subprocess.CalledProcessError:
            return []

    # === Helper Methods ===

    def _get_workspace(self) -> Path:
        """Get workspace path, isolated per repo if multi-tenant."""
        if self.config.WORKSPACE_ISOLATION:
            # Create unique workspace per repo URL
            repo_hash = hashlib.md5(self.repo_url.encode()).hexdigest()[:8]
            return cast(Path, self.config.TIMELINE_WORKSPACE) / repo_hash
        return cast(Path, self.config.TIMELINE_WORKSPACE)

    def _is_git_repo(self) -> bool:
        """Check if workspace is a git repository."""
        return self.workspace.exists() and (self.workspace / '.git').exists()

    def _get_current_commit(self) -> Optional[str]:
        """Get current commit hash."""
        try:
            cmd = ['git', '-C', str(self.workspace), 'rev-parse', 'HEAD']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def _get_current_branch(self) -> Optional[str]:
        """Get current branch name."""
        try:
            cmd = ['git', '-C', str(self.workspace), 'branch', '--show-current']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def _check_conflicts(self) -> List[str]:
        """Check for merge conflicts."""
        try:
            cmd = ['git', '-C', str(self.workspace), 'diff', '--name-only', '--diff-filter=U']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            conflicts = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return conflicts
        except subprocess.CalledProcessError:
            return []

    def _count_commits_between(self, commit1: str, commit2: str) -> int:
        """Count commits between two commit hashes."""
        try:
            cmd = ['git', '-C', str(self.workspace), 'rev-list', '--count', f'{commit1}..{commit2}']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return 0

    def _get_changed_files_between(self, commit1: str, commit2: str) -> List[str]:
        """Get files changed between two commits."""
        try:
            cmd = ['git', '-C', str(self.workspace), 'diff', '--name-only', commit1, commit2]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []

    def _get_commits_behind(self) -> int:
        """Get number of commits behind remote."""
        try:
            # Fetch remote
            cmd = ['git', '-C', str(self.workspace), 'fetch', 'origin', self.branch]
            subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Count commits
            cmd = ['git', '-C', str(self.workspace), 'rev-list', '--count', f'HEAD..origin/{self.branch}']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return 0

    def _count_local_changes(self) -> int:
        """Count number of local uncommitted changes."""
        try:
            cmd = ['git', '-C', str(self.workspace), 'status', '--short']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return len([l for l in lines if l])
        except subprocess.CalledProcessError:
            return 0
