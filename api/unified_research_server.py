#!/usr/bin/env python3
"""
Unified Research Server - Combined Timeline Events + Research Priorities API
Merges research_server.py and research_priorities_server.py into single service
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import threading
import time
import logging
from flask import Flask, jsonify, request, abort
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedResearchDatabase:
    def __init__(self, 
                 events_dir: str = "timeline_data/events",
                 priorities_dir: str = "research_priorities", 
                 db_path: str = "unified_research.db"):
        self.events_dir = Path(events_dir)
        self.priorities_dir = Path(priorities_dir)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self.file_hashes = {'events': {}, 'priorities': {}}
        
        self.init_database()
        self.load_timeline_events()
        self.load_research_priorities()
        
    def init_database(self):
        """Initialize unified database with timeline events and research priorities"""
        cursor = self.conn.cursor()
        
        # ===== TIMELINE EVENTS TABLES =====
        
        # Main events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                date DATE NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                importance INTEGER CHECK(importance BETWEEN 1 AND 10),
                status TEXT DEFAULT 'confirmed',
                file_path TEXT,
                file_hash TEXT
            )
        ''')
        
        # Actors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Tags table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                outlet TEXT,
                date DATE,
                FOREIGN KEY (event_id) REFERENCES events(id)
            )
        ''')
        
        # Junction tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_actors (
                event_id TEXT NOT NULL,
                actor_id INTEGER NOT NULL,
                PRIMARY KEY (event_id, actor_id),
                FOREIGN KEY (event_id) REFERENCES events(id),
                FOREIGN KEY (actor_id) REFERENCES actors(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_tags (
                event_id TEXT NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (event_id, tag_id),
                FOREIGN KEY (event_id) REFERENCES events(id),
                FOREIGN KEY (tag_id) REFERENCES tags(id)
            )
        ''')
        
        # ===== RESEARCH PRIORITIES TABLES =====
        
        # Main research priorities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_priorities (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 5 CHECK(priority BETWEEN 1 AND 10),
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'blocked', 'abandoned')),
                category TEXT,
                tags TEXT,
                estimated_events INTEGER DEFAULT 1,
                actual_events INTEGER DEFAULT 0,
                created_date DATE,
                updated_date DATE,
                completion_date DATE,
                triggered_by TEXT,
                time_period TEXT,
                constitutional_issues TEXT,
                estimated_importance INTEGER,
                research_notes TEXT,
                file_path TEXT,
                file_hash TEXT
            )
        ''')
        
        # Research sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                priority_id TEXT NOT NULL,
                title TEXT NOT NULL,
                type TEXT,
                credibility INTEGER CHECK(credibility BETWEEN 1 AND 10),
                why TEXT,
                url TEXT,
                author TEXT,
                FOREIGN KEY (priority_id) REFERENCES research_priorities(id)
            )
        ''')
        
        # Events created from research
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_events_created (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                priority_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                event_title TEXT,
                event_date DATE,
                created_date DATE,
                FOREIGN KEY (priority_id) REFERENCES research_priorities(id)
            )
        ''')
        
        # ===== FULL-TEXT SEARCH =====
        
        # Events FTS
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS events_fts 
            USING fts5(id, title, summary, content=events)
        ''')
        
        # Research priorities FTS
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS research_priorities_fts 
            USING fts5(id, title, description, tags, research_notes, content=research_priorities)
        ''')
        
        # ===== INDEXES =====
        
        # Timeline events indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_importance ON events(importance DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)')
        
        # Research priorities indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_status ON research_priorities(priority DESC, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_category ON research_priorities(category)')
        
        self.conn.commit()
        logger.info("Unified research database initialized")
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for change detection"""
        if not file_path.exists():
            return ""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def load_timeline_events(self):
        """Load timeline events from JSON files"""
        if not self.events_dir.exists():
            logger.warning(f"Timeline events directory {self.events_dir} does not exist")
            return
        
        with self.lock:
            cursor = self.conn.cursor()
            json_files = list(self.events_dir.glob("*.json"))
            logger.info(f"Found {len(json_files)} timeline event files")
            
            for json_file in json_files:
                try:
                    file_hash = self.calculate_file_hash(json_file)
                    
                    # Check if file changed
                    if json_file.name in self.file_hashes['events'] and \
                       self.file_hashes['events'][json_file.name] == file_hash:
                        continue
                    
                    # Load and parse JSON
                    with open(json_file, 'r', encoding='utf-8') as f:
                        event_data = json.load(f)
                    
                    self.insert_or_update_event(event_data, str(json_file), file_hash)
                    self.file_hashes['events'][json_file.name] = file_hash
                    
                except Exception as e:
                    logger.error(f"Error loading timeline event {json_file}: {e}")
            
            self.conn.commit()
            logger.info("Timeline events loaded successfully")
    
    def load_research_priorities(self):
        """Load research priorities from JSON files"""
        if not self.priorities_dir.exists():
            logger.warning(f"Research priorities directory {self.priorities_dir} does not exist")
            return
        
        with self.lock:
            cursor = self.conn.cursor()
            json_files = list(self.priorities_dir.glob("*.json"))
            logger.info(f"Found {len(json_files)} research priority files")
            
            for json_file in json_files:
                try:
                    file_hash = self.calculate_file_hash(json_file)
                    
                    # Check if file changed
                    if json_file.name in self.file_hashes['priorities'] and \
                       self.file_hashes['priorities'][json_file.name] == file_hash:
                        continue
                    
                    # Load and parse JSON
                    with open(json_file, 'r', encoding='utf-8') as f:
                        priority_data = json.load(f)
                    
                    self.insert_or_update_priority(priority_data, str(json_file), file_hash)
                    self.file_hashes['priorities'][json_file.name] = file_hash
                    
                except Exception as e:
                    logger.error(f"Error loading research priority {json_file}: {e}")
            
            self.conn.commit()
            logger.info("Research priorities loaded successfully")
    
    def insert_or_update_event(self, event_data: Dict, file_path: str, file_hash: str):
        """Insert or update a timeline event"""
        cursor = self.conn.cursor()
        
        # Insert main event
        cursor.execute('''
            INSERT OR REPLACE INTO events 
            (id, date, title, summary, importance, status, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_data.get('id', ''),
            event_data.get('date', ''),
            event_data.get('title', ''),
            event_data.get('summary', ''),
            event_data.get('importance', 5),
            event_data.get('status', 'confirmed'),
            file_path,
            file_hash
        ))
        
        event_id = event_data.get('id', '')
        
        # Clear related data
        cursor.execute('DELETE FROM sources WHERE event_id = ?', (event_id,))
        cursor.execute('DELETE FROM event_actors WHERE event_id = ?', (event_id,))
        cursor.execute('DELETE FROM event_tags WHERE event_id = ?', (event_id,))
        
        # Insert sources
        for source in event_data.get('sources', []):
            cursor.execute('''
                INSERT INTO sources (event_id, title, url, outlet, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (event_id, source.get('title', ''), source.get('url'), 
                  source.get('outlet'), source.get('date')))
        
        # Insert actors
        for actor_name in event_data.get('actors', []):
            cursor.execute('INSERT OR IGNORE INTO actors (name) VALUES (?)', (actor_name,))
            cursor.execute('SELECT id FROM actors WHERE name = ?', (actor_name,))
            actor_id = cursor.fetchone()[0]
            cursor.execute('INSERT INTO event_actors (event_id, actor_id) VALUES (?, ?)', 
                          (event_id, actor_id))
        
        # Insert tags
        for tag_name in event_data.get('tags', []):
            cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag_name,))
            cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
            tag_id = cursor.fetchone()[0]
            cursor.execute('INSERT INTO event_tags (event_id, tag_id) VALUES (?, ?)', 
                          (event_id, tag_id))
    
    def insert_or_update_priority(self, priority_data: Dict, file_path: str, file_hash: str):
        """Insert or update a research priority"""
        cursor = self.conn.cursor()
        
        # Insert/update main priority
        cursor.execute('''
            INSERT OR REPLACE INTO research_priorities 
            (id, title, description, priority, status, category, tags, estimated_events, actual_events,
             created_date, updated_date, completion_date, triggered_by, time_period, 
             constitutional_issues, estimated_importance, research_notes, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            priority_data['id'],
            priority_data['title'],
            priority_data['description'],
            priority_data['priority'],
            priority_data['status'],
            priority_data.get('category'),
            json.dumps(priority_data.get('tags', [])),
            priority_data.get('estimated_events', 1),
            priority_data.get('actual_events', 0),
            priority_data.get('created_date'),
            priority_data.get('updated_date'),
            priority_data.get('completion_date'),
            json.dumps(priority_data.get('triggered_by', [])),
            priority_data.get('time_period'),
            json.dumps(priority_data.get('constitutional_issues', [])),
            priority_data.get('estimated_importance'),
            priority_data.get('research_notes'),
            file_path,
            file_hash
        ))
        
        priority_id = priority_data['id']
        
        # Clear and insert research sources
        cursor.execute('DELETE FROM research_sources WHERE priority_id = ?', (priority_id,))
        for source in priority_data.get('key_sources', []):
            cursor.execute('''
                INSERT INTO research_sources (priority_id, title, type, credibility, why, url, author)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (priority_id, source['title'], source.get('type'), source.get('credibility'),
                  source.get('why'), source.get('url'), source.get('author')))
        
        # Clear and insert events created
        cursor.execute('DELETE FROM research_events_created WHERE priority_id = ?', (priority_id,))
        for event in priority_data.get('events_created', []):
            cursor.execute('''
                INSERT INTO research_events_created (priority_id, event_id, event_title, event_date, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (priority_id, event['event_id'], event.get('event_title'), 
                  event.get('event_date'), event.get('created_date')))
    
    # ===== TIMELINE EVENT QUERIES =====
    
    def search_events(self, query: str, limit: int = 20, **filters) -> List[Dict]:
        """Search timeline events with filters"""
        cursor = self.conn.cursor()
        
        base_query = '''
            SELECT DISTINCT e.* FROM events e
            JOIN events_fts fts ON e.id = fts.id
            WHERE events_fts MATCH ?
        '''
        params = [query]
        
        # Add filters
        if filters.get('start_date'):
            base_query += ' AND e.date >= ?'
            params.append(filters['start_date'])
        
        if filters.get('end_date'):
            base_query += ' AND e.date <= ?'
            params.append(filters['end_date'])
        
        if filters.get('min_importance'):
            base_query += ' AND e.importance >= ?'
            params.append(filters['min_importance'])
        
        if filters.get('actor'):
            base_query += '''
                AND e.id IN (
                    SELECT ea.event_id FROM event_actors ea
                    JOIN actors a ON ea.actor_id = a.id
                    WHERE a.name LIKE ?
                )
            '''
            params.append(f'%{filters["actor"]}%')
        
        base_query += ' ORDER BY e.importance DESC, e.date DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(base_query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """Get timeline event with full details"""
        cursor = self.conn.cursor()
        
        # Get main event
        cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
        event = cursor.fetchone()
        if not event:
            return None
        
        event = dict(event)
        
        # Get actors
        cursor.execute('''
            SELECT a.name FROM actors a
            JOIN event_actors ea ON a.id = ea.actor_id
            WHERE ea.event_id = ?
        ''', (event_id,))
        event['actors'] = [row[0] for row in cursor.fetchall()]
        
        # Get tags
        cursor.execute('''
            SELECT t.name FROM tags t
            JOIN event_tags et ON t.id = et.tag_id
            WHERE et.event_id = ?
        ''', (event_id,))
        event['tags'] = [row[0] for row in cursor.fetchall()]
        
        # Get sources
        cursor.execute('SELECT * FROM sources WHERE event_id = ?', (event_id,))
        event['sources'] = [dict(row) for row in cursor.fetchall()]
        
        return event
    
    # ===== RESEARCH PRIORITY QUERIES =====
    
    def search_priorities(self, query: str, limit: int = 20) -> List[Dict]:
        """Search research priorities"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT rp.* FROM research_priorities rp
            JOIN research_priorities_fts fts ON rp.id = fts.id
            WHERE research_priorities_fts MATCH ?
            ORDER BY rp.priority DESC
            LIMIT ?
        ''', (query, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_priority_by_id(self, priority_id: str) -> Optional[Dict]:
        """Get research priority with full details"""
        cursor = self.conn.cursor()
        
        # Get main priority
        cursor.execute('SELECT * FROM research_priorities WHERE id = ?', (priority_id,))
        priority = cursor.fetchone()
        if not priority:
            return None
        
        priority = dict(priority)
        
        # Get sources
        cursor.execute('SELECT * FROM research_sources WHERE priority_id = ?', (priority_id,))
        priority['key_sources'] = [dict(row) for row in cursor.fetchall()]
        
        # Get events created
        cursor.execute('SELECT * FROM research_events_created WHERE priority_id = ?', (priority_id,))
        priority['events_created'] = [dict(row) for row in cursor.fetchall()]
        
        return priority
    
    def get_priorities_by_status(self, status: str = 'pending', limit: int = 20) -> List[Dict]:
        """Get research priorities by status"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM research_priorities 
            WHERE status = ?
            ORDER BY priority DESC, created_date ASC
            LIMIT ?
        ''', (status, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ===== STATISTICS =====
    
    def get_statistics(self) -> Dict:
        """Get combined statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Timeline events stats
        cursor.execute('SELECT COUNT(*) FROM events')
        stats['timeline_events_total'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(importance) FROM events')
        stats['timeline_avg_importance'] = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT status, COUNT(*) FROM events GROUP BY status')
        stats['timeline_by_status'] = dict(cursor.fetchall())
        
        # Research priorities stats
        cursor.execute('SELECT COUNT(*) FROM research_priorities')
        stats['research_priorities_total'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT status, COUNT(*) FROM research_priorities GROUP BY status')
        stats['research_by_status'] = dict(cursor.fetchall())
        
        cursor.execute('SELECT SUM(actual_events) FROM research_priorities')
        stats['events_from_research'] = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(priority) FROM research_priorities WHERE status = "pending"')
        stats['research_avg_pending_priority'] = cursor.fetchone()[0] or 0
        
        return stats

# Flask API
app = Flask(__name__)
CORS(app)
db = UnifiedResearchDatabase()

# ===== TIMELINE EVENTS ENDPOINTS =====

@app.route('/api/events/search')
def search_events():
    """Search timeline events"""
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 20)), 100)
    
    filters = {}
    if request.args.get('start_date'):
        filters['start_date'] = request.args.get('start_date')
    if request.args.get('end_date'):  
        filters['end_date'] = request.args.get('end_date')
    if request.args.get('min_importance'):
        filters['min_importance'] = int(request.args.get('min_importance'))
    if request.args.get('actor'):
        filters['actor'] = request.args.get('actor')
    
    if not query:
        return jsonify({'error': 'Query parameter q required'}), 400
    
    results = db.search_events(query, limit, **filters)
    return jsonify({
        'results': results,
        'count': len(results),
        'query': query,
        'filters': filters
    })

@app.route('/api/events/<event_id>')
def get_event(event_id):
    """Get specific timeline event"""
    event = db.get_event_by_id(event_id)
    if not event:
        abort(404)
    return jsonify(event)

# ===== RESEARCH PRIORITIES ENDPOINTS =====

@app.route('/api/research-priorities/search')
def search_priorities():
    """Search research priorities"""
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 20)), 100)
    
    if not query:
        return jsonify({'error': 'Query parameter q required'}), 400
    
    results = db.search_priorities(query, limit)
    return jsonify({
        'results': results,
        'count': len(results),
        'query': query
    })

