#!/usr/bin/env python3
"""
Test suite for Enhanced Timeline Server
"""

import unittest
import json
import sys
import os
from pathlib import Path
import tempfile
import yaml
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the enhanced server
import enhanced_timeline_server as server

class TestEnhancedTimelineServer(unittest.TestCase):
    """Test the enhanced timeline server functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.app = server.app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
        # Create temporary directories for test data
        cls.test_dir = tempfile.mkdtemp()
        cls.timeline_dir = Path(cls.test_dir) / "timeline_data"
        cls.posts_dir = Path(cls.test_dir) / "posts"
        cls.book_dir = Path(cls.test_dir) / "book_vision"
        
        cls.timeline_dir.mkdir()
        cls.posts_dir.mkdir()
        cls.book_dir.mkdir()
        
        # Create subdirectories for posts
        (cls.posts_dir / "tech_frame").mkdir()
        (cls.posts_dir / "expose_frame").mkdir()
        
        # Patch the server paths
        server.TIMELINE_DIR = cls.timeline_dir
        server.POSTS_DIR = cls.posts_dir
        server.BOOK_DIR = cls.book_dir
        
        # Reset cache
        server._cache = {
            'events': None,
            'posts': None,
            'book_chapters': None,
            'last_load': 0
        }
        
        # Create test data
        cls.create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        shutil.rmtree(cls.test_dir)
    
    @classmethod
    def create_test_data(cls):
        """Create test timeline events, posts, and book chapters"""
        
        # Create test timeline events
        events = [
            {
                'id': '2025-01-01--test-event-1',
                'title': 'Test Event 1',
                'date': '2025-01-01',
                'summary': 'First test event',
                'tags': ['test', 'sample'],
                'actors': ['Actor 1', 'Actor 2'],
                'citations': ['https://example.com/1']
            },
            {
                'id': '2025-01-15--test-event-2',
                'title': 'Test Event 2',
                'date': '2025-01-15',
                'summary': 'Second test event with reference',
                'tags': ['test', 'reference'],
                'actors': ['Actor 2', 'Actor 3'],
                'citations': ['https://example.com/2']
            },
            {
                'id': '2025-02-01--test-event-3',
                'title': 'Test Event 3',
                'date': '2025-02-01',
                'summary': 'Third test event',
                'tags': ['sample', 'demo'],
                'actors': ['Actor 1'],
                'citations': ['https://example.com/3']
            }
        ]
        
        for event in events:
            filepath = cls.timeline_dir / f"{event['id']}.yaml"
            with open(filepath, 'w') as f:
                yaml.dump(event, f)
        
        # Create test posts
        post1 = """---
title: Test Post 1
date: 2025-01-10
tags: [analysis, test]
summary: This is a test post
---

# Test Post 1

This post references [[2025-01-01--test-event-1]] and discusses important topics.

It also mentions [[2025-01-15--test-event-2]] in the context of analysis.
"""
        
        post2 = """# Technical Analysis

This is a technical post in the tech_frame category.

It references the timeline event [[2025-02-01--test-event-3]].
"""
        
        with open(cls.posts_dir / "test_post_1.md", 'w') as f:
            f.write(post1)
        
        with open(cls.posts_dir / "tech_frame" / "technical_analysis.md", 'w') as f:
            f.write(post2)
        
        # Create test book chapter
        chapter1 = """---
title: Chapter 1 - Introduction
---

# Chapter 1: Introduction

This chapter introduces the concept and references [[2025-01-01--test-event-1]].

## Background

