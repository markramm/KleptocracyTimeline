#!/usr/bin/env python3
"""
Enhanced Research Monitor with full CRUD endpoints
Thread-safe implementation with proper API for Claude Code orchestration
"""

from flask import Flask, render_template, jsonify, request, abort
from flask_socketio import SocketIO
from flask_cors import CORS
import sqlite3
import json
import hashlib
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
from collections import deque
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global buffers and locks
log_buffer = deque(maxlen=1000)
metrics_cache = {}
metrics_lock = threading.Lock()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('RESEARCH_MONITOR_SECRET', 'research-monitor-key')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration from environment
API_KEY = os.environ.get('RESEARCH_MONITOR_API_KEY', None)
DB_PATH = os.environ.get('RESEARCH_DB_PATH', '../unified_research.db')
EVENTS_PATH = Path(os.environ.get('TIMELINE_EVENTS_PATH', '../timeline_data/events'))
PRIORITIES_PATH = Path(os.environ.get('RESEARCH_PRIORITIES_PATH', '../research_priorities'))

# Thread-local storage for database connections
thread_local = threading.local()

def get_db_connection():
    """Get a thread-local database connection"""
    if not hasattr(thread_local, 'conn'):
        thread_local.conn = sqlite3.connect(DB_PATH)
        thread_local.conn.row_factory = sqlite3.Row
        init_database(thread_local.conn)
    return thread_local.conn

