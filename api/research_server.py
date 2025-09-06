#!/usr/bin/env python3
"""
Timeline Research Server - SQLite-based API for research workflow
Supports full-text search, timeline entry management, and research automation
"""

import os
import sqlite3
import yaml
import json
import hashlib
import threading
import time
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Any
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
import re

# Import existing timeline manager
import sys
sys.path.append(str(Path(__file__).parent.parent))
from timeline_event_manager import TimelineEventManager

app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = Path(__file__).parent.parent
TIMELINE_DIR = BASE_DIR / "timeline_data" / "events"
DATABASE_PATH = BASE_DIR / "research_timeline.db"
CACHE_DURATION = 300  # 5 minutes

class TimelineDatabase:
    """SQLite database manager for timeline events with full-text search"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with full-text search tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Main events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    importance INTEGER,
                    status TEXT,
                    notes TEXT,
                    file_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Actors table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS actors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            """)
            
            # Tags table  
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            """)
            
            # Sources table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    outlet TEXT NOT NULL,
                    date TEXT,
                    archived_url TEXT,
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                )
            """)
            
            # Junction tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS event_actors (
                    event_id TEXT NOT NULL,
                    actor_id INTEGER NOT NULL,
                    PRIMARY KEY (event_id, actor_id),
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                    FOREIGN KEY (actor_id) REFERENCES actors(id) ON DELETE CASCADE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS event_tags (
                    event_id TEXT NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (event_id, tag_id),
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                )
            """)
            
            # Full-text search virtual table
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(
                    id UNINDEXED,
                    title,
                    summary,
                    notes,
                    actors,
                    tags,
                    content='events',
                    content_rowid='rowid'
                )
            """)
            
            # Research notes table for workflow
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    results TEXT,
                    priority INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Research connections table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id_1 TEXT NOT NULL,
                    event_id_2 TEXT NOT NULL,
                    connection_type TEXT,
                    strength REAL DEFAULT 1.0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id_1) REFERENCES events(id) ON DELETE CASCADE,
                    FOREIGN KEY (event_id_2) REFERENCES events(id) ON DELETE CASCADE
                )
            """)
            
            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_importance ON events(importance)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_event_id ON sources(event_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_research_status ON research_notes(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_research_priority ON research_notes(priority)")
            
            conn.commit()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def calculate_file_hash(self, event_data: Dict) -> str:
        """Calculate hash of event data for change detection"""
        # Create consistent string representation for hashing
        def default_serializer(obj):
            """Custom serializer for date objects"""
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
        
        hashable = json.dumps(event_data, sort_keys=True, default=default_serializer)
        return hashlib.md5(hashable.encode()).hexdigest()
    
    def upsert_event(self, event_data: Dict) -> bool:
        """Insert or update event in database, returns True if changed"""
        with self.get_connection() as conn:
            current_hash = self.calculate_file_hash(event_data)
            
            # Check if event exists and if it's changed
            existing = conn.execute(
                "SELECT file_hash FROM events WHERE id = ?", 
                (event_data['id'],)
            ).fetchone()
            
            if existing and existing['file_hash'] == current_hash:
                return False  # No change
            
            # Insert/update main event
            conn.execute("""
                INSERT OR REPLACE INTO events 
                (id, date, title, summary, importance, status, notes, file_hash, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                event_data['id'],
                str(event_data['date']),
                event_data['title'],
                event_data['summary'],
                event_data.get('importance'),
                event_data.get('status', 'confirmed'),
                event_data.get('notes', ''),
                current_hash
            ))
            
            # Clear existing relationships
            conn.execute("DELETE FROM event_actors WHERE event_id = ?", (event_data['id'],))
            conn.execute("DELETE FROM event_tags WHERE event_id = ?", (event_data['id'],))
            conn.execute("DELETE FROM sources WHERE event_id = ?", (event_data['id'],))
            
            # Insert actors
            for actor_name in event_data.get('actors', []):
                # Insert actor if not exists
                conn.execute("INSERT OR IGNORE INTO actors (name) VALUES (?)", (actor_name,))
                actor_id = conn.execute("SELECT id FROM actors WHERE name = ?", (actor_name,)).fetchone()['id']
                conn.execute("INSERT INTO event_actors (event_id, actor_id) VALUES (?, ?)", 
                           (event_data['id'], actor_id))
            
            # Insert tags
            for tag_name in event_data.get('tags', []):
                # Insert tag if not exists
                conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()['id']
                conn.execute("INSERT INTO event_tags (event_id, tag_id) VALUES (?, ?)", 
                           (event_data['id'], tag_id))
            
            # Insert sources
            for source in event_data.get('sources', []):
                conn.execute("""
                    INSERT INTO sources (event_id, title, url, outlet, date, archived_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event_data['id'],
                    source.get('title', ''),
                    source.get('url', ''),
                    source.get('outlet', ''),
                    source.get('date', ''),
                    source.get('archived', '')
                ))
            
            # Update full-text search - Clean text for FTS5 compatibility
            def clean_fts_text(text_list):
                """Clean text for FTS5 insertion by removing/replacing problematic characters"""
                if not text_list:
                    return ''
                # Replace problematic characters that could confuse FTS5
                cleaned = []
                for item in text_list:
                    # Replace common problematic characters
                    cleaned_item = str(item).replace('"', '').replace("'", '').replace('(', '').replace(')', '')
                    cleaned.append(cleaned_item)
                return ', '.join(cleaned)
            
            actors_text = clean_fts_text(event_data.get('actors', []))
            tags_text = clean_fts_text(event_data.get('tags', []))
            
            conn.execute("""
                INSERT OR REPLACE INTO events_fts 
                (rowid, id, title, summary, notes, actors, tags)
                SELECT rowid, id, title, summary, notes, ?, ?
                FROM events WHERE id = ?
            """, (actors_text, tags_text, event_data['id']))
            
            conn.commit()
            return True
    
    def search_events(self, query: str = '', filters: Dict = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Search events with full-text search and filters"""
        filters = filters or {}
        
        with self.get_connection() as conn:
            base_query = """
                SELECT DISTINCT e.*, 
                       GROUP_CONCAT(DISTINCT a.name) as actors,
                       GROUP_CONCAT(DISTINCT t.name) as tags
                FROM events e
                LEFT JOIN event_actors ea ON e.id = ea.event_id
                LEFT JOIN actors a ON ea.actor_id = a.id
                LEFT JOIN event_tags et ON e.id = et.event_id
                LEFT JOIN tags t ON et.tag_id = t.id
            """
            
            conditions = []
            params = []
            
            # Full-text search
            if query.strip():
                base_query = """
                    SELECT DISTINCT e.*, 
                           GROUP_CONCAT(DISTINCT a.name) as actors,
                           GROUP_CONCAT(DISTINCT t.name) as tags,
                           fts.rank
                    FROM events_fts fts
                    JOIN events e ON e.id = fts.id
                    LEFT JOIN event_actors ea ON e.id = ea.event_id
                    LEFT JOIN actors a ON ea.actor_id = a.id
                    LEFT JOIN event_tags et ON e.id = et.event_id
                    LEFT JOIN tags t ON et.tag_id = t.id
                    WHERE events_fts MATCH ?
                """
                params.append(query)
            
            # Date filters
            if filters.get('start_date'):
                conditions.append("e.date >= ?")
                params.append(filters['start_date'])
            if filters.get('end_date'):
                conditions.append("e.date <= ?")
                params.append(filters['end_date'])
            
            # Importance filter
            if filters.get('min_importance'):
                conditions.append("e.importance >= ?")
                params.append(filters['min_importance'])
            if filters.get('max_importance'):
                conditions.append("e.importance <= ?")
                params.append(filters['max_importance'])
            
            # Status filter
            if filters.get('status'):
                conditions.append("e.status = ?")
                params.append(filters['status'])
            
            # Actor filter
            if filters.get('actor'):
                conditions.append("EXISTS (SELECT 1 FROM event_actors ea2 JOIN actors a2 ON ea2.actor_id = a2.id WHERE ea2.event_id = e.id AND a2.name LIKE ?)")
                params.append(f"%{filters['actor']}%")
            
            # Tag filter
            if filters.get('tag'):
                conditions.append("EXISTS (SELECT 1 FROM event_tags et2 JOIN tags t2 ON et2.tag_id = t2.id WHERE et2.event_id = e.id AND t2.name LIKE ?)")
                params.append(f"%{filters['tag']}%")
            
            # Combine conditions
            if conditions:
                if query.strip():
                    base_query += " AND " + " AND ".join(conditions)
                else:
                    base_query += " WHERE " + " AND ".join(conditions)
            
            # Group and order
            base_query += " GROUP BY e.id"
            if query.strip():
                base_query += " ORDER BY fts.rank, e.date DESC"
            else:
                base_query += " ORDER BY e.date DESC"
            
            base_query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            rows = conn.execute(base_query, params).fetchall()
            
            events = []
            for row in rows:
                event = dict(row)
                # Convert comma-separated strings back to lists
                event['actors'] = [a.strip() for a in (event['actors'] or '').split(',') if a.strip()]
                event['tags'] = [t.strip() for t in (event['tags'] or '').split(',') if t.strip()]
                
                # Get sources
                sources = conn.execute("""
                    SELECT title, url, outlet, date, archived_url
                    FROM sources WHERE event_id = ?
                """, (event['id'],)).fetchall()
                event['sources'] = [dict(source) for source in sources]
                
                events.append(event)
            
            return events
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """Get single event by ID with all related data"""
        events = self.search_events(filters={'event_id': event_id}, limit=1)
        return events[0] if events else None
    
    def get_all_actors(self) -> List[str]:
        """Get all unique actors"""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT name FROM actors ORDER BY name").fetchall()
            return [row['name'] for row in rows]
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags"""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT name FROM tags ORDER BY name").fetchall()
            return [row['name'] for row in rows]
    
    def add_research_note(self, query: str, results: str = '', priority: int = 5, status: str = 'pending') -> int:
        """Add research note for workflow tracking"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO research_notes (query, results, priority, status)
                VALUES (?, ?, ?, ?)
            """, (query, results, priority, status))
            conn.commit()
            return cursor.lastrowid
    
    def get_research_notes(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get research notes with optional status filter"""
        with self.get_connection() as conn:
            if status:
                rows = conn.execute("""
                    SELECT * FROM research_notes 
                    WHERE status = ?
                    ORDER BY priority DESC, created_at DESC
                    LIMIT ?
                """, (status, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM research_notes 
                    ORDER BY priority DESC, created_at DESC
                    LIMIT ?
                """, (limit,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def add_connection(self, event_id_1: str, event_id_2: str, connection_type: str = 'related', 
                      strength: float = 1.0, notes: str = '') -> int:
        """Add connection between two events"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO research_connections 
                (event_id_1, event_id_2, connection_type, strength, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (event_id_1, event_id_2, connection_type, strength, notes))
            conn.commit()
            return cursor.lastrowid
    
    def get_event_connections(self, event_id: str) -> List[Dict]:
        """Get all connections for an event"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT rc.*, e1.title as event1_title, e2.title as event2_title
                FROM research_connections rc
                JOIN events e1 ON rc.event_id_1 = e1.id
                JOIN events e2 ON rc.event_id_2 = e2.id
                WHERE rc.event_id_1 = ? OR rc.event_id_2 = ?
                ORDER BY rc.strength DESC
            """, (event_id, event_id)).fetchall()
            
            return [dict(row) for row in rows]

# Global database instance
db = TimelineDatabase(DATABASE_PATH)
timeline_manager = TimelineEventManager()

def load_timeline_from_yaml():
    """Load all YAML events into database"""
    print("Loading timeline events from YAML files...")
    loaded_count = 0
    updated_count = 0
    
    if TIMELINE_DIR.exists():
        for yaml_file in TIMELINE_DIR.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    event_data = yaml.safe_load(f)
                    if event_data and event_data.get('id'):
                        if db.upsert_event(event_data):
                            updated_count += 1
                        loaded_count += 1
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")
    
    print(f"Loaded {loaded_count} events ({updated_count} updated)")
    return loaded_count

# Background loading thread
def background_loader():
    """Periodically reload events from YAML files"""
    while True:
        try:
            load_timeline_from_yaml()
            time.sleep(CACHE_DURATION)
        except Exception as e:
            print(f"Background loader error: {e}")
            time.sleep(60)  # Wait longer on error

# Start background loader
loader_thread = threading.Thread(target=background_loader, daemon=True)
loader_thread.start()

# API Routes

@app.route('/api/search')
def search_events():
    """Search timeline events with full-text search and filters"""
    query = request.args.get('q', '')
    
    filters = {}
    if request.args.get('start_date'):
        filters['start_date'] = request.args.get('start_date')
    if request.args.get('end_date'):
        filters['end_date'] = request.args.get('end_date')
    if request.args.get('min_importance'):
        filters['min_importance'] = int(request.args.get('min_importance'))
    if request.args.get('max_importance'):
        filters['max_importance'] = int(request.args.get('max_importance'))
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('actor'):
        filters['actor'] = request.args.get('actor')
    if request.args.get('tag'):
        filters['tag'] = request.args.get('tag')
    
    limit = min(int(request.args.get('limit', 50)), 500)
    offset = int(request.args.get('offset', 0))
    
    events = db.search_events(query, filters, limit, offset)
    
    return jsonify({
        'events': events,
        'total': len(events),
        'query': query,
        'filters': filters,
        'limit': limit,
        'offset': offset
    })

@app.route('/api/event/<event_id>')
def get_event(event_id):
    """Get single event by ID"""
    event = db.get_event_by_id(event_id)
    if event:
        # Get connections
        connections = db.get_event_connections(event_id)
        event['connections'] = connections
        return jsonify(event)
    else:
        return jsonify({'error': 'Event not found'}), 404

@app.route('/api/actors')
def get_actors():
    """Get all unique actors"""
    actors = db.get_all_actors()
    return jsonify({'actors': actors, 'total': len(actors)})

@app.route('/api/tags')
def get_tags():
    """Get all unique tags"""
    tags = db.get_all_tags()
    return jsonify({'tags': tags, 'total': len(tags)})

@app.route('/api/events', methods=['POST'])
def create_event():
    """Create new timeline event"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['date', 'title', 'summary', 'importance', 'actors', 'tags', 'sources']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Use timeline manager to create and validate event
        event = timeline_manager.create_event(
            date=data['date'],
            title=data['title'],
            summary=data['summary'],
            importance=data['importance'],
            actors=data['actors'],
            tags=data['tags'],
            sources=data['sources'],
            status=data.get('status', 'confirmed'),
            notes=data.get('notes'),
            event_id=data.get('id')
        )
        
        # Save to database
        db.upsert_event(event)
        
        # Optionally save to YAML file
        if request.args.get('save_yaml', 'false').lower() == 'true':
            filepath = timeline_manager.save_event(event)
            return jsonify({
                'event': event,
                'saved_to': str(filepath),
                'message': 'Event created and saved to YAML'
            })
        else:
            return jsonify({
                'event': event,
                'message': 'Event created in database (not saved to YAML)'
            })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@app.route('/api/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    """Update existing timeline event"""
    try:
        data = request.get_json()
        data['id'] = event_id  # Ensure ID matches URL
        
        # Update in database
        db.upsert_event(data)
        
        # Optionally update YAML file
        if request.args.get('save_yaml', 'false').lower() == 'true':
            filepath = timeline_manager.save_event(data, overwrite=True)
            return jsonify({
                'event': data,
                'saved_to': str(filepath),
                'message': 'Event updated and saved to YAML'
            })
        else:
            return jsonify({
                'event': data,
                'message': 'Event updated in database (not saved to YAML)'
            })
    
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@app.route('/api/research/notes', methods=['GET', 'POST'])
def research_notes():
    """Get or create research notes"""
    if request.method == 'GET':
        status = request.args.get('status')
        limit = min(int(request.args.get('limit', 50)), 200)
        notes = db.get_research_notes(status, limit)
        return jsonify({'notes': notes, 'total': len(notes)})
    
    else:  # POST
        data = request.get_json()
        note_id = db.add_research_note(
            query=data['query'],
            results=data.get('results', ''),
            priority=data.get('priority', 5),
            status=data.get('status', 'pending')
        )
        return jsonify({'note_id': note_id, 'message': 'Research note added'})

@app.route('/api/research/connections', methods=['POST'])
def add_connection():
    """Add connection between events"""
    data = request.get_json()
    connection_id = db.add_connection(
        event_id_1=data['event_id_1'],
        event_id_2=data['event_id_2'],
        connection_type=data.get('connection_type', 'related'),
        strength=data.get('strength', 1.0),
        notes=data.get('notes', '')
    )
    return jsonify({'connection_id': connection_id, 'message': 'Connection added'})

@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    with db.get_connection() as conn:
        stats = {}
        
        # Event stats
        stats['total_events'] = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        stats['total_actors'] = conn.execute("SELECT COUNT(*) FROM actors").fetchone()[0]  
        stats['total_tags'] = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
        stats['total_sources'] = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        
        # Events by year
        yearly = conn.execute("""
            SELECT substr(date, 1, 4) as year, COUNT(*) as count 
            FROM events 
            WHERE date IS NOT NULL
            GROUP BY substr(date, 1, 4)
            ORDER BY year
        """).fetchall()
        stats['events_by_year'] = {row['year']: row['count'] for row in yearly}
        
        # Status distribution
        status_dist = conn.execute("""
            SELECT status, COUNT(*) as count 
            FROM events 
            GROUP BY status
        """).fetchall()
        stats['status_distribution'] = {row['status']: row['count'] for row in status_dist}
        
        # Research workflow stats
        research_stats = conn.execute("""
            SELECT status, COUNT(*) as count
            FROM research_notes
            GROUP BY status
        """).fetchall()
        stats['research_notes'] = {row['status']: row['count'] for row in research_stats}
        
        stats['total_connections'] = conn.execute("SELECT COUNT(*) FROM research_connections").fetchone()[0]
    
    return jsonify(stats)

@app.route('/api/reload')
def reload_data():
    """Force reload from YAML files"""
    count = load_timeline_from_yaml()
    return jsonify({'message': f'Reloaded {count} events from YAML files'})

@app.route('/')
def index():
    """API documentation"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Timeline Research API</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                   max-width: 1000px; margin: 50px auto; padding: 20px; 
                   background: #0f172a; color: #e5e7eb; }}
            .endpoint {{ background: #1e293b; padding: 15px; margin: 15px 0; 
                       border-radius: 8px; font-family: monospace; border: 1px solid #334155; }}
            .method {{ display: inline-block; padding: 4px 8px; border-radius: 4px; 
                      font-weight: bold; margin-right: 10px; }}
            .get {{ background: #059669; }}
            .post {{ background: #dc2626; }}
            .put {{ background: #d97706; }}
            h1 {{ color: #3b82f6; }}
            h2 {{ color: #94a3b8; margin-top: 30px; }}
            .status {{ color: #10b981; margin: 20px 0; padding: 15px; 
                     background: rgba(16, 185, 129, 0.1); border-radius: 8px; 
                     border: 1px solid rgba(16, 185, 129, 0.3); }}
            code {{ background: #374151; padding: 2px 6px; border-radius: 4px; }}
            .description {{ margin: 10px 0; color: #9ca3af; }}
            .params {{ margin: 10px 0; color: #fbbf24; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <h1>🔍 Timeline Research API</h1>
        <div class="status">✅ SQLite-based research server with full-text search</div>
        
        <h2>Search & Query</h2>
        <div class="endpoint">
            <span class="method get">GET</span> /api/search
            <div class="description">Full-text search with advanced filters</div>
            <div class="params">
                Parameters: q, start_date, end_date, min_importance, max_importance, status, actor, tag, limit, offset
            </div>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> /api/event/&lt;event_id&gt;
            <div class="description">Get single event with connections</div>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> /api/actors
            <div class="description">Get all unique actors</div>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> /api/tags
            <div class="description">Get all unique tags</div>
        </div>
        
        <h2>Timeline Management</h2>
        <div class="endpoint">
            <span class="method post">POST</span> /api/events
            <div class="description">Create new timeline event</div>
            <div class="params">Add ?save_yaml=true to save to YAML file</div>
        </div>
        
        <div class="endpoint">
            <span class="method put">PUT</span> /api/events/&lt;event_id&gt;
            <div class="description">Update existing event</div>
            <div class="params">Add ?save_yaml=true to update YAML file</div>
        </div>
        
        <h2>Research Workflow</h2>
        <div class="endpoint">
            <span class="method get">GET</span> /api/research/notes
            <div class="description">Get research notes</div>
            <div class="params">Parameters: status, limit</div>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> /api/research/notes
            <div class="description">Add research note</div>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> /api/research/connections
            <div class="description">Add connection between events</div>
        </div>
        
        <h2>Utilities</h2>
        <div class="endpoint">
            <span class="method get">GET</span> /api/stats
            <div class="description">Get database statistics</div>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> /api/reload
            <div class="description">Force reload from YAML files</div>
        </div>
        
        <h2>Database</h2>
        <p>Database: <code>{DATABASE_PATH}</code></p>
        <p>YAML Events: <code>{TIMELINE_DIR}</code></p>
        <p>Full-text search enabled with SQLite FTS5</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("🔍 Timeline Research Server Starting...")
    print(f"📁 Loading events from: {TIMELINE_DIR}")
    print(f"💾 Database: {DATABASE_PATH}")
    
    # Initial load
    count = load_timeline_from_yaml()
    print(f"✅ Loaded {count} events")
    
    print("\n" + "="*60)
    print("🌐 Research API Server: http://127.0.0.1:5174")
    print("💡 Features:")
    print("   • Full-text search across all events")
    print("   • SQLite database with FTS5")
    print("   • Research workflow support")
    print("   • Event creation and editing")
    print("   • Connection tracking")
    print("   • Auto-sync with YAML files")
    print("="*60)
    
    app.run(debug=True, host='127.0.0.1', port=5174, use_reloader=False)