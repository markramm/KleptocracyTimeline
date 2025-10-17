#!/usr/bin/env python3
"""
Thread-safe Research Monitor with proper database connection handling
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import sqlite3
import json
import hashlib
import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import threading
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global log buffer for live streaming
log_buffer = deque(maxlen=1000)
metrics_cache = {}
metrics_lock = threading.Lock()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'research-monitor-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Thread-local storage for database connections
thread_local = threading.local()

def get_db_connection():
    """Get a thread-local database connection"""
    if not hasattr(thread_local, 'conn'):
        thread_local.conn = sqlite3.connect('../unified_research.db')
        thread_local.conn.row_factory = sqlite3.Row
        init_database(thread_local.conn)
    return thread_local.conn

def init_database(conn):
    """Initialize database tables"""
    cursor = conn.cursor()
    
    # Research priorities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_priorities (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            priority INTEGER DEFAULT 5,
            status TEXT DEFAULT 'pending',
            category TEXT,
            tags TEXT,
            estimated_events INTEGER DEFAULT 1,
            actual_events INTEGER DEFAULT 0,
            created_date TEXT,
            updated_date TEXT,
            completion_date TEXT,
            file_path TEXT,
            file_hash TEXT
        )
    ''')
    
    # Timeline events table - match existing schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeline_events (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            date DATE NOT NULL,
            description TEXT,
            category TEXT,
            actors TEXT,
            location TEXT,
            sources TEXT,
            constitutional_issues TEXT,
            importance INTEGER DEFAULT 5,
            tags TEXT,
            connections TEXT,
            historical_significance TEXT,
            file_path TEXT,
            file_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Research logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source TEXT,
            level TEXT,
            message TEXT,
            data TEXT
        )
    ''')
    
    # Metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            metric_type TEXT,
            value REAL,
            details TEXT
        )
    ''')
    
    conn.commit()

def load_json_files_to_db():
    """Load JSON files into database (called periodically)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Load research priorities
    priorities_dir = Path('../research_priorities')
    if priorities_dir.exists():
        for json_file in priorities_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    file_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO research_priorities 
                        (id, title, description, priority, status, category, tags, 
                         estimated_events, created_date, updated_date, file_path, file_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data.get('id', json_file.stem),
                        data.get('title', ''),
                        data.get('description', ''),
                        data.get('priority', 5),
                        data.get('status', 'pending'),
                        data.get('category', ''),
                        json.dumps(data.get('tags', [])),
                        data.get('estimated_events', 1),
                        data.get('created_date', ''),
                        data.get('updated_date', ''),
                        str(json_file),
                        file_hash
                    ))
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
    
    # Load timeline events  
    events_dir = Path('../timeline_data/events')
    if events_dir.exists():
        for json_file in events_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    file_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO timeline_events
                        (id, date, title, description, importance, category, 
                         created_at, file_path, file_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data.get('id', json_file.stem),
                        data.get('date', ''),
                        data.get('title', ''),
                        data.get('description', ''),
                        data.get('importance', 5),
                        data.get('category', ''),
                        datetime.now().isoformat(),
                        str(json_file),
                        file_hash
                    ))
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
    
    conn.commit()
    logger.info("Loaded JSON files to database")

