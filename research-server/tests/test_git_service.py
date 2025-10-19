#!/usr/bin/env python3
"""
Tests for GitService.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from research_monitor.services.git_service import GitService
from research_monitor.core.config import GitConfig


class TestGitService(unittest.TestCase):
    """Test GitService core operations"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = GitConfig()
        self.config.TIMELINE_REPO_URL = 'https://github.com/test/test-timeline'
        self.config.TIMELINE_BRANCH = 'main'
        self.config.TIMELINE_WORKSPACE = self.temp_dir
        self.service = GitService(self.config)

    def tearDown(self):
        """Clean up temp directory"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_init_creates_workspace_path(self):
        """Test that GitService initializes with correct workspace"""
        self.assertIsNotNone(self.service.workspace)
        self.assertTrue(str(self.service.workspace).startswith(str(self.temp_dir)))

    def test_workspace_isolation(self):
        """Test that workspace isolation creates unique paths"""
        service1 = GitService(self.config)

        config2 = GitConfig()
        config2.TIMELINE_REPO_URL = 'https://github.com/other/other-timeline'
        config2.TIMELINE_WORKSPACE = self.temp_dir
        service2 = GitService(config2)

        # Different repos should get different workspace paths
        self.assertNotEqual(service1.workspace, service2.workspace)

    @patch('subprocess.run')
    def test_clone_repo_success(self, mock_run):
        """Test successful repository clone"""
        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

        result = self.service._clone_repo()

        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'clone')
        self.assertIn('Cloned', result['message'])
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_clone_repo_failure(self, mock_run):
        """Test failed repository clone"""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, 'git', stderr='Repository not found')

        result = self.service._clone_repo()

        self.assertFalse(result['success'])
        self.assertIn('error', result)

    def test_is_git_repo_false_when_no_git_dir(self):
        """Test _is_git_repo returns False when .git doesn't exist"""
        self.assertFalse(self.service._is_git_repo())

    def test_is_git_repo_true_when_git_dir_exists(self):
        """Test _is_git_repo returns True when .git exists"""
        # Create fake git repo
        self.service.workspace.mkdir(parents=True, exist_ok=True)
        (self.service.workspace / '.git').mkdir()

        self.assertTrue(self.service._is_git_repo())

    @patch('subprocess.run')
    def test_get_current_commit(self, mock_run):
        """Test getting current commit hash"""
        # Create fake git repo
        self.service.workspace.mkdir(parents=True, exist_ok=True)
        (self.service.workspace / '.git').mkdir()

        mock_run.return_value = Mock(
            returncode=0,
            stdout='abc123def456\n',
            stderr=''
        )

        commit = self.service._get_current_commit()

        self.assertEqual(commit, 'abc123def456')
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_get_current_branch(self, mock_run):
        """Test getting current branch name"""
        # Create fake git repo
        self.service.workspace.mkdir(parents=True, exist_ok=True)
        (self.service.workspace / '.git').mkdir()

        mock_run.return_value = Mock(
            returncode=0,
            stdout='main\n',
            stderr=''
        )

        branch = self.service._get_current_branch()

        self.assertEqual(branch, 'main')

    @patch('subprocess.run')
    def test_create_branch_success(self, mock_run):
        """Test creating a new branch"""
        # Create fake git repo
        self.service.workspace.mkdir(parents=True, exist_ok=True)
        (self.service.workspace / '.git').mkdir()

        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

        result = self.service.create_branch('test-branch')

        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_commit_changes_success(self, mock_run):
        """Test committing changes"""
        # Create fake git repo
        self.service.workspace.mkdir(parents=True, exist_ok=True)
        (self.service.workspace / '.git').mkdir()

        # Mock git add and git commit
        mock_run.side_effect = [
            Mock(returncode=0),  # git add
            Mock(returncode=0),  # git commit
            Mock(returncode=0, stdout='abc123\n')  # git rev-parse
        ]

        files = [Path('test.json')]
        commit_hash = self.service.commit_changes('Test commit', files)

        self.assertEqual(commit_hash, 'abc123')
        self.assertEqual(mock_run.call_count, 3)

    @patch('subprocess.run')
    def test_push_branch_success(self, mock_run):
        """Test pushing branch to remote"""
        # Create fake git repo
        self.service.workspace.mkdir(parents=True, exist_ok=True)
        (self.service.workspace / '.git').mkdir()

        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

        result = self.service.push_branch('test-branch')

        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_get_status_when_repo_exists(self, mock_run):
        """Test get_status for existing repository"""
        # Create fake git repo
        self.service.workspace.mkdir(parents=True, exist_ok=True)
        (self.service.workspace / '.git').mkdir()

        # Mock git commands
        mock_run.side_effect = [
            Mock(returncode=0, stdout='main\n'),  # current branch
            Mock(returncode=0),  # fetch
            Mock(returncode=0, stdout='0\n'),  # commits behind
            Mock(returncode=0, stdout='')  # local changes
        ]

        status = self.service.get_status()

        self.assertTrue(status['exists'])
        self.assertEqual(status['current_branch'], 'main')
        self.assertEqual(status['commits_behind'], 0)
        self.assertEqual(status['local_changes'], 0)

    def test_get_status_when_repo_not_exists(self):
        """Test get_status when repository doesn't exist"""
        status = self.service.get_status()

        self.assertFalse(status['exists'])
        self.assertIn('repo_url', status)
        self.assertIn('workspace', status)

    @patch('subprocess.run')
    def test_pull_latest_success(self, mock_run):
        """Test pulling latest changes"""
        # Create fake git repo
        self.service.workspace.mkdir(parents=True, exist_ok=True)
        (self.service.workspace / '.git').mkdir()

        # Mock git commands
        before_commit = 'abc123'
        after_commit = 'def456'

        mock_run.side_effect = [
            Mock(returncode=0, stdout=f'{before_commit}\n'),  # before commit
            Mock(returncode=0),  # git pull
            Mock(returncode=0, stdout=f'{after_commit}\n'),  # after commit
            Mock(returncode=0, stdout=''),  # check conflicts
            Mock(returncode=0, stdout='2\n'),  # count commits
            Mock(returncode=0, stdout='file1.json\nfile2.json\n')  # changed files
        ]

        result = self.service.pull_latest()

        self.assertTrue(result['success'])
        self.assertEqual(result['new_commits'], 2)
        self.assertEqual(len(result['files_changed']), 2)
        self.assertEqual(result['before_commit'], before_commit)
        self.assertEqual(result['after_commit'], after_commit)

    @patch('subprocess.run')
    def test_pull_latest_no_changes(self, mock_run):
        """Test pulling when already up to date"""
        # Create fake git repo
        self.service.workspace.mkdir(parents=True, exist_ok=True)
        (self.service.workspace / '.git').mkdir()

        commit = 'abc123'

        mock_run.side_effect = [
            Mock(returncode=0, stdout=f'{commit}\n'),  # before commit
            Mock(returncode=0),  # git pull
            Mock(returncode=0, stdout=f'{commit}\n'),  # after commit (same)
            Mock(returncode=0, stdout='')  # check conflicts
        ]

        result = self.service.pull_latest()

        self.assertTrue(result['success'])
        self.assertEqual(result['new_commits'], 0)
        self.assertEqual(len(result['files_changed']), 0)

    @patch('subprocess.run')
    def test_get_changed_files_uncommitted(self, mock_run):
        """Test getting uncommitted changes"""
        # Create fake git repo
        self.service.workspace.mkdir(parents=True, exist_ok=True)
        (self.service.workspace / '.git').mkdir()

        mock_run.return_value = Mock(
            returncode=0,
            stdout=' M file1.json\n A file2.json\n'
        )

        files = self.service.get_changed_files()

        self.assertEqual(len(files), 2)
        self.assertIn('file1.json', files)
        self.assertIn('file2.json', files)


