#!/usr/bin/env python3
"""
Unified Research Monitor - Combined API server and web interface
Real-time timeline research pipeline with integrated database
"""

from flask import Flask, render_template, jsonify, request, abort
from flask_socketio import SocketIO, emit
import sqlite3
import json
import hashlib
import os
import time
import signal
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import glob
import re
from collections import deque, defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global log buffer for live streaming
log_buffer = deque(maxlen=1000)
metrics_cache = {}
metrics_lock = threading.Lock()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'research-monitor-key'
socketio = SocketIO(app, cors_allowed_origins="*")

class FileChangeHandler(FileSystemEventHandler):
    """Handle filesystem changes for auto-reload"""
    def __init__(self, database):
        self.database = database
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            logger.info(f"File changed: {event.src_path}")
            time.sleep(0.1)
            self.database.load_priorities()
            # Emit WebSocket update
            socketio.emit('data_reloaded', {
                'message': f'Data reloaded: {Path(event.src_path).name}',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            logger.info(f"File created: {event.src_path}")
            time.sleep(0.1)
            self.database.load_priorities()
            
            # Check if it's a timeline event
            if 'timeline_data/events' in event.src_path:
                socketio.emit('new_timeline_event', {
                    'message': f'New timeline event: {Path(event.src_path).stem}',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
            else:
                socketio.emit('priority_updated', {
                    'message': f'Research priority updated: {Path(event.src_path).name}',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
    
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            logger.info(f"File deleted: {event.src_path}")
            self.database.load_priorities()

class UnifiedResearchDatabase:
    def __init__(self, priorities_dir: str = "../research_priorities", db_path: str = "../unified_research.db", 
                 timeline_dir: str = "../timeline_data/events"):
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
        
        # Create optimized indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_status ON research_priorities(priority DESC, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_date ON timeline_events(date DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_importance ON timeline_events(importance DESC)')
        
        self.conn.commit()
        logger.info("Research database initialized")
        
        # Enable WAL mode and optimize for performance
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA synchronous=NORMAL')
        cursor.execute('PRAGMA cache_size=20000')
        cursor.execute('PRAGMA temp_store=memory')
        cursor.execute('PRAGMA mmap_size=268435456')  # 256MB memory mapping
        cursor.execute('PRAGMA optimize')
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
            json_files = list(self.priorities_dir.glob("*.json"))
            logger.info(f"Found {len(json_files)} research priority files")
            
            for json_file in json_files:
                try:
                    file_hash = self.calculate_file_hash(json_file)
                    if json_file.name in self.file_hashes and self.file_hashes[json_file.name] == file_hash:
                        continue
                    
                    with open(json_file, 'r', encoding='utf-8') as f:
                        priority_data = json.load(f)
                    
                    self.insert_or_update_priority(priority_data, str(json_file), file_hash)
                    self.file_hashes[json_file.name] = file_hash
                    
                except Exception as e:
                    logger.error(f"Error loading {json_file}: {e}")
            
            self.conn.commit()
            logger.info("Research priorities loaded successfully")
            
    def load_timeline_events(self):
        """Load all JSON timeline events from timeline directory"""
        if not self.timeline_dir.exists():
            logger.warning(f"Timeline directory {self.timeline_dir} does not exist")
            return
        
        with self.lock:
            cursor = self.conn.cursor()
            json_files = list(self.timeline_dir.glob("*.json"))
            logger.info(f"Found {len(json_files)} timeline event files")
            
            for json_file in json_files:
                try:
                    file_hash = self.calculate_file_hash(json_file)
                    if json_file.name in self.timeline_hashes and self.timeline_hashes[json_file.name] == file_hash:
                        continue
                    
                    with open(json_file, 'r', encoding='utf-8') as f:
                        event_data = json.load(f)
                    
                    self.insert_or_update_timeline_event(event_data, str(json_file), file_hash)
                    self.timeline_hashes[json_file.name] = file_hash
                    
                except Exception as e:
                    logger.error(f"Error loading timeline event {json_file}: {e}")
            
            self.conn.commit()
            logger.info("Timeline events loaded successfully")
            
    def insert_or_update_priority(self, priority_data: Dict, file_path: str, file_hash: str):
        """Insert or update a research priority in the database"""
        cursor = self.conn.cursor()
        
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
        
    def insert_or_update_timeline_event(self, event_data: Dict, file_path: str, file_hash: str):
        """Insert or update a timeline event in the database"""
        cursor = self.conn.cursor()
        
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
        
    def search_timeline(self, query: str = None, limit: int = 20, importance_min: int = None) -> List[Dict]:
        """Search timeline events"""
        cursor = self.conn.cursor()
        
        if query:
            sql = 'SELECT * FROM timeline_events WHERE LOWER(title) LIKE ? OR LOWER(description) LIKE ?'
            params = [f'%{query.lower()}%', f'%{query.lower()}%']
        else:
            sql = 'SELECT * FROM timeline_events WHERE 1=1'
            params = []
        
        if importance_min:
            sql += ' AND importance >= ?'
            params.append(importance_min)
        
        sql += ' ORDER BY date DESC, importance DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
        
    def get_statistics(self) -> Dict:
        """Get research priorities statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Priorities by status
        cursor.execute('SELECT status, COUNT(*) FROM research_priorities GROUP BY status')
        stats['by_status'] = dict(cursor.fetchall())
        
        # Timeline stats
        cursor.execute('SELECT COUNT(*) FROM timeline_events')
        stats['total_timeline_events'] = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(importance) FROM timeline_events')
        stats['avg_timeline_importance'] = cursor.fetchone()[0] or 0
        
        return stats
        
    def setup_file_monitoring(self):
        """Setup file system monitoring for auto-reload - DISABLED DUE TO SEGFAULTS"""
        # File monitoring disabled - causing segmentation faults
        self.observer = None
        logger.info("File monitoring disabled to prevent segmentation faults")
            
    def stop_monitoring(self):
        """Stop file system monitoring"""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("File monitoring stopped")

class ResearchMonitor:
    def __init__(self, db: UnifiedResearchDatabase):
        self.db = db
        self.pdfs_dir = Path("../documents/incoming")
        self.processed_dir = Path("../documents/processed")
        
        # Monitoring state
        self.active_tasks = {}
        self.recent_events = []
        self.queue_stats = {}
        self.system_metrics = {
            'events_created_today': 0,
            'priorities_completed_today': 0,
            'pdfs_processed_today': 0,
            'api_status': 'integrated'
        }
        
        # self.start_file_monitoring()  # Disabled due to segfaults
        
    def get_pdf_queue(self) -> List[Dict]:
        """Get PDF processing queue"""
        queue = []
        if self.pdfs_dir.exists():
            for pdf_file in self.pdfs_dir.glob("*.pdf"):
                if pdf_file.is_file():
                    stat = pdf_file.stat()
                    queue.append({
                        'filename': pdf_file.name,
                        'size_mb': round(stat.st_size / 1024 / 1024, 2),
                        'added_date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                        'status': 'pending',
                        'priority': self.estimate_pdf_priority(pdf_file.name)
                    })
        
        # Sort by priority then by date
        queue.sort(key=lambda x: (-x['priority'], x['added_date']))
        return queue
    
    def estimate_pdf_priority(self, filename: str) -> int:
        """Estimate PDF priority based on filename"""
        filename_lower = filename.lower()
        
        if any(term in filename_lower for term in ['constitutional', 'crisis', 'capture']):
            return 10
        elif any(term in filename_lower for term in ['trump', 'bush', 'institutional']):
            return 9
        elif any(term in filename_lower for term in ['intelligence', 'surveillance', 'whig']):
            return 8
        elif any(term in filename_lower for term in ['obama', 'biden', 'privatization']):
            return 7
        else:
            return 6
    
    def get_research_priorities(self) -> List[Dict]:
        """Get research priorities from database"""
        try:
            priorities = self.db.get_priorities_by_status('pending', 50)
            return priorities
        except Exception as e:
            logger.error(f"Error getting research priorities: {e}")
        
        return []
    
    def get_recent_timeline_events(self, hours: int = 24) -> List[Dict]:
        """Get recently created timeline events from database"""
        try:
            cursor = self.db.conn.cursor()
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT id, title, date, importance, category, tags, created_at
                FROM timeline_events 
                WHERE created_at >= ?
                ORDER BY created_at DESC
                LIMIT 20
            ''', (cutoff_time.strftime('%Y-%m-%d %H:%M:%S'),))
            
            events = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                # Parse tags JSON
                try:
                    row_dict['tags'] = json.loads(row_dict['tags'] or '[]')[:3]
                except:
                    row_dict['tags'] = []
                events.append(row_dict)
            
            return events
        except Exception as e:
            logger.error(f"Error getting recent timeline events: {e}")
            return []
    
    def get_system_stats(self) -> Dict:
        """Get system statistics from integrated database"""
        try:
            api_stats = self.db.get_statistics()
            
            # Count today's activity
            today = datetime.now().date()
            events_today = len([e for e in self.get_recent_timeline_events(24) 
                              if datetime.fromisoformat(e['created_at']).date() == today])
            
            return {
                'api_status': 'integrated',
                'total_timeline_events': api_stats.get('total_timeline_events', 0),
                'total_research_priorities': sum(api_stats.get('by_status', {}).values()),
                'pending_priorities': api_stats.get('by_status', {}).get('pending', 0),
                'completed_priorities': api_stats.get('by_status', {}).get('completed', 0),
                'events_created_today': events_today,
                'pdfs_in_queue': len(self.get_pdf_queue()),
                'avg_timeline_importance': round(api_stats.get('avg_timeline_importance', 0), 1)
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
        
        # Fallback stats
        return {
            'api_status': 'error',
            'total_timeline_events': 0,
            'total_research_priorities': 0,
            'pending_priorities': 0,
            'completed_priorities': 0,
            'events_created_today': 0,
            'pdfs_in_queue': len(self.get_pdf_queue()),
            'avg_timeline_importance': 'N/A'
        }
    
    def start_file_monitoring(self):
        """Start monitoring PDF files for real-time updates - DISABLED DUE TO SEGFAULTS"""
        # PDF monitoring disabled - causing segmentation faults
        self.observer = None
        logger.info("PDF file monitoring disabled to prevent segmentation faults")

class PDFQueueHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.pdf'):
            socketio.emit('pdf_queue_update', {
                'message': f'PDF added to queue: {Path(event.src_path).name}',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
    
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.pdf'):
            socketio.emit('pdf_processed', {
                'message': f'PDF processed: {Path(event.src_path).name}',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })

# Initialize unified database and monitor
db = UnifiedResearchDatabase()
monitor = ResearchMonitor(db)

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/queue')
def get_queue():
    """Get current PDF processing queue"""
    return jsonify({
        'pdf_queue': monitor.get_pdf_queue(),
        'research_priorities': monitor.get_research_priorities()
    })

@app.route('/api/recent-events')
def get_recent_events():
    """Get recently created timeline events"""
    return jsonify({
        'events': monitor.get_recent_timeline_events(24)
    })

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    return jsonify(monitor.get_system_stats())

@app.route('/api/timeline-search')
def search_timeline():
    """Search timeline events"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    try:
        events = db.search_timeline(query, limit=10)
        return jsonify({
            'events': events,
            'count': len(events)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('status', {'message': 'Connected to Research Monitor'})

@socketio.on('get_live_stats')
def handle_live_stats():
    """Send live statistics to client"""
    stats = monitor.get_system_stats()
    emit('live_stats', stats)

# Research API routes
@app.route('/api/research-priorities/search')
def search_priorities():
    """Search research priorities"""
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 20)), 100)
    
    if not query:
        return jsonify({'error': 'Query parameter q required'}), 400
    
    try:
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT * FROM research_priorities 
            WHERE LOWER(title) LIKE ? OR LOWER(description) LIKE ?
            ORDER BY priority DESC
            LIMIT ?
        ''', (f'%{query.lower()}%', f'%{query.lower()}%', limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        return jsonify({
            'results': results,
            'count': len(results),
            'query': query
        })
    except Exception as e:
        logger.error(f"Error searching priorities: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/research-priorities/<priority_id>')
def get_priority(priority_id):
    """Get specific research priority"""
    try:
        cursor = db.conn.cursor()
        cursor.execute('SELECT * FROM research_priorities WHERE id = ?', (priority_id,))
        priority = cursor.fetchone()
        if not priority:
            abort(404)
        return jsonify(dict(priority))
    except Exception as e:
        logger.error(f"Error getting priority {priority_id}: {e}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/research-priorities')
def get_research_priorities():
    """Get all research priorities"""
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        priorities = db.get_priorities_by_status('pending', limit)
        return jsonify({
            'priorities': priorities,
            'count': len(priorities),
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error getting research priorities: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/research-priorities/stats')
def get_research_stats():
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

@app.route('/api/timeline/<event_id>')
def get_timeline_event(event_id):
    """Get specific timeline event"""
    try:
        cursor = db.conn.cursor()
        cursor.execute('SELECT * FROM timeline_events WHERE id = ?', (event_id,))
        event = cursor.fetchone()
        if event:
            return jsonify({'event': dict(event)})
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

def parse_log_files():
    """Parse recent log files for throughput metrics"""
    logs_dir = Path('../logs')
    metrics = {
        'events_created': 0,
        'research_completed': 0,
        'validation_completed': 0,
        'errors': 0,
        'throughput_per_hour': {},
        'recent_activity': []
    }
    
    if not logs_dir.exists():
        return metrics
    
    try:
        # Look for recent log files
        log_patterns = [
            'queue_based_orchestrator/orchestrator_*.jsonl',
            'validation_orchestrator/orchestrator_*.jsonl',
            'fact_checking/fact_check_*.jsonl',
            'source_enhancement/enhancement_*.jsonl'
        ]
        
        recent_logs = []
        for pattern in log_patterns:
            recent_logs.extend(glob.glob(str(logs_dir / pattern)))
        
        # Sort by modification time, get most recent
        recent_logs.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        
        # Parse recent log entries
        for log_file in recent_logs[:5]:  # Process 5 most recent log files
            try:
                with open(log_file, 'r') as f:
                    for line_num, line in enumerate(f):
                        if line_num > 500:  # Limit to prevent memory issues
                            break
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # Count different types of activities
                            if 'action' in log_entry:
                                action = log_entry['action']
                                if 'event_created' in action or 'timeline_event' in action:
                                    metrics['events_created'] += 1
                                elif 'research_completed' in action or 'priority_completed' in action:
                                    metrics['research_completed'] += 1
                                elif 'fact_check' in action or 'validation' in action:
                                    metrics['validation_completed'] += 1
                                elif 'error' in action.lower():
                                    metrics['errors'] += 1
                            
                            # Add to recent activity
                            if len(metrics['recent_activity']) < 50:
                                timestamp = log_entry.get('timestamp', '')
                                if timestamp:
                                    metrics['recent_activity'].append({
                                        'timestamp': timestamp,
                                        'action': log_entry.get('action', 'Unknown'),
                                        'details': log_entry.get('task_type', log_entry.get('validation_type', ''))
                                    })
                                    
                        except (json.JSONDecodeError, KeyError):
                            continue
                            
            except Exception as e:
                logger.error(f"Error parsing log file {log_file}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error parsing logs: {e}")
    
    return metrics

def get_system_throughput():
    """Get real-time system throughput metrics"""
    with metrics_lock:
        if 'last_update' in metrics_cache:
            # Return cached metrics if updated recently (within 30 seconds)
            if time.time() - metrics_cache['last_update'] < 30:
                return metrics_cache.copy()
        
        # Parse fresh metrics
        metrics = parse_log_files()
        
        # Add queue-based orchestrator metrics if available
        try:
            from api.queue_based_orchestrator import QueueBasedOrchestrator
            # This would connect to running orchestrator if possible
            # For now, we'll use log-based metrics
        except:
            pass
        
        # Add validation database metrics
        validation_db_path = Path('../validation_tracking.db')
        if validation_db_path.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(str(validation_db_path))
                cursor = conn.cursor()
                
                # Get recent validation stats
                cursor.execute("""
                    SELECT COUNT(*) FROM fact_check_results 
                    WHERE validation_timestamp > datetime('now', '-1 day')
                """)
                metrics['validations_24h'] = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT AVG(accuracy_score) FROM fact_check_results 
                    WHERE validation_timestamp > datetime('now', '-1 day')
                """)
                result = cursor.fetchone()
                metrics['avg_accuracy_score'] = round(result[0], 2) if result[0] else 0
                
                conn.close()
            except Exception as e:
                logger.error(f"Error reading validation database: {e}")
        
        metrics['last_update'] = time.time()
        metrics_cache.update(metrics)
        return metrics

@app.route('/api/logs')
def get_recent_logs():
    """Get recent log entries"""
    limit = min(int(request.args.get('limit', 100)), 500)
    log_type = request.args.get('type', 'all')  # all, error, activity
    
    try:
        logs = parse_log_files()
        recent_logs = logs['recent_activity']
        
        if log_type == 'error':
            recent_logs = [log for log in recent_logs if 'error' in log['action'].lower()]
        
        return jsonify({
            'logs': recent_logs[:limit],
            'total_count': len(recent_logs),
            'type': log_type
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics')
def get_throughput_metrics():
    """Get system throughput and performance metrics"""
    try:
        metrics = get_system_throughput()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-health')
def get_system_health():
    """Get overall system health status"""
    try:
        # Check various system components
        health = {
            'status': 'healthy',
            'components': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Check database connectivity
        try:
            db.conn.cursor().execute('SELECT 1')
            health['components']['database'] = 'healthy'
        except:
            health['components']['database'] = 'error'
            health['status'] = 'degraded'
        
        # Check log files
        logs_dir = Path('../logs')
        if logs_dir.exists():
            recent_logs = glob.glob(str(logs_dir / '**/*.jsonl'), recursive=True)
            if recent_logs:
                # Check if any logs were updated recently
                recent_activity = any(
                    time.time() - os.path.getmtime(log_file) < 300  # 5 minutes
                    for log_file in recent_logs[:10]
                )
                health['components']['logging'] = 'active' if recent_activity else 'idle'
            else:
                health['components']['logging'] = 'no_logs'
        else:
            health['components']['logging'] = 'missing'
        
        # Check validation databases
        validation_db = Path('../validation_tracking.db')
        fact_check_db = Path('../validation_orchestrator.db')
        
        health['components']['validation_system'] = 'available' if validation_db.exists() else 'missing'
        health['components']['fact_check_system'] = 'available' if fact_check_db.exists() else 'missing'
        
        return jsonify(health)
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/events/log', methods=['POST'])
def log_event():
    """Receive log events from orchestrator and trigger updates"""
    try:
        data = request.json
        event_type = data.get('type', 'unknown')
        
        # Process different event types
        if event_type == 'priority_created':
            priority_data = data.get('data')
            if priority_data:
                file_hash = hashlib.md5(json.dumps(priority_data, sort_keys=True).encode()).hexdigest()
                db.insert_or_update_priority(priority_data, data.get('file_path', ''), file_hash)
                socketio.emit('priority_update', {
                    'action': 'created',
                    'priority': priority_data,
                    'timestamp': datetime.now().isoformat()
                })
        
        elif event_type == 'event_created':
            event_data = data.get('data')
            if event_data:
                file_hash = hashlib.md5(json.dumps(event_data, sort_keys=True).encode()).hexdigest()
                db.insert_or_update_event(event_data, data.get('file_path', ''), file_hash)
                socketio.emit('event_update', {
                    'action': 'created',
                    'event': event_data,
                    'timestamp': datetime.now().isoformat()
                })
        
        elif event_type == 'status_update':
            # Update queue status or worker status
            socketio.emit('status_update', data)
        
        elif event_type == 'log':
            # Store log message
            log_level = data.get('level', 'info')
            message = data.get('message', '')
            logger.log(getattr(logging, log_level.upper(), logging.INFO), f"[Orchestrator] {message}")
            socketio.emit('log_message', {
                'level': log_level,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        logger.error(f"Error processing event log: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orchestrator/status', methods=['POST'])
def update_orchestrator_status():
    """Receive status updates from orchestrator"""
    try:
        status_data = request.json
        
        # Save status to file for persistence
        status_file = Path('../orchestrator_status.json')
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
        
        # Emit to connected clients
        socketio.emit('orchestrator_status', status_data)
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        logger.error(f"Error updating orchestrator status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue-status')
def get_queue_status():
    """Get queue status from the orchestrator"""
    try:
        # Try to import and get status from queue-based orchestrator if running
        queue_status = {
            'queues': {
                'pdf': {
                    'size': 0,
                    'workers': 1,
                    'processed': 0,
                    'errors': 0,
                    'health': 'unknown',
                    'throughput_per_hour': 0
                },
                'research': {
                    'size': 0,
                    'workers': 4,
                    'processed': 0,
                    'errors': 0,
                    'health': 'unknown',
                    'throughput_per_hour': 0
                },
                'validation': {
                    'size': 0,
                    'workers': 2,
                    'processed': 0,
                    'errors': 0,
                    'health': 'unknown',
                    'throughput_per_hour': 0
                },
                'analysis': {
                    'size': 0,
                    'workers': 1,
                    'processed': 0,
                    'errors': 0,
                    'health': 'unknown',
                    'throughput_per_hour': 0
                },
                'event_creation': {
                    'size': 0,
                    'workers': 3,
                    'processed': 0,
                    'errors': 0,
                    'health': 'unknown',
                    'throughput_per_hour': 0
                }
            },
            'status': 'not_running'
        }
        
        # Try to read queue metrics from a shared file or database
        queue_metrics_file = Path('../queue_metrics.json')
        if queue_metrics_file.exists():
            try:
                with open(queue_metrics_file, 'r') as f:
                    queue_status = json.load(f)
            except:
                pass
        
        return jsonify(queue_status)
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

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
        logger.info("Shutting down unified research monitor...")
        db.stop_monitoring()
        if hasattr(monitor, 'observer') and monitor.observer:
            monitor.observer.stop()
            monitor.observer.join()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🖥️  Starting Unified Research Monitor (API + Web Interface)...")
    print("📊 Dashboard: http://127.0.0.1:5555")
    print("🔗 API Base: http://127.0.0.1:5555/api")
    
    try:
        app.run(host='127.0.0.1', port=5555, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Unified Research Monitor")
    finally:
        db.stop_monitoring()
        if hasattr(monitor, 'observer') and monitor.observer:
            monitor.observer.stop()
            monitor.observer.join()