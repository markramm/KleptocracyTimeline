#!/usr/bin/env python3
"""
Research Priorities Server - Mirrors JSON files in SQLite for API access
Similar to the timeline research server but for research priorities management
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
import os
import signal
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Flask, jsonify, request, abort

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileChangeHandler(FileSystemEventHandler):
    """Handle filesystem changes for auto-reload"""
    def __init__(self, database):
        self.database = database
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            logger.info(f"File changed: {event.src_path}")
            # Debounce rapid changes
            time.sleep(0.1)
            self.database.load_priorities()
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            logger.info(f"File created: {event.src_path}")
            time.sleep(0.1)
            self.database.load_priorities()
    
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            logger.info(f"File deleted: {event.src_path}")
            self.database.load_priorities()

class UnifiedResearchDatabase:
    def __init__(self, priorities_dir: str = "research_priorities", db_path: str = "unified_research.db", 
                 timeline_dir: str = "timeline_data/events"):
        self.priorities_dir = Path(priorities_dir)
        self.timeline_dir = Path(timeline_dir)
        self.db_path = db_path
        self.backup_db_path = f"{db_path}.backup"
        self.lock = threading.Lock()
        self.file_hashes = {}
        self.timeline_hashes = {}
        self.observer = None
        
        # Initialize database with corruption recovery
        self.init_database_with_recovery()
        self.load_priorities()
        self.load_timeline_events()
        self.setup_file_monitoring()
        
    def init_database_with_recovery(self):
        """Initialize database with corruption recovery"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.init_database()
        except sqlite3.DatabaseError as e:
            logger.error(f"Database corrupted: {e}")
            self.recover_database()
    
    def recover_database(self):
        """Recover from database corruption by rebuilding from JSON files"""
        logger.info("Attempting database recovery...")
        
        # Backup corrupted database
        if os.path.exists(self.db_path):
            corrupted_backup = f"{self.db_path}.corrupted.{int(time.time())}"
            shutil.move(self.db_path, corrupted_backup)
            logger.info(f"Corrupted database backed up to: {corrupted_backup}")
        
        # Create new database
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_database()
        
        # Clear file hashes to force full reload
        self.file_hashes = {}
        
        logger.info("Database recovered successfully")
    
    def init_database(self):
        """Initialize research priorities tables"""
        cursor = self.conn.cursor()
        
        # Main research priorities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_priorities (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 5 CHECK(priority BETWEEN 1 AND 10),
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'blocked', 'abandoned')),
                category TEXT,
                tags TEXT, -- JSON array
                estimated_events INTEGER DEFAULT 1,
                actual_events INTEGER DEFAULT 0,
                created_date DATE,
                updated_date DATE,
                completion_date DATE,
                triggered_by TEXT, -- JSON array of event IDs
                time_period TEXT,
                constitutional_issues TEXT, -- JSON array
                estimated_importance INTEGER,
                research_notes TEXT,
                file_path TEXT,
                file_hash TEXT
            )
        ''')
        
        # Key sources table
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
        
        # Connections between research priorities
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_priority_id TEXT NOT NULL,
                to_priority_id TEXT NOT NULL,
                connection_type TEXT,
                description TEXT,
                FOREIGN KEY (from_priority_id) REFERENCES research_priorities(id),
                FOREIGN KEY (to_priority_id) REFERENCES research_priorities(id)
            )
        ''')
        
        # Actors to investigate
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_actors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                priority_id TEXT NOT NULL,
                actor_name TEXT NOT NULL,
                FOREIGN KEY (priority_id) REFERENCES research_priorities(id)
            )
        ''')
        
        # Expected outcomes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                priority_id TEXT NOT NULL,
                outcome_description TEXT NOT NULL,
                achieved BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (priority_id) REFERENCES research_priorities(id)
            )
        ''')
        
        # Create optimized indexes for research priorities
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_status ON research_priorities(priority DESC, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_category ON research_priorities(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_importance ON research_priorities(estimated_importance DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_created ON research_priorities(created_date DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_composite ON research_priorities(status, priority DESC, estimated_importance DESC)')
        
        # Timeline events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS timeline_events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                date DATE NOT NULL,
                description TEXT,
                category TEXT,
                actors TEXT, -- JSON
                location TEXT,
                sources TEXT, -- JSON
                constitutional_issues TEXT, -- JSON
                importance INTEGER DEFAULT 5 CHECK(importance BETWEEN 1 AND 10),
                tags TEXT, -- JSON
                connections TEXT, -- JSON
                historical_significance TEXT,
                file_path TEXT,
                file_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Timeline actors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS timeline_actors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                actor_name TEXT NOT NULL,
                actor_role TEXT,
                actor_affiliation TEXT,
                actor_type TEXT, -- primary/secondary
                FOREIGN KEY (event_id) REFERENCES timeline_events(id)
            )
        ''')
        
        # Timeline sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS timeline_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                title TEXT NOT NULL,
                type TEXT,
                credibility INTEGER CHECK(credibility BETWEEN 1 AND 10),
                description TEXT,
                url TEXT,
                author TEXT,
                FOREIGN KEY (event_id) REFERENCES timeline_events(id)
            )
        ''')
        
        # Create optimized timeline indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_date ON timeline_events(date DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_importance ON timeline_events(importance DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_category ON timeline_events(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_title ON timeline_events(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_date_importance ON timeline_events(date, importance DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_composite ON timeline_events(date DESC, importance DESC, category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_actors ON timeline_actors(actor_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_actor_event ON timeline_actors(event_id, actor_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_sources_event ON timeline_sources(event_id, credibility DESC)')
        
        # Full-text search tables
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS research_priorities_fts 
            USING fts5(id, title, description, tags, research_notes, content=research_priorities)
        ''')
        
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS timeline_events_fts 
            USING fts5(id, title, description, tags, historical_significance, content=timeline_events)
        ''')
        
        self.conn.commit()
        logger.info("Research priorities database initialized")
        
        # Enable WAL mode and optimize for performance
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA synchronous=NORMAL')
        cursor.execute('PRAGMA cache_size=20000')  # Increased cache
        cursor.execute('PRAGMA temp_store=memory')
        cursor.execute('PRAGMA mmap_size=268435456')  # 256MB memory mapping
        cursor.execute('PRAGMA optimize')  # Analyze statistics
        self.conn.commit()
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for change detection"""
        if not file_path.exists():
            return ""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def load_priorities(self):
        """Load all JSON files from research_priorities directory"""
        if not self.priorities_dir.exists():
            logger.warning(f"Research priorities directory {self.priorities_dir} does not exist")
            return
        
        with self.lock:
            cursor = self.conn.cursor()
            
            # Get current files
            json_files = list(self.priorities_dir.glob("*.json"))
            logger.info(f"Found {len(json_files)} research priority files")
            
            for json_file in json_files:
                try:
                    file_hash = self.calculate_file_hash(json_file)
                    
                    # Check if file changed
                    if json_file.name in self.file_hashes and self.file_hashes[json_file.name] == file_hash:
                        continue
                    
                    # Load and parse JSON
                    with open(json_file, 'r', encoding='utf-8') as f:
                        priority_data = json.load(f)
                    
                    self.insert_or_update_priority(priority_data, str(json_file), file_hash)
                    self.file_hashes[json_file.name] = file_hash
                    
                except Exception as e:
                    logger.error(f"Error loading {json_file}: {e}")
            
            self.conn.commit()
            self.create_backup()
            logger.info("Research priorities loaded successfully")
    
    def setup_file_monitoring(self):
        """Setup file system monitoring for auto-reload"""
        try:
            self.observer = Observer()
            
            # Monitor research priorities directory
            if self.priorities_dir.exists():
                handler = FileChangeHandler(self)
                self.observer.schedule(handler, str(self.priorities_dir), recursive=False)
                logger.info(f"Monitoring {self.priorities_dir} for changes")
            
            # Monitor timeline directory for new events
            if self.timeline_dir.exists():
                timeline_handler = FileChangeHandler(self)
                self.observer.schedule(timeline_handler, str(self.timeline_dir), recursive=False)
                logger.info(f"Monitoring {self.timeline_dir} for timeline changes")
                
            self.observer.start()
            
        except Exception as e:
            logger.error(f"Failed to setup file monitoring: {e}")
            self.observer = None
    
    def create_backup(self):
        """Create backup of current database"""
        try:
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, self.backup_db_path)
                logger.debug("Database backup created")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
    
    def stop_monitoring(self):
        """Stop file system monitoring"""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("File monitoring stopped")
    
    def load_timeline_events(self):
        """Load all JSON timeline events from timeline directory"""
        if not self.timeline_dir.exists():
            logger.warning(f"Timeline directory {self.timeline_dir} does not exist")
            return
        
        with self.lock:
            cursor = self.conn.cursor()
            
            # Get current timeline files
            json_files = list(self.timeline_dir.glob("*.json"))
            logger.info(f"Found {len(json_files)} timeline event files")
            
            for json_file in json_files:
                try:
                    file_hash = self.calculate_file_hash(json_file)
                    
                    # Check if file changed
                    if json_file.name in self.timeline_hashes and self.timeline_hashes[json_file.name] == file_hash:
                        continue
                    
                    # Load and parse JSON
                    with open(json_file, 'r', encoding='utf-8') as f:
                        event_data = json.load(f)
                    
                    self.insert_or_update_timeline_event(event_data, str(json_file), file_hash)
                    self.timeline_hashes[json_file.name] = file_hash
                    
                except Exception as e:
                    logger.error(f"Error loading timeline event {json_file}: {e}")
            
            self.conn.commit()
            logger.info("Timeline events loaded successfully")
    
    def insert_or_update_timeline_event(self, event_data: Dict, file_path: str, file_hash: str):
        """Insert or update a timeline event in the database"""
        cursor = self.conn.cursor()
        
        # Insert/update main event
        cursor.execute('''
            INSERT OR REPLACE INTO timeline_events 
            (id, title, date, description, category, actors, location, sources, 
             constitutional_issues, importance, tags, connections, historical_significance, 
             file_path, file_hash, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            event_data['id'],
            event_data['title'],
            event_data['date'],
            event_data.get('description', ''),
            event_data.get('category', ''),
            json.dumps(event_data.get('actors', {})),
            event_data.get('location', ''),
            json.dumps(event_data.get('sources', [])),
            json.dumps(event_data.get('constitutional_issues', [])),
            event_data.get('importance', 5),
            json.dumps(event_data.get('tags', [])),
            json.dumps(event_data.get('connections', {})),
            event_data.get('historical_significance', ''),
            file_path,
            file_hash
        ))
        
        event_id = event_data['id']
        
        # Clear existing related data
        cursor.execute('DELETE FROM timeline_actors WHERE event_id = ?', (event_id,))
        cursor.execute('DELETE FROM timeline_sources WHERE event_id = ?', (event_id,))
        
        # Insert actors (handle both list and object formats)
        actors = event_data.get('actors', {})
        if isinstance(actors, list):
            # Handle legacy list format
            for actor in actors:
                if isinstance(actor, str):
                    actor_name = actor
                    actor_role = ''
                    actor_affiliation = ''
                else:
                    actor_name = actor.get('name', '')
                    actor_role = actor.get('role', '')
                    actor_affiliation = actor.get('affiliation', '')
                cursor.execute('''
                    INSERT INTO timeline_actors (event_id, actor_name, actor_role, actor_affiliation, actor_type)
                    VALUES (?, ?, ?, ?, ?)
                ''', (event_id, actor_name, actor_role, actor_affiliation, 'primary'))
        else:
            # Handle object format with primary/secondary
            for actor_type in ['primary', 'secondary']:
                for actor in actors.get(actor_type, []):
                    if isinstance(actor, str):
                        actor_name = actor
                        actor_role = ''
                        actor_affiliation = ''
                    else:
                        actor_name = actor.get('name', '')
                        actor_role = actor.get('role', '')
                        actor_affiliation = actor.get('affiliation', '')
                    cursor.execute('''
                        INSERT INTO timeline_actors (event_id, actor_name, actor_role, actor_affiliation, actor_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (event_id, actor_name, actor_role, actor_affiliation, actor_type))
        
        # Insert sources
        for source in event_data.get('sources', []):
            cursor.execute('''
                INSERT INTO timeline_sources (event_id, title, type, credibility, description, url, author)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (event_id, source.get('title', ''), source.get('type', ''), 
                  source.get('credibility', 5), source.get('description', ''), 
                  source.get('url', ''), source.get('author', '')))
        
        # Update FTS
        cursor.execute('''
            INSERT OR REPLACE INTO timeline_events_fts (id, title, description, tags, historical_significance)
            VALUES (?, ?, ?, ?, ?)
        ''', (event_id, event_data['title'], event_data.get('description', ''),
              json.dumps(event_data.get('tags', [])), event_data.get('historical_significance', '')))
    
    def insert_or_update_priority(self, priority_data: Dict, file_path: str, file_hash: str):
        """Insert or update a research priority in the database"""
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
        
        # Clear related data
        cursor.execute('DELETE FROM research_sources WHERE priority_id = ?', (priority_id,))
        cursor.execute('DELETE FROM research_events_created WHERE priority_id = ?', (priority_id,))
        cursor.execute('DELETE FROM research_connections WHERE from_priority_id = ?', (priority_id,))
        cursor.execute('DELETE FROM research_actors WHERE priority_id = ?', (priority_id,))
        cursor.execute('DELETE FROM research_outcomes WHERE priority_id = ?', (priority_id,))
        
        # Insert sources
        for source in priority_data.get('key_sources', []):
            cursor.execute('''
                INSERT INTO research_sources (priority_id, title, type, credibility, why, url, author)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (priority_id, source['title'], source.get('type'), source.get('credibility'),
                  source.get('why'), source.get('url'), source.get('author')))
        
        # Insert events created
        for event in priority_data.get('events_created', []):
            cursor.execute('''
                INSERT INTO research_events_created (priority_id, event_id, event_title, event_date, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (priority_id, event['event_id'], event.get('event_title'), 
                  event.get('event_date'), event.get('created_date')))
        
        # Insert connections
        for connection in priority_data.get('connections', []):
            cursor.execute('''
                INSERT INTO research_connections (from_priority_id, to_priority_id, connection_type, description)
                VALUES (?, ?, ?, ?)
            ''', (priority_id, connection['to'], connection.get('type'), connection.get('description')))
        
        # Insert actors
        for actor in priority_data.get('actors_to_investigate', []):
            cursor.execute('INSERT INTO research_actors (priority_id, actor_name) VALUES (?, ?)', 
                          (priority_id, actor))
        
        # Insert expected outcomes
        for outcome in priority_data.get('expected_outcomes', []):
            cursor.execute('INSERT INTO research_outcomes (priority_id, outcome_description) VALUES (?, ?)',
                          (priority_id, outcome))
    
    def search_priorities(self, query: str, limit: int = 20) -> List[Dict]:
        """Full-text search research priorities"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT rp.* FROM research_priorities rp
            JOIN research_priorities_fts fts ON rp.id = fts.id
            WHERE research_priorities_fts MATCH ?
            ORDER BY rp.priority DESC
            LIMIT ?
        ''', (query, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_timeline(self, query: str = None, limit: int = 20, importance_min: int = None, 
                       date_from: str = None, date_to: str = None, category: str = None) -> List[Dict]:
        """Search timeline events with various filters"""
        cursor = self.conn.cursor()
        
        if query:
            # Full-text search
            sql = '''
                SELECT te.* FROM timeline_events te
                JOIN timeline_events_fts fts ON te.id = fts.id
                WHERE timeline_events_fts MATCH ?
            '''
            params = [query]
        else:
            # Regular search with filters
            sql = 'SELECT * FROM timeline_events WHERE 1=1'
            params = []
        
        # Add filters
        if importance_min:
            sql += ' AND importance >= ?'
            params.append(importance_min)
        
        if date_from:
            sql += ' AND date >= ?'
            params.append(date_from)
            
        if date_to:
            sql += ' AND date <= ?'
            params.append(date_to)
            
        if category:
            sql += ' AND category = ?'
            params.append(category)
        
        sql += ' ORDER BY date DESC, importance DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_timeline_event_by_id(self, event_id: str) -> Optional[Dict]:
        """Get a timeline event with all related data"""
        cursor = self.conn.cursor()
        
        # Get main event
        cursor.execute('SELECT * FROM timeline_events WHERE id = ?', (event_id,))
        event = cursor.fetchone()
        if not event:
            return None
        
        event = dict(event)
        
        # Get actors
        cursor.execute('SELECT * FROM timeline_actors WHERE event_id = ? ORDER BY actor_type, actor_name', (event_id,))
        actors = {'primary': [], 'secondary': []}
        for actor in cursor.fetchall():
            actor_dict = dict(actor)
            actor_type = actor_dict.pop('actor_type', 'primary')
            actors[actor_type].append(actor_dict)
        event['actors'] = actors
        
        # Get sources
        cursor.execute('SELECT * FROM timeline_sources WHERE event_id = ? ORDER BY credibility DESC', (event_id,))
        event['sources'] = [dict(row) for row in cursor.fetchall()]
        
        return event
    
    def get_priority_by_id(self, priority_id: str) -> Optional[Dict]:
        """Get a research priority with all related data"""
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
        
        # Get connections
        cursor.execute('SELECT * FROM research_connections WHERE from_priority_id = ?', (priority_id,))
        priority['connections'] = [dict(row) for row in cursor.fetchall()]
        
        # Get actors
        cursor.execute('SELECT actor_name FROM research_actors WHERE priority_id = ?', (priority_id,))
        priority['actors_to_investigate'] = [row[0] for row in cursor.fetchall()]
        
        # Get outcomes
        cursor.execute('SELECT * FROM research_outcomes WHERE priority_id = ?', (priority_id,))
        priority['expected_outcomes'] = [dict(row) for row in cursor.fetchall()]
        
        return priority
    
    def get_priorities_by_status(self, status: str = 'pending', limit: int = 20) -> List[Dict]:
        """Get research priorities by status, ordered by priority"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM research_priorities 
            WHERE status = ?
            ORDER BY priority DESC, created_date ASC
            LIMIT ?
        ''', (status, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def find_similar_timeline_events(self, event_data: Dict) -> List[Dict]:
        """Optimized similarity detection for timeline events"""
        cursor = self.conn.cursor()
        similar = []
        seen_event_ids = set()
        
        proposed_date = event_data.get('date', '')
        proposed_title = event_data.get('title', '').lower()
        proposed_actors = set()
        
        # Extract actor names from various formats (optimized)
        actors = event_data.get('actors', {})
        if isinstance(actors, list):
            proposed_actors = {str(actor).lower() for actor in actors}
        elif isinstance(actors, dict):
            for actor_type in ['primary', 'secondary']:
                for actor in actors.get(actor_type, []):
                    if isinstance(actor, str):
                        proposed_actors.add(actor.lower())
                    else:
                        proposed_actors.add(actor.get('name', '').lower())
        
        # Phase 1: Fast exact date match with indexed query
        cursor.execute('SELECT * FROM timeline_events WHERE date = ? ORDER BY importance DESC LIMIT 10', (proposed_date,))
        same_date_events = cursor.fetchall()
        
        # Pre-compute title words for efficiency
        title_words = set(proposed_title.split())
        
        for event in same_date_events:
            event_dict = dict(event)
            event_id = event_dict['id']
            if event_id in seen_event_ids:
                continue
            seen_event_ids.add(event_id)
            
            existing_title = event_dict['title'].lower()
            existing_words = set(existing_title.split())
            
            # Title similarity check (optimized)
            title_overlap = len(title_words.intersection(existing_words))
            if title_overlap >= 3:
                similarity_score = title_overlap / min(len(title_words), len(existing_words))
                similar.append({
                    'event': event_dict,
                    'similarity_type': 'title_similarity',
                    'similarity_score': similarity_score,
                    'reason': f'Shares {title_overlap} words in title'
                })
        
        # Phase 2: Actor overlap check (batch query optimization)
        if proposed_actors and same_date_events:
            event_ids = [dict(event)['id'] for event in same_date_events]
            placeholders = ','.join('?' * len(event_ids))
            cursor.execute(f'SELECT event_id, actor_name FROM timeline_actors WHERE event_id IN ({placeholders})', event_ids)
            
            # Group actors by event for efficient processing
            event_actors = {}
            for row in cursor.fetchall():
                event_id, actor_name = row
                if event_id not in event_actors:
                    event_actors[event_id] = set()
                event_actors[event_id].add(actor_name.lower())
            
            for event_id, existing_actors in event_actors.items():
                if event_id in seen_event_ids:
                    continue
                
                actor_overlap = len(proposed_actors.intersection(existing_actors))
                if actor_overlap >= 1:
                    # Find the event dict
                    event_dict = next((dict(e) for e in same_date_events if dict(e)['id'] == event_id), None)
                    if event_dict:
                        similarity_score = actor_overlap / max(len(proposed_actors), len(existing_actors))
                        similar.append({
                            'event': event_dict,
                            'similarity_type': 'actor_overlap',
                            'similarity_score': similarity_score,
                            'reason': f'Shares {actor_overlap} actors'
                        })
                        seen_event_ids.add(event_id)
        
        # Phase 3: Key term matching (optimized with single query)
        key_terms = ['cambridge analytica', 'mueller', 'blackwater', 'nisour', 
                    'barr', 'immunity', 'twitter files', 'whig', 'nsa', 'surveillance']
        
        matching_terms = [term for term in key_terms if term in proposed_title]
        if matching_terms:
            # Single query for all matching terms
            term_conditions = ' OR '.join(['LOWER(title) LIKE ?' for _ in matching_terms])
            term_params = [f'%{term}%' for term in matching_terms]
            
            cursor.execute(f'SELECT * FROM timeline_events WHERE ({term_conditions}) ORDER BY importance DESC LIMIT 20', 
                          term_params)
            term_matches = cursor.fetchall()
            
            for event in term_matches:
                event_dict = dict(event)
                event_id = event_dict['id']
                if event_id not in seen_event_ids:
                    # Find which terms matched
                    matched_terms = [term for term in matching_terms if term in event_dict['title'].lower()]
                    similar.append({
                        'event': event_dict,
                        'similarity_type': 'key_term_match',
                        'similarity_score': 0.7,
                        'reason': f'Contains key term: {", ".join(matched_terms)}'
                    })
                    seen_event_ids.add(event_id)
        
        # Sort by similarity score and limit results
        similar.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar[:5]  # Return top 5 matches
    
    def add_timeline_event(self, event_data: Dict, check_duplicates: bool = True) -> Dict:
        """Add a new timeline event with duplicate detection"""
        if check_duplicates:
            similar_events = self.find_similar_timeline_events(event_data)
            if similar_events:
                return {
                    'status': 'duplicate_detected',
                    'message': 'Similar events found - consider enhancing existing events instead',
                    'similar_events': similar_events,
                    'event_data': event_data
                }
        
        # Generate filename if not provided
        if 'id' not in event_data:
            date = event_data.get('date', datetime.now().strftime('%Y-%m-%d'))
            title_slug = event_data.get('title', '').lower()
            # Simple slugification
            title_slug = ''.join(c if c.isalnum() else '-' for c in title_slug)[:50]
            event_data['id'] = f"{date}--{title_slug}"
        
        # Create file path
        filename = f"{event_data['id']}.json"
        file_path = self.timeline_dir / filename
        
        try:
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(event_data, f, indent=2, ensure_ascii=False)
            
            # Add to database
            file_hash = self.calculate_file_hash(file_path)
            self.insert_or_update_timeline_event(event_data, str(file_path), file_hash)
            self.conn.commit()
            
            return {
                'status': 'success',
                'message': 'Event created successfully',
                'event_id': event_data['id'],
                'file_path': str(file_path)
            }
            
        except Exception as e:
            logger.error(f"Error adding timeline event: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_statistics(self) -> Dict:
        """Get research priorities statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Priorities by status
        cursor.execute('SELECT status, COUNT(*) FROM research_priorities GROUP BY status')
        stats['by_status'] = dict(cursor.fetchall())
        
        # Total events created
        cursor.execute('SELECT SUM(actual_events) FROM research_priorities')
        stats['total_events_created'] = cursor.fetchone()[0] or 0
        
        # Average priority
        cursor.execute('SELECT AVG(priority) FROM research_priorities WHERE status = "pending"')
        stats['avg_pending_priority'] = cursor.fetchone()[0] or 0
        
        # By category
        cursor.execute('SELECT category, COUNT(*) FROM research_priorities GROUP BY category')
        stats['by_category'] = dict(cursor.fetchall())
        
        # Timeline stats
        cursor.execute('SELECT COUNT(*) FROM timeline_events')
        stats['total_timeline_events'] = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(importance) FROM timeline_events')
        stats['avg_timeline_importance'] = cursor.fetchone()[0] or 0
        
        return stats

# Flask API
app = Flask(__name__)
db = UnifiedResearchDatabase()

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

@app.route('/api/research-priorities/stats')
def get_stats():
    """Get research priorities statistics"""
    return jsonify(db.get_statistics())

@app.route('/api/research-priorities/reload', methods=['GET'])
def reload_priorities():
    """Force reload research priorities from JSON files"""
    try:
        db.load_priorities()
        return jsonify({'status': 'success', 'message': 'Research priorities reloaded'})
    except Exception as e:
        logger.error(f"Error reloading priorities: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Timeline endpoints
@app.route('/api/timeline/search')
def search_timeline():
    """Search timeline events"""
    try:
        query = request.args.get('q', '')
        limit = min(int(request.args.get('limit', 20)), 100)
        importance_min = request.args.get('importance_min')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        category = request.args.get('category')
        
        if importance_min:
            importance_min = int(importance_min)
            
        events = db.search_timeline(
            query=query if query else None,
            limit=limit,
            importance_min=importance_min,
            date_from=date_from,
            date_to=date_to,
            category=category
        )
        
        return jsonify({
            'events': events,
            'count': len(events),
            'query': query,
            'filters': {
                'importance_min': importance_min,
                'date_from': date_from,
                'date_to': date_to,
                'category': category
            }
        })
    except Exception as e:
        logger.error(f"Error searching timeline: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/timeline/<event_id>')
def get_timeline_event(event_id):
    """Get specific timeline event"""
    try:
        event = db.get_timeline_event_by_id(event_id)
        if event:
            return jsonify({'event': event})
        else:
            return jsonify({'error': 'Event not found'}), 404
    except Exception as e:
        logger.error(f"Error getting timeline event {event_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/timeline/reload', methods=['GET'])
def reload_timeline():
    """Force reload timeline events"""
    try:
        db.load_timeline_events()
        return jsonify({'status': 'success', 'message': 'Timeline events reloaded'})
    except Exception as e:
        logger.error(f"Error reloading timeline: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Event addition and duplicate detection endpoints
@app.route('/api/timeline/add', methods=['POST'])
def add_timeline_event():
    """Add a new timeline event with duplicate detection"""
    try:
        event_data = request.get_json()
        if not event_data:
            return jsonify({'error': 'No event data provided'}), 400
        
        # Validate required fields
        required_fields = ['title', 'date']
        for field in required_fields:
            if field not in event_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        check_duplicates = request.args.get('check_duplicates', 'true').lower() == 'true'
        result = db.add_timeline_event(event_data, check_duplicates)
        
        if result['status'] == 'duplicate_detected':
            return jsonify(result), 409  # Conflict status
        elif result['status'] == 'success':
            return jsonify(result), 201  # Created
        else:
            return jsonify(result), 500  # Server error
            
    except Exception as e:
        logger.error(f"Error adding timeline event: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/timeline/check-duplicates', methods=['POST'])
def check_event_duplicates():
    """Check for duplicate events without adding"""
    try:
        event_data = request.get_json()
        if not event_data:
            return jsonify({'error': 'No event data provided'}), 400
        
        similar_events = db.find_similar_timeline_events(event_data)
        
        return jsonify({
            'has_duplicates': len(similar_events) > 0,
            'duplicate_count': len(similar_events),
            'similar_events': similar_events,
            'checked_event': {
                'title': event_data.get('title', ''),
                'date': event_data.get('date', ''),
                'actors': event_data.get('actors', {})
            }
        })
        
    except Exception as e:
        logger.error(f"Error checking duplicates: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/timeline/similar/<event_id>')
def find_similar_events(event_id):
    """Find events similar to an existing event"""
    try:
        # Get the existing event
        event = db.get_timeline_event_by_id(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Find similar events
        similar_events = db.find_similar_timeline_events(event)
        
        return jsonify({
            'base_event': event,
            'similar_events': similar_events,
            'count': len(similar_events)
        })
        
    except Exception as e:
        logger.error(f"Error finding similar events: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reload', methods=['GET'])
def reload_all():
    """Force reload all data"""
    try:
        db.load_priorities()
        db.load_timeline_events()
        return jsonify({'status': 'success', 'message': 'All data reloaded'})
    except Exception as e:
        logger.error(f"Error reloading data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Background thread to reload data periodically
    def background_reload():
        while True:
            time.sleep(300)  # 5 minutes
            try:
                db.load_priorities()
                db.load_timeline_events()
            except Exception as e:
                logger.error(f"Background reload failed: {e}")
    
    reload_thread = threading.Thread(target=background_reload, daemon=True)
    reload_thread.start()
    
    # Signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Shutting down server...")
        db.stop_monitoring()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Unified Research Server (Priorities + Timeline) on http://127.0.0.1:5175")
    try:
        app.run(host='127.0.0.1', port=5175, debug=False)
    finally:
        db.stop_monitoring()