class TestGitServiceWorkspaceIsolation(unittest.TestCase):
    """Test workspace isolation for multi-tenant scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up temp directory"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_different_repos_get_different_workspaces(self):
        """Test that different repositories get isolated workspaces"""
        config1 = GitConfig()
        config1.TIMELINE_REPO_URL = 'https://github.com/user1/timeline1'
        config1.TIMELINE_WORKSPACE = self.temp_dir
        config1.WORKSPACE_ISOLATION = True

        config2 = GitConfig()
        config2.TIMELINE_REPO_URL = 'https://github.com/user2/timeline2'
        config2.TIMELINE_WORKSPACE = self.temp_dir
        config2.WORKSPACE_ISOLATION = True

        service1 = GitService(config1)
        service2 = GitService(config2)

        # Should have different workspace paths
        self.assertNotEqual(service1.workspace, service2.workspace)

        # Both should be under temp_dir
        self.assertTrue(str(service1.workspace).startswith(str(self.temp_dir)))
        self.assertTrue(str(service2.workspace).startswith(str(self.temp_dir)))

    def test_same_repo_gets_same_workspace(self):
        """Test that same repository gets same workspace"""
        config1 = GitConfig()
        config1.TIMELINE_REPO_URL = 'https://github.com/user/timeline'
        config1.TIMELINE_WORKSPACE = self.temp_dir
        config1.WORKSPACE_ISOLATION = True

        config2 = GitConfig()
        config2.TIMELINE_REPO_URL = 'https://github.com/user/timeline'
        config2.TIMELINE_WORKSPACE = self.temp_dir
        config2.WORKSPACE_ISOLATION = True

        service1 = GitService(config1)
        service2 = GitService(config2)

        # Should have same workspace path
        self.assertEqual(service1.workspace, service2.workspace)


if __name__ == '__main__':
    unittest.main()
