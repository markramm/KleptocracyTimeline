#!/usr/bin/env python3
"""
Enhanced Timeline Server v3 - With improved content organization and series grouping
"""

import os
import yaml
import json
import webbrowser
import threading
import time
import re
import markdown
from flask import Flask, jsonify, send_from_directory, request, render_template_string
from flask_cors import CORS
from datetime import datetime
from pathlib import Path
import glob
from collections import defaultdict, OrderedDict
from markupsafe import Markup

app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = Path(__file__).parent
TIMELINE_DIR = BASE_DIR / "timeline_data"
POSTS_DIR = BASE_DIR / "posts"
BOOK_DIR = BASE_DIR / "book_vision"
STATIC_DIR = BASE_DIR / "timeline-app" / "build"

# Cache for loaded data
_cache = {
    'events': None,
    'posts': None,
    'book_chapters': None,
    'events_by_id': {},
    'last_load': 0
}

CACHE_DURATION = 60  # seconds

# Series metadata
SERIES_INFO = {
    'tech_frame': {
        'title': '🔧 Debugging Democracy',
        'description': 'Technical analysis of democratic system failures through an engineering lens',
        'icon': '💻',
        'order': 1
    },
    'expose_frame': {
        'title': '🎭 How Democracy Gets Pwned',
        'description': 'Narrative exposé of kleptocratic capture patterns',
        'icon': '📖',
        'order': 2
    },
    '_footnotes': {
        'title': '📑 Citations & References',
        'description': 'Supporting documentation and footnotes',
        'icon': '📎',
        'order': 3
    }
}

def load_timeline_events():
    """Load all timeline events from YAML files"""
    events = []
    events_by_id = {}
    
    events_dir = TIMELINE_DIR / "events"
    if events_dir.exists():
        for yaml_file in events_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    event = yaml.safe_load(f)
                    if event and event.get('id'):
                        # Convert dates to strings for JSON serialization
                        if 'date' in event:
                            if hasattr(event['date'], 'isoformat'):
                                event['date'] = event['date'].isoformat()
                            else:
                                event['date'] = str(event['date'])
                        event['_file'] = yaml_file.name
                        events.append(event)
                        events_by_id[event['id']] = event
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")
    
    # Sort by date
    events.sort(key=lambda x: x.get('date', '9999-12-31'))
    return events, events_by_id

def natural_sort_key(filename):
    """Generate a key for natural sorting (handles numbers properly)"""
    parts = []
    for part in re.split(r'(\d+)', filename):
        if part.isdigit():
            parts.append(int(part))
        else:
            parts.append(part.lower())
    return parts

def load_posts():
    """Load all posts from markdown files, organized by series"""
    posts = []
    posts_by_id = {}
    posts_by_series = defaultdict(list)
    
    if POSTS_DIR.exists():
        # Load from main posts directory
        for md_file in POSTS_DIR.glob("*.md"):
            post = load_markdown_file(md_file, 'post')
            if post:
                posts.append(post)
                posts_by_id[post['id']] = post
                posts_by_series['general'].append(post)
        
        # Load from subdirectories with series organization
        for subdir in POSTS_DIR.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('.'):
                series_posts = []
                for md_file in subdir.glob("*.md"):
                    post = load_markdown_file(md_file, 'post', category=subdir.name)
                    if post:
                        posts.append(post)
                        posts_by_id[post['id']] = post
                        series_posts.append(post)
                
                # Sort posts within series naturally
                series_posts.sort(key=lambda p: natural_sort_key(p['filename']))
                posts_by_series[subdir.name] = series_posts
    
    # Sort main posts list by date/filename
    posts.sort(key=lambda x: natural_sort_key(x.get('filename', '')))
    
    return posts, posts_by_id, posts_by_series

