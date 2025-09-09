#!/usr/bin/env python3
"""
Research Tracker - SQLite-based system for managing research priorities and threads
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchTracker:
    def __init__(self, db_path: str = "research_tracker.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.init_database()
    
    def init_database(self):
        """Initialize research tracking tables"""
        cursor = self.conn.cursor()
        
        # Research threads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 5 CHECK(priority BETWEEN 1 AND 10),
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'blocked', 'abandoned')),
                category TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completion_date TIMESTAMP,
                parent_thread_id TEXT,
                estimated_events INTEGER DEFAULT 1,
                actual_events INTEGER DEFAULT 0,
                tags TEXT,
                notes TEXT
            )
        ''')
        
        # Research sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                source_type TEXT CHECK(source_type IN ('document', 'book', 'article', 'website', 'video', 'testimony', 'report')),
                title TEXT NOT NULL,
                url TEXT,
                author TEXT,
                publication_date DATE,
                accessed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                credibility_score INTEGER CHECK(credibility_score BETWEEN 1 AND 10),
                key_findings TEXT,
                FOREIGN KEY (thread_id) REFERENCES research_threads(thread_id)
            )
        ''')
        
        # Research connections table (links between threads)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_thread_id TEXT NOT NULL,
                to_thread_id TEXT NOT NULL,
                connection_type TEXT,
                description TEXT,
                strength INTEGER DEFAULT 5 CHECK(strength BETWEEN 1 AND 10),
                discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_thread_id) REFERENCES research_threads(thread_id),
                FOREIGN KEY (to_thread_id) REFERENCES research_threads(thread_id)
            )
        ''')
        
        # Events created from research
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_events_created (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                event_date DATE,
                event_title TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (thread_id) REFERENCES research_threads(thread_id)
            )
        ''')
        
        # Research actors (people/orgs to investigate)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_actors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_name TEXT UNIQUE NOT NULL,
                actor_type TEXT CHECK(actor_type IN ('person', 'organization', 'government', 'corporation')),
                priority INTEGER DEFAULT 5,
                investigation_status TEXT DEFAULT 'pending',
                known_connections TEXT,
                time_period TEXT,
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_thread_priority ON research_threads(priority DESC, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_thread_status ON research_threads(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_thread_category ON research_threads(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_thread ON research_sources(thread_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_thread ON research_events_created(thread_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actor_priority ON research_actors(priority DESC)')
        
        # Create full-text search
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS research_threads_fts 
            USING fts5(thread_id, title, description, tags, notes, content=research_threads)
        ''')
        
        # Create triggers to keep FTS in sync
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS research_threads_ai 
            AFTER INSERT ON research_threads BEGIN
                INSERT INTO research_threads_fts(thread_id, title, description, tags, notes)
                VALUES (new.thread_id, new.title, new.description, new.tags, new.notes);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS research_threads_ad 
            AFTER DELETE ON research_threads BEGIN
                DELETE FROM research_threads_fts WHERE thread_id = old.thread_id;
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS research_threads_au
            AFTER UPDATE ON research_threads BEGIN
                UPDATE research_threads_fts 
                SET title = new.title, description = new.description, 
                    tags = new.tags, notes = new.notes
                WHERE thread_id = new.thread_id;
            END
        ''')
        
        self.conn.commit()
    
    def generate_thread_id(self, title: str) -> str:
        """Generate unique thread ID from title"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_digest = hashlib.md5(title.encode()).hexdigest()[:8]
        return f"RT-{timestamp}-{hash_digest}"
    
    def add_research_thread(self, title: str, description: str, priority: int = 5, 
                          category: str = None, tags: List[str] = None,
                          estimated_events: int = 1, parent_thread_id: str = None) -> str:
        """Add a new research thread"""
        thread_id = self.generate_thread_id(title)
        tags_str = json.dumps(tags) if tags else None
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO research_threads 
            (thread_id, title, description, priority, category, tags, estimated_events, parent_thread_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (thread_id, title, description, priority, category, tags_str, estimated_events, parent_thread_id))
        
        self.conn.commit()
        logger.info(f"Added research thread: {thread_id} - {title}")
        return thread_id
    
    def update_thread_status(self, thread_id: str, status: str, notes: str = None):
        """Update research thread status"""
        cursor = self.conn.cursor()
        
        if status == 'completed':
            cursor.execute('''
                UPDATE research_threads 
                SET status = ?, updated_date = CURRENT_TIMESTAMP, 
                    completion_date = CURRENT_TIMESTAMP, notes = ?
                WHERE thread_id = ?
            ''', (status, notes, thread_id))
        else:
            cursor.execute('''
                UPDATE research_threads 
                SET status = ?, updated_date = CURRENT_TIMESTAMP, notes = ?
                WHERE thread_id = ?
            ''', (status, notes, thread_id))
        
        self.conn.commit()
        logger.info(f"Updated thread {thread_id} status to: {status}")
    
    def add_research_source(self, thread_id: str, title: str, source_type: str,
                          url: str = None, author: str = None, 
                          credibility_score: int = 7, key_findings: str = None):
        """Add a source to a research thread"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO research_sources 
            (thread_id, title, source_type, url, author, credibility_score, key_findings)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (thread_id, title, source_type, url, author, credibility_score, key_findings))
        
        self.conn.commit()
        logger.info(f"Added source to thread {thread_id}: {title}")
    
    def add_event_created(self, thread_id: str, event_id: str, event_date: str, event_title: str):
        """Record that a timeline event was created from this research"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO research_events_created 
            (thread_id, event_id, event_date, event_title)
            VALUES (?, ?, ?, ?)
        ''', (thread_id, event_id, event_date, event_title))
        
        # Update actual events count
        cursor.execute('''
            UPDATE research_threads 
            SET actual_events = actual_events + 1
            WHERE thread_id = ?
        ''', (thread_id,))
        
        self.conn.commit()
        logger.info(f"Linked event {event_id} to thread {thread_id}")
    
    def add_connection(self, from_thread: str, to_thread: str, 
                       connection_type: str, description: str, strength: int = 5):
        """Add a connection between research threads"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO research_connections 
            (from_thread_id, to_thread_id, connection_type, description, strength)
            VALUES (?, ?, ?, ?, ?)
        ''', (from_thread, to_thread, connection_type, description, strength))
        
        self.conn.commit()
        logger.info(f"Connected threads: {from_thread} -> {to_thread}")
    
    def add_actor(self, actor_name: str, actor_type: str, priority: int = 5,
                  known_connections: str = None, time_period: str = None, notes: str = None):
        """Add an actor to investigate"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO research_actors 
            (actor_name, actor_type, priority, known_connections, time_period, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (actor_name, actor_type, priority, known_connections, time_period, notes))
        
        self.conn.commit()
        logger.info(f"Added actor for investigation: {actor_name}")
    
    def get_priority_threads(self, limit: int = 10, status: str = 'pending') -> List[Dict]:
        """Get highest priority research threads"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM research_threads 
            WHERE status = ?
            ORDER BY priority DESC, created_date ASC
            LIMIT ?
        ''', (status, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_threads(self, query: str) -> List[Dict]:
        """Full-text search across research threads"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT rt.* FROM research_threads rt
            JOIN research_threads_fts fts ON rt.thread_id = fts.thread_id
            WHERE research_threads_fts MATCH ?
            ORDER BY rt.priority DESC
        ''', (query,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_thread_details(self, thread_id: str) -> Dict:
        """Get complete details for a research thread"""
        cursor = self.conn.cursor()
        
        # Get thread
        cursor.execute('SELECT * FROM research_threads WHERE thread_id = ?', (thread_id,))
        thread = dict(cursor.fetchone()) if cursor.fetchone() else None
        
        if not thread:
            return None
        
        # Get sources
        cursor.execute('SELECT * FROM research_sources WHERE thread_id = ?', (thread_id,))
        thread['sources'] = [dict(row) for row in cursor.fetchall()]
        
        # Get events created
        cursor.execute('SELECT * FROM research_events_created WHERE thread_id = ?', (thread_id,))
        thread['events_created'] = [dict(row) for row in cursor.fetchall()]
        
        # Get connections
        cursor.execute('''
            SELECT * FROM research_connections 
            WHERE from_thread_id = ? OR to_thread_id = ?
        ''', (thread_id, thread_id))
        thread['connections'] = [dict(row) for row in cursor.fetchall()]
        
        return thread
    
    def get_statistics(self) -> Dict:
        """Get research tracker statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Thread counts by status
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM research_threads 
            GROUP BY status
        ''')
        stats['threads_by_status'] = dict(cursor.fetchall())
        
        # Total events created
        cursor.execute('SELECT COUNT(*) FROM research_events_created')
        stats['total_events_created'] = cursor.fetchone()[0]
        
        # Total sources
        cursor.execute('SELECT COUNT(*) FROM research_sources')
        stats['total_sources'] = cursor.fetchone()[0]
        
        # Actors to investigate
        cursor.execute('SELECT COUNT(*) FROM research_actors WHERE investigation_status = "pending"')
        stats['pending_actors'] = cursor.fetchone()[0]
        
        # Average priority
        cursor.execute('SELECT AVG(priority) FROM research_threads WHERE status = "pending"')
        stats['avg_pending_priority'] = cursor.fetchone()[0] or 0
        
        return stats
    
    def suggest_next_research(self, completed_thread_id: str = None) -> List[Dict]:
        """Suggest next research based on connections and priorities"""
        suggestions = []
        cursor = self.conn.cursor()
        
        if completed_thread_id:
            # Find connected threads
            cursor.execute('''
                SELECT rt.*, rc.connection_type, rc.description as connection_desc
                FROM research_threads rt
                JOIN research_connections rc ON rt.thread_id = rc.to_thread_id
                WHERE rc.from_thread_id = ? AND rt.status = 'pending'
                ORDER BY rc.strength DESC, rt.priority DESC
                LIMIT 5
            ''', (completed_thread_id,))
            
            connected = [dict(row) for row in cursor.fetchall()]
            if connected:
                suggestions.extend(connected)
        
        # Add high-priority pending threads
        remaining_slots = 10 - len(suggestions)
        if remaining_slots > 0:
            cursor.execute('''
                SELECT * FROM research_threads 
                WHERE status = 'pending'
                ORDER BY priority DESC, created_date ASC
                LIMIT ?
            ''', (remaining_slots,))
            
            suggestions.extend([dict(row) for row in cursor.fetchall()])
        
        return suggestions
    
    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    # Test the research tracker
    tracker = ResearchTracker()
    
    # Add sample research threads
    thread1 = tracker.add_research_thread(
        title="Niger Uranium Forgeries Investigation",
        description="Research the forged documents claiming Iraq sought uranium from Niger",
        priority=9,
        category="iraq-war",
        tags=["wmd", "forgery", "intelligence"],
        estimated_events=2
    )
    
    thread2 = tracker.add_research_thread(
        title="Office of Special Plans Operations",
        description="Document how OSP bypassed CIA to manipulate intelligence",
        priority=8,
        category="iraq-war",
        tags=["pentagon", "intelligence", "manipulation"],
        estimated_events=3
    )
    
    # Add connection
    tracker.add_connection(
        thread1, thread2,
        "related",
        "Both involved in false WMD intelligence",
        strength=8
    )
    
    # Add a source
    tracker.add_research_source(
        thread1,
        "The Italian Letter Affair",
        "article",
        url="https://example.com/article",
        author="Seymour Hersh",
        credibility_score=9,
        key_findings="Documents were crude forgeries"
    )
    
    # Get statistics
    stats = tracker.get_statistics()
    print("Research Tracker Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Get priority threads
    priority = tracker.get_priority_threads(limit=5)
    print("\nTop Priority Research:")
    for thread in priority:
        print(f"- [{thread['priority']}] {thread['title']}")
    
    tracker.close()