def require_api_key(f):
    """Decorator to require API key for write operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if API_KEY:
            provided_key = request.headers.get('X-API-Key')
            if provided_key != API_KEY:
                abort(401, description="Invalid or missing API key")
        return f(*args, **kwargs)
    return decorated_function

def init_database(conn):
    """Initialize database tables with enhanced schema"""
    cursor = conn.cursor()
    
    # Enhanced research priorities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_priorities (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            priority INTEGER DEFAULT 5 CHECK(priority BETWEEN 1 AND 10),
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'blocked', 'abandoned')),
            category TEXT,
            tags TEXT,  -- JSON array
            estimated_events INTEGER DEFAULT 1,
            actual_events INTEGER DEFAULT 0,
            created_date TEXT,
            updated_date TEXT,
            completion_date TEXT,
            triggered_by TEXT,  -- JSON array of event IDs
            notes TEXT,
            file_path TEXT,
            file_hash TEXT
        )
    ''')
    
    # Enhanced timeline events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeline_events (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            date DATE NOT NULL,
            summary TEXT,
            category TEXT,
            actors TEXT,  -- JSON array
            location TEXT,
            sources TEXT,  -- JSON array
            importance INTEGER DEFAULT 5 CHECK(importance BETWEEN 1 AND 10),
            tags TEXT,  -- JSON array
            status TEXT DEFAULT 'confirmed' CHECK(status IN ('confirmed', 'alleged', 'disputed')),
            validation_status TEXT DEFAULT 'pending' CHECK(validation_status IN ('pending', 'validated', 'rejected')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            priority_id TEXT,  -- Link to research priority
            file_path TEXT,
            file_hash TEXT,
            FOREIGN KEY (priority_id) REFERENCES research_priorities(id)
        )
    ''')
    
    # Activity log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT,  -- 'priority' or 'event'
            entity_id TEXT,
            agent TEXT,
            details TEXT,  -- JSON
            ip_address TEXT
        )
    ''')
    
    # Metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            metric_type TEXT,
            value REAL,
            details TEXT  -- JSON
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_status ON research_priorities(status, priority DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_date ON timeline_events(date DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_validation ON timeline_events(validation_status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp DESC)')
    
    # Enable WAL mode for better concurrency
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.execute('PRAGMA synchronous=NORMAL')
    cursor.execute('PRAGMA cache_size=10000')
    cursor.execute('PRAGMA busy_timeout=5000')
    
    conn.commit()

def log_activity(action: str, entity_type: str = None, entity_id: str = None, 
                 agent: str = None, details: Dict = None):
    """Log an activity to the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO activity_log (timestamp, action, entity_type, entity_id, agent, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            action,
            entity_type,
            entity_id,
            agent or 'claude-code',
            json.dumps(details) if details else None,
            request.remote_addr if request else None
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

# ==================== RESEARCH PRIORITY ENDPOINTS ====================

@app.route('/api/priorities/next')
def get_next_priority():
    """Get the highest priority pending research task"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM research_priorities 
            WHERE status = 'pending'
            ORDER BY priority DESC, created_date ASC
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        if row:
            priority = dict(row)
            if priority.get('tags'):
                priority['tags'] = json.loads(priority['tags'])
            if priority.get('triggered_by'):
                priority['triggered_by'] = json.loads(priority['triggered_by'])
            
            log_activity('priority_retrieved', 'priority', priority['id'])
            return jsonify(priority)
        else:
            return jsonify({"message": "No pending priorities"}), 404
            
    except Exception as e:
        logger.error(f"Error getting next priority: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/priorities/<priority_id>')
def get_priority(priority_id):
    """Get a specific research priority"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM research_priorities WHERE id = ?', (priority_id,))
        row = cursor.fetchone()
        
        if row:
            priority = dict(row)
            if priority.get('tags'):
                priority['tags'] = json.loads(priority['tags'])
            return jsonify(priority)
        else:
            return jsonify({"error": "Priority not found"}), 404
            
    except Exception as e:
        logger.error(f"Error getting priority: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/priorities', methods=['POST'])
@require_api_key
def create_priority():
    """Create a new research priority"""
    try:
        data = request.json
        if not data.get('title'):
            return jsonify({"error": "Title is required"}), 400
        
        # Generate ID if not provided
        if not data.get('id'):
            title_slug = data['title'].lower().replace(' ', '-')[:50]
            data['id'] = f"RT-{datetime.now().strftime('%Y%m%d')}-{title_slug}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO research_priorities 
            (id, title, description, priority, status, category, tags, 
             estimated_events, created_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['id'],
            data['title'],
            data.get('description', ''),
            data.get('priority', 5),
            'pending',
            data.get('category', ''),
            json.dumps(data.get('tags', [])),
            data.get('estimated_events', 1),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        
        # Also save to file system if path exists
        if PRIORITIES_PATH.exists():
            file_path = PRIORITIES_PATH / f"{data['id']}.json"
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        log_activity('priority_created', 'priority', data['id'], details=data)
        
        # Emit WebSocket update
        socketio.emit('priority_update', {
            'action': 'created',
            'priority': data,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({"id": data['id'], "status": "created"}), 201
        
    except Exception as e:
        logger.error(f"Error creating priority: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/priorities/<priority_id>/status', methods=['PUT'])
@require_api_key
def update_priority_status(priority_id):
    """Update the status of a research priority"""
    try:
        data = request.json
        status = data.get('status')
        
        if status not in ['pending', 'in_progress', 'completed', 'blocked', 'abandoned']:
            return jsonify({"error": "Invalid status"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build update query
        update_fields = ['status = ?', 'updated_date = ?']
        update_values = [status, datetime.now().isoformat()]
        
        if status == 'completed':
            update_fields.append('completion_date = ?')
            update_values.append(datetime.now().isoformat())
            
        if 'actual_events' in data:
            update_fields.append('actual_events = ?')
            update_values.append(data['actual_events'])
            
        if 'notes' in data:
            update_fields.append('notes = ?')
            update_values.append(data['notes'])
        
        update_values.append(priority_id)
        
        cursor.execute(f'''
            UPDATE research_priorities 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', update_values)
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Priority not found"}), 404
        
        conn.commit()
        
        log_activity('priority_status_updated', 'priority', priority_id, 
                    details={'status': status, **data})
        
        # Emit WebSocket update
        socketio.emit('priority_update', {
            'action': 'status_updated',
            'priority_id': priority_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({"status": "updated"})
        
    except Exception as e:
        logger.error(f"Error updating priority status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/priorities/<priority_id>', methods=['DELETE'])
@require_api_key
def delete_priority(priority_id):
    """Delete a research priority"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM research_priorities WHERE id = ?', (priority_id,))
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Priority not found"}), 404
        
        conn.commit()
        
        log_activity('priority_deleted', 'priority', priority_id)
        
        return jsonify({"status": "deleted"})
        
    except Exception as e:
        logger.error(f"Error deleting priority: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== TIMELINE EVENT ENDPOINTS ====================

@app.route('/api/events/search')
def search_events():
    """Search existing events to avoid duplicates"""
    try:
        query = request.args.get('q', '')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = min(int(request.args.get('limit', 20)), 100)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build search query
        conditions = []
        params = []
        
        if query:
            conditions.append('(LOWER(title) LIKE ? OR LOWER(summary) LIKE ?)')
            params.extend([f'%{query.lower()}%', f'%{query.lower()}%'])
        
        if date_from:
            conditions.append('date >= ?')
            params.append(date_from)
            
        if date_to:
            conditions.append('date <= ?')
            params.append(date_to)
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        params.append(limit)
        
        cursor.execute(f'''
            SELECT id, title, date, importance, validation_status, tags
            FROM timeline_events 
            WHERE {where_clause}
            ORDER BY date DESC, importance DESC
            LIMIT ?
        ''', params)
        
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            if event.get('tags'):
                event['tags'] = json.loads(event['tags'])
            events.append(event)
        
        return jsonify({
            'count': len(events),
            'events': events,
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Error searching events: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/events/validate', methods=['POST'])
def validate_event():
    """Validate an event before saving"""
    try:
        event = request.json
        errors = []
        warnings = []
        
        # Required fields validation
        required_fields = ['id', 'date', 'title', 'summary']
        for field in required_fields:
            if not event.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Date format validation
        if event.get('date'):
            try:
                datetime.strptime(event['date'], '%Y-%m-%d')
            except ValueError:
                errors.append("Date must be in YYYY-MM-DD format")
        
        # Sources validation
        if not event.get('sources') or len(event['sources']) < 1:
            warnings.append("Event should have at least one source")
        else:
            for i, source in enumerate(event['sources']):
                if not source.get('url'):
                    warnings.append(f"Source {i+1} missing URL")
                if not source.get('title'):
                    warnings.append(f"Source {i+1} missing title")
        
        # Importance validation
        importance = event.get('importance', 5)
        if not isinstance(importance, int) or importance < 1 or importance > 10:
            errors.append("Importance must be an integer between 1 and 10")
        
        # Check for duplicates
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check by ID
        cursor.execute('SELECT id FROM timeline_events WHERE id = ?', (event['id'],))
        if cursor.fetchone():
            errors.append(f"Event with ID {event['id']} already exists")
        
        # Check for similar events (same date and similar title)
        if event.get('date') and event.get('title'):
            cursor.execute('''
                SELECT id, title FROM timeline_events 
                WHERE date = ? AND LOWER(title) LIKE ?
                LIMIT 5
            ''', (event['date'], f'%{event["title"][:20].lower()}%'))
            
            similar = cursor.fetchall()
            if similar:
                warnings.append(f"Similar events exist: {', '.join([row['id'] for row in similar])}")
        
        valid = len(errors) == 0
        
        return jsonify({
            'valid': valid,
            'errors': errors,
            'warnings': warnings,
            'duplicate': False
        })
        
    except Exception as e:
        logger.error(f"Error validating event: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/events/created', methods=['POST'])
@require_api_key
def record_event_creation():
    """Record that an event was created (for tracking)"""
    try:
        data = request.json
        event_id = data.get('id')
        priority_id = data.get('priority_id')
        created_by = data.get('created_by', 'claude-code')
        
        if not event_id:
            return jsonify({"error": "Event ID required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update the database record if it exists
        cursor.execute('''
            UPDATE timeline_events 
            SET created_by = ?, priority_id = ?, validation_status = 'validated'
            WHERE id = ?
        ''', (created_by, priority_id, event_id))
        
        # If priority_id provided, increment actual_events count
        if priority_id:
            cursor.execute('''
                UPDATE research_priorities 
                SET actual_events = actual_events + 1
                WHERE id = ?
            ''', (priority_id,))
        
        conn.commit()
        
        log_activity('event_created', 'event', event_id, agent=created_by,
                    details={'priority_id': priority_id})
        
        # Update metrics
        with metrics_lock:
            if 'events_created_today' not in metrics_cache:
                metrics_cache['events_created_today'] = 0
            metrics_cache['events_created_today'] += 1
        
        return jsonify({"status": "recorded"})
        
    except Exception as e:
        logger.error(f"Error recording event creation: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== PROGRESS TRACKING ENDPOINTS ====================

@app.route('/api/stats')
def get_stats():
    """Get current progress and system statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Priority statistics
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM research_priorities 
            GROUP BY status
        ''')
        priority_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        stats['priorities'] = {
            'total': sum(priority_counts.values()),
            'pending': priority_counts.get('pending', 0),
            'in_progress': priority_counts.get('in_progress', 0),
            'completed': priority_counts.get('completed', 0),
            'blocked': priority_counts.get('blocked', 0)
        }
        
        # Event statistics
        cursor.execute('SELECT COUNT(*) as count FROM timeline_events')
        stats['events'] = {'total': cursor.fetchone()['count']}
        
        # Today's events
        cursor.execute('''
            SELECT COUNT(*) as count FROM timeline_events 
            WHERE DATE(created_at) = DATE('now')
        ''')
        stats['events']['created_today'] = cursor.fetchone()['count']
        
        # This week's events
        cursor.execute('''
            SELECT COUNT(*) as count FROM timeline_events 
            WHERE created_at >= datetime('now', '-7 days')
        ''')
        stats['events']['created_week'] = cursor.fetchone()['count']
        
        # Calculate velocity
        cursor.execute('''
            SELECT 
                COUNT(*) as events_7d,
                (SELECT COUNT(*) FROM research_priorities 
                 WHERE completion_date >= datetime('now', '-7 days')) as priorities_7d
            FROM timeline_events 
            WHERE created_at >= datetime('now', '-7 days')
        ''')
        velocity = cursor.fetchone()
        
        stats['research_velocity'] = {
            'events_per_day': round(velocity['events_7d'] / 7, 1),
            'priorities_per_week': velocity['priorities_7d']
        }
        
        # Add cached metrics
        with metrics_lock:
            stats.update(metrics_cache)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/activity', methods=['POST'])
@require_api_key
def log_activity_endpoint():
    """Log research activity for monitoring"""
    try:
        data = request.json
        action = data.get('action')
        
        if not action:
            return jsonify({"error": "Action required"}), 400
        
        log_activity(
            action=action,
            entity_type=data.get('entity_type'),
            entity_id=data.get('entity_id'),
            agent=data.get('agent'),
            details=data.get('details')
        )
        
        # Add to log buffer for real-time display
        log_entry = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'action': action,
            'agent': data.get('agent', 'unknown'),
            'details': data.get('details', {})
        }
        log_buffer.append(log_entry)
        
        # Emit to WebSocket
        socketio.emit('activity_log', log_entry)
        
        return jsonify({"status": "logged"})
        
    except Exception as e:
        logger.error(f"Error logging activity: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/activity/recent')
def get_recent_activity():
    """Get recent activity log"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM activity_log 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''')
        
        activities = []
        for row in cursor.fetchall():
            activity = dict(row)
            if activity.get('details'):
                activity['details'] = json.loads(activity['details'])
            activities.append(activity)
        
        return jsonify(activities)
        
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== FILE SYNC SERVICE ====================

def sync_files_to_database():
    """Sync JSON files to database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Sync research priorities
        if PRIORITIES_PATH.exists():
            for json_file in PRIORITIES_PATH.glob('*.json'):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    file_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
                    
                    # Check if needs update
                    cursor.execute('SELECT file_hash FROM research_priorities WHERE id = ?', 
                                 (data.get('id', json_file.stem),))
                    existing = cursor.fetchone()
                    
                    if not existing or existing['file_hash'] != file_hash:
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
                            data.get('updated_date', datetime.now().isoformat()),
                            str(json_file),
                            file_hash
                        ))
                except Exception as e:
                    logger.error(f"Error syncing priority {json_file}: {e}")
        
        # Sync timeline events
        if EVENTS_PATH.exists():
            for json_file in EVENTS_PATH.glob('*.json'):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    file_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
                    
                    # Check if needs update
                    cursor.execute('SELECT file_hash FROM timeline_events WHERE id = ?', 
                                 (data.get('id', json_file.stem),))
                    existing = cursor.fetchone()
                    
                    if not existing or existing['file_hash'] != file_hash:
                        cursor.execute('''
                            INSERT OR REPLACE INTO timeline_events
                            (id, date, title, summary, importance, tags, sources, actors,
                             status, file_path, file_hash, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            data.get('id', json_file.stem),
                            data.get('date', ''),
                            data.get('title', ''),
                            data.get('summary', ''),
                            data.get('importance', 5),
                            json.dumps(data.get('tags', [])),
                            json.dumps(data.get('sources', [])),
                            json.dumps(data.get('actors', [])),
                            data.get('status', 'confirmed'),
                            str(json_file),
                            file_hash,
                            datetime.now().isoformat()
                        ))
                except Exception as e:
                    logger.error(f"Error syncing event {json_file}: {e}")
        
        conn.commit()
        logger.info("File sync completed")
        
    except Exception as e:
        logger.error(f"Error in file sync: {e}")

# ==================== WEB INTERFACE ====================

@app.route('/')
def index():
    """Dashboard interface"""
    return render_template('dashboard.html')

# ==================== WEBSOCKET HANDLERS ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to Research Monitor'})

@socketio.on('request_stats')
def handle_stats_request():
    """Send stats on request"""
    emit('stats_update', get_stats().json)

# ==================== BACKGROUND TASKS ====================

def background_sync():
    """Periodically sync files to database"""
    while True:
        try:
            time.sleep(30)  # Sync every 30 seconds
            sync_files_to_database()
        except Exception as e:
            logger.error(f"Background sync error: {e}")

# Start background thread
sync_thread = threading.Thread(target=background_sync, daemon=True)
sync_thread.start()

# Initial sync
sync_files_to_database()

if __name__ == '__main__':
    PORT = int(os.environ.get('RESEARCH_MONITOR_PORT', 5555))
    logger.info(f"Starting Enhanced Research Monitor on http://localhost:{PORT}")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Events path: {EVENTS_PATH}")
    logger.info(f"Priorities path: {PRIORITIES_PATH}")
    logger.info(f"API Key required: {bool(API_KEY)}")
    
    app.run(host='127.0.0.1', port=PORT, debug=False)