def load_book_chapters():
    """Load book chapters from book_vision directory"""
    chapters = []
    chapters_by_id = {}
    
    # Load from chapters subdirectory first
    chapters_dir = BOOK_DIR / "chapters"
    if chapters_dir.exists():
        for md_file in chapters_dir.glob("*.md"):
            chapter = load_markdown_file(md_file, 'chapter', category='chapters')
            if chapter:
                chapters.append(chapter)
                chapters_by_id[chapter['id']] = chapter
    
    # Then load from main book directory
    if BOOK_DIR.exists():
        for md_file in BOOK_DIR.glob("*.md"):
            chapter = load_markdown_file(md_file, 'chapter', category='meta')
            if chapter:
                chapters.append(chapter)
                chapters_by_id[chapter['id']] = chapter
    
    # Sort by natural order (handles chapter_01, chapter_02, etc.)
    chapters.sort(key=lambda x: natural_sort_key(x.get('filename', '')))
    
    # Separate into chapters and meta documents
    main_chapters = [c for c in chapters if c.get('category') == 'chapters']
    meta_docs = [c for c in chapters if c.get('category') != 'chapters']
    
    return main_chapters, chapters_by_id, meta_docs

def load_markdown_file(filepath, doc_type, category=None):
    """Load and parse a markdown file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata from frontmatter if present
        metadata = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1])
                    content = parts[2]
                except:
                    pass
        
        # Extract title from first H1 if not in metadata
        title = metadata.get('title', '')
        if not title:
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                title = title_match.group(1)
        
        # Clean up title for display
        if not title:
            # Generate title from filename
            title = filepath.stem.replace('_', ' ').replace('-', ' ').title()
            # Handle numbered files specially
            title = re.sub(r'^(\d+)\s+', r'Part \1: ', title)
            title = re.sub(r'^Episode\s+(\d+)', r'Episode \1:', title)
            title = re.sub(r'^Chapter\s+(\d+)', r'Chapter \1:', title)
        
        # Extract timeline event references
        event_refs = extract_timeline_references(content)
        
        # Convert markdown to HTML for preview
        html_preview = markdown.markdown(content[:500] + '...' if len(content) > 500 else content)
        
        # Handle path safely
        try:
            path_str = str(filepath.relative_to(BASE_DIR))
        except ValueError:
            path_str = filepath.name
        
        # Extract episode/chapter number for sorting
        number_match = re.match(r'^(?:episode_)?(\d+)', filepath.stem)
        sort_order = int(number_match.group(1)) if number_match else 999
        
        return {
            'id': filepath.stem,
            'filename': filepath.name,
            'path': path_str,
            'type': doc_type,
            'category': category,
            'title': title,
            'date': metadata.get('date', ''),
            'tags': metadata.get('tags', []),
            'summary': metadata.get('summary', ''),
            'content': content,
            'html_preview': html_preview,
            'timeline_events': event_refs,
            'metadata': metadata,
            'sort_order': sort_order
        }
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def extract_timeline_references(content):
    """Extract references to timeline events from markdown content"""
    refs = []
    
    # Pattern 1: Direct timeline links like [[2025-01-24--inspector-general-mass-firings]]
    pattern1 = r'\[\[(\d{4}-\d{2}-\d{2}--[^\]]+)\]\]'
    refs.extend(re.findall(pattern1, content))
    
    # Pattern 2: Markdown links to timeline events
    pattern2 = r'\[([^\]]+)\]\(#timeline:(\d{4}-\d{2}-\d{2}--[^\)]+)\)'
    for match in re.finditer(pattern2, content):
        refs.append(match.group(2))
    
    # Pattern 3: Old format with underscores (for backwards compatibility)
    pattern3 = r'\[\[(\d{4}-\d{2}-\d{2}_[^\]]+)\]\]'
    old_refs = re.findall(pattern3, content)
    refs.extend([ref.replace('_', '--', 1) for ref in old_refs])
    
    return list(set(refs))

def enhance_content_with_timeline_links(content, events_by_id):
    """Replace timeline references with interactive links"""
    enhanced = content
    
    for event_id in events_by_id:
        pattern = f'\\[\\[{re.escape(event_id)}\\]\\]'
        if event_id in events_by_id:
            event = events_by_id[event_id]
            replacement = f'<a href="/timeline/{event_id}" class="timeline-link" data-event-id="{event_id}" title="{event.get("title", "")}">{event.get("title", event_id)}</a>'
            enhanced = re.sub(pattern, replacement, enhanced)
        
        # Old format support
        old_id = event_id.replace('--', '_', 1)
        pattern_old = f'\\[\\[{re.escape(old_id)}\\]\\]'
        if old_id != event_id:
            replacement = f'<a href="/timeline/{event_id}" class="timeline-link" data-event-id="{event_id}" title="{event.get("title", "")}">{event.get("title", event_id)}</a>'
            enhanced = re.sub(pattern_old, replacement, enhanced)
    
    return enhanced

def extract_all_tags(events):
    """Extract all unique tags from events"""
    tags = set()
    for event in events:
        if 'tags' in event:
            if isinstance(event['tags'], list):
                tags.update(event['tags'])
            else:
                tags.add(event['tags'])
    return sorted(list(tags))

def extract_all_actors(events):
    """Extract all unique actors from events"""
    actors = set()
    for event in events:
        if 'actors' in event:
            if isinstance(event['actors'], list):
                actors.update(event['actors'])
            else:
                actors.add(event['actors'])
    return sorted(list(actors))

def get_cached_data():
    """Get cached data or reload if expired"""
    now = time.time()
    if _cache['last_load'] == 0 or (now - _cache['last_load']) > CACHE_DURATION:
        print("Reloading data...")
        events, events_by_id = load_timeline_events()
        posts, posts_by_id, posts_by_series = load_posts()
        chapters, chapters_by_id, meta_docs = load_book_chapters()
        
        _cache['events'] = events
        _cache['events_by_id'] = events_by_id
        _cache['posts'] = posts
        _cache['posts_by_id'] = posts_by_id
        _cache['posts_by_series'] = posts_by_series
        _cache['book_chapters'] = chapters
        _cache['chapters_by_id'] = chapters_by_id
        _cache['meta_docs'] = meta_docs
        _cache['last_load'] = now
    return _cache

# HTML Templates
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header h1 { 
            font-size: 1.5rem; 
            margin-bottom: 0.5rem; 
        }
        .header a {
            color: white;
            text-decoration: none;
            opacity: 0.9;
        }
        .header a:hover {
            opacity: 1;
        }
        .breadcrumb {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        .nav-bar {
            background: white;
            padding: 0.5rem 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        .nav-bar a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            padding: 0.5rem 0;
        }
        .nav-bar a:hover {
            color: #764ba2;
        }
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        .content {
            background: white;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .series-section {
            margin-bottom: 3rem;
            padding: 1.5rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .series-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #667eea;
        }
        .series-icon {
            font-size: 2rem;
        }
        .series-title {
            font-size: 1.5rem;
            color: #333;
        }
        .series-description {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        .post-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }
        .post-card {
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 4px;
            transition: all 0.2s;
            cursor: pointer;
        }
        .post-card:hover {
            background: #e9ecef;
            transform: translateY(-2px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .post-number {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            margin-bottom: 0.5rem;
        }
        .post-title {
            font-weight: 500;
            color: #333;
            margin-bottom: 0.5rem;
        }
        .post-summary {
            font-size: 0.85rem;
            color: #666;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .metadata {
            display: flex;
            gap: 2rem;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #e9ecef;
            font-size: 0.9rem;
            color: #666;
        }
        .tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 1rem 0;
        }
        .tag {
            background: #667eea;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            text-decoration: none;
        }
        .tag:hover {
            background: #764ba2;
        }
        .timeline-link {
            color: #667eea;
            text-decoration: none;
            border-bottom: 1px dotted #667eea;
            position: relative;
        }
        .timeline-link:hover {
            color: #764ba2;
            border-bottom-color: #764ba2;
        }
        .markdown-content {
            font-size: 1.1rem;
            line-height: 1.8;
        }
        .markdown-content h1 { 
            font-size: 2rem; 
            margin: 2rem 0 1rem; 
            color: #2c3e50;
        }
        .markdown-content h2 { 
            font-size: 1.5rem; 
            margin: 1.5rem 0 0.75rem;
            color: #34495e;
        }
        .markdown-content h3 { 
            font-size: 1.25rem; 
            margin: 1.25rem 0 0.5rem;
            color: #34495e;
        }
        .markdown-content p { 
            margin: 1rem 0; 
        }
        .markdown-content ul, .markdown-content ol {
            margin: 1rem 0 1rem 2rem;
        }
        .markdown-content li {
            margin: 0.5rem 0;
        }
        .markdown-content blockquote {
            border-left: 4px solid #667eea;
            padding-left: 1rem;
            margin: 1rem 0;
            color: #666;
            font-style: italic;
        }
        .markdown-content code {
            background: #f4f4f4;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        .markdown-content pre {
            background: #f4f4f4;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
        }
        .sidebar {
            position: fixed;
            right: 2rem;
            top: 10rem;
            width: 250px;
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .sidebar h3 {
            font-size: 0.9rem;
            margin-bottom: 0.75rem;
            color: #666;
        }
        .sidebar ul {
            list-style: none;
        }
        .sidebar li {
            margin: 0.5rem 0;
        }
        .sidebar a {
            color: #667eea;
            text-decoration: none;
            font-size: 0.9rem;
        }
        .sidebar a:hover {
            text-decoration: underline;
        }
        .chapter-list {
            display: grid;
            gap: 1rem;
        }
        .chapter-card {
            padding: 1.5rem;
            background: white;
            border-left: 4px solid #667eea;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: all 0.2s;
        }
        .chapter-card:hover {
            transform: translateX(4px);
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }
        .chapter-number {
            font-size: 0.85rem;
            color: #667eea;
            font-weight: 600;
        }
        .chapter-title {
            font-size: 1.2rem;
            color: #333;
            margin: 0.5rem 0;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 1rem;
            color: #667eea;
            text-decoration: none;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        @media (max-width: 1400px) {
            .sidebar {
                display: none;
            }
        }
        @media (max-width: 768px) {
            .container {
                padding: 0 1rem;
            }
            .content {
                padding: 1rem;
            }
            .post-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1><a href="/">🔍 Kleptocracy Research</a></h1>
        <div class="breadcrumb">
            {{ breadcrumb | safe }}
        </div>
    </div>
    
    <div class="nav-bar">
        <a href="/">📊 Dashboard</a>
        <a href="/timeline">📅 Timeline</a>
        <a href="/posts">📝 Posts</a>
        <a href="/book">📚 Book</a>
    </div>
    
    <div class="container">
        {{ content | safe }}
    </div>
    
    {{ sidebar | safe }}
</body>
</html>
'''

# API endpoints remain the same...
@app.route('/api/timeline')
def get_timeline():
    """Get all timeline events with optional filtering"""
    cache = get_cached_data()
    events = cache['events']
    
    tags_filter = request.args.getlist('tags')
    if tags_filter:
        events = [e for e in events if any(tag in e.get('tags', []) for tag in tags_filter)]
    
    actors_filter = request.args.getlist('actors')
    if actors_filter:
        events = [e for e in events if any(actor in e.get('actors', []) for actor in actors_filter)]
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date:
        events = [e for e in events if e.get('date', '') >= start_date]
    if end_date:
        events = [e for e in events if e.get('date', '') <= end_date]
    
    search = request.args.get('search', '').lower()
    if search:
        events = [e for e in events if 
                 search in e.get('title', '').lower() or 
                 search in e.get('summary', '').lower() or
                 search in str(e.get('notes', '')).lower()]
    
    return jsonify({
        'events': events,
        'total': len(events)
    })

@app.route('/api/stats')
def get_stats():
    """Get statistics about the data"""
    cache = get_cached_data()
    
    events = cache['events']
    events_by_year = defaultdict(int)
    for event in events:
        if 'date' in event:
            year = event['date'][:4]
            events_by_year[year] += 1
    
    posts_by_series = cache['posts_by_series']
    
    return jsonify({
        'timeline': {
            'total_events': len(events),
            'total_tags': len(extract_all_tags(events)),
            'total_actors': len(extract_all_actors(events)),
            'events_by_year': dict(events_by_year),
            'date_range': {
                'start': events[0]['date'] if events else None,
                'end': events[-1]['date'] if events else None
            }
        },
        'posts': {
            'total': len(cache['posts']),
            'by_series': {k: len(v) for k, v in posts_by_series.items()}
        },
        'book': {
            'total_chapters': len(cache['book_chapters']),
            'meta_docs': len(cache.get('meta_docs', []))
        }
    })

# Enhanced HTML views with better organization

@app.route('/')
def index():
    """Dashboard with organized content"""
    cache = get_cached_data()
    
    recent_events = cache['events'][-10:][::-1]
    stats = {
        'events': len(cache['events']),
        'posts': len(cache['posts']),
        'chapters': len(cache['book_chapters']),
        'tags': len(extract_all_tags(cache['events'])),
        'actors': len(extract_all_actors(cache['events']))
    }
    
    content = f'''
    <div class="content">
        <h1>Research Dashboard</h1>
        
        <div class="metadata">
            <span>📅 {stats['events']} Events</span>
            <span>📝 {stats['posts']} Posts</span>
            <span>📚 {stats['chapters']} Chapters</span>
            <span>🏷️ {stats['tags']} Tags</span>
            <span>👥 {stats['actors']} Actors</span>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div>
                <h2>📅 Recent Timeline Events</h2>
                <div style="margin-top: 1rem;">
    '''
    
    for event in recent_events:
        content += f'''
            <div style="padding: 1rem; margin-bottom: 1rem; background: #f8f9fa; border-radius: 4px;">
                <div style="font-size: 0.85rem; color: #666;">{event.get('date', '')}</div>
                <h3 style="margin: 0.5rem 0; font-size: 1.1rem;">
                    <a href="/timeline/{event['id']}" style="color: #333; text-decoration: none;">
                        {event.get('title', '')}
                    </a>
                </h3>
                <div style="font-size: 0.9rem; color: #666;">
                    {event.get('summary', '')[:150]}{'...' if len(event.get('summary', '')) > 150 else ''}
                </div>
            </div>
        '''
    
    content += '''
                </div>
            </div>
            
            <div>
                <h2>📚 Content Series</h2>
                <div style="margin-top: 1rem;">
    '''
    
    # Show series overview
    posts_by_series = cache['posts_by_series']
    for series_key in ['tech_frame', 'expose_frame']:
        if series_key in posts_by_series and posts_by_series[series_key]:
            info = SERIES_INFO.get(series_key, {})
            count = len(posts_by_series[series_key])
            content += f'''
                <div style="padding: 1rem; margin-bottom: 1rem; background: #f8f9fa; border-radius: 4px;">
                    <h3 style="margin: 0.5rem 0; font-size: 1.1rem;">
                        <a href="/posts#{series_key}" style="color: #333; text-decoration: none;">
                            {info.get('icon', '')} {info.get('title', series_key)}
                        </a>
                    </h3>
                    <div style="font-size: 0.9rem; color: #666;">
                        {count} posts • {info.get('description', '')}
                    </div>
                </div>
            '''
    
    # Add book info
    content += f'''
                <div style="padding: 1rem; margin-bottom: 1rem; background: #f8f9fa; border-radius: 4px;">
                    <h3 style="margin: 0.5rem 0; font-size: 1.1rem;">
                        <a href="/book" style="color: #333; text-decoration: none;">
                            📖 Book Manuscript
                        </a>
                    </h3>
                    <div style="font-size: 0.9rem; color: #666;">
                        {stats['chapters']} chapters in development
                    </div>
                </div>
            '''
    
    content += '''
                </div>
            </div>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE, 
        title="Kleptocracy Research Dashboard",
        breadcrumb="Dashboard",
        content=Markup(content),
        sidebar='')

@app.route('/posts')
def posts_list():
    """Organized posts by series"""
    cache = get_cached_data()
    posts_by_series = cache['posts_by_series']
    
    content = '<div class="content"><h1>All Posts</h1>'
    
    # Sort series by defined order
    series_order = ['tech_frame', 'expose_frame', '_footnotes']
    other_series = [s for s in posts_by_series.keys() if s not in series_order and s != 'general']
    all_series = series_order + other_series
    
    for series_key in all_series:
        if series_key not in posts_by_series or not posts_by_series[series_key]:
            continue
            
        series_posts = posts_by_series[series_key]
        info = SERIES_INFO.get(series_key, {
            'title': series_key.replace('_', ' ').title(),
            'description': '',
            'icon': '📄'
        })
        
        content += f'''
        <div class="series-section" id="{series_key}">
            <div class="series-header">
                <span class="series-icon">{info['icon']}</span>
                <h2 class="series-title">{info['title']}</h2>
            </div>
            <div class="series-description">{info['description']}</div>
            <div class="post-grid">
        '''
        
        for post in series_posts:
            # Extract number from filename if present
            number_match = re.match(r'^(\d+)', post['filename'])
            number = number_match.group(1) if number_match else ''
            
            # Clean up title
            title = post.get('title', '')
            if title.startswith('Part '):
                title = title[7:]  # Remove "Part " prefix
            
            content += f'''
                <div class="post-card" onclick="window.location.href='/post/{post['id']}'">
                    {f'<span class="post-number">{number}</span>' if number else ''}
                    <div class="post-title">{title}</div>
                    <div class="post-summary">
                        {post.get('summary', '')[:150] or 'Click to read...'}
                    </div>
                </div>
            '''
        
        content += '''
            </div>
        </div>
        '''
    
    content += '</div>'
    
    return render_template_string(BASE_TEMPLATE,
        title="All Posts",
        breadcrumb='<a href="/">Dashboard</a> / Posts',
        content=Markup(content),
        sidebar='')

@app.route('/book')
def book_list():
    """Organized book chapters"""
    cache = get_cached_data()
    chapters = cache['book_chapters']
    meta_docs = cache.get('meta_docs', [])
    
    content = '''
    <div class="content">
        <h1>Book Manuscript</h1>
        <p style="margin: 1rem 0; color: #666;">
            Exploring the patterns of kleptocratic capture through historical and theoretical analysis.
        </p>
        
        <h2 style="margin-top: 2rem;">📖 Chapters</h2>
        <div class="chapter-list" style="margin-top: 1rem;">
    '''
    
    for chapter in chapters:
        # Extract chapter number
        number_match = re.match(r'chapter[_-](\d+)', chapter['filename'])
        chapter_num = f"Chapter {int(number_match.group(1))}" if number_match else ''
        
        content += f'''
        <div class="chapter-card" onclick="window.location.href='/book/{chapter['id']}'">
            <div class="chapter-number">{chapter_num}</div>
            <div class="chapter-title">{chapter.get('title', '')}</div>
            <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
                {chapter.get('summary', '')[:200] or 'Click to read...'}
            </div>
        </div>
        '''
    
    if meta_docs:
        content += '''
        <h2 style="margin-top: 3rem;">📑 Supporting Documents</h2>
        <div class="chapter-list" style="margin-top: 1rem;">
        '''
        
        for doc in meta_docs:
            content += f'''
            <div class="chapter-card" onclick="window.location.href='/book/{doc['id']}'">
                <div class="chapter-title">{doc.get('title', '')}</div>
                <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
                    {doc.get('summary', '')[:200] or 'Click to read...'}
                </div>
            </div>
            '''
        
        content += '</div>'
    
    content += '</div></div>'
    
    return render_template_string(BASE_TEMPLATE,
        title="Book Chapters",
        breadcrumb='<a href="/">Dashboard</a> / Book',
        content=Markup(content),
        sidebar='')

@app.route('/timeline')
def timeline_list():
    """Timeline events list"""
    cache = get_cached_data()
    events = cache['events'][::-1]
    
    content = '<div class="content"><h1>Timeline Events</h1>'
    
    current_year = None
    for event in events:
        year = event.get('date', '')[:4]
        if year != current_year:
            if current_year:
                content += '</div>'
            content += f'<h2 style="margin-top: 2rem; color: #667eea;">{year}</h2><div>'
            current_year = year
        
        content += f'''
        <div style="padding: 1rem; margin-bottom: 1rem; background: #f8f9fa; border-radius: 4px;">
            <div style="font-size: 0.85rem; color: #666;">{event.get('date', '')}</div>
            <h3 style="margin: 0.5rem 0; font-size: 1.1rem;">
                <a href="/timeline/{event['id']}" style="color: #333; text-decoration: none;">
                    {event.get('title', '')}
                </a>
            </h3>
            <div style="font-size: 0.9rem; color: #666; margin: 0.5rem 0;">
                {event.get('summary', '')}
            </div>
        '''
        
        if event.get('tags'):
            content += '<div class="tags">'
            for tag in event['tags'][:5]:
                content += f'<span class="tag">{tag}</span>'
            content += '</div>'
        
        content += '</div>'
    
    content += '</div></div>'
    
    return render_template_string(BASE_TEMPLATE,
        title="Timeline Events",
        breadcrumb='<a href="/">Dashboard</a> / Timeline',
        content=Markup(content),
        sidebar='')

@app.route('/timeline/<event_id>')
def view_timeline_event(event_id):
    """View specific timeline event"""
    cache = get_cached_data()
    events_by_id = cache.get('events_by_id', {})
    
    if event_id not in events_by_id:
        old_id = event_id.replace('_', '--', 1)
        if old_id in events_by_id:
            event_id = old_id
        else:
            return "Event not found", 404
    
    event = events_by_id[event_id]
    
    content = f'''
    <div class="content">
        <a href="/timeline" class="back-link">← Back to Timeline</a>
        
        <h1>{event.get('title', '')}</h1>
        
        <div class="metadata">
            <span>📅 {event.get('date', '')}</span>
            {f"<span>📍 {event.get('location', '')}</span>" if event.get('location') else ''}
            {f"<span>Status: {event.get('status', '')}</span>" if event.get('status') else ''}
        </div>
        
        <div style="font-size: 1.2rem; margin: 2rem 0;">
            {event.get('summary', '')}
        </div>
    '''
    
    if event.get('notes'):
        content += f'''
        <div style="margin: 2rem 0;">
            <h3>Notes</h3>
            <p>{event.get('notes', '')}</p>
        </div>
        '''
    
    if event.get('actors'):
        content += '<div style="margin: 2rem 0;"><h3>Actors</h3><ul>'
        for actor in event['actors']:
            content += f'<li>{actor}</li>'
        content += '</ul></div>'
    
    if event.get('tags'):
        content += '<div style="margin: 2rem 0;"><h3>Tags</h3><div class="tags">'
        for tag in event['tags']:
            content += f'<span class="tag">{tag}</span>'
        content += '</div></div>'
    
    if event.get('citations'):
        content += '<div style="margin: 2rem 0;"><h3>Citations</h3>'
        for i, citation in enumerate(event['citations'], 1):
            if isinstance(citation, dict):
                url = citation.get('archived') or citation.get('url', '')
                content += f'<div style="padding: 0.5rem; margin: 0.5rem 0; background: #f8f9fa; border-radius: 4px;">[{i}] <a href="{url}" target="_blank">{url}</a></div>'
            else:
                content += f'<div style="padding: 0.5rem; margin: 0.5rem 0; background: #f8f9fa; border-radius: 4px;">[{i}] <a href="{citation}" target="_blank">{citation}</a></div>'
        content += '</div>'
    
    content += '</div>'
    
    # Find posts that reference this event
    posts_with_ref = []
    for post in cache['posts']:
        if event_id in post.get('timeline_events', []):
            posts_with_ref.append(post)
    
    sidebar = ''
    if posts_with_ref:
        sidebar = '''
        <div class="sidebar">
            <h3>Referenced in Posts</h3>
            <ul>
        '''
        for post in posts_with_ref[:5]:
            sidebar += f'<li><a href="/post/{post["id"]}">{post.get("title", "")}</a></li>'
        sidebar += '</ul></div>'
    
    return render_template_string(BASE_TEMPLATE,
        title=event.get('title', ''),
        breadcrumb=f'<a href="/">Dashboard</a> / <a href="/timeline">Timeline</a> / {event.get("date", "")}',
        content=Markup(content),
        sidebar=Markup(sidebar))

@app.route('/post/<post_id>')
def view_post(post_id):
    """View specific post with timeline links"""
    cache = get_cached_data()
    posts_by_id = cache.get('posts_by_id', {})
    events_by_id = cache.get('events_by_id', {})
    
    if post_id not in posts_by_id:
        return "Post not found", 404
    
    post = posts_by_id[post_id]
    
    # Enhance content with timeline links
    enhanced_content = enhance_content_with_timeline_links(post['content'], events_by_id)
    html_content = markdown.markdown(enhanced_content, extensions=['extra', 'codehilite'])
    
    # Get series info
    series_info = SERIES_INFO.get(post.get('category'), {})
    
    content = f'''
    <div class="content">
        <a href="/posts#{post.get('category', '')}" class="back-link">
            ← Back to {series_info.get('title', 'Posts')}
        </a>
        
        <div class="markdown-content">
            {html_content}
        </div>
    </div>
    '''
    
    # Sidebar with timeline events
    sidebar = ''
    if post.get('timeline_events'):
        sidebar = '''
        <div class="sidebar">
            <h3>Timeline References</h3>
            <ul>
        '''
        for event_id in post['timeline_events'][:10]:
            if event_id in events_by_id:
                event = events_by_id[event_id]
                sidebar += f'<li><a href="/timeline/{event_id}">{event.get("date", "")} - {event.get("title", "")}</a></li>'
        sidebar += '</ul></div>'
    
    return render_template_string(BASE_TEMPLATE,
        title=post.get('title', ''),
        breadcrumb=f'<a href="/">Dashboard</a> / <a href="/posts">Posts</a> / {series_info.get("title", "")}',
        content=Markup(content),
        sidebar=Markup(sidebar))

@app.route('/book/<chapter_id>')
def view_chapter(chapter_id):
    """View specific book chapter"""
    cache = get_cached_data()
    chapters_by_id = cache.get('chapters_by_id', {})
    events_by_id = cache.get('events_by_id', {})
    
    if chapter_id not in chapters_by_id:
        return "Chapter not found", 404
    
    chapter = chapters_by_id[chapter_id]
    
    # Enhance content with timeline links
    enhanced_content = enhance_content_with_timeline_links(chapter['content'], events_by_id)
    html_content = markdown.markdown(enhanced_content, extensions=['extra', 'codehilite'])
    
    content = f'''
    <div class="content">
        <a href="/book" class="back-link">← Back to Book</a>
        
        <div class="markdown-content">
            {html_content}
        </div>
    </div>
    '''
    
    # Sidebar with timeline events
    sidebar = ''
    if chapter.get('timeline_events'):
        sidebar = '''
        <div class="sidebar">
            <h3>Timeline References</h3>
            <ul>
        '''
        for event_id in chapter['timeline_events'][:10]:
            if event_id in events_by_id:
                event = events_by_id[event_id]
                sidebar += f'<li><a href="/timeline/{event_id}">{event.get("date", "")} - {event.get("title", "")}</a></li>'
        sidebar += '</ul></div>'
    
    return render_template_string(BASE_TEMPLATE,
        title=chapter.get('title', ''),
        breadcrumb=f'<a href="/">Dashboard</a> / <a href="/book">Book</a> / Chapter',
        content=Markup(content),
        sidebar=Markup(sidebar))

def open_browser():
    """Open browser after server starts"""
    time.sleep(1)
    webbrowser.open('http://localhost:8080')

if __name__ == '__main__':
    print("Starting Enhanced Timeline Server v3...")
    print("With improved content organization and series grouping")
    print("Server running at http://localhost:8080")
    print("Press Ctrl+C to stop")
    
    # Start browser in separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Run server
    app.run(host='0.0.0.0', port=8080, debug=False)