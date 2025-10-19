#!/usr/bin/env python3
"""
Tests for PRBuilderService.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from research_monitor.services.pr_builder import PRBuilderService
from research_monitor.services.git_service import GitService
from research_monitor.services.timeline_sync import TimelineSyncService


class TestPRBuilderService(unittest.TestCase):
    """Test PRBuilderService operations"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mock services
        self.git_service = Mock(spec=GitService)
        self.git_service.repo_url = 'https://github.com/user/timeline-repo'
        self.git_service.branch = 'main'
        self.git_service.github_token = 'test-token-123'

        self.sync_service = Mock(spec=TimelineSyncService)

        self.pr_builder = PRBuilderService(self.git_service, self.sync_service)

    def test_init_sets_correct_services(self):
        """Test that initialization sets correct services"""
        self.assertEqual(self.pr_builder.git, self.git_service)
        self.assertEqual(self.pr_builder.sync, self.sync_service)
        self.assertEqual(self.pr_builder.github_token, 'test-token-123')

    def test_create_pr_with_no_events(self):
        """Test creating PR with no events fails"""
        result = self.pr_builder.create_pr([])

        self.assertFalse(result['success'])
        self.assertIn('No events', result['error'])

    @patch('research_monitor.services.pr_builder.requests.post')
    def test_create_pr_success(self, mock_post):
        """Test successful PR creation"""
        # Setup test events
        events = [
            {
                'id': '2025-01-01--event1',
                'date': '2025-01-01',
                'title': 'Event 1',
                'importance': 8,
                'sources': [{'url': 'http://example.com'}]
            },
            {
                'id': '2025-01-02--event2',
                'date': '2025-01-02',
                'title': 'Event 2',
                'importance': 7,
                'sources': [{'url': 'http://example.com'}]
            }
        ]

        # Mock git operations
        self.git_service.create_branch.return_value = True
        self.git_service.commit_changes.return_value = 'abc123'
        self.git_service.push_branch.return_value = True

        # Mock file writing
        self.sync_service.prepare_export_files.return_value = [
            Path('timeline_data/events/2025-01-01--event1.json'),
            Path('timeline_data/events/2025-01-02--event2.json')
        ]

        # Mock GitHub API response
        mock_post.return_value = Mock(
            status_code=201,
            json=lambda: {
                'number': 42,
                'html_url': 'https://github.com/user/timeline-repo/pull/42'
            }
        )
        mock_post.return_value.raise_for_status = Mock()

        result = self.pr_builder.create_pr(events)

        self.assertTrue(result['success'])
        self.assertEqual(result['pr_number'], 42)
        self.assertEqual(result['events_count'], 2)
        self.assertIn('github.com', result['pr_url'])
        self.assertEqual(result['commit_hash'], 'abc123')

    def test_create_pr_branch_creation_fails(self):
        """Test PR creation when branch creation fails"""
        events = [{'id': 'event1', 'date': '2025-01-01', 'title': 'Event'}]

        self.git_service.create_branch.return_value = False

        result = self.pr_builder.create_pr(events)

        self.assertFalse(result['success'])
        self.assertIn('branch', result['error'].lower())

    def test_create_pr_no_files_written(self):
        """Test PR creation when file writing fails"""
        events = [{'id': 'event1', 'date': '2025-01-01', 'title': 'Event'}]

        self.git_service.create_branch.return_value = True
        self.sync_service.prepare_export_files.return_value = []

        result = self.pr_builder.create_pr(events)

        self.assertFalse(result['success'])
        self.assertIn('No files', result['error'])

    def test_create_pr_commit_fails(self):
        """Test PR creation when commit fails"""
        events = [{'id': 'event1', 'date': '2025-01-01', 'title': 'Event'}]

        self.git_service.create_branch.return_value = True
        self.sync_service.prepare_export_files.return_value = [Path('event.json')]
        self.git_service.commit_changes.return_value = None

        result = self.pr_builder.create_pr(events)

        self.assertFalse(result['success'])
        self.assertIn('Commit', result['error'])

    def test_create_pr_push_fails(self):
        """Test PR creation when push fails"""
        events = [{'id': 'event1', 'date': '2025-01-01', 'title': 'Event'}]

        self.git_service.create_branch.return_value = True
        self.sync_service.prepare_export_files.return_value = [Path('event.json')]
        self.git_service.commit_changes.return_value = 'abc123'
        self.git_service.push_branch.return_value = False

        result = self.pr_builder.create_pr(events)

        self.assertFalse(result['success'])
        self.assertIn('push', result['error'].lower())

    def test_generate_branch_name(self):
        """Test branch name generation"""
        branch = self.pr_builder._generate_branch_name(5, 'research-batch')

        self.assertIn('research-batch', branch)
        self.assertIn('5-events', branch)
        self.assertIn('-', branch)  # Has timestamp separator

    def test_generate_commit_message(self):
        """Test commit message generation"""
        events = [
            {'id': 'event1', 'date': '2025-01-01', 'title': 'First Event'},
            {'id': 'event2', 'date': '2025-01-02', 'title': 'Second Event'}
        ]

        message = self.pr_builder._generate_commit_message(events)

        self.assertIn('Add 2', message)
        self.assertIn('event1', message)
        self.assertIn('event2', message)
        self.assertIn('2025-01-01 to 2025-01-02', message)

    def test_generate_commit_message_truncates_long_list(self):
        """Test commit message truncates long event lists"""
        events = [
            {'id': f'event{i}', 'date': f'2025-01-{i:02d}', 'title': f'Event {i}'}
            for i in range(1, 11)  # 10 events
        ]

        message = self.pr_builder._generate_commit_message(events)

        self.assertIn('... and 5 more events', message)

    def test_generate_pr_title(self):
        """Test PR title generation"""
        events = [
            {'id': 'event1', 'date': '2025-01-15'},
            {'id': 'event2', 'date': '2025-01-20'}
        ]

        title = self.pr_builder._generate_pr_title(events)

        self.assertIn('Add 2', title)
        self.assertIn('2025-01-15 to 2025-01-20', title)

    def test_generate_pr_description(self):
        """Test PR description generation"""
        events = [
            {
                'id': 'event1',
                'date': '2025-01-01',
                'title': 'Test Event',
                'importance': 8,
                'sources': [{'url': 'http://example.com'}]
            }
        ]

        description = self.pr_builder._generate_pr_description(events)

        self.assertIn('Research Batch Summary', description)
        self.assertIn('**Events**: 1', description)  # Markdown bold
        self.assertIn('Test Event', description)
        self.assertIn('importance: 8/10', description)
        self.assertIn('Timeline Research Tools', description)

    def test_get_date_range_single_date(self):
        """Test date range with single date"""
        events = [{'date': '2025-01-15'}]

        date_range = self.pr_builder._get_date_range(events)

        self.assertEqual(date_range, '2025-01-15')

    def test_get_date_range_multiple_dates(self):
        """Test date range with multiple dates"""
        events = [
            {'date': '2025-01-15'},
            {'date': '2025-01-20'},
            {'date': '2025-01-10'}
        ]

        date_range = self.pr_builder._get_date_range(events)

        self.assertEqual(date_range, '2025-01-10 to 2025-01-20')

    def test_get_date_range_no_dates(self):
        """Test date range with no dates"""
        events = [{'title': 'Event without date'}]

        date_range = self.pr_builder._get_date_range(events)

        self.assertEqual(date_range, 'Unknown')

    def test_avg_importance(self):
        """Test average importance calculation"""
        events = [
            {'importance': 8},
            {'importance': 6},
            {'importance': 10}
        ]

        avg = self.pr_builder._avg_importance(events)

        self.assertEqual(avg, 8.0)

    def test_avg_importance_with_missing_values(self):
        """Test average importance with missing values"""
        events = [
            {'importance': 8},
            {'title': 'Event without importance'},
            {'importance': 6}
        ]

        avg = self.pr_builder._avg_importance(events)

        self.assertEqual(avg, 7.0)

    def test_get_repo_path_from_https_url(self):
        """Test extracting repo path from HTTPS URL"""
        self.git_service.repo_url = 'https://github.com/user/timeline-repo'

        repo_path = self.pr_builder._get_repo_path()

        self.assertEqual(repo_path, 'user/timeline-repo')

    def test_get_repo_path_from_https_url_with_git(self):
        """Test extracting repo path from HTTPS URL with .git"""
        self.git_service.repo_url = 'https://github.com/user/timeline-repo.git'

        repo_path = self.pr_builder._get_repo_path()

        self.assertEqual(repo_path, 'user/timeline-repo')

    def test_validate_github_config_success(self):
        """Test GitHub config validation when valid"""
        result = self.pr_builder.validate_github_config()

        self.assertTrue(result['valid'])
        self.assertEqual(len(result['issues']), 0)
        self.assertEqual(result['repo_path'], 'user/timeline-repo')
        self.assertTrue(result['has_token'])

    def test_validate_github_config_no_token(self):
        """Test GitHub config validation without token"""
        self.git_service.github_token = None
        self.pr_builder.github_token = None

        result = self.pr_builder.validate_github_config()

        self.assertFalse(result['valid'])
        self.assertGreater(len(result['issues']), 0)
        self.assertFalse(result['has_token'])

    def test_validate_github_config_invalid_url(self):
        """Test GitHub config validation with invalid URL"""
        self.git_service.repo_url = 'not-a-valid-url'

        result = self.pr_builder.validate_github_config()

        self.assertFalse(result['valid'])
        self.assertGreater(len(result['issues']), 0)

    @patch('research_monitor.services.pr_builder.requests.post')
    def test_create_github_pr_success(self, mock_post):
        """Test creating PR via GitHub API"""
        mock_post.return_value = Mock(
            status_code=201,
            json=lambda: {
                'number': 42,
                'html_url': 'https://github.com/user/repo/pull/42'
            }
        )
        mock_post.return_value.raise_for_status = Mock()

        pr_data = self.pr_builder._create_github_pr(
            branch='test-branch',
            title='Test PR',
            description='Test description'
        )

        self.assertIsNotNone(pr_data)
        self.assertEqual(pr_data['number'], 42)
        self.assertIn('github.com', pr_data['html_url'])

    @patch('research_monitor.services.pr_builder.requests.post')
    def test_create_github_pr_api_error(self, mock_post):
        """Test creating PR when GitHub API fails"""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        pr_data = self.pr_builder._create_github_pr(
            branch='test-branch',
            title='Test PR',
            description='Test description'
        )

        self.assertIsNone(pr_data)

    def test_create_github_pr_no_token(self):
        """Test creating PR without GitHub token"""
        self.git_service.github_token = None
        self.pr_builder.github_token = None

        pr_data = self.pr_builder._create_github_pr(
            branch='test-branch',
            title='Test PR',
            description='Test description'
        )

        self.assertIsNone(pr_data)


if __name__ == '__main__':
    unittest.main()
