#!/usr/bin/env python3
"""
Tests for git configuration module.
"""

import os
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

from config import GitConfig


# NOTE: TestConfig class removed - tested deprecated core.config.Config class
# The new Config class in server/config.py is instance-based and tested elsewhere


class TestGitConfig(unittest.TestCase):
    """Test git service configuration"""

    def setUp(self):
        """Save original environment"""
        self.orig_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.orig_env)

    def test_default_branch(self):
        """Test default branch is 'main'"""
        self.assertEqual(GitConfig.TIMELINE_BRANCH, 'main')

    def test_default_workspace(self):
        """Test default workspace path"""
        self.assertEqual(GitConfig.TIMELINE_WORKSPACE, Path('/tmp/timeline-workspace'))

    def test_workspace_isolation_enabled(self):
        """Test workspace isolation is enabled by default"""
        self.assertTrue(GitConfig.WORKSPACE_ISOLATION)

    def test_auto_pull_enabled_by_default(self):
        """Test auto pull is enabled by default"""
        self.assertTrue(GitConfig.AUTO_PULL_ON_START)

    def test_get_repo_name_from_url(self):
        """Test extracting repository name from URL"""
        os.environ['TIMELINE_REPO_URL'] = 'https://github.com/user/my-timeline'
        # Need to reload GitConfig to pick up new env var
        from importlib import reload
        import config
        reload(config)

        repo_name = config.GitConfig.get_repo_name()
        self.assertEqual(repo_name, 'my-timeline')

    def test_validate_requires_repo_url(self):
        """Test validation fails without repo URL"""
        os.environ.pop('TIMELINE_REPO_URL', None)
        from importlib import reload
        import config
        reload(config)

        self.assertFalse(config.GitConfig.validate())

    def test_pr_branch_prefix(self):
        """Test PR branch prefix default"""
        self.assertEqual(GitConfig.PR_AUTO_BRANCH_PREFIX, 'research-batch')


class TestMultiTenantConfiguration(unittest.TestCase):
    """Test multi-tenant configuration scenarios"""

    def setUp(self):
        """Save original environment"""
        self.orig_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.orig_env)

    def test_configure_alternative_repo(self):
        """Test configuring alternative timeline repository"""
        os.environ['TIMELINE_REPO_URL'] = 'https://github.com/alice/fork-timeline'
        os.environ['TIMELINE_BRANCH'] = 'develop'

        from importlib import reload
        import config
        reload(config)

        self.assertEqual(config.GitConfig.TIMELINE_REPO_URL,
                        'https://github.com/alice/fork-timeline')
        self.assertEqual(config.GitConfig.TIMELINE_BRANCH, 'develop')

    def test_configure_custom_workspace(self):
        """Test configuring custom workspace path"""
        os.environ['TIMELINE_WORKSPACE'] = '/custom/workspace'

        from importlib import reload
        import config
        reload(config)

        self.assertEqual(config.GitConfig.TIMELINE_WORKSPACE, Path('/custom/workspace'))


if __name__ == '__main__':
    unittest.main()
