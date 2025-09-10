#!/usr/bin/env python3
"""
Research Monitor v2 - Clean architecture with proper separation of concerns
- Events table: Read-only mirror of filesystem (filesystem authoritative)
- Research priorities: Database authoritative (repo is initial seed)
- Single sync thread for filesystem → database
- Orchestrated commits every N events
"""

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import json
import hashlib
import os
import time
import logging
import threading
# import subprocess  # Not needed - orchestrator handles git operations
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import wraps

from sqlalchemy import create_engine, text, and_, or_
from sqlalchemy.orm import sessionmaker, scoped_session
from models import (
    Base, TimelineEvent, EventMetadata, ResearchPriority, 
    EventResearchLink, ActivityLog, ResearchSession, SystemMetrics,
    init_database
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('RESEARCH_MONITOR_SECRET', 'research-monitor-key')
CORS(app)

# Configuration
API_KEY = os.environ.get('RESEARCH_MONITOR_API_KEY', None)
DB_PATH = os.environ.get('RESEARCH_DB_PATH', '../unified_research.db')
EVENTS_PATH = Path(os.environ.get('TIMELINE_EVENTS_PATH', '../timeline_data/events'))
PRIORITIES_PATH = Path(os.environ.get('RESEARCH_PRIORITIES_PATH', '../research_priorities'))
COMMIT_THRESHOLD = int(os.environ.get('COMMIT_THRESHOLD', '10'))

# Database setup
engine = init_database(DB_PATH)
Session = scoped_session(sessionmaker(bind=engine))

# Current session tracking
current_session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
events_since_commit = 0
sync_lock = threading.Lock()

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

def get_db():
    """Get a database session"""
    return Session()

# ==================== FILESYSTEM SYNC (One-way, Read-only) ====================

class FilesystemSyncer:
    """Single-threaded filesystem to database syncer"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the sync thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.thread.start()
            logger.info("Filesystem sync thread started")
    
    def stop(self):
        """Stop the sync thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            logger.info("Filesystem sync thread stopped")
    
    def _sync_loop(self):
        """Main sync loop - runs every 30 seconds"""
        while self.running:
            try:
                with sync_lock:
                    self.sync_events()
                    self.seed_priorities()
                    self.release_expired_reservations()
            except Exception as e:
                logger.error(f"Sync error: {e}")
            
            time.sleep(30)
    
    def release_expired_reservations(self):
        """Release priority reservations that have expired (1 hour timeout)"""
        from datetime import timedelta
        db = Session()
        try:
            cutoff = datetime.now() - timedelta(hours=1)
            
            expired = db.query(ResearchPriority)\
                .filter_by(status='reserved')\
                .filter(ResearchPriority.reserved_at < cutoff)\
                .all()
            
            if expired:
                for priority in expired:
                    priority.status = 'pending'
                    priority.assigned_agent = None
                    priority.reserved_at = None
                    
                    # Log timeout
                    activity = ActivityLog(
                        action='priority_timeout',
                        priority_id=priority.id,
                        agent=priority.assigned_agent,
                        details={'reason': 'reservation_expired'}
                    )
                    db.add(activity)
                
                db.commit()
                logger.info(f"Released {len(expired)} expired priority reservations")
                
        except Exception as e:
            logger.error(f"Error releasing expired reservations: {e}")
            db.rollback()
        finally:
            db.close()
    
    def sync_events(self):
        """Sync timeline events from filesystem to database (one-way)"""
        db = Session()
        try:
            synced = 0
            for json_file in EVENTS_PATH.glob('*.json'):
                try:
                    # Calculate file hash
                    with open(json_file, 'rb') as f:
                        file_content = f.read()
                        file_hash = hashlib.md5(file_content).hexdigest()
                    
                    # Check if needs update
                    event_id = json_file.stem
                    existing = db.query(TimelineEvent).filter_by(id=event_id).first()
                    
                    if not existing or existing.file_hash != file_hash:
                        # Parse JSON
                        data = json.loads(file_content)
                        
                        # Create or update event (filesystem is authoritative)
                        if not existing:
                            event = TimelineEvent(id=event_id)
                        else:
                            event = existing
                        
                        event.json_content = data
                        event.date = data.get('date', '')
                        event.title = data.get('title', '')
                        event.summary = data.get('summary', '')
                        event.importance = data.get('importance', 5)
                        event.status = data.get('status', 'confirmed')
                        event.file_path = str(json_file)
                        event.file_hash = file_hash
                        event.last_synced = datetime.now()
                        
                        if not existing:
                            db.add(event)
                        
                        synced += 1
                
                except Exception as e:
                    logger.error(f"Error syncing {json_file}: {e}")
            
            db.commit()
            if synced > 0:
                logger.info(f"Synced {synced} events from filesystem")
                
        except Exception as e:
            logger.error(f"Events sync error: {e}")
            db.rollback()
        finally:
            db.close()
    
    def seed_priorities(self):
        """Seed initial priorities from filesystem (only if not exists)"""
        db = Session()
        try:
            seeded = 0
            for json_file in PRIORITIES_PATH.glob('*.json'):
                try:
                    priority_id = json_file.stem
                    
                    # Only seed if doesn't exist (database is authoritative)
                    existing = db.query(ResearchPriority).filter_by(id=priority_id).first()
                    if not existing:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                        
                        priority = ResearchPriority(
                            id=priority_id,
                            title=data.get('title', ''),
                            description=data.get('description', ''),
                            priority=data.get('priority', 5),
                            status=data.get('status', 'pending'),
                            estimated_events=data.get('estimated_events', 1),
                            actual_events=data.get('actual_events', 0),
                            category=data.get('category', ''),
                            tags=data.get('tags', []),
                            source_file=str(json_file),
                            is_generated=False
                        )
                        db.add(priority)
                        seeded += 1
                
                except Exception as e:
                    logger.error(f"Error seeding priority {json_file}: {e}")
            
            if seeded > 0:
                db.commit()
                logger.info(f"Seeded {seeded} new priorities from filesystem")
                
        except Exception as e:
            logger.error(f"Priority seed error: {e}")
            db.rollback()
        finally:
            db.close()

# Create and start the syncer
syncer = FilesystemSyncer()

# ==================== RESEARCH PRIORITY APIS (Database Authoritative) ====================

@app.route('/api/priorities/next', methods=['POST'])
@require_api_key
def reserve_next_priority():
    """Atomically reserve the next priority for an agent (prevents race conditions)"""
    from datetime import timedelta
    
    db = get_db()
    try:
        data = request.json or {}
        agent_id = data.get('agent_id', f'agent-{int(time.time())}')
        
        # Start transaction with row locking
        db.begin()
        
        # Find highest priority pending task with row lock
        priority = db.query(ResearchPriority)\
            .filter_by(status='pending')\
            .order_by(ResearchPriority.priority.desc(), ResearchPriority.created_date)\
            .with_for_update()\
            .first()
        
        if not priority:
            db.rollback()
            return jsonify({'message': 'No pending priorities', 'error': 'queue_empty'}), 404
        
        # Atomically reserve priority
        priority.status = 'reserved'
        priority.assigned_agent = agent_id
        priority.reserved_at = datetime.now()
        
        # Log activity
        activity = ActivityLog(
            action='priority_reserved',
            priority_id=priority.id,
            agent=agent_id,
            details={'reserved_until': (datetime.now() + timedelta(hours=1)).isoformat()}
        )
        db.add(activity)
        
        db.commit()
        
        return jsonify({
            'id': priority.id,
            'title': priority.title,
            'description': priority.description,
            'priority': priority.priority,
            'estimated_events': priority.estimated_events,
            'tags': priority.tags,
            'agent_id': agent_id,
            'status': 'reserved',
            'reserved_until': (datetime.now() + timedelta(hours=1)).isoformat()
        })
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error reserving priority: {e}")
        return jsonify({'error': 'reservation_failed', 'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/priorities/next', methods=['GET'])
def get_next_priority_info():
    """Get info about next priority without reserving (for inspection only)"""
    db = get_db()
    try:
        priority = db.query(ResearchPriority)\
            .filter_by(status='pending')\
            .order_by(ResearchPriority.priority.desc(), ResearchPriority.created_date)\
            .first()
        
        if priority:
            return jsonify({
                'id': priority.id,
                'title': priority.title,
                'description': priority.description,
                'priority': priority.priority,
                'estimated_events': priority.estimated_events,
                'tags': priority.tags,
                'status': 'pending'
            })
        else:
            return jsonify({'message': 'No pending priorities', 'error': 'queue_empty'}), 404
            
    finally:
        db.close()

@app.route('/api/priorities/<priority_id>/start', methods=['PUT'])
@require_api_key
def confirm_priority_work(priority_id):
    """Confirm that agent is starting work on reserved priority"""
    db = get_db()
    try:
        priority = db.query(ResearchPriority).filter_by(id=priority_id).first()
        if not priority:
            return jsonify({'error': 'Priority not found'}), 404
            
        if priority.status != 'reserved':
            return jsonify({'error': 'Priority not reserved or already started'}), 400
        
        # Confirm work started
        priority.status = 'in_progress'
        priority.started_date = datetime.now()
        
        # Log activity
        activity = ActivityLog(
            action='work_confirmed',
            priority_id=priority_id,
            agent=priority.assigned_agent
        )
        db.add(activity)
        
        db.commit()
        return jsonify({'status': 'confirmed', 'priority_status': 'in_progress'})
        
    finally:
        db.close()

@app.route('/api/priorities/<priority_id>/status', methods=['PUT'])
@require_api_key
def update_priority_status(priority_id):
    """Update priority status (database authoritative)"""
    db = get_db()
    try:
        priority = db.query(ResearchPriority).filter_by(id=priority_id).first()
        if not priority:
            return jsonify({'error': 'Priority not found'}), 404
        
        data = request.json
        priority.status = data.get('status', priority.status)
        
        if priority.status == 'in_progress' and not priority.started_date:
            priority.started_date = datetime.now()
        elif priority.status == 'completed':
            priority.completion_date = datetime.now()
            priority.progress_percentage = 100.0
        
        if 'actual_events' in data:
            priority.actual_events = data['actual_events']
            if priority.estimated_events > 0:
                priority.progress_percentage = (priority.actual_events / priority.estimated_events) * 100
        
        if 'notes' in data:
            priority.research_notes = data['notes']
        
        # Log activity
        activity = ActivityLog(
            action='priority_status_updated',
            agent=request.headers.get('User-Agent', 'unknown'),
            priority_id=priority_id,
            details={'old_status': priority.status, 'new_status': data.get('status')}
        )
        db.add(activity)
        
        db.commit()
        return jsonify({'status': 'updated'})
        
    finally:
        db.close()

@app.route('/api/priorities/export')
def export_priorities():
    """Export valuable priorities for persistence"""
    db = get_db()
    try:
        # Get priorities worth exporting
        priorities = db.query(ResearchPriority)\
            .filter(or_(
                ResearchPriority.export_worthy == True,
                and_(ResearchPriority.is_generated == True, 
                     ResearchPriority.actual_events > 0)
            )).all()
        
        export_data = []
        for p in priorities:
            export_data.append({
                'id': p.id,
                'title': p.title,
                'description': p.description,
                'priority': p.priority,
                'status': p.status,
                'estimated_events': p.estimated_events,
                'actual_events': p.actual_events,
                'category': p.category,
                'tags': p.tags,
                'research_notes': p.research_notes
            })
        
        return jsonify({'priorities': export_data, 'count': len(export_data)})
        
    finally:
        db.close()

# ==================== EVENT SEARCH APIS (Read from synced data) ====================

@app.route('/api/events/search')
def search_events():
    """Search events using JSON queries and full-text search"""
    db = get_db()
    try:
        query_text = request.args.get('q', '')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Use SQLite FTS if query provided
        if query_text:
            # Full-text search
            results = db.execute(text('''
                SELECT e.id, e.date, e.title, e.summary, e.importance
                FROM timeline_events e
                JOIN events_fts ON events_fts.id = e.id
                WHERE events_fts MATCH :query
                ORDER BY rank
                LIMIT :limit
            '''), {'query': query_text, 'limit': limit})
        else:
            # Regular search
            query = db.query(TimelineEvent)
            
            if date_from:
                query = query.filter(TimelineEvent.date >= date_from)
            if date_to:
                query = query.filter(TimelineEvent.date <= date_to)
            
            results = query.order_by(TimelineEvent.date.desc()).limit(limit)
        
        events = []
        for row in results:
            if hasattr(row, 'json_content'):
                events.append(row.json_content)
            else:
                events.append({
                    'id': row.id,
                    'date': row.date,
                    'title': row.title,
                    'summary': row.summary,
                    'importance': row.importance
                })
        
        return jsonify({'events': events, 'count': len(events)})
        
    finally:
        db.close()

@app.route('/api/events/validate', methods=['POST'])
def validate_event():
    """Validate an event before saving"""
    event = request.json
    errors = []
    warnings = []
    
    # Check required fields
    for field in ['id', 'date', 'title', 'summary']:
        if not event.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Check for duplicates
    if event.get('id'):
        db = get_db()
        try:
            existing = db.query(TimelineEvent).filter_by(id=event['id']).first()
            if existing:
                errors.append(f"Event {event['id']} already exists")
        finally:
            db.close()
    
    # Date format
    if event.get('date'):
        try:
            datetime.strptime(event['date'], '%Y-%m-%d')
        except ValueError:
            errors.append("Date must be YYYY-MM-DD format")
    
    return jsonify({
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    })

# ==================== COMMIT ORCHESTRATION ====================

@app.route('/api/events/staged', methods=['POST'])
@require_api_key
def stage_event():
    """Stage an event for the next commit"""
    global events_since_commit
    
    db = get_db()
    try:
        data = request.json
        event_id = data.get('id')
        priority_id = data.get('priority_id')
        
        # Save event to filesystem
        if not event_id:
            return jsonify({'error': 'Event ID required'}), 400
        
        event_path = EVENTS_PATH / f"{event_id}.json"
        with open(event_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Create metadata
        metadata = EventMetadata(
            event_id=event_id,
            created_by=request.headers.get('User-Agent', 'claude-code'),
            research_priority_id=priority_id,
            validation_status='pending'
        )
        db.add(metadata)
        
        # Update session tracking
        session = db.query(ResearchSession).filter_by(session_id=current_session_id).first()
        if not session:
            session = ResearchSession(
                session_id=current_session_id, 
                commit_threshold=COMMIT_THRESHOLD,
                events_created=0,
                priorities_completed=0
            )
            db.add(session)
        
        session.events_created = (session.events_created or 0) + 1
        events_since_commit += 1
        
        # Log activity
        activity = ActivityLog(
            action='event_staged',
            event_id=event_id,
            priority_id=priority_id,
            agent=request.headers.get('User-Agent', 'claude-code')
        )
        db.add(activity)
        
        db.commit()
        
        # Check if we should trigger a commit
        if events_since_commit >= COMMIT_THRESHOLD:
            trigger_commit()
        
        return jsonify({'status': 'staged', 'events_since_commit': events_since_commit})
        
    finally:
        db.close()

def trigger_commit():
    """Orchestrate a git commit with new events and updated priorities"""
    global events_since_commit
    
    db = get_db()
    try:
        # Export valuable priorities
        priorities = db.query(ResearchPriority)\
            .filter(ResearchPriority.export_worthy == True).all()
        
        for p in priorities:
            priority_file = PRIORITIES_PATH / f"{p.id}.json"
            with open(priority_file, 'w') as f:
                json.dump({
                    'id': p.id,
                    'title': p.title,
                    'description': p.description,
                    'priority': p.priority,
                    'status': p.status,
                    'estimated_events': p.estimated_events,
                    'actual_events': p.actual_events,
                    'category': p.category,
                    'tags': p.tags,
                    'research_notes': p.research_notes
                }, f, indent=2)
        
        # Signal commit needed - actual git operations should be done by orchestrator
        # Update session to record that commit threshold was reached
        session = db.query(ResearchSession).filter_by(session_id=current_session_id).first()
        if session:
            session.last_commit = datetime.now()
        
        db.commit()
        
        # Log for orchestrator to see
        logger.info(f"COMMIT THRESHOLD REACHED: {events_since_commit} events ready for commit")
        logger.info(f"Exported {len(priorities)} priorities marked as export_worthy")
        logger.info("Orchestrator should perform: git add timeline_data/events research_priorities && git commit")
        
        # Reset counter
        events_since_commit = 0
            
    finally:
        db.close()

# ==================== STATISTICS ====================

@app.route('/api/commit/status')
def get_commit_status():
    """Check if a commit is needed"""
    return jsonify({
        'events_since_commit': events_since_commit,
        'threshold': COMMIT_THRESHOLD,
        'commit_needed': events_since_commit >= COMMIT_THRESHOLD,
        'session_id': current_session_id
    })

@app.route('/api/commit/reset', methods=['POST'])
@require_api_key
def reset_commit_counter():
    """Reset the commit counter after orchestrator performs commit"""
    global events_since_commit
    events_since_commit = 0
    logger.info("Commit counter reset by orchestrator")
    return jsonify({'status': 'reset', 'events_since_commit': 0})

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    db = get_db()
    try:
        stats = {
            'events': {
                'total': db.query(TimelineEvent).count(),
                'validated': db.query(EventMetadata).filter_by(validation_status='validated').count()
            },
            'priorities': {
                'total': db.query(ResearchPriority).count(),
                'pending': db.query(ResearchPriority).filter_by(status='pending').count(),
                'reserved': db.query(ResearchPriority).filter_by(status='reserved').count(),
                'in_progress': db.query(ResearchPriority).filter_by(status='in_progress').count(),
                'completed': db.query(ResearchPriority).filter_by(status='completed').count()
            },
            'session': {
                'id': current_session_id,
                'events_since_commit': events_since_commit,
                'commit_threshold': COMMIT_THRESHOLD
            }
        }
        return jsonify(stats)
        
    finally:
        db.close()

# ==================== STARTUP ====================

if __name__ == '__main__':
    PORT = int(os.environ.get('RESEARCH_MONITOR_PORT', 5555))
    
    # Start filesystem syncer
    syncer.start()
    
    logger.info(f"Research Monitor v2 starting on port {PORT}")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Events path: {EVENTS_PATH}")
    logger.info(f"Priorities path: {PRIORITIES_PATH}")
    logger.info(f"Commit threshold: {COMMIT_THRESHOLD} events")
    
    try:
        app.run(host='127.0.0.1', port=PORT, debug=False)
    finally:
        syncer.stop()