@app.route('/api/research-priorities/<priority_id>')
def get_priority(priority_id):
    """Get specific research priority"""
    priority = db.get_priority_by_id(priority_id)
    if not priority:
        abort(404)
    return jsonify(priority)

@app.route('/api/research-priorities/status/<status>')
def get_priorities_by_status(status):
    """Get research priorities by status"""
    limit = min(int(request.args.get('limit', 20)), 100)
    priorities = db.get_priorities_by_status(status, limit)
    return jsonify({
        'priorities': priorities,
        'count': len(priorities),
        'status': status
    })

# ===== UNIFIED ENDPOINTS =====

@app.route('/api/stats')
def get_stats():
    """Get unified statistics"""
    return jsonify(db.get_statistics())

@app.route('/api/reload')
def reload_data():
    """Force reload from JSON files"""
    db.load_timeline_events()
    db.load_research_priorities()
    return jsonify({'status': 'reloaded'})

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'services': ['timeline-events', 'research-priorities'],
        'database': 'unified_research.db'
    })

if __name__ == '__main__':
    # Background thread to reload data periodically
    def background_reload():
        while True:
            time.sleep(300)  # 5 minutes
            try:
                db.load_timeline_events()
                db.load_research_priorities()
            except Exception as e:
                logger.error(f"Background reload failed: {e}")
    
    reload_thread = threading.Thread(target=background_reload, daemon=True)
    reload_thread.start()
    
    logger.info("Starting Unified Research Server on http://127.0.0.1:5174")
    app.run(host='127.0.0.1', port=5174, debug=False)