The timeline shows that [[2025-01-15--test-event-2]] is significant.
"""
        
        with open(cls.book_dir / "chapter_01_introduction.md", 'w') as f:
            f.write(chapter1)
    
    def test_timeline_endpoint(self):
        """Test /api/timeline endpoint"""
        response = self.client.get('/api/timeline')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('events', data)
        self.assertIn('total', data)
        self.assertEqual(data['total'], 3)
        
        # Check event structure
        event = data['events'][0]
        self.assertIn('id', event)
        self.assertIn('title', event)
        self.assertIn('date', event)
        self.assertIn('tags', event)
    
    def test_timeline_filtering(self):
        """Test timeline filtering by tags, actors, and date"""
        # Test tag filtering
        response = self.client.get('/api/timeline?tags=test')
        data = json.loads(response.data)
        self.assertEqual(data['total'], 2)
        
        # Test actor filtering
        response = self.client.get('/api/timeline?actors=Actor%201')
        data = json.loads(response.data)
        self.assertEqual(data['total'], 2)
        
        # Test date range filtering
        response = self.client.get('/api/timeline?start_date=2025-01-10&end_date=2025-01-20')
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        
        # Test search
        response = self.client.get('/api/timeline?search=reference')
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
    
    def test_event_endpoint(self):
        """Test /api/event/<id> endpoint"""
        response = self.client.get('/api/event/2025-01-01--test-event-1')
        self.assertEqual(response.status_code, 200)
        
        event = json.loads(response.data)
        self.assertEqual(event['id'], '2025-01-01--test-event-1')
        self.assertEqual(event['title'], 'Test Event 1')
        
        # Test non-existent event
        response = self.client.get('/api/event/non-existent')
        self.assertEqual(response.status_code, 404)
    
    def test_posts_endpoint(self):
        """Test /api/posts endpoint"""
        response = self.client.get('/api/posts')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('posts', data)
        self.assertIn('total', data)
        self.assertGreaterEqual(data['total'], 2)
        
        # Check post structure
        post = data['posts'][0]
        self.assertIn('id', post)
        self.assertIn('title', post)
        self.assertIn('timeline_events', post)
        self.assertNotIn('content', post)  # Content should be removed in list view
    
    def test_posts_filtering(self):
        """Test posts filtering"""
        # Test category filtering
        response = self.client.get('/api/posts?category=tech_frame')
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        
        # Test search
        response = self.client.get('/api/posts?search=analysis')
        data = json.loads(response.data)
        self.assertGreaterEqual(data['total'], 1)
    
    def test_post_detail_endpoint(self):
        """Test /api/post/<id> endpoint"""
        response = self.client.get('/api/post/test_post_1')
        self.assertEqual(response.status_code, 200)
        
        post = json.loads(response.data)
        self.assertEqual(post['id'], 'test_post_1')
        self.assertIn('content', post)
        self.assertIn('content_enhanced', post)
        self.assertIn('html', post)
        self.assertIn('timeline_events', post)
        
        # Check that timeline events are referenced
        self.assertIn('2025-01-01--test-event-1', post['timeline_events'])
        self.assertIn('2025-01-15--test-event-2', post['timeline_events'])
        
        # Check that content is enhanced with links
        self.assertIn('timeline-link', post['content_enhanced'])
        self.assertIn('data-event-id', post['content_enhanced'])
    
    def test_book_endpoint(self):
        """Test /api/book endpoint"""
        response = self.client.get('/api/book')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('chapters', data)
        self.assertIn('total', data)
        self.assertGreaterEqual(data['total'], 1)
        
        # Check chapter structure
        chapter = data['chapters'][0]
        self.assertIn('id', chapter)
        self.assertIn('title', chapter)
        self.assertNotIn('content', chapter)  # Content removed in list view
    
    def test_book_chapter_endpoint(self):
        """Test /api/book/<id> endpoint"""
        response = self.client.get('/api/book/chapter_01_introduction')
        self.assertEqual(response.status_code, 200)
        
        chapter = json.loads(response.data)
        self.assertEqual(chapter['id'], 'chapter_01_introduction')
        self.assertIn('content', chapter)
        self.assertIn('content_enhanced', chapter)
        self.assertIn('html', chapter)
        
        # Check that timeline events are enhanced
        self.assertIn('timeline-link', chapter['content_enhanced'])
    
    def test_tags_endpoint(self):
        """Test /api/tags endpoint"""
        response = self.client.get('/api/tags')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('tags', data)
        self.assertIn('total', data)
        
        tags = data['tags']
        self.assertIn('test', tags)
        self.assertIn('sample', tags)
        self.assertIn('reference', tags)
    
    def test_actors_endpoint(self):
        """Test /api/actors endpoint"""
        response = self.client.get('/api/actors')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('actors', data)
        self.assertIn('total', data)
        
        actors = data['actors']
        self.assertIn('Actor 1', actors)
        self.assertIn('Actor 2', actors)
        self.assertIn('Actor 3', actors)
    
    def test_stats_endpoint(self):
        """Test /api/stats endpoint"""
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        
        stats = json.loads(response.data)
        self.assertIn('timeline', stats)
        self.assertIn('posts', stats)
        self.assertIn('book', stats)
        
        # Check timeline stats
        self.assertEqual(stats['timeline']['total_events'], 3)
        self.assertGreater(stats['timeline']['total_tags'], 0)
        self.assertGreater(stats['timeline']['total_actors'], 0)
        self.assertIn('events_by_year', stats['timeline'])
        self.assertIn('2025', stats['timeline']['events_by_year'])
        
        # Check posts stats
        self.assertGreaterEqual(stats['posts']['total'], 2)
        self.assertIn('by_category', stats['posts'])
        
        # Check book stats
        self.assertGreaterEqual(stats['book']['total_chapters'], 1)
    
    def test_search_endpoint(self):
        """Test /api/search global search endpoint"""
        response = self.client.get('/api/search?q=test')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('query', data)
        self.assertIn('results', data)
        self.assertIn('total', data)
        
        self.assertEqual(data['query'], 'test')
        self.assertGreater(data['total'], 0)
        
        # Check result structure
        if data['results']:
            result = data['results'][0]
            self.assertIn('type', result)
            self.assertIn('id', result)
            self.assertIn('title', result)
            self.assertIn('summary', result)
    
    def test_timeline_reference_extraction(self):
        """Test extraction of timeline references from content"""
        content = """
        This references [[2025-01-01--test-event-1]] directly.
        And links to [an event](#timeline:2025-01-15--test-event-2).
        Old format [[2025-02-01_old-format]] should work too.
        """
        
        refs = server.extract_timeline_references(content)
        self.assertIn('2025-01-01--test-event-1', refs)
        self.assertIn('2025-01-15--test-event-2', refs)
        self.assertIn('2025-02-01--old-format', refs)  # Converted from old format
    
    def test_content_enhancement(self):
        """Test enhancement of content with timeline links"""
        events_by_id = {
            '2025-01-01--test-event-1': {
                'id': '2025-01-01--test-event-1',
                'title': 'Test Event 1'
            }
        }
        
        content = "This references [[2025-01-01--test-event-1]] directly."
        enhanced = server.enhance_content_with_timeline_links(content, events_by_id)
        
        self.assertIn('timeline-link', enhanced)
        self.assertIn('data-event-id="2025-01-01--test-event-1"', enhanced)
        self.assertIn('Test Event 1', enhanced)
        self.assertIn('href="#timeline/2025-01-01--test-event-1"', enhanced)
    
    def test_index_page(self):
        """Test the main index page"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        html = response.data.decode('utf-8')
        self.assertIn('Kleptocracy Research Dashboard', html)
        self.assertIn('Timeline', html)
        self.assertIn('Posts', html)
        self.assertIn('Book', html)
    
    def test_cache_functionality(self):
        """Test that caching works correctly"""
        # First load should populate cache
        server._cache['last_load'] = 0
        cache1 = server.get_cached_data()
        self.assertIsNotNone(cache1['events'])
        self.assertIsNotNone(cache1['posts'])
        self.assertIsNotNone(cache1['book_chapters'])
        
        # Second load within cache duration should return same data
        original_time = cache1['last_load']
        cache2 = server.get_cached_data()
        self.assertEqual(cache2['last_load'], original_time)
        
        # Force cache expiration
        server._cache['last_load'] = 0
        cache3 = server.get_cached_data()
        self.assertNotEqual(cache3['last_load'], original_time)


class TestDataValidation(unittest.TestCase):
    """Test data validation and error handling"""
    
    def setUp(self):
        """Set up test client"""
        self.app = server.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        server.TIMELINE_DIR = Path(self.test_dir) / "timeline_data"
        server.POSTS_DIR = Path(self.test_dir) / "posts"
        server.BOOK_DIR = Path(self.test_dir) / "book_vision"
        
        # Reset cache
        server._cache = {
            'events': None,
            'posts': None,
            'book_chapters': None,
            'last_load': 0
        }
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def test_missing_directories(self):
        """Test handling of missing directories"""
        response = self.client.get('/api/timeline')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 0)
        
        response = self.client.get('/api/posts')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 0)
    
    def test_malformed_yaml(self):
        """Test handling of malformed YAML files"""
        server.TIMELINE_DIR.mkdir(parents=True)
        
        # Create malformed YAML
        bad_file = server.TIMELINE_DIR / "bad.yaml"
        with open(bad_file, 'w') as f:
            f.write("{ this is: not valid yaml }")
        
        # Should not crash
        response = self.client.get('/api/timeline')
        self.assertEqual(response.status_code, 200)
    
    def test_invalid_date_format(self):
        """Test handling of invalid date formats"""
        server.TIMELINE_DIR.mkdir(parents=True)
        
        event = {
            'id': 'test-event',
            'title': 'Test',
            'date': 'not-a-date',
            'summary': 'Test event'
        }
        
        with open(server.TIMELINE_DIR / "test.yaml", 'w') as f:
            yaml.dump(event, f)
        
        response = self.client.get('/api/timeline')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Should still load the event
        self.assertEqual(data['total'], 1)


def run_tests():
    """Run all tests with formatted output"""
    print("=" * 70)
    print("Running Enhanced Timeline Server Tests")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedTimelineServer))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())