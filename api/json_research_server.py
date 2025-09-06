#!/usr/bin/env python3
"""
JSON-Based Timeline Research Server - Simplified SQLite + JSON approach
Uses SQLite's native JSON functions for optimal performance and simplicity
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

class JSONTimelineDatabase:
    """Simplified database using SQLite's JSON capabilities"""
    
    def __init__(self, db_path: str = "research_timeline_json.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize database with JSON-based schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Simple events table with JSON columns
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    importance INTEGER,
                    status TEXT DEFAULT 'confirmed',
                    notes TEXT DEFAULT '',
                    actors JSON,  -- JSON array of actor names
                    tags JSON,    -- JSON array of tag names  
                    sources JSON, -- JSON array of source objects
                    file_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Research notes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    results TEXT DEFAULT '',
                    priority INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_importance ON events(importance)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)")
            
            # JSON indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_actors ON events(json_extract(actors, '$'))")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_tags ON events(json_extract(tags, '$'))")
            
            conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def calculate_file_hash(self, event_data: Dict) -> str:
        """Calculate hash of event data for change detection"""
        def default_serializer(obj):
            """Custom serializer for date objects"""
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
        
        hashable = json.dumps(event_data, sort_keys=True, default=default_serializer)
        return hashlib.md5(hashable.encode()).hexdigest()

    def upsert_event(self, event_data: Dict) -> bool:
        """Insert or update event using JSON columns"""
        with self.get_connection() as conn:
            current_hash = self.calculate_file_hash(event_data)
            
            # Check if event exists and if it's changed
            existing = conn.execute(
                "SELECT file_hash FROM events WHERE id = ?", 
                (event_data['id'],)
            ).fetchone()
            
            if existing and existing['file_hash'] == current_hash:
                return False  # No change
            
            # Convert arrays to JSON
            actors_json = json.dumps(event_data.get('actors', []))
            tags_json = json.dumps(event_data.get('tags', []))
            sources_json = json.dumps(event_data.get('sources', []))
            
            # Insert/update event with JSON data
            conn.execute("""
                INSERT OR REPLACE INTO events 
                (id, date, title, summary, importance, status, notes, 
                 actors, tags, sources, file_hash, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                event_data['id'],
                str(event_data['date']),
                event_data['title'],
                event_data['summary'],
                event_data.get('importance'),
                event_data.get('status', 'confirmed'),
                event_data.get('notes', ''),
                actors_json,
                tags_json,
                sources_json,
                current_hash
            ))
            
            conn.commit()
            return True

    def search_events(self, query: str = '', filters: Dict = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Search events using JSON functions and LIKE queries"""
        filters = filters or {}
        
        with self.get_connection() as conn:
            # Base query
            base_query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            # Text search across multiple fields using LIKE
            if query.strip():
                base_query += """ AND (
                    title LIKE ? OR 
                    summary LIKE ? OR 
                    notes LIKE ? OR
                    actors LIKE ? OR
                    tags LIKE ?
                )"""
                search_term = f"%{query}%"
                params.extend([search_term, search_term, search_term, search_term, search_term])
            
            # Date filters
            if filters.get('start_date'):
                base_query += " AND date >= ?"
                params.append(filters['start_date'])
            if filters.get('end_date'):
                base_query += " AND date <= ?"
                params.append(filters['end_date'])
            
            # Importance filters
            if filters.get('min_importance'):
                base_query += " AND importance >= ?"
                params.append(filters['min_importance'])
            if filters.get('max_importance'):
                base_query += " AND importance <= ?"
                params.append(filters['max_importance'])
            
            # Status filter
            if filters.get('status'):
                base_query += " AND status = ?"
                params.append(filters['status'])
            
            # Actor filter using JSON
            if filters.get('actor'):
                base_query += " AND EXISTS (SELECT 1 FROM json_each(actors) WHERE value LIKE ?)"
                params.append(f"%{filters['actor']}%")
            
            # Tag filter using JSON
            if filters.get('tag'):
                base_query += " AND EXISTS (SELECT 1 FROM json_each(tags) WHERE value LIKE ?)"
                params.append(f"%{filters['tag']}%")
            
            # Order and limit
            base_query += " ORDER BY date DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            rows = conn.execute(base_query, params).fetchall()
            
            events = []
            for row in rows:
                event = dict(row)
                # Parse JSON fields
                event['actors'] = json.loads(event['actors']) if event['actors'] else []
                event['tags'] = json.loads(event['tags']) if event['tags'] else []
                event['sources'] = json.loads(event['sources']) if event['sources'] else []
                events.append(event)
            
            return events

    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            stats = {}
            
            # Basic counts
            stats['total_events'] = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            
            # Status distribution
            status_rows = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM events 
                GROUP BY status
            """).fetchall()
            stats['status_distribution'] = {row['status']: row['count'] for row in status_rows}
            
            # Events by year
            year_rows = conn.execute("""
                SELECT substr(date, 1, 4) as year, COUNT(*) as count
                FROM events 
                WHERE date IS NOT NULL
                GROUP BY substr(date, 1, 4)
                ORDER BY year
            """).fetchall()
            stats['events_by_year'] = {row['year']: row['count'] for row in year_rows}
            
            # Count unique actors using JSON
            total_actors = conn.execute("""
                SELECT COUNT(DISTINCT value) 
                FROM events, json_each(events.actors)
                WHERE value IS NOT NULL AND value != ''
            """).fetchone()[0]
            stats['total_actors'] = total_actors
            
            # Count unique tags using JSON
            total_tags = conn.execute("""
                SELECT COUNT(DISTINCT value) 
                FROM events, json_each(events.tags)
                WHERE value IS NOT NULL AND value != ''
            """).fetchone()[0]
            stats['total_tags'] = total_tags
            
            # Count total sources
            total_sources = conn.execute("""
                SELECT COUNT(*) 
                FROM events, json_each(events.sources)
            """).fetchone()[0]
            stats['total_sources'] = total_sources
            
            # Research notes stats
            research_stats = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM research_notes
                GROUP BY status
            """).fetchall()
            stats['research_notes'] = {row['status']: row['count'] for row in research_stats}
            
            return stats

    def get_actors(self) -> List[str]:
        """Get all unique actors"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT DISTINCT value as actor
                FROM events, json_each(events.actors)
                WHERE value IS NOT NULL AND value != ''
                ORDER BY value
            """).fetchall()
            return [row['actor'] for row in rows]

    def get_tags(self) -> List[str]:
        """Get all unique tags"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT DISTINCT value as tag
                FROM events, json_each(events.tags)
                WHERE value IS NOT NULL AND value != ''
                ORDER BY value
            """).fetchall()
            return [row['tag'] for row in rows]

    def add_research_note(self, query: str, results: str = '', priority: int = 5, status: str = 'pending') -> Dict:
        """Add research note"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO research_notes (query, results, priority, status)
                VALUES (?, ?, ?, ?)
            """, (query, results, priority, status))
            
            return {
                'note_id': cursor.lastrowid,
                'query': query,
                'results': results,
                'priority': priority,
                'status': status
            }

    def get_research_notes(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get research notes"""
        with self.get_connection() as conn:
            if status:
                rows = conn.execute("""
                    SELECT * FROM research_notes 
                    WHERE status = ? 
                    ORDER BY priority DESC, created_at ASC 
                    LIMIT ?
                """, (status, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM research_notes 
                    ORDER BY priority DESC, created_at ASC 
                    LIMIT ?
                """, (limit,)).fetchall()
            
            return [dict(row) for row in rows]

class JSONEventLoader:
    """Load events from YAML files into JSON database"""
    
    def __init__(self, db: JSONTimelineDatabase, events_dir: str):
        self.db = db
        self.events_dir = Path(events_dir)
        
    def load_all_events(self):
        """Load all YAML event files"""
        print("Loading timeline events from YAML files...")
        loaded_count = 0
        updated_count = 0
        
        for yaml_file in self.events_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    event_data = yaml.safe_load(f)
                    
                if event_data and self.db.upsert_event(event_data):
                    updated_count += 1
                loaded_count += 1
                    
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")
                continue
        
        print(f"Loaded {loaded_count} events ({updated_count} updated)")
        return loaded_count, updated_count

# Flask App
app = Flask(__name__)
CORS(app)

# Global database instance
db = None

def get_db():
    """Get database instance"""
    global db
    if db is None:
        db_path = os.path.join(os.getcwd(), "research_timeline_json.db")
        db = JSONTimelineDatabase(db_path)
        
        # Load events from YAML files
        events_dir = os.path.join(os.getcwd(), "timeline_data", "events")
        if os.path.exists(events_dir):
            loader = JSONEventLoader(db, events_dir)
            loader.load_all_events()
    
    return db

@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    return jsonify(get_db().get_stats())

@app.route('/api/search')  
def search_events():
    """Search events with filters"""
    query = request.args.get('q', '').strip()
    
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

    events = get_db().search_events(query, filters, limit, offset)

    return jsonify({
        'events': events,
        'total': len(events),
        'query': query,
        'filters': filters,
        'limit': limit,
        'offset': offset
    })

@app.route('/api/actors')
def get_actors():
    """Get all unique actors"""
    return jsonify({'actors': get_db().get_actors()})

@app.route('/api/tags')
def get_tags():
    """Get all unique tags"""
    return jsonify({'tags': get_db().get_tags()})

@app.route('/api/research/notes', methods=['GET', 'POST'])
def research_notes():
    """Get or add research notes"""
    if request.method == 'POST':
        data = request.get_json()
        note = get_db().add_research_note(
            query=data['query'],
            results=data.get('results', ''),
            priority=data.get('priority', 5),
            status=data.get('status', 'pending')
        )
        return jsonify(note)
    else:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        notes = get_db().get_research_notes(status, limit)
        return jsonify({'notes': notes})

@app.route('/api/reload')
def reload_data():
    """Force reload from YAML files"""
    events_dir = os.path.join(os.getcwd(), "timeline_data", "events")
    if os.path.exists(events_dir):
        loader = JSONEventLoader(get_db(), events_dir)
        loaded_count, updated_count = loader.load_all_events()
        return jsonify({
            'message': f'Reloaded {loaded_count} events ({updated_count} updated)',
            'loaded': loaded_count,
            'updated': updated_count
        })
    else:
        return jsonify({'error': 'Events directory not found'}), 404

if __name__ == "__main__":
    print("🔍 JSON Timeline Research Server Starting...")
    print(f"📁 Loading events from: {os.path.join(os.getcwd(), 'timeline_data', 'events')}")
    print(f"💾 Database: {os.path.join(os.getcwd(), 'research_timeline_json.db')}")
    
    # Initialize database
    get_db()
    
    print("✅ JSON-based timeline research server ready!")
    print()
    print("=" * 60)
    print("🌐 Research API Server: http://127.0.0.1:5174")
    print("💡 Features:")
    print("   • JSON-based SQLite storage with native JSON functions")
    print("   • Simple text search using LIKE queries")
    print("   • Actor and tag filtering with json_each()")
    print("   • Research workflow support")
    print("   • High performance with JSON indexes")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=5174, debug=True)