# Routes
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/research-priorities')
def get_research_priorities():
    """Get all research priorities"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM research_priorities 
            ORDER BY priority DESC, created_date DESC
        ''')
        
        priorities = []
        for row in cursor.fetchall():
            priority = dict(row)
            if priority.get('tags'):
                priority['tags'] = json.loads(priority['tags'])
            priorities.append(priority)
        
        return jsonify({"priorities": priorities})
    except Exception as e:
        logger.error(f"Error fetching priorities: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/timeline-events')
def get_timeline_events():
    """Get timeline events"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM timeline_events 
            ORDER BY date DESC
            LIMIT 100
        ''')
        
        events = [dict(row) for row in cursor.fetchall()]
        return jsonify({"events": events})
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Count priorities by status
        cursor.execute('SELECT status, COUNT(*) as count FROM research_priorities GROUP BY status')
        stats['priorities_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Count timeline events
        cursor.execute('SELECT COUNT(*) as count FROM timeline_events')
        stats['total_events'] = cursor.fetchone()['count']
        
        # Recent activity
        cursor.execute('''
            SELECT COUNT(*) as count FROM research_priorities 
            WHERE datetime(updated_date) > datetime('now', '-7 days')
        ''')
        stats['recent_priorities'] = cursor.fetchone()['count']
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/events/log', methods=['POST'])
def log_event():
    """Receive log events from orchestrator"""
    try:
        data = request.json
        event_type = data.get('type', 'unknown')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Log the event
        cursor.execute('''
            INSERT INTO research_logs (timestamp, source, level, message, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            data.get('source', 'orchestrator'),
            data.get('level', 'info'),
            data.get('message', ''),
            json.dumps(data.get('data', {}))
        ))
        
        # Handle specific event types
        if event_type == 'priority_created':
            priority_data = data.get('data')
            if priority_data:
                file_hash = hashlib.md5(json.dumps(priority_data, sort_keys=True).encode()).hexdigest()
                cursor.execute('''
                    INSERT OR REPLACE INTO research_priorities 
                    (id, title, description, priority, status, category, tags, 
                     estimated_events, created_date, updated_date, file_path, file_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    priority_data.get('id'),
                    priority_data.get('title', ''),
                    priority_data.get('description', ''),
                    priority_data.get('priority', 5),
                    priority_data.get('status', 'pending'),
                    priority_data.get('category', ''),
                    json.dumps(priority_data.get('tags', [])),
                    priority_data.get('estimated_events', 1),
                    priority_data.get('created_date', ''),
                    priority_data.get('updated_date', ''),
                    data.get('file_path', ''),
                    file_hash
                ))
                
                # Emit WebSocket update
                socketio.emit('priority_update', {
                    'type': 'created',
                    'data': priority_data,
                    'timestamp': datetime.now().isoformat()
                })
        
        elif event_type == 'event_created':
            event_data = data.get('data')
            if event_data:
                file_hash = hashlib.md5(json.dumps(event_data, sort_keys=True).encode()).hexdigest()
                cursor.execute('''
                    INSERT OR REPLACE INTO timeline_events
                    (id, date, title, description, importance, category, 
                     created_at, file_path, file_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_data.get('id'),
                    event_data.get('date', ''),
                    event_data.get('title', ''),
                    event_data.get('description', ''),
                    event_data.get('importance', 5),
                    event_data.get('category', ''),
                    datetime.now().isoformat(),
                    data.get('file_path', ''),
                    file_hash
                ))
                
                # Emit WebSocket update
                socketio.emit('event_update', {
                    'type': 'created',
                    'data': event_data,
                    'timestamp': datetime.now().isoformat()
                })
        
        conn.commit()
        
        # Add to log buffer
        log_entry = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'type': event_type,
            'message': data.get('message', ''),
            'level': data.get('level', 'info')
        }
        log_buffer.append(log_entry)
        
        # Emit to WebSocket clients
        socketio.emit('log_update', log_entry)
        
        return jsonify({"status": "logged"})
    except Exception as e:
        logger.error(f"Error logging event: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/orchestrator/status', methods=['POST'])
def orchestrator_status():
    """Receive status updates from orchestrator"""
    try:
        data = request.json
        
        # Update metrics cache
        with metrics_lock:
            metrics_cache.update(data)
        
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO metrics (timestamp, metric_type, value, details)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            'orchestrator_status',
            data.get('active_tasks', 0),
            json.dumps(data)
        ))
        conn.commit()
        
        # Emit WebSocket update
        socketio.emit('orchestrator_update', {
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({"status": "received"})
    except Exception as e:
        logger.error(f"Error updating orchestrator status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/recent')
def get_recent_logs():
    """Get recent log entries"""
    return jsonify(list(log_buffer))

@app.route('/api/metrics')
def get_metrics():
    """Get current metrics"""
    with metrics_lock:
        return jsonify(metrics_cache)

# Background task to periodically reload data
def background_reload():
    """Periodically reload data from files"""
    while True:
        try:
            time.sleep(300)  # 5 minutes
            load_json_files_to_db()
            logger.info("Background data reload completed")
        except Exception as e:
            logger.error(f"Background reload error: {e}")

# Start background thread
reload_thread = threading.Thread(target=background_reload, daemon=True)
reload_thread.start()

# Initial data load
load_json_files_to_db()

if __name__ == '__main__':
    logger.info("Starting Thread-Safe Research Monitor on http://localhost:5556")
    logger.info("Database: Using thread-local connections")
    logger.info("File monitoring: Disabled (using periodic reload)")
    
    # Run with threading enabled but debug disabled for production
    socketio.run(app, host='0.0.0.0', port=5556, debug=False)