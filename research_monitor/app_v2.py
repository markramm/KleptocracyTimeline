#!/usr/bin/env python3
"""
Research Monitor v2 - Clean architecture with proper separation of concerns
- Events table: Read-only mirror of filesystem (filesystem authoritative)
- Research priorities: Database authoritative (repo is initial seed)
- Single sync thread for filesystem → database
- Orchestrated commits every N events
"""

from flask import Flask, jsonify, request, abort, send_file, send_from_directory
from flask_cors import CORS
from flask_caching import Cache
import json
import hashlib
import os
import signal
import time
import logging
import threading
# import subprocess  # Not needed - orchestrator handles git operations
from datetime import datetime, timedelta, timezone
import sys
sys.path.append('..')
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import wraps
import re
# from timeline_event_manager import TimelineEventManager  # Has circular dependency

from sqlalchemy import create_engine, text, and_, or_, func
from sqlalchemy.orm import sessionmaker, scoped_session
from models import (
    Base, TimelineEvent, EventMetadata, ResearchPriority, 
    EventResearchLink, ActivityLog, ResearchSession, SystemMetrics,
    ValidationLog, ValidationRun, ValidationRunEvent,
    init_database
)
from validation_calculator import ValidationRunCalculator
from event_validator import EventValidator as TimelineEventValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('RESEARCH_MONITOR_SECRET', 'research-monitor-key')

# Configure Flask-Caching
app.config['CACHE_TYPE'] = 'simple'  # In-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes default
app.config['CACHE_THRESHOLD'] = 1000  # Maximum cached items

cache = Cache(app)
CORS(app)

# Global error handlers for JSON API responses
@app.errorhandler(400)
def handle_bad_request(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if error.description else 'Invalid request',
            'status_code': 400
        }), 400
    return error

@app.errorhandler(401)
def handle_unauthorized(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Unauthorized',
            'message': str(error.description) if error.description else 'Authentication required',
            'status_code': 401
        }), 401
    return error

@app.errorhandler(404)
def handle_not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Not Found',
            'message': str(error.description) if error.description else 'Resource not found',
            'status_code': 404
        }), 404
    return error

@app.errorhandler(500)
def handle_internal_error(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(error.description) if error.description else 'An internal error occurred',
            'status_code': 500
        }), 500
    return error

# Configuration
API_KEY = os.environ.get('RESEARCH_MONITOR_API_KEY', None)
DB_PATH = os.environ.get('RESEARCH_DB_PATH', '../unified_research.db')
EVENTS_PATH = Path(os.environ.get('TIMELINE_EVENTS_PATH', '../timeline_data/events'))
PRIORITIES_PATH = Path(os.environ.get('RESEARCH_PRIORITIES_PATH', '../research_priorities'))
VALIDATION_LOGS_PATH = Path(os.environ.get('VALIDATION_LOGS_PATH', '../timeline_data/validation_logs'))
COMMIT_THRESHOLD = int(os.environ.get('COMMIT_THRESHOLD', '10'))

# Store configuration in app.config for blueprint access
app.config['API_KEY'] = API_KEY
app.config['DB_PATH'] = DB_PATH
app.config['EVENTS_PATH'] = EVENTS_PATH
app.config['PRIORITIES_PATH'] = PRIORITIES_PATH
app.config['VALIDATION_LOGS_PATH'] = VALIDATION_LOGS_PATH
app.config['COMMIT_THRESHOLD'] = COMMIT_THRESHOLD
app.config['CACHE'] = cache  # Make cache available to blueprints

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

# ==================== CACHING UTILITIES ====================

def make_cache_key(*args, **kwargs):
    """Generate cache key from request args and kwargs"""
    path = request.path
    args_str = str(sorted(request.args.items()))
    return f"{path}:{args_str}"

def cache_with_invalidation(timeout=300, key_prefix=None):
    """Custom caching decorator with invalidation support"""
    def decorator(f):
        @cache.memoize(timeout=timeout, make_name=lambda fname: key_prefix or fname)
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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
                    
                    # Release expired QA reservations
                    try:
                        db = Session()
                        qa_manager = QAQueueManager(db)
                        released_count = qa_manager.release_expired_qa_reservations()
                        if released_count > 0:
                            logger.info(f"Released {released_count} expired QA reservations")
                        db.close()
                    except Exception as e:
                        logger.error(f"Error releasing expired QA reservations: {e}")
                        if db:
                            db.close()
            except Exception as e:
                logger.error(f"Sync error: {e}")
            
            time.sleep(30)
    
    def release_expired_reservations(self):
        """Release priority reservations that have expired (1 hour timeout)"""
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
                
                # Log activity for monitoring
                activity = ActivityLog(
                    action='filesystem_sync',
                    agent='system',
                    details={'new_events': synced}
                )
                db.add(activity)
                db.commit()
                
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

def write_validation_log_to_filesystem(validation_log_data: dict):
    """Write validation log to filesystem for persistence"""
    try:
        # Ensure validation logs directory exists
        VALIDATION_LOGS_PATH.mkdir(parents=True, exist_ok=True)
        
        # Create filename with timestamp and ID
        timestamp = validation_log_data['validation_date'].replace(':', '-').replace('.', '-')
        filename = f"validation-log-{validation_log_data['id']}-{timestamp}.json"
        file_path = VALIDATION_LOGS_PATH / filename
        
        # Write to filesystem
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(validation_log_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Validation log {validation_log_data['id']} written to filesystem: {filename}")
        
    except Exception as e:
        logger.error(f"Failed to write validation log to filesystem: {e}")

def sync_validation_logs_from_filesystem():
    """Sync validation logs from filesystem to database on startup"""
    db = Session()
    try:
        synced = 0
        if VALIDATION_LOGS_PATH.exists():
            for json_file in VALIDATION_LOGS_PATH.glob('validation-log-*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Check if log already exists
                    log_id = data.get('id')
                    if log_id and not db.query(ValidationLog).filter_by(id=log_id).first():
                        # Create validation log from filesystem data
                        validation_log = ValidationLog(
                            id=data.get('id'),
                            event_id=data.get('event_id'),
                            validation_run_id=data.get('validation_run_id'),
                            validator_type=data.get('validator_type'),
                            validator_id=data.get('validator_id'),
                            status=data.get('status'),
                            confidence=data.get('confidence'),
                            notes=data.get('notes'),
                            issues_found=data.get('issues_found'),
                            sources_verified=data.get('sources_verified'),
                            corrections_made=data.get('corrections_made'),
                            time_spent_minutes=data.get('time_spent_minutes'),
                            validation_criteria=data.get('validation_criteria'),
                            validation_date=datetime.fromisoformat(data['validation_date'].replace('Z', '+00:00'))
                        )
                        
                        db.add(validation_log)
                        synced += 1
                
                except Exception as e:
                    logger.error(f"Error syncing validation log {json_file}: {e}")
        
        if synced > 0:
            db.commit()
            logger.info(f"Synced {synced} validation logs from filesystem")
    
    except Exception as e:
        logger.error(f"Validation logs sync error: {e}")
        db.rollback()
    finally:
        db.close()

def validate_timeline_event(event: dict) -> dict:
    """
    Server-side event validation with helpful error messages
    Returns {'valid': bool, 'errors': list, 'warnings': list, 'fixed_event': dict}
    """
    errors = []
    
    # Required fields validation
    required_fields = ['id', 'date', 'title', 'summary', 'importance', 'actors', 'tags', 'sources']
    for field in required_fields:
        if field not in event or event.get(field) is None:
            errors.append(f"Missing required field: {field}")
    
    # ID format validation  
    if event.get('id'):
        if not re.match(r'^\d{4}-\d{2}-\d{2}--[\w-]+$', event['id']):
            errors.append(f"Invalid ID format: {event['id']}. Expected: YYYY-MM-DD--descriptive-slug")
    
    # Date format validation
    if event.get('date'):
        try:
            datetime.strptime(event['date'], '%Y-%m-%d')
        except ValueError:
            errors.append(f"Invalid date format: {event['date']}. Expected: YYYY-MM-DD")
    
    # Importance validation
    importance = event.get('importance')
    if importance is not None and (not isinstance(importance, int) or not 1 <= importance <= 10):
        errors.append(f"Importance must be integer 1-10, got: {importance} ({type(importance).__name__})")
    
    validation_errors = errors
    
    # Auto-fix common issues
    fixed_event = event.copy()
    warnings = []
    
    # Auto-fix importance if string
    if isinstance(event.get('importance'), str):
        try:
            fixed_event['importance'] = int(event['importance'])
            warnings.append(f"Converted importance from string to integer")
        except ValueError:
            pass
    
    # Auto-fix missing fields with defaults
    if 'importance' not in event or event.get('importance') is None:
        fixed_event['importance'] = 5
        warnings.append("Missing importance, defaulted to 5")
    
    if 'status' not in event:
        fixed_event['status'] = 'confirmed'
        warnings.append("Missing status, defaulted to 'confirmed'")
    
    # Initialize missing arrays
    for field in ['tags', 'actors', 'sources']:
        if field not in event or not isinstance(event.get(field), list):
            fixed_event[field] = []
            warnings.append(f"Initialized empty {field} list")
    
    # Check for placeholder sources
    sources = event.get('sources', [])
    placeholder_sources = ['example.com', 'TBD', 'TODO', 'FIXME', 'placeholder']
    if any(placeholder in str(sources) for placeholder in placeholder_sources):
        warnings.append("Event contains placeholder sources that should be replaced")
    
    return {
        'valid': len(validation_errors) == 0,
        'errors': validation_errors,
        'warnings': warnings,
        'fixed_event': fixed_event
    }

def log_update_failure(event_id: str, validation_log_id: int, validator_id: str, 
                      failure_type: str, error_message: str, stack_trace: str = None,
                      attempted_corrections: dict = None, file_path: str = None):
    """
    Log a failed event update attempt to the database for analysis
    """
    db = get_db()
    try:
        from models import EventUpdateFailure
        import stat
        
        # Gather file context if possible
        file_exists = False
        file_permissions = None
        if file_path and os.path.exists(file_path):
            file_exists = True
            try:
                file_stat = os.stat(file_path)
                file_permissions = oct(stat.S_IMODE(file_stat.st_mode))
            except:
                file_permissions = "unknown"
        
        failure_record = EventUpdateFailure(
            event_id=event_id,
            validation_log_id=validation_log_id,
            failure_type=failure_type,
            error_message=error_message,
            stack_trace=stack_trace,
            validator_id=validator_id,
            attempted_corrections=attempted_corrections,
            file_path=file_path,
            file_exists=file_exists,
            file_permissions=file_permissions
        )
        
        db.add(failure_record)
        db.commit()
        logger.error(f"Logged update failure for event {event_id}: {failure_type} - {error_message}")
        
    except Exception as log_error:
        logger.error(f"Failed to log update failure for event {event_id}: {log_error}")
        db.rollback()
    finally:
        db.close()

def apply_validation_corrections(event_id: str, corrections: dict, validator_id: str, validation_log_id: int) -> bool:
    """
    Apply validation corrections to event files with comprehensive failure logging
    Returns True if corrections were successfully applied
    """
    import traceback
    from pathlib import Path
    
    event_file = None
    events_dir = Path(__file__).parent.parent / 'timeline_data' / 'events'
    
    try:
        # Find event file with detailed logging
        exact_file = events_dir / f"{event_id}.json"
        if exact_file.exists():
            event_file = exact_file
        else:
            # Search for files containing the event ID
            for file_path in events_dir.glob("*.json"):
                if event_id in file_path.name:
                    event_file = file_path
                    break
        
        if not event_file or not event_file.exists():
            error_msg = f"Event file not found for ID: {event_id}. Searched in {events_dir}"
            log_update_failure(
                event_id=event_id,
                validation_log_id=validation_log_id,
                validator_id=validator_id,
                failure_type="file_not_found",
                error_message=error_msg,
                attempted_corrections=corrections,
                file_path=str(exact_file) if exact_file else None
            )
            return False
        
        # Check file permissions before attempting to read
        if not os.access(event_file, os.R_OK):
            error_msg = f"No read permission for event file: {event_file}"
            log_update_failure(
                event_id=event_id,
                validation_log_id=validation_log_id,
                validator_id=validator_id,
                failure_type="permission_error",
                error_message=error_msg,
                attempted_corrections=corrections,
                file_path=str(event_file)
            )
            return False
        
        # Read current event data with error handling
        try:
            with open(event_file, 'r') as f:
                event_data = json.load(f)
        except json.JSONDecodeError as json_error:
            error_msg = f"JSON decode error reading event file: {json_error}"
            log_update_failure(
                event_id=event_id,
                validation_log_id=validation_log_id,
                validator_id=validator_id,
                failure_type="json_read_error",
                error_message=error_msg,
                stack_trace=traceback.format_exc(),
                attempted_corrections=corrections,
                file_path=str(event_file)
            )
            return False
        
        # Apply corrections with detailed tracking
        corrections_made = []
        try:
            # Handle different correction data structures
            if corrections is None or corrections == False:
                # No corrections to apply
                corrections_made.append("No specific corrections applied")
            elif corrections == True:
                # Boolean true indicates validation but no specific corrections
                corrections_made.append("Event validated - no corrections needed")
            elif isinstance(corrections, dict):
                # Standard field-value corrections
                for field, new_value in corrections.items():
                    if field in event_data:
                        old_value = event_data[field]
                        event_data[field] = new_value
                        corrections_made.append(f"{field}: '{old_value}' → '{new_value}'")
                    else:
                        event_data[field] = new_value
                        corrections_made.append(f"{field}: (added) '{new_value}'")
            elif isinstance(corrections, list):
                # List of correction objects (source improvements, etc.)
                for correction_obj in corrections:
                    if isinstance(correction_obj, dict):
                        if 'added_sources' in correction_obj or 'removed_sources' in correction_obj:
                            # Handle source modifications
                            sources = event_data.get('sources', [])
                            if not isinstance(sources, list):
                                sources = []
                            
                            # Remove placeholder sources
                            if 'removed_sources' in correction_obj:
                                removed = correction_obj['removed_sources']
                                original_count = len(sources)
                                sources = [s for s in sources if not any(
                                    placeholder in str(s) for placeholder in removed
                                )]
                                if len(sources) < original_count:
                                    corrections_made.append(f"Removed placeholder sources: {removed}")
                            
                            # Add new sources
                            if 'added_sources' in correction_obj:
                                added = correction_obj['added_sources']
                                for source in added:
                                    if isinstance(source, str):
                                        sources.append({"title": source, "url": source})
                                    else:
                                        sources.append(source)
                                corrections_made.append(f"Added sources: {added}")
                            
                            event_data['sources'] = sources
                        else:
                            # Generic field updates
                            for field, new_value in correction_obj.items():
                                if field in event_data:
                                    old_value = event_data[field]
                                    event_data[field] = new_value
                                    corrections_made.append(f"{field}: '{old_value}' → '{new_value}'")
                                else:
                                    event_data[field] = new_value
                                    corrections_made.append(f"{field}: (added) '{new_value}'")
            else:
                # Log the unexpected format but don't fail
                corrections_made.append(f"Validation completed (corrections format: {type(corrections).__name__})")
                
        except Exception as correction_error:
            error_msg = f"Error applying corrections: {correction_error}"
            log_update_failure(
                event_id=event_id,
                validation_log_id=validation_log_id,
                validator_id=validator_id,
                failure_type="correction_application_error",
                error_message=error_msg,
                stack_trace=traceback.format_exc(),
                attempted_corrections=corrections,
                file_path=str(event_file)
            )
            return False
        
        # Add validation metadata
        if 'validation_metadata' not in event_data:
            event_data['validation_metadata'] = {}
        
        event_data['validation_metadata'].update({
            'last_corrected': datetime.now().isoformat(),
            'corrected_by': validator_id,
            'validation_log_id': validation_log_id,
            'corrections_applied': corrections_made
        })
        
        # Check write permissions before attempting to write
        if not os.access(event_file, os.W_OK):
            error_msg = f"No write permission for event file: {event_file}"
            log_update_failure(
                event_id=event_id,
                validation_log_id=validation_log_id,
                validator_id=validator_id,
                failure_type="permission_error",
                error_message=error_msg,
                attempted_corrections=corrections,
                file_path=str(event_file)
            )
            return False
        
        # Write updated event data with error handling
        try:
            # Create backup before writing
            backup_content = None
            try:
                with open(event_file, 'r') as f:
                    backup_content = f.read()
            except:
                pass  # If we can't backup, still try to write
            
            with open(event_file, 'w') as f:
                json.dump(event_data, f, indent=2)
            
            # Verify the write was successful by reading back
            try:
                with open(event_file, 'r') as f:
                    verification_data = json.load(f)
                    # Basic verification that our changes are there
                    if 'validation_metadata' not in verification_data:
                        raise Exception("Validation metadata missing from written file")
            except Exception as verify_error:
                # Try to restore backup if verification fails
                if backup_content:
                    try:
                        with open(event_file, 'w') as f:
                            f.write(backup_content)
                    except:
                        pass  # Backup restore failed too
                
                error_msg = f"File write verification failed: {verify_error}"
                log_update_failure(
                    event_id=event_id,
                    validation_log_id=validation_log_id,
                    validator_id=validator_id,
                    failure_type="write_verification_error",
                    error_message=error_msg,
                    stack_trace=traceback.format_exc(),
                    attempted_corrections=corrections,
                    file_path=str(event_file)
                )
                return False
            
        except IOError as write_error:
            error_msg = f"IO error writing event file: {write_error}"
            log_update_failure(
                event_id=event_id,
                validation_log_id=validation_log_id,
                validator_id=validator_id,
                failure_type="io_write_error",
                error_message=error_msg,
                stack_trace=traceback.format_exc(),
                attempted_corrections=corrections,
                file_path=str(event_file)
            )
            return False
        except json.JSONEncodeError as json_error:
            error_msg = f"JSON encode error writing event file: {json_error}"
            log_update_failure(
                event_id=event_id,
                validation_log_id=validation_log_id,
                validator_id=validator_id,
                failure_type="json_write_error",
                error_message=error_msg,
                stack_trace=traceback.format_exc(),
                attempted_corrections=corrections,
                file_path=str(event_file)
            )
            return False
        
        logger.info(f"Successfully applied {len(corrections_made)} corrections to event {event_id}: {corrections_made}")
        return True
        
    except Exception as e:
        error_msg = f"Unexpected error applying corrections to event {event_id}: {e}"
        log_update_failure(
            event_id=event_id,
            validation_log_id=validation_log_id,
            validator_id=validator_id,
            failure_type="unexpected_error",
            error_message=error_msg,
            stack_trace=traceback.format_exc(),
            attempted_corrections=corrections,
            file_path=str(event_file) if event_file else None
        )
        return False

# ==================== BLUEPRINT REGISTRATION ====================
# Import and register route blueprints
from research_monitor.routes import register_blueprints
register_blueprints(app)

# ==================== RESEARCH PRIORITY APIS (Database Authoritative) ====================
# MOVED TO routes/priorities.py blueprint

# @app.route('/api/priorities/next', methods=['POST'])
@require_api_key
def reserve_next_priority():
    """Atomically reserve the next priority for an agent (prevents race conditions)"""
    
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
# MOVED TO routes/events.py blueprint - 8 event routes + helpers
# Lines 997-1593 have been extracted to routes/events.py
#
# @app.route('/api/events/search')
# def search_events():
#     """Search events using JSON queries and full-text search"""
#     db = get_db()
#     try:
#         query_text = request.args.get('q', '')
#         date_from = request.args.get('date_from')
#         date_to = request.args.get('date_to')
#         limit = min(int(request.args.get('limit', 20)), 5000)
        
        # Use SQLite FTS if query provided
#         if query_text:
            # Escape special characters for FTS5
#             fts_query = query_text.replace('.', ' ').replace('-', ' ').replace(':', ' ')
            # For exact phrase matching with special chars, use LIKE fallback
#             if any(char in query_text for char in ['.', ':', '/', '@']):
                # Use LIKE search for URLs and special content including JSON sources
#                 results = db.execute(text('''
#                     SELECT e.id, e.date, e.title, e.summary, e.importance
#                     FROM timeline_events e
#                     WHERE e.title LIKE :query_pattern
#                        OR e.summary LIKE :query_pattern
#                        OR e.json_content LIKE :query_pattern
#                     ORDER BY e.importance DESC
#                     LIMIT :limit
#                 '''), {'query_pattern': f'%{query_text}%', 'limit': limit})
#             else:
                # Use FTS5 for regular text search
#                 results = db.execute(text('''
#                     SELECT e.id, e.date, e.title, e.summary, e.importance
#                     FROM timeline_events e
#                     JOIN events_fts ON events_fts.id = e.id
#                     WHERE events_fts MATCH :query
#                     ORDER BY rank
#                     LIMIT :limit
#                 '''), {'query': fts_query, 'limit': limit})
#         else:
            # Regular search
#             query = db.query(TimelineEvent)
            
#             if date_from:
#                 query = query.filter(TimelineEvent.date >= date_from)
#             if date_to:
#                 query = query.filter(TimelineEvent.date <= date_to)
            
#             results = query.order_by(TimelineEvent.date.desc()).limit(limit)
        
#         events = []
#         for row in results:
#             if hasattr(row, 'json_content'):
#                 events.append(row.json_content)
#             else:
#                 events.append({
#                     'id': row.id,
#                     'date': row.date,
#                     'title': row.title,
#                     'summary': row.summary,
#                     'importance': row.importance
#                 })
        
#         return jsonify({'events': events, 'count': len(events)})
        
#     finally:
#         db.close()

# @app.route('/api/events/missing-sources')
# def find_events_missing_sources():
#     """Find events with missing or insufficient sources"""
#     db = get_db()
#     try:
#         min_sources = int(request.args.get('min_sources', 2))
#         limit = min(int(request.args.get('limit', 50)), 5000)
        
        # Query events and check their sources
#         events = db.query(TimelineEvent).order_by(TimelineEvent.importance.desc()).all()
        
#         missing_sources_events = []
#         for event in events:
#             if event.json_content:
#                 sources = event.json_content.get('sources', [])
#                 source_count = 0
                
#                 if isinstance(sources, list):
#                     source_count = len(sources)
#                 elif isinstance(sources, dict):
#                     source_count = 1
#                 elif sources:
#                     source_count = 1
                
#                 if source_count < min_sources:
#                     event_dict = event.json_content.copy()
#                     event_dict['source_count'] = source_count
#                     event_dict['sources_needed'] = min_sources - source_count
#                     missing_sources_events.append(event_dict)
                    
#                     if len(missing_sources_events) >= limit:
#                         break
        
#         return jsonify({
#             'events': missing_sources_events, 
#             'count': len(missing_sources_events),
#             'criteria': {
#                 'min_sources': min_sources,
#                 'limit': limit
#             }
#         })
        
#     finally:
#         db.close()

# @app.route('/api/events/validation-queue')
# def get_validation_queue():
#     """Get events prioritized for validation by importance and source quality"""
#     db = get_db()
#     try:
#         limit = min(int(request.args.get('limit', 20)), 5000)
#         min_importance = int(request.args.get('min_importance', 6))
#         max_sources = int(request.args.get('max_sources', 2))
        
        # Get events that are high importance but low source count
#         events = db.query(TimelineEvent).order_by(TimelineEvent.importance.desc()).all()
        
#         validation_queue = []
#         for event in events:
#             if event.json_content and event.importance >= min_importance:
#                 sources = event.json_content.get('sources', [])
#                 source_count = 0
                
#                 if isinstance(sources, list):
#                     source_count = len(sources)
#                 elif isinstance(sources, dict):
#                     source_count = 1
#                 elif sources:
#                     source_count = 1
                
#                 if source_count <= max_sources:
#                     event_dict = event.json_content.copy()
#                     event_dict['source_count'] = source_count
#                     event_dict['validation_priority'] = event.importance - source_count
#                     validation_queue.append(event_dict)
                    
#                     if len(validation_queue) >= limit:
#                         break
        
        # Sort by validation priority (importance minus source count)
#         validation_queue.sort(key=lambda x: x.get('validation_priority', 0), reverse=True)
        
#         return jsonify({
#             'events': validation_queue,
#             'count': len(validation_queue),
#             'criteria': {
#                 'min_importance': min_importance,
#                 'max_sources': max_sources,
#                 'limit': limit
#             }
#         })
        
#     finally:
#         db.close()

# @app.route('/api/events/broken-links')
# def find_broken_links():
#     """Find events with potentially broken or inaccessible source links"""
#     db = get_db()
#     try:
#         limit = min(int(request.args.get('limit', 50)), 5000)
#         check_links = request.args.get('check_links', 'false').lower() == 'true'
        
#         events = db.query(TimelineEvent).order_by(TimelineEvent.importance.desc()).all()
        
#         broken_link_events = []
#         for event in events:
#             if event.json_content:
#                 sources = event.json_content.get('sources', [])
#                 if isinstance(sources, list):
#                     suspicious_urls = []
#                     for source in sources:
#                         if isinstance(source, dict) and 'url' in source:
#                             url = source['url']
                            # Basic checks for potentially broken links
#                             if (url.startswith('http://example.com') or 
#                                 url.startswith('https://example.com') or
#                                 url == 'TBD' or 
#                                 url == 'internal-research' or
#                                 'internal-research-portal' in url):
#                                 suspicious_urls.append(url)
                    
#                     if suspicious_urls:
#                         event_dict = event.json_content.copy()
#                         event_dict['suspicious_urls'] = suspicious_urls
#                         event_dict['suspicious_count'] = len(suspicious_urls)
#                         broken_link_events.append(event_dict)
                        
#                         if len(broken_link_events) >= limit:
#                             break
        
#         return jsonify({
#             'events': broken_link_events,
#             'count': len(broken_link_events),
#             'criteria': {
#                 'check_links': check_links,
#                 'limit': limit
#             }
#         })
        
#     finally:
#         db.close()

# @app.route('/api/events/research-candidates')
# def get_research_candidates():
#     """Get high-importance events with insufficient sources - ideal for research"""
#     db = get_db()
#     try:
#         limit = min(int(request.args.get('limit', 20)), 5000)
#         min_importance = int(request.args.get('min_importance', 7))
#         max_sources = int(request.args.get('max_sources', 2))
        
#         events = db.query(TimelineEvent).order_by(TimelineEvent.importance.desc()).all()
        
#         research_candidates = []
#         for event in events:
#             if event.json_content and event.importance >= min_importance:
#                 sources = event.json_content.get('sources', [])
#                 source_count = 0
                
#                 if isinstance(sources, list):
#                     source_count = len(sources)
#                 elif isinstance(sources, dict):
#                     source_count = 1
#                 elif sources:
#                     source_count = 1
                
#                 if source_count <= max_sources:
#                     event_dict = event.json_content.copy()
#                     event_dict['source_count'] = source_count
#                     event_dict['research_priority'] = event.importance * 2 - source_count
#                     research_candidates.append(event_dict)
                    
#                     if len(research_candidates) >= limit:
#                         break
        
        # Sort by research priority
#         research_candidates.sort(key=lambda x: x.get('research_priority', 0), reverse=True)
        
#         return jsonify({
#             'events': research_candidates,
#             'count': len(research_candidates),
#             'criteria': {
#                 'min_importance': min_importance,
#                 'max_sources': max_sources,
#                 'limit': limit
#             }
#         })
        
#     finally:
#         db.close()

# @app.route('/api/timeline/actor/<actor>/timeline')
# def get_actor_timeline(actor):
#     """Get chronological timeline of all events for a specific actor"""
#     db = get_db()
#     try:
#         limit = min(int(request.args.get('limit', 100)), 500)
        
        # Search for events containing the actor
#         events = db.query(TimelineEvent)\
#             .filter(TimelineEvent.json_content.contains(actor))\
#             .order_by(TimelineEvent.date.asc())\
#             .limit(limit)\
#             .all()
        
#         timeline_events = []
#         for event in events:
#             if event.json_content:
                # Verify actor is actually in the actors list, not just mentioned
#                 actors = event.json_content.get('actors', [])
#                 if isinstance(actors, list) and any(actor.lower() in str(a).lower() for a in actors):
#                     event_dict = {
#                         'date': event.date,
#                         'id': event.id,
#                         'title': event.title,
#                         'summary': event.summary,
#                         'importance': event.importance,
#                         'actors': actors,
#                         'tags': event.json_content.get('tags', [])
#                     }
#                     timeline_events.append(event_dict)
        
        # Group by year for easier navigation
#         timeline_by_year = {}
#         for event in timeline_events:
#             year = event['date'][:4]
#             if year not in timeline_by_year:
#                 timeline_by_year[year] = []
#             timeline_by_year[year].append(event)
        
#         return jsonify({
#             'actor': actor,
#             'events': timeline_events,
#             'events_by_year': timeline_by_year,
#             'total_events': len(timeline_events),
#             'date_range': {
#                 'earliest': timeline_events[0]['date'] if timeline_events else None,
#                 'latest': timeline_events[-1]['date'] if timeline_events else None
#             }
#         })
        
#     finally:
#         db.close()

# @app.route('/api/events/validate', methods=['POST'])
# def validate_event():
#     """Validate an event before saving with helpful error messages"""
#     try:
#         event = request.json
#         if not event:
#             return jsonify({
#                 'valid': False,
#                 'errors': ['No event data provided'],
#                 'warnings': [],
#                 'fixed_event': None
#             }), 400
            
        # Use built-in validation
#         validation_result = validate_timeline_event(event)
#         errors = validation_result['errors']
#         warnings = validation_result['warnings'] 
#         fixed_event = validation_result['fixed_event']
        
        # Check for duplicates
#         if event.get('id'):
#             db = get_db()
#             try:
#                 existing = db.query(TimelineEvent).filter_by(id=event['id']).first()
#                 if existing:
#                     errors.append(f"Event {event['id']} already exists")
#             finally:
#                 db.close()
        
#         status_code = 400 if errors else 200
#         return jsonify({
#             'valid': len(errors) == 0,
#             'errors': errors,
#             'warnings': warnings,
#             'fixed_event': fixed_event
#         }), status_code
        
#     except Exception as e:
#         return jsonify({
#             'valid': False,
#             'errors': [f'Validation error: {str(e)}'],
#             'warnings': []
#         }), 500

# ==================== COMMIT ORCHESTRATION ====================

# @app.route('/api/events/batch', methods=['POST'])
# @require_api_key
# def batch_create_events():
#     """Create multiple events with validation and error handling"""
#     global events_since_commit
    
#     db = get_db()
#     try:
#         data = request.json
#         events = data.get('events', [])
#         priority_id = data.get('priority_id')
        
#         if not events:
#             return jsonify({'error': 'No events provided'}), 400
        
#         results = []
#         successful_events = 0
#         failed_events = 0
        
#         for i, event in enumerate(events):
#             event_result = {
#                 'index': i,
#                 'event_id': event.get('id', f'event-{i}'),
#                 'status': 'success',
#                 'errors': [],
#                 'warnings': []
#             }
            
#             try:
                # Validate and fix event using enhanced validator
#                 validation_errors, fixed_event = validate_single_event(event, db)
#                 if validation_errors:
#                     event_result['status'] = 'failed'
#                     event_result['errors'] = validation_errors
#                     failed_events += 1
#                     results.append(event_result)
#                     continue
                
                # Use the fixed event (validator handles ID generation, type fixing, etc.)
#                 event_result['event_id'] = fixed_event['id']
                
                # Save fixed event to filesystem
#                 event_path = EVENTS_PATH / f"{fixed_event['id']}.json"
#                 with open(event_path, 'w') as f:
#                     json.dump(fixed_event, f, indent=2)
                
                # Create metadata
#                 metadata = EventMetadata(
#                     event_id=fixed_event['id'],
#                     created_by=request.headers.get('User-Agent', 'claude-code'),
#                     research_priority_id=priority_id,
#                     validation_status='validated'
#                 )
#                 db.add(metadata)
                
                # Log activity
#                 activity = ActivityLog(
#                     action='event_batched',
#                     event_id=event['id'],
#                     priority_id=priority_id,
#                     agent=request.headers.get('User-Agent', 'claude-code')
#                 )
#                 db.add(activity)
                
#                 successful_events += 1
#                 events_since_commit += 1
                
#             except Exception as e:
#                 event_result['status'] = 'failed'
#                 event_result['errors'].append(f'System error: {str(e)}')
#                 failed_events += 1
            
#             results.append(event_result)
        
        # Update session tracking
#         session = db.query(ResearchSession).filter_by(session_id=current_session_id).first()
#         if not session:
#             session = ResearchSession(
#                 session_id=current_session_id, 
#                 commit_threshold=COMMIT_THRESHOLD,
#                 events_created=0,
#                 priorities_completed=0
#             )
#             db.add(session)
        
#         session.events_created = (session.events_created or 0) + successful_events
        
#         db.commit()
        
        # Check if we should trigger a commit
#         if events_since_commit >= COMMIT_THRESHOLD:
#             trigger_commit()
        
#         return jsonify({
#             'status': 'completed',
#             'successful_events': successful_events,
#             'failed_events': failed_events,
#             'total_events': len(events),
#             'events_since_commit': events_since_commit,
#             'results': results
#         })
        
#     except Exception as e:
#         logger.error(f"Batch event creation failed: {e}")
#         return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500
#     finally:
#         db.close()

# def validate_single_event(event: dict, db) -> tuple[List[str], dict]:
#     """Validate a single event using built-in validator and return errors and fixed event"""
#     validation_result = validate_timeline_event(event)
    
#     errors = validation_result['errors'].copy()
#     fixed_event = validation_result['fixed_event']
    
    # Check for duplicates by ID (only real error we can't fix)
#     if fixed_event.get('id'):
#         existing = db.query(TimelineEvent).filter_by(id=fixed_event['id']).first()
#         if existing:
#             errors.append(f"Event {fixed_event['id']} already exists")
    
#     return errors, fixed_event

# @app.route('/api/events/staged', methods=['POST'])
# @require_api_key
# def stage_event():
#     """Stage an event for the next commit"""
#     global events_since_commit
    
#     db = get_db()
#     try:
#         data = request.json
#         priority_id = data.get('priority_id')
        
        # Validate and fix event using enhanced validator
#         validation_errors, fixed_event = validate_single_event(data, db)
        
        # Only reject if there are truly unfixable errors (like duplicates)
        # Type conversion errors and missing fields are auto-fixed
#         unfixable_errors = [err for err in validation_errors if 'already exists' in err]
#         if unfixable_errors:
#             return jsonify({
#                 'error': 'Validation failed',
#                 'details': unfixable_errors
#             }), 400
        
        # Use fixed event
#         event_id = fixed_event['id']
        
        # Save fixed event to filesystem
#         event_path = EVENTS_PATH / f"{event_id}.json"
#         with open(event_path, 'w') as f:
#             json.dump(fixed_event, f, indent=2)
        
        # Create metadata
#         metadata = EventMetadata(
#             event_id=event_id,
#             created_by=request.headers.get('User-Agent', 'claude-code'),
#             research_priority_id=priority_id,
#             validation_status='pending'
#         )
#         db.add(metadata)
        
        # Update session tracking
#         session = db.query(ResearchSession).filter_by(session_id=current_session_id).first()
#         if not session:
#             session = ResearchSession(
#                 session_id=current_session_id, 
#                 commit_threshold=COMMIT_THRESHOLD,
#                 events_created=0,
#                 priorities_completed=0
#             )
#             db.add(session)
        
#         session.events_created = (session.events_created or 0) + 1
#         events_since_commit += 1
        
        # Log activity
#         activity = ActivityLog(
#             action='event_staged',
#             event_id=event_id,
#             priority_id=priority_id,
#             agent=request.headers.get('User-Agent', 'claude-code')
#         )
#         db.add(activity)
        
#         db.commit()
        
        # Check if we should trigger a commit
#         if events_since_commit >= COMMIT_THRESHOLD:
#             trigger_commit()
        
#         return jsonify({'status': 'staged', 'events_since_commit': events_since_commit})
        
#     finally:
#         db.close()

# def trigger_commit():
#     """Orchestrate a git commit with new events and updated priorities"""
#     global events_since_commit
    
#     db = get_db()
#     try:
        # Export valuable priorities
#         priorities = db.query(ResearchPriority)\
#             .filter(ResearchPriority.export_worthy == True).all()
        
#         for p in priorities:
#             priority_file = PRIORITIES_PATH / f"{p.id}.json"
#             with open(priority_file, 'w') as f:
#                 json.dump({
#                     'id': p.id,
#                     'title': p.title,
#                     'description': p.description,
#                     'priority': p.priority,
#                     'status': p.status,
#                     'estimated_events': p.estimated_events,
#                     'actual_events': p.actual_events,
#                     'category': p.category,
#                     'tags': p.tags,
#                     'research_notes': p.research_notes
#                 }, f, indent=2)
        
        # Signal commit needed - actual git operations should be done by orchestrator
        # Update session to record that commit threshold was reached
#         session = db.query(ResearchSession).filter_by(session_id=current_session_id).first()
#         if session:
#             session.last_commit = datetime.now()
        
#         db.commit()
        
        # Log for orchestrator to see
#         logger.info(f"COMMIT THRESHOLD REACHED: {events_since_commit} events ready for commit")
#         logger.info(f"Exported {len(priorities)} priorities marked as export_worthy")
#         logger.info("Orchestrator should perform: git add timeline_data/events research_priorities && git commit")
        
        # Reset counter
#         events_since_commit = 0
            
#     finally:
#         db.close()

# ==================== STATISTICS ====================

# MOVED TO routes/git.py blueprint
# def get_qa_validation_stats(db):
#     """Get QA validation statistics for commit metadata"""
#     from models import EventMetadata
#
#     try:
#         # Count events by validation status
#         validation_counts = db.query(
#             EventMetadata.validation_status,
#             func.count(EventMetadata.event_id)
#         ).group_by(EventMetadata.validation_status).all()
#
#         # Convert to dictionary
#         stats = {}
#         total_events = 0
#         for status, count in validation_counts:
#             stats[status or 'pending'] = count
#             total_events += count
#
#         # Ensure all statuses are represented
#         for status in ['pending', 'validated', 'rejected']:
#             if status not in stats:
#                 stats[status] = 0
#
#         # Calculate recent validation activity (last 24 hours)
#         recent_cutoff = datetime.now() - timedelta(hours=24)
#
#         recent_validations = db.query(EventMetadata).filter(
#             EventMetadata.validation_date >= recent_cutoff,
#             EventMetadata.validation_status.in_(['validated', 'rejected'])
#         ).count()
#
#         return {
#             'total_events_with_metadata': total_events,
#             'validation_breakdown': stats,
#             'recent_validations_24h': recent_validations,
#             'validation_rate': round((stats['validated'] + stats['rejected']) / max(total_events, 1) * 100, 1)
#         }
#
#     except Exception as e:
#         logger.error(f"Error getting QA validation stats: {e}")
#         return {
#             'total_events_with_metadata': 0,
#             'validation_breakdown': {'pending': 0, 'validated': 0, 'rejected': 0},
#             'recent_validations_24h': 0,
#             'validation_rate': 0.0
#         }
#
# @app.route('/api/commit/status')
# def get_commit_status():
#     """Check if a commit is needed with QA validation metadata"""
#     db = get_db()
#
#     try:
#         # Get QA validation statistics
#         qa_stats = get_qa_validation_stats(db)
#
#         # Basic commit status
#         commit_status = {
#             'events_since_commit': events_since_commit,
#             'threshold': COMMIT_THRESHOLD,
#             'commit_needed': events_since_commit >= COMMIT_THRESHOLD,
#             'session_id': current_session_id
#         }
#
#         # Add QA validation metadata
#         commit_status['qa_validation'] = qa_stats
#
#         # Add suggested commit message components
#         if commit_status['commit_needed']:
#             validated_count = qa_stats['validation_breakdown']['validated']
#             rejected_count = qa_stats['validation_breakdown']['rejected']
#             pending_count = qa_stats['validation_breakdown']['pending']
#
#             commit_status['suggested_commit_message'] = {
#                 'title': f"Add {events_since_commit} researched events with QA validation",
#                 'qa_summary': f"QA Status: {validated_count} validated, {rejected_count} rejected, {pending_count} pending review",
#                 'validation_rate': f"Overall validation rate: {qa_stats['validation_rate']}%"
#             }
#
#         return jsonify(commit_status)
#
#     finally:
#         db.close()
#
# @app.route('/api/commit/reset', methods=['POST'])
# @require_api_key
# def reset_commit_counter():
#     """Reset the commit counter after orchestrator performs commit"""
#     global events_since_commit
#     events_since_commit = 0
#     logger.info("Commit counter reset by orchestrator")
#     return jsonify({'status': 'reset', 'events_since_commit': 0})

# ==================== SERVER MANAGEMENT ====================

# MOVED TO routes/system.py blueprint
# @app.route('/api/server/shutdown', methods=['POST'])
# @require_api_key
# def graceful_shutdown():
#     """Gracefully shutdown the Research Monitor server"""
#     global syncer
#
#     try:
#         # Stop the filesystem sync thread
#         if syncer:
#             syncer.stop()
#             logger.info("Filesystem sync thread stopped")
#
#         # Close database connections
#         try:
#             Session.remove()
#             engine.dispose()
#             logger.info("Database connections closed")
#         except Exception as e:
#             logger.warning(f"Error closing database connections: {e}")
#
#         # Schedule Flask server shutdown
#         def shutdown_server():
#             time.sleep(1)  # Give response time to be sent
#             try:
#                 os.kill(os.getpid(), signal.SIGTERM)
#             except Exception as e:
#                 logger.error(f"Error during shutdown: {e}")
#         threading.Thread(target=shutdown_server).start()
#
#         return jsonify({
#             'status': 'shutting_down',
#             'message': 'Research Monitor server is shutting down gracefully'
#         })
#
#     except Exception as e:
#         logger.error(f"Error during graceful shutdown: {e}")
#         return jsonify({
#             'status': 'error',
#             'message': f'Shutdown error: {str(e)}'
#         }), 500
#
# @app.route('/api/server/health', methods=['GET'])
# def health_check():
#     """Simple health check endpoint"""
#     db = get_db()
#     try:
#         # Test database connection
#         db.execute(text('SELECT 1'))
#         db_status = 'healthy'
#     except Exception as e:
#         db_status = f'unhealthy: {str(e)}'
#     finally:
#         db.close()
#
#     return jsonify({
#         'status': 'healthy',
#         'database': db_status,
#         'session_id': current_session_id,
#         'events_since_commit': events_since_commit,
#         'timestamp': datetime.now().isoformat()
#     })

# MOVED TO routes/docs.py blueprint
# @app.route('/api/openapi.json', methods=['GET'])
# @cache.cached(timeout=3600)  # Cache for 1 hour
# def get_openapi_spec():
#     """Return OpenAPI 3.0 specification"""
#     try:
#         openapi_path = Path(__file__).parent / 'openapi.json'
#         with open(openapi_path, 'r') as f:
#             spec = json.load(f)
#         return jsonify(spec)
#     except Exception as e:
#         logger.error(f"Error loading OpenAPI spec: {e}")
#         return jsonify({
#             'error': 'OpenAPI specification not available',
#             'message': str(e)
#         }), 500
#
# @app.route('/api/docs', methods=['GET'])
# def api_documentation():
#     """Redirect to API documentation"""
#     return jsonify({
#         'documentation': {
#             'markdown': '/static/API_DOCUMENTATION.md',
#             'openapi': '/api/openapi.json',
#             'interactive': 'Planned for future release'
#         },
#         'endpoints': {
#             'events': [
#                 '/api/events/search',
#                 '/api/events/{id}',
#                 '/api/events/staged'
#             ],
#             'timeline': [
#                 '/api/timeline/events',
#                 '/api/timeline/actors',
#                 '/api/timeline/tags',
#                 '/api/timeline/sources'
#             ],
#             'visualization': [
#                 '/api/viewer/timeline-data',
#                 '/api/viewer/actor-network',
#                 '/api/viewer/tag-cloud'
#             ],
#             'statistics': [
#                 '/api/viewer/stats/overview',
#                 '/api/viewer/stats/actors',
#                 '/api/viewer/stats/patterns'
#             ],
#             'research': [
#                 '/api/priorities/next',
#                 '/api/priorities/{id}/status'
#             ],
#             'system': [
#                 '/api/server/health',
#                 '/api/stats',
#                 '/api/commit/status'
#             ]
#         }
#     })

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

# ==================== TIMELINE VIEWER API ENDPOINTS ====================
# MOVED TO routes/timeline.py blueprint - 12 timeline routes
# Lines 1846-2442 have been extracted to routes/timeline.py
#
# @app.route('/api/timeline/events', methods=['GET'])
# def get_timeline_events():
#     """Get timeline events with pagination and filtering"""
#     db = get_db()
#     try:
        # Pagination parameters
#         page = int(request.args.get('page', 1))
#         per_page = min(int(request.args.get('per_page', 50)), 5000)  # Max 5000 per page for loading all events
        
        # Filtering parameters
#         date_from = request.args.get('date_from')
#         date_to = request.args.get('date_to')
#         importance_min = request.args.get('importance_min', type=int)
#         importance_max = request.args.get('importance_max', type=int)
#         search_text = request.args.get('search')
        
        # Build query
#         query = db.query(TimelineEvent)
        
        # Apply filters
#         if date_from:
#             query = query.filter(TimelineEvent.date >= date_from)
#         if date_to:
#             query = query.filter(TimelineEvent.date <= date_to)
#         if importance_min:
#             query = query.filter(TimelineEvent.importance >= importance_min)
#         if importance_max:
#             query = query.filter(TimelineEvent.importance <= importance_max)
        
        # Full-text search if provided
#         if search_text:
#             search_query = f'%{search_text}%'
#             query = query.filter(
#                 or_(
#                     TimelineEvent.title.ilike(search_query),
#                     TimelineEvent.summary.ilike(search_query)
#                 )
#             )
        
        # Order by date descending
#         query = query.order_by(TimelineEvent.date.desc())
        
        # Get total count for pagination
#         total = query.count()
        
        # Apply pagination
#         offset = (page - 1) * per_page
#         events = query.offset(offset).limit(per_page).all()
        
        # Convert to JSON format using the json_content field
#         events_data = []
#         for event in events:
            # Start with the full JSON content
#             event_dict = event.json_content.copy() if event.json_content else {}
            
            # Add filesystem metadata
#             event_dict.update({
#                 'file_path': event.file_path,
#                 'last_synced': event.last_synced.isoformat() if event.last_synced else None
#             })
            
#             events_data.append(event_dict)
        
        # Calculate pagination info
#         pages = (total + per_page - 1) // per_page
#         has_prev = page > 1
#         has_next = page < pages
        
#         return jsonify({
#             'events': events_data,
#             'pagination': {
#                 'page': page,
#                 'per_page': per_page,
#                 'total': total,
#                 'pages': pages,
#                 'has_prev': has_prev,
#                 'has_next': has_next,
#                 'prev_page': page - 1 if has_prev else None,
#                 'next_page': page + 1 if has_next else None
#             },
#             'filters_applied': {
#                 'date_from': date_from,
#                 'date_to': date_to,
#                 'importance_min': importance_min,
#                 'importance_max': importance_max,
#                 'search_text': search_text
#             }
#         })
        
#     except Exception as e:
#         logger.error(f"Error getting timeline events: {e}")
#         return jsonify({'error': 'Failed to retrieve timeline events'}), 500
#     finally:
#         db.close()

# @app.route('/api/timeline/events/<event_id>', methods=['GET'])
# def get_timeline_event(event_id):
#     """Get a single timeline event by ID"""
#     db = get_db()
#     try:
#         event = db.query(TimelineEvent).filter_by(id=event_id).first()
#         if not event:
#             return jsonify({'error': 'Event not found'}), 404
        
        # Return full JSON content for single event
#         event_dict = event.json_content.copy() if event.json_content else {}
        
        # Add filesystem metadata
#         event_dict.update({
#             'file_path': event.file_path,
#             'last_synced': event.last_synced.isoformat() if event.last_synced else None
#         })
        
#         return jsonify(event_dict)
        
#     except Exception as e:
#         logger.error(f"Error getting event {event_id}: {e}")
#         return jsonify({'error': 'Failed to retrieve event'}), 500
#     finally:
#         db.close()

# @app.route('/api/timeline/events/date/<date>', methods=['GET'])
# def get_timeline_events_by_date(date):
#     """Get timeline events for a specific date"""
#     db = get_db()
#     try:
#         events = db.query(TimelineEvent).filter_by(date=date).order_by(TimelineEvent.importance.desc()).all()
        
#         events_data = []
#         for event in events:
            # Use full JSON content
#             event_dict = event.json_content.copy() if event.json_content else {}
#             events_data.append(event_dict)
        
#         return jsonify({
#             'date': date,
#             'count': len(events_data),
#             'events': events_data
#         })
        
#     except Exception as e:
#         logger.error(f"Error getting events for date {date}: {e}")
#         return jsonify({'error': 'Failed to retrieve events for date'}), 500
#     finally:
#         db.close()

# @app.route('/api/timeline/events/year/<int:year>', methods=['GET'])
# def get_timeline_events_by_year(year):
#     """Get timeline events for a specific year"""
#     db = get_db()
#     try:
        # Filter events by year
#         start_date = f"{year}-01-01"
#         end_date = f"{year}-12-31"
        
#         events = db.query(TimelineEvent)\
#             .filter(TimelineEvent.date >= start_date)\
#             .filter(TimelineEvent.date <= end_date)\
#             .order_by(TimelineEvent.date.desc())\
#             .all()
        
#         events_data = []
#         for event in events:
            # Use full JSON content
#             event_dict = event.json_content.copy() if event.json_content else {}
#             events_data.append(event_dict)
        
#         return jsonify({
#             'year': year,
#             'count': len(events_data),
#             'events': events_data
#         })
        
#     except Exception as e:
#         logger.error(f"Error getting events for year {year}: {e}")
#         return jsonify({'error': 'Failed to retrieve events for year'}), 500
#     finally:
#         db.close()

# @app.route('/api/timeline/events/actor/<actor>', methods=['GET'])
# def get_timeline_events_by_actor(actor):
#     """Get timeline events involving a specific actor"""
#     db = get_db()
#     try:
        # Search for events containing the actor in the JSON content
#         events = db.query(TimelineEvent)\
#             .filter(TimelineEvent.json_content.contains(actor))\
#             .order_by(TimelineEvent.date.desc())\
#             .all()
        
#         events_data = []
#         for event in events:
            # Use full JSON content
#             event_dict = event.json_content.copy() if event.json_content else {}
#             events_data.append(event_dict)
        
#         return jsonify({
#             'actor': actor,
#             'count': len(events_data),
#             'events': events_data
#         })
        
#     except Exception as e:
#         logger.error(f"Error getting events for actor {actor}: {e}")
#         return jsonify({'error': 'Failed to retrieve events for actor'}), 500
#     finally:
#         db.close()

# ==================== TIMELINE METADATA ENDPOINTS ====================

# @app.route('/api/timeline/actors', methods=['GET'])
# @cache.cached(timeout=600, key_prefix='timeline_actors')  # Cache for 10 minutes
# def get_timeline_actors():
#     """Get all unique actors mentioned in timeline events"""
#     db = get_db()
#     try:
        # Get all events and extract actors from JSON content
#         events = db.query(TimelineEvent).all()
#         actors_set = set()
        
#         for event in events:
#             if event.json_content and 'actors' in event.json_content:
#                 actors = event.json_content.get('actors', [])
#                 if isinstance(actors, list):
#                     for actor in actors:
#                         if isinstance(actor, str) and actor.strip():
#                             actors_set.add(actor.strip())
        
        # Convert to sorted list
#         actors_list = sorted(list(actors_set))
        
#         return jsonify({
#             'actors': actors_list,
#             'count': len(actors_list)
#         })
        
#     except Exception as e:
#         logger.error(f"Error getting timeline actors: {e}")
#         return jsonify({'error': 'Failed to retrieve actors'}), 500
#     finally:
#         db.close()

# @app.route('/api/timeline/tags', methods=['GET'])
# @cache.cached(timeout=600, key_prefix='timeline_tags')  # Cache for 10 minutes
# def get_timeline_tags():
#     """Get all unique tags used in timeline events"""
#     db = get_db()
#     try:
        # Get all events and extract tags from JSON content
#         events = db.query(TimelineEvent).all()
#         tags_set = set()
        
#         for event in events:
#             if event.json_content and 'tags' in event.json_content:
#                 tags = event.json_content.get('tags', [])
#                 if isinstance(tags, list):
#                     for tag in tags:
#                         if isinstance(tag, str) and tag.strip():
#                             tags_set.add(tag.strip())
        
        # Convert to sorted list
#         tags_list = sorted(list(tags_set))
        
#         return jsonify({
#             'tags': tags_list,
#             'count': len(tags_list)
#         })
        
#     except Exception as e:
#         logger.error(f"Error getting timeline tags: {e}")
#         return jsonify({'error': 'Failed to retrieve tags'}), 500
#     finally:
#         db.close()

# @app.route('/api/timeline/sources', methods=['GET'])
# @cache.cached(timeout=600, key_prefix='timeline_sources')  # Cache for 10 minutes
# def get_timeline_sources():
#     """Get all unique sources/outlets used in timeline events"""
#     db = get_db()
#     try:
        # Get all events and extract sources from JSON content
#         events = db.query(TimelineEvent).all()
#         outlets_set = set()
        
#         for event in events:
#             if event.json_content and 'sources' in event.json_content:
#                 sources = event.json_content.get('sources', [])
#                 if isinstance(sources, list):
#                     for source in sources:
#                         if isinstance(source, dict) and 'outlet' in source:
#                             outlet = source.get('outlet', '').strip()
#                             if outlet:
#                                 outlets_set.add(outlet)
        
        # Convert to sorted list
#         outlets_list = sorted(list(outlets_set))
        
#         return jsonify({
#             'sources': outlets_list,
#             'count': len(outlets_list)
#         })
        
#     except Exception as e:
#         logger.error(f"Error getting timeline sources: {e}")
#         return jsonify({'error': 'Failed to retrieve sources'}), 500
#     finally:
#         db.close()

# @app.route('/api/timeline/date-range', methods=['GET'])
# @cache.cached(timeout=600, key_prefix='timeline_date_range')  # Cache for 10 minutes
# def get_timeline_date_range():
#     """Get the date range of all timeline events"""
#     db = get_db()
#     try:
        # Get min and max dates
#         result = db.query(
#             func.min(TimelineEvent.date).label('min_date'),
#             func.max(TimelineEvent.date).label('max_date'),
#             func.count(TimelineEvent.id).label('total_events')
#         ).first()
        
#         return jsonify({
#             'date_range': {
#                 'min_date': result.min_date,
#                 'max_date': result.max_date
#             },
#             'total_events': result.total_events
#         })
        
#     except Exception as e:
#         logger.error(f"Error getting timeline date range: {e}")
#         return jsonify({'error': 'Failed to retrieve date range'}), 500
#     finally:
#         db.close()

# ==================== TIMELINE FILTERING AND SEARCH ENDPOINTS ====================

# @app.route('/api/timeline/filter', methods=['GET'])
# def filter_timeline_events():
#     """Advanced filtering of timeline events with multiple criteria"""
#     db = get_db()
#     try:
        # Get filter parameters
#         date_from = request.args.get('date_from')
#         date_to = request.args.get('date_to') 
#         importance_min = request.args.get('importance_min', type=int)
#         importance_max = request.args.get('importance_max', type=int)
#         actors = request.args.getlist('actor')
#         tags = request.args.getlist('tag')
#         sources = request.args.getlist('source')
#         search_text = request.args.get('search')
        
        # Pagination
#         page = int(request.args.get('page', 1))
#         per_page = min(int(request.args.get('per_page', 50)), 200)
        
        # Build base query
#         query = db.query(TimelineEvent)
        
        # Apply filters
#         if date_from:
#             query = query.filter(TimelineEvent.date >= date_from)
#         if date_to:
#             query = query.filter(TimelineEvent.date <= date_to)
#         if importance_min:
#             query = query.filter(TimelineEvent.importance >= importance_min)
#         if importance_max:
#             query = query.filter(TimelineEvent.importance <= importance_max)
        
        # Actor filtering - check if any of the specified actors appear in JSON content
#         if actors:
#             actor_conditions = []
#             for actor in actors:
#                 actor_conditions.append(TimelineEvent.json_content.contains(actor))
#             query = query.filter(or_(*actor_conditions))
        
        # Tag filtering - check if any of the specified tags appear in JSON content
#         if tags:
#             tag_conditions = []
#             for tag in tags:
#                 tag_conditions.append(TimelineEvent.json_content.contains(tag))
#             query = query.filter(or_(*tag_conditions))
        
        # Source filtering - check if any of the specified sources appear in JSON content
#         if sources:
#             source_conditions = []
#             for source in sources:
#                 source_conditions.append(TimelineEvent.json_content.contains(source))
#             query = query.filter(or_(*source_conditions))
        
        # Text search across title and summary
#         if search_text:
#             search_query = f'%{search_text}%'
#             query = query.filter(
#                 or_(
#                     TimelineEvent.title.ilike(search_query),
#                     TimelineEvent.summary.ilike(search_query)
#                 )
#             )
        
        # Order by date descending
#         query = query.order_by(TimelineEvent.date.desc())
        
        # Get total count for pagination
#         total = query.count()
        
        # Apply pagination
#         offset = (page - 1) * per_page
#         events = query.offset(offset).limit(per_page).all()
        
        # Convert to JSON format
#         events_data = []
#         for event in events:
#             event_dict = event.json_content.copy() if event.json_content else {}
#             event_dict.update({
#                 'file_path': event.file_path,
#                 'last_synced': event.last_synced.isoformat() if event.last_synced else None
#             })
#             events_data.append(event_dict)
        
        # Calculate pagination info
#         pages = (total + per_page - 1) // per_page
#         has_prev = page > 1
#         has_next = page < pages
        
#         return jsonify({
#             'events': events_data,
#             'pagination': {
#                 'page': page,
#                 'per_page': per_page,
#                 'total': total,
#                 'pages': pages,
#                 'has_prev': has_prev,
#                 'has_next': has_next,
#                 'prev_page': page - 1 if has_prev else None,
#                 'next_page': page + 1 if has_next else None
#             },
#             'filters_applied': {
#                 'date_from': date_from,
#                 'date_to': date_to,
#                 'importance_min': importance_min,
#                 'importance_max': importance_max,
#                 'actors': actors,
#                 'tags': tags,
#                 'sources': sources,
#                 'search_text': search_text
#             }
#         })
        
#     except Exception as e:
#         logger.error(f"Error filtering timeline events: {e}")
#         return jsonify({'error': 'Failed to filter events'}), 500
#     finally:
#         db.close()

# @app.route('/api/timeline/search', methods=['POST'])
# def search_timeline_events():
#     """Full-text search with advanced options"""
#     db = get_db()
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'error': 'No search data provided'}), 400
            
#         query_text = data.get('query', '').strip()
#         if not query_text:
#             return jsonify({'error': 'No search query provided'}), 400
        
        # Search options
#         search_fields = data.get('fields', ['title', 'summary'])  # title, summary, actors, tags
#         case_sensitive = data.get('case_sensitive', False)
#         exact_match = data.get('exact_match', False)
        
        # Additional filters
#         date_from = data.get('date_from')
#         date_to = data.get('date_to')
#         importance_min = data.get('importance_min')
#         importance_max = data.get('importance_max')
        
        # Pagination
#         page = data.get('page', 1)
#         per_page = min(data.get('per_page', 50), 200)
        
        # Build search query
#         query = db.query(TimelineEvent)
        
        # Apply date filters first
#         if date_from:
#             query = query.filter(TimelineEvent.date >= date_from)
#         if date_to:
#             query = query.filter(TimelineEvent.date <= date_to)
#         if importance_min:
#             query = query.filter(TimelineEvent.importance >= importance_min)
#         if importance_max:
#             query = query.filter(TimelineEvent.importance <= importance_max)
        
        # Build search conditions based on fields
#         search_conditions = []
        
#         if exact_match:
            # Exact match search
#             for field in search_fields:
#                 if field == 'title':
#                     if case_sensitive:
#                         search_conditions.append(TimelineEvent.title.contains(query_text))
#                     else:
#                         search_conditions.append(TimelineEvent.title.ilike(f'%{query_text}%'))
#                 elif field == 'summary':
#                     if case_sensitive:
#                         search_conditions.append(TimelineEvent.summary.contains(query_text))
#                     else:
#                         search_conditions.append(TimelineEvent.summary.ilike(f'%{query_text}%'))
#                 elif field in ['actors', 'tags', 'sources']:
                    # Search in JSON content for these fields
#                     search_conditions.append(TimelineEvent.json_content.contains(query_text))
#         else:
            # Fuzzy/partial match search
#             search_pattern = f'%{query_text}%'
#             for field in search_fields:
#                 if field == 'title':
#                     if case_sensitive:
#                         search_conditions.append(TimelineEvent.title.contains(query_text))
#                     else:
#                         search_conditions.append(TimelineEvent.title.ilike(search_pattern))
#                 elif field == 'summary':
#                     if case_sensitive:
#                         search_conditions.append(TimelineEvent.summary.contains(query_text))
#                     else:
#                         search_conditions.append(TimelineEvent.summary.ilike(search_pattern))
#                 elif field in ['actors', 'tags', 'sources']:
                    # Search in JSON content
#                     if case_sensitive:
#                         search_conditions.append(TimelineEvent.json_content.contains(query_text))
#                     else:
                        # For JSON content, we need to do case-insensitive search differently
#                         search_conditions.append(TimelineEvent.json_content.ilike(search_pattern))
        
        # Apply search conditions (OR logic)
#         if search_conditions:
#             query = query.filter(or_(*search_conditions))
        
        # Order by relevance (for now, just date desc)
#         query = query.order_by(TimelineEvent.date.desc())
        
        # Get total count
#         total = query.count()
        
        # Apply pagination
#         offset = (page - 1) * per_page
#         events = query.offset(offset).limit(per_page).all()
        
        # Convert to JSON format
#         events_data = []
#         for event in events:
#             event_dict = event.json_content.copy() if event.json_content else {}
#             event_dict.update({
#                 'file_path': event.file_path,
#                 'last_synced': event.last_synced.isoformat() if event.last_synced else None
#             })
#             events_data.append(event_dict)
        
        # Calculate pagination info
#         pages = (total + per_page - 1) // per_page
#         has_prev = page > 1
#         has_next = page < pages
        
#         return jsonify({
#             'query': query_text,
#             'events': events_data,
#             'pagination': {
#                 'page': page,
#                 'per_page': per_page,
#                 'total': total,
#                 'pages': pages,
#                 'has_prev': has_prev,
#                 'has_next': has_next,
#                 'prev_page': page - 1 if has_prev else None,
#                 'next_page': page + 1 if has_next else None
#             },
#             'search_options': {
#                 'fields': search_fields,
#                 'case_sensitive': case_sensitive,
#                 'exact_match': exact_match,
#                 'filters': {
#                     'date_from': date_from,
#                     'date_to': date_to,
#                     'importance_min': importance_min,
#                     'importance_max': importance_max
#                 }
#             }
#         })
        
#     except Exception as e:
#         logger.error(f"Error searching timeline events: {e}")
#         return jsonify({'error': 'Failed to search events'}), 500
#     finally:
#         db.close()

# ==================== VIEWER-SPECIFIC DATA ENDPOINTS ====================

@app.route('/api/viewer/timeline-data', methods=['GET'])
def get_viewer_timeline_data():
    """Get timeline data optimized for viewer application"""
    db = get_db()
    try:
        # Get parameters for date range and aggregation
        start_year = int(request.args.get('start_year', 1970))
        end_year = int(request.args.get('end_year', 2025))
        granularity = request.args.get('granularity', 'year')  # year, month, day
        
        # Build date filters
        start_date = f"{start_year}-01-01"
        end_date = f"{end_year}-12-31"
        
        # Get events in date range
        events = db.query(TimelineEvent)\
            .filter(TimelineEvent.date >= start_date)\
            .filter(TimelineEvent.date <= end_date)\
            .order_by(TimelineEvent.date)\
            .all()
        
        # Aggregate events by time period
        timeline_data = {}
        event_details = []
        
        for event in events:
            if not event.json_content:
                continue
                
            # Extract date parts for aggregation
            date_parts = event.date.split('-')
            if len(date_parts) != 3:
                continue
                
            year, month, day = date_parts
            
            # Create aggregation key based on granularity
            if granularity == 'year':
                period_key = year
            elif granularity == 'month':
                period_key = f"{year}-{month}"
            else:  # day
                period_key = event.date
            
            # Initialize period if not exists
            if period_key not in timeline_data:
                timeline_data[period_key] = {
                    'period': period_key,
                    'count': 0,
                    'importance_avg': 0,
                    'importance_sum': 0,
                    'top_actors': {},
                    'top_tags': {},
                    'events': []
                }
            
            # Add event to aggregation
            period_data = timeline_data[period_key]
            period_data['count'] += 1
            importance = event.importance or 0
            period_data['importance_sum'] += importance
            period_data['importance_avg'] = period_data['importance_sum'] / period_data['count']
            
            # Track top actors and tags
            content = event.json_content
            if 'actors' in content and isinstance(content['actors'], list):
                for actor in content['actors'][:3]:  # Top 3 actors per event
                    if isinstance(actor, str) and actor.strip():
                        actor_key = actor.strip()
                        period_data['top_actors'][actor_key] = period_data['top_actors'].get(actor_key, 0) + 1
                        
            if 'tags' in content and isinstance(content['tags'], list):
                for tag in content['tags'][:5]:  # Top 5 tags per event
                    if isinstance(tag, str) and tag.strip():
                        tag_key = tag.strip()
                        period_data['top_tags'][tag_key] = period_data['top_tags'].get(tag_key, 0) + 1
            
            # Add simplified event data
            event_summary = {
                'id': event.id,
                'date': event.date,
                'title': content.get('title', ''),
                'importance': importance,
                'actors': content.get('actors', [])[:2],  # Limit for performance
                'tags': content.get('tags', [])[:3]
            }
            period_data['events'].append(event_summary)
        
        # Convert to sorted list and limit top actors/tags
        timeline_list = []
        for period_key in sorted(timeline_data.keys()):
            period_data = timeline_data[period_key]
            
            # Sort and limit top actors/tags
            period_data['top_actors'] = dict(sorted(period_data['top_actors'].items(), 
                                                   key=lambda x: x[1], reverse=True)[:10])
            period_data['top_tags'] = dict(sorted(period_data['top_tags'].items(), 
                                                 key=lambda x: x[1], reverse=True)[:15])
            
            # Sort events by importance
            period_data['events'] = sorted(period_data['events'], 
                                         key=lambda x: x['importance'], reverse=True)
            
            timeline_list.append(period_data)
        
        return jsonify({
            'timeline': timeline_list,
            'metadata': {
                'start_year': start_year,
                'end_year': end_year,
                'granularity': granularity,
                'total_periods': len(timeline_list),
                'total_events': sum(p['count'] for p in timeline_list)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting viewer timeline data: {e}")
        return jsonify({'error': 'Failed to retrieve timeline data'}), 500
    finally:
        db.close()

@app.route('/api/viewer/actor-network', methods=['GET'])
def get_actor_network():
    """Get actor co-occurrence network data for visualization"""
    db = get_db()
    try:
        # Parameters
        min_connections = int(request.args.get('min_connections', 2))
        max_actors = int(request.args.get('max_actors', 100))
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query with optional date filters
        query = db.query(TimelineEvent)
        if date_from:
            query = query.filter(TimelineEvent.date >= date_from)
        if date_to:
            query = query.filter(TimelineEvent.date <= date_to)
        
        events = query.all()
        
        # Build actor co-occurrence matrix
        actor_connections = {}
        actor_events = {}
        
        for event in events:
            if not event.json_content or 'actors' not in event.json_content:
                continue
                
            actors = event.json_content.get('actors', [])
            if not isinstance(actors, list):
                continue
                
            # Clean actor names
            clean_actors = []
            for actor in actors:
                if isinstance(actor, str) and actor.strip():
                    clean_name = actor.strip()
                    clean_actors.append(clean_name)
                    # Track events per actor
                    if clean_name not in actor_events:
                        actor_events[clean_name] = []
                    actor_events[clean_name].append({
                        'id': event.id,
                        'date': event.date,
                        'title': event.json_content.get('title', ''),
                        'importance': event.importance or 0
                    })
            
            # Create connections between actors in same event
            for i, actor1 in enumerate(clean_actors):
                if actor1 not in actor_connections:
                    actor_connections[actor1] = {}
                    
                for j, actor2 in enumerate(clean_actors):
                    if i != j:  # Don't connect actor to themselves
                        if actor2 not in actor_connections[actor1]:
                            actor_connections[actor1][actor2] = 0
                        actor_connections[actor1][actor2] += 1
        
        # Filter actors by minimum connections and event count
        significant_actors = {}
        for actor, connections in actor_connections.items():
            total_connections = sum(connections.values())
            event_count = len(actor_events.get(actor, []))
            
            if total_connections >= min_connections and event_count >= 1:
                significant_actors[actor] = {
                    'name': actor,
                    'total_connections': total_connections,
                    'event_count': event_count,
                    'connections': connections,
                    'events': actor_events.get(actor, [])
                }
        
        # Sort by connection strength and limit
        sorted_actors = sorted(significant_actors.items(), 
                             key=lambda x: x[1]['total_connections'], 
                             reverse=True)[:max_actors]
        
        # Build network data
        nodes = []
        edges = []
        actor_set = {actor_name for actor_name, _ in sorted_actors}
        
        for actor_name, actor_data in sorted_actors:
            nodes.append({
                'id': actor_name,
                'label': actor_name,
                'size': actor_data['event_count'],
                'connections': actor_data['total_connections'],
                'events': len(actor_data['events'])
            })
            
            # Add edges only between actors in our filtered set
            for connected_actor, weight in actor_data['connections'].items():
                if connected_actor in actor_set and weight >= min_connections:
                    # Avoid duplicate edges
                    if actor_name < connected_actor:  # Lexicographic ordering
                        edges.append({
                            'from': actor_name,
                            'to': connected_actor,
                            'weight': weight
                        })
        
        return jsonify({
            'network': {
                'nodes': nodes,
                'edges': edges
            },
            'metadata': {
                'total_actors': len(nodes),
                'total_connections': len(edges),
                'min_connections': min_connections,
                'date_range': {
                    'from': date_from,
                    'to': date_to
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting actor network: {e}")
        return jsonify({'error': 'Failed to retrieve actor network'}), 500
    finally:
        db.close()

@app.route('/api/viewer/tag-cloud', methods=['GET'])
def get_tag_cloud():
    """Get tag frequency data for word cloud visualization"""
    db = get_db()
    try:
        # Parameters
        max_tags = int(request.args.get('max_tags', 100))
        min_frequency = int(request.args.get('min_frequency', 2))
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        importance_min = request.args.get('importance_min', type=int)
        
        # Build query with optional filters
        query = db.query(TimelineEvent)
        if date_from:
            query = query.filter(TimelineEvent.date >= date_from)
        if date_to:
            query = query.filter(TimelineEvent.date <= date_to)
        if importance_min:
            query = query.filter(TimelineEvent.importance >= importance_min)
        
        events = query.all()
        
        # Collect tag frequencies with metadata
        tag_data = {}
        
        for event in events:
            if not event.json_content or 'tags' not in event.json_content:
                continue
                
            tags = event.json_content.get('tags', [])
            if not isinstance(tags, list):
                continue
                
            event_importance = event.importance or 0
            event_date = event.date
            
            for tag in tags:
                if isinstance(tag, str) and tag.strip():
                    clean_tag = tag.strip()
                    
                    if clean_tag not in tag_data:
                        tag_data[clean_tag] = {
                            'tag': clean_tag,
                            'frequency': 0,
                            'total_importance': 0,
                            'avg_importance': 0,
                            'first_occurrence': event_date,
                            'last_occurrence': event_date,
                            'events': []
                        }
                    
                    tag_info = tag_data[clean_tag]
                    tag_info['frequency'] += 1
                    tag_info['total_importance'] += event_importance
                    tag_info['avg_importance'] = tag_info['total_importance'] / tag_info['frequency']
                    
                    # Update date range
                    if event_date < tag_info['first_occurrence']:
                        tag_info['first_occurrence'] = event_date
                    if event_date > tag_info['last_occurrence']:
                        tag_info['last_occurrence'] = event_date
                    
                    # Add event reference (limit to avoid too much data)
                    if len(tag_info['events']) < 5:
                        tag_info['events'].append({
                            'id': event.id,
                            'date': event_date,
                            'title': event.json_content.get('title', ''),
                            'importance': event_importance
                        })
        
        # Filter by minimum frequency and sort
        filtered_tags = [
            tag_info for tag_info in tag_data.values()
            if tag_info['frequency'] >= min_frequency
        ]
        
        # Sort by frequency * average importance for better ranking
        sorted_tags = sorted(filtered_tags, 
                           key=lambda x: x['frequency'] * (x['avg_importance'] + 1), 
                           reverse=True)[:max_tags]
        
        # Format for cloud visualization
        cloud_data = []
        for tag_info in sorted_tags:
            cloud_data.append({
                'text': tag_info['tag'],
                'size': tag_info['frequency'],
                'weight': tag_info['frequency'] * (tag_info['avg_importance'] + 1),
                'frequency': tag_info['frequency'],
                'avg_importance': round(tag_info['avg_importance'], 2),
                'date_span': {
                    'first': tag_info['first_occurrence'],
                    'last': tag_info['last_occurrence']
                },
                'sample_events': tag_info['events']
            })
        
        return jsonify({
            'tag_cloud': cloud_data,
            'metadata': {
                'total_unique_tags': len(tag_data),
                'displayed_tags': len(cloud_data),
                'min_frequency': min_frequency,
                'filters': {
                    'date_from': date_from,
                    'date_to': date_to,
                    'importance_min': importance_min
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting tag cloud: {e}")
        return jsonify({'error': 'Failed to retrieve tag cloud data'}), 500
    finally:
        db.close()

# ==================== VIEWER STATISTICS ENDPOINTS ====================

@app.route('/api/viewer/stats/overview', methods=['GET'])
@cache.cached(timeout=300, key_prefix='stats_overview')  # Cache for 5 minutes
def get_overview_stats():
    """Get high-level overview statistics for the timeline"""
    db = get_db()
    try:
        # Date range filter
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build base query
        query = db.query(TimelineEvent)
        if date_from:
            query = query.filter(TimelineEvent.date >= date_from)
        if date_to:
            query = query.filter(TimelineEvent.date <= date_to)
        
        events = query.all()
        
        # Basic counts
        total_events = len(events)
        
        # Collect statistics
        importance_scores = []
        years = {}
        actor_count = set()
        tag_count = set()
        source_count = set()
        
        for event in events:
            # Importance distribution
            if event.importance:
                importance_scores.append(event.importance)
            
            # Year distribution
            if event.date and len(event.date.split('-')) >= 1:
                year = event.date.split('-')[0]
                years[year] = years.get(year, 0) + 1
            
            # Unique counts from JSON content
            if event.json_content:
                content = event.json_content
                
                # Actors
                if 'actors' in content and isinstance(content['actors'], list):
                    for actor in content['actors']:
                        if isinstance(actor, str) and actor.strip():
                            actor_count.add(actor.strip())
                
                # Tags
                if 'tags' in content and isinstance(content['tags'], list):
                    for tag in content['tags']:
                        if isinstance(tag, str) and tag.strip():
                            tag_count.add(tag.strip())
                
                # Sources
                if 'sources' in content and isinstance(content['sources'], list):
                    for source in content['sources']:
                        if isinstance(source, dict) and 'outlet' in source:
                            outlet = source.get('outlet', '').strip()
                            if outlet:
                                source_count.add(outlet)
        
        # Calculate statistics
        stats = {
            'total_events': total_events,
            'unique_actors': len(actor_count),
            'unique_tags': len(tag_count),
            'unique_sources': len(source_count),
            'date_range': {
                'from': date_from,
                'to': date_to
            }
        }
        
        # Importance statistics
        if importance_scores:
            stats['importance'] = {
                'min': min(importance_scores),
                'max': max(importance_scores),
                'avg': round(sum(importance_scores) / len(importance_scores), 2),
                'distribution': {}
            }
            
            # Importance distribution by score
            for score in range(1, 11):
                count = sum(1 for s in importance_scores if s == score)
                if count > 0:
                    stats['importance']['distribution'][str(score)] = count
        
        # Year distribution (top 10)
        if years:
            top_years = sorted(years.items(), key=lambda x: x[1], reverse=True)[:10]
            stats['year_distribution'] = dict(top_years)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting overview stats: {e}")
        return jsonify({'error': 'Failed to retrieve overview statistics'}), 500
    finally:
        db.close()

@app.route('/api/viewer/stats/timeline', methods=['GET'])
def get_timeline_stats():
    """Get detailed timeline statistics by time period"""
    db = get_db()
    try:
        # Parameters
        start_year = int(request.args.get('start_year', 2020))
        end_year = int(request.args.get('end_year', 2025))
        granularity = request.args.get('granularity', 'year')  # year, month
        
        # Build date filters
        start_date = f"{start_year}-01-01"
        end_date = f"{end_year}-12-31"
        
        events = db.query(TimelineEvent)\
            .filter(TimelineEvent.date >= start_date)\
            .filter(TimelineEvent.date <= end_date)\
            .order_by(TimelineEvent.date)\
            .all()
        
        # Aggregate by time period
        periods = {}
        
        for event in events:
            if not event.date or not event.json_content:
                continue
            
            date_parts = event.date.split('-')
            if len(date_parts) < 2:
                continue
                
            year, month = date_parts[0], date_parts[1]
            
            # Create period key
            if granularity == 'year':
                period_key = year
            else:  # month
                period_key = f"{year}-{month}"
            
            # Initialize period
            if period_key not in periods:
                periods[period_key] = {
                    'period': period_key,
                    'events': 0,
                    'importance_sum': 0,
                    'importance_avg': 0,
                    'high_importance_events': 0,  # importance >= 8
                    'top_actors': {},
                    'top_tags': {}
                }
            
            period_data = periods[period_key]
            period_data['events'] += 1
            
            importance = event.importance or 0
            period_data['importance_sum'] += importance
            period_data['importance_avg'] = period_data['importance_sum'] / period_data['events']
            
            if importance >= 8:
                period_data['high_importance_events'] += 1
            
            # Track actors and tags
            content = event.json_content
            
            if 'actors' in content and isinstance(content['actors'], list):
                for actor in content['actors'][:3]:
                    if isinstance(actor, str) and actor.strip():
                        actor_key = actor.strip()
                        period_data['top_actors'][actor_key] = period_data['top_actors'].get(actor_key, 0) + 1
            
            if 'tags' in content and isinstance(content['tags'], list):
                for tag in content['tags'][:5]:
                    if isinstance(tag, str) and tag.strip():
                        tag_key = tag.strip()
                        period_data['top_tags'][tag_key] = period_data['top_tags'].get(tag_key, 0) + 1
        
        # Process and sort periods
        timeline_stats = []
        for period_key in sorted(periods.keys()):
            period_data = periods[period_key]
            
            # Limit and sort top items
            period_data['top_actors'] = dict(sorted(period_data['top_actors'].items(),
                                                  key=lambda x: x[1], reverse=True)[:5])
            period_data['top_tags'] = dict(sorted(period_data['top_tags'].items(),
                                                key=lambda x: x[1], reverse=True)[:5])
            
            # Round averages
            period_data['importance_avg'] = round(period_data['importance_avg'], 2)
            
            timeline_stats.append(period_data)
        
        return jsonify({
            'timeline_stats': timeline_stats,
            'metadata': {
                'start_year': start_year,
                'end_year': end_year,
                'granularity': granularity,
                'total_periods': len(timeline_stats),
                'total_events': sum(p['events'] for p in timeline_stats)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting timeline stats: {e}")
        return jsonify({'error': 'Failed to retrieve timeline statistics'}), 500
    finally:
        db.close()

@app.route('/api/viewer/stats/actors', methods=['GET'])
@cache.cached(timeout=300, key_prefix='stats_actors')  # Cache for 5 minutes
def get_actor_stats():
    """Get statistics about actors in the timeline"""
    db = get_db()
    try:
        # Parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        top_n = int(request.args.get('top_n', 20))
        min_events = int(request.args.get('min_events', 2))
        
        # Build query
        query = db.query(TimelineEvent)
        if date_from:
            query = query.filter(TimelineEvent.date >= date_from)
        if date_to:
            query = query.filter(TimelineEvent.date <= date_to)
        
        events = query.all()
        
        # Collect actor statistics
        actor_stats = {}
        
        for event in events:
            if not event.json_content or 'actors' not in event.json_content:
                continue
                
            actors = event.json_content.get('actors', [])
            if not isinstance(actors, list):
                continue
            
            event_importance = event.importance or 0
            event_date = event.date
            
            for actor in actors:
                if isinstance(actor, str) and actor.strip():
                    actor_name = actor.strip()
                    
                    if actor_name not in actor_stats:
                        actor_stats[actor_name] = {
                            'name': actor_name,
                            'event_count': 0,
                            'total_importance': 0,
                            'avg_importance': 0,
                            'max_importance': 0,
                            'first_appearance': event_date,
                            'last_appearance': event_date,
                            'years_active': set()
                        }
                    
                    stats = actor_stats[actor_name]
                    stats['event_count'] += 1
                    stats['total_importance'] += event_importance
                    stats['avg_importance'] = stats['total_importance'] / stats['event_count']
                    stats['max_importance'] = max(stats['max_importance'], event_importance)
                    
                    # Update date range
                    if event_date < stats['first_appearance']:
                        stats['first_appearance'] = event_date
                    if event_date > stats['last_appearance']:
                        stats['last_appearance'] = event_date
                    
                    # Track active years
                    if event_date and len(event_date.split('-')) >= 1:
                        year = event_date.split('-')[0]
                        stats['years_active'].add(year)
        
        # Filter and process results
        filtered_actors = [
            stats for stats in actor_stats.values()
            if stats['event_count'] >= min_events
        ]
        
        # Convert years_active to count and sort
        for actor in filtered_actors:
            actor['years_active'] = len(actor['years_active'])
            actor['avg_importance'] = round(actor['avg_importance'], 2)
        
        # Sort by event count and limit
        top_actors = sorted(filtered_actors, key=lambda x: x['event_count'], reverse=True)[:top_n]
        
        return jsonify({
            'actor_stats': top_actors,
            'metadata': {
                'total_actors': len(actor_stats),
                'filtered_actors': len(filtered_actors),
                'displayed_actors': len(top_actors),
                'min_events': min_events,
                'filters': {
                    'date_from': date_from,
                    'date_to': date_to
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting actor stats: {e}")
        return jsonify({'error': 'Failed to retrieve actor statistics'}), 500
    finally:
        db.close()

@app.route('/api/viewer/stats/importance', methods=['GET'])
@cache.cached(timeout=300, key_prefix='stats_importance')  # Cache for 5 minutes
def get_importance_stats():
    """Get statistics about event importance distribution"""
    db = get_db()
    try:
        # Parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = db.query(TimelineEvent)
        if date_from:
            query = query.filter(TimelineEvent.date >= date_from)
        if date_to:
            query = query.filter(TimelineEvent.date <= date_to)
        
        events = query.all()
        
        # Collect importance statistics
        importance_data = {
            'distribution': {},
            'by_year': {},
            'high_importance_events': [],
            'low_importance_events': []
        }
        
        importance_scores = []
        
        for event in events:
            importance = event.importance or 0
            importance_scores.append(importance)
            
            # Distribution by score
            score_str = str(importance)
            importance_data['distribution'][score_str] = importance_data['distribution'].get(score_str, 0) + 1
            
            # Distribution by year
            if event.date and len(event.date.split('-')) >= 1:
                year = event.date.split('-')[0]
                if year not in importance_data['by_year']:
                    importance_data['by_year'][year] = {
                        'total_events': 0,
                        'importance_sum': 0,
                        'avg_importance': 0,
                        'high_importance': 0
                    }
                
                year_data = importance_data['by_year'][year]
                year_data['total_events'] += 1
                year_data['importance_sum'] += importance
                year_data['avg_importance'] = year_data['importance_sum'] / year_data['total_events']
                
                if importance >= 8:
                    year_data['high_importance'] += 1
            
            # Collect examples
            event_summary = {
                'id': event.id,
                'date': event.date,
                'title': event.json_content.get('title', '') if event.json_content else '',
                'importance': importance
            }
            
            if importance >= 9 and len(importance_data['high_importance_events']) < 10:
                importance_data['high_importance_events'].append(event_summary)
            elif importance <= 3 and len(importance_data['low_importance_events']) < 5:
                importance_data['low_importance_events'].append(event_summary)
        
        # Calculate overall statistics
        if importance_scores:
            importance_data['summary'] = {
                'total_events': len(importance_scores),
                'min': min(importance_scores),
                'max': max(importance_scores),
                'avg': round(sum(importance_scores) / len(importance_scores), 2),
                'median': sorted(importance_scores)[len(importance_scores) // 2],
                'high_importance_count': sum(1 for s in importance_scores if s >= 8),
                'critical_count': sum(1 for s in importance_scores if s >= 9)
            }
        
        # Round yearly averages
        for year_data in importance_data['by_year'].values():
            year_data['avg_importance'] = round(year_data['avg_importance'], 2)
        
        return jsonify(importance_data)
        
    except Exception as e:
        logger.error(f"Error getting importance stats: {e}")
        return jsonify({'error': 'Failed to retrieve importance statistics'}), 500
    finally:
        db.close()

# ==================== CACHE MANAGEMENT ====================

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached responses (admin endpoint)"""
    try:
        cache.clear()
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return jsonify({'error': 'Failed to clear cache'}), 500

@app.route('/api/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics"""
    try:
        # Simple cache stats - Flask-Caching doesn't provide detailed stats for simple cache
        return jsonify({
            'cache_type': app.config.get('CACHE_TYPE', 'simple'),
            'default_timeout': app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
            'threshold': app.config.get('CACHE_THRESHOLD', 1000),
            'status': 'active'
        })
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return jsonify({'error': 'Failed to get cache stats'}), 500

# ==================== ACTIVITY MONITORING ====================

@app.route('/api/activity/recent', methods=['GET'])
def get_recent_activity():
    """Get recent research activity for monitoring dashboard"""
    db = get_db()
    try:
        since_param = request.args.get('since')
        limit = int(request.args.get('limit', 20))
        
        # Build query for recent activity
        query = db.query(ActivityLog)
        
        if since_param:
            try:
                # Parse ISO format timestamp
                since_dt = datetime.fromisoformat(since_param.replace('Z', '+00:00'))
                query = query.filter(ActivityLog.timestamp >= since_dt)
            except ValueError:
                return jsonify({'error': 'Invalid timestamp format. Use ISO format.'}), 400
        
        # Get recent activities ordered by timestamp
        activities = query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
        
        # Format activities for response
        activity_list = []
        for activity in activities:
            activity_data = {
                'type': activity.action,
                'timestamp': activity.timestamp.isoformat() + 'Z',
                'data': {}
            }
            
            # Add relevant data based on activity type
            if activity.action == 'priority_status_updated':
                activity_data['data'] = {
                    'priority_id': activity.priority_id,
                    'new_status': activity.details.get('new_status') if activity.details else None,
                    'old_status': activity.details.get('old_status') if activity.details else None
                }
            elif activity.action == 'event_staged':
                activity_data['data'] = {
                    'event_id': activity.event_id,
                    'priority_id': activity.priority_id
                }
            elif activity.action == 'filesystem_sync':
                activity_data['data'] = activity.details or {}
            
            activity_list.append(activity_data)
        
        # Get current summary
        summary = get_current_summary(db)

        return jsonify({
            'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
            'activities': activity_list,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return jsonify({'error': 'Failed to get activity'}), 500
    finally:
        db.close()

@app.route('/api/research/session', methods=['GET'])
def get_session_status():
    """Get current research session metrics"""
    db = get_db()
    try:
        # Get current session
        session = db.query(ResearchSession).filter_by(session_id=current_session_id).first()
        
        if not session:
            # Create default session if none exists
            session = ResearchSession(
                session_id=current_session_id,
                commit_threshold=COMMIT_THRESHOLD,
                events_created=0,
                priorities_completed=0
            )
            db.add(session)
            db.commit()
        
        # Get active priorities count
        active_priorities = db.query(ResearchPriority).filter_by(status='in_progress').count()
        
        # Calculate quality trend (simplified)
        recent_events = db.query(EventMetadata).order_by(EventMetadata.created_at.desc()).limit(10).all()
        quality_trend = 'stable'  # Default
        
        if len(recent_events) > 5:
            # Simple quality trend based on validation status
            recent_validated = sum(1 for e in recent_events[:5] if e.validation_status == 'validated')
            older_validated = sum(1 for e in recent_events[5:] if e.validation_status == 'validated')
            
            if recent_validated > older_validated:
                quality_trend = 'improving'
            elif recent_validated < older_validated:
                quality_trend = 'declining'
        
        return jsonify({
            'session_active': True,
            'session_id': current_session_id,
            'session_start': session.created_at.isoformat() + 'Z' if session.created_at else None,
            'events_this_session': session.events_created or 0,
            'priorities_completed': session.priorities_completed or 0,
            'commit_threshold': session.commit_threshold,
            'events_since_commit': events_since_commit,
            'quality_trend': quality_trend,
            'active_priorities': active_priorities
        })
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': 'Failed to get session status'}), 500
    finally:
        db.close()

def get_current_summary(db):
    """Get current research status summary with QA queue stats"""
    try:
        # Total events count (from database mirror)
        total_events = db.query(TimelineEvent).count()
        
        # Active priorities
        active_priorities = db.query(ResearchPriority).filter_by(status='in_progress').count()
        
        # Events needing validation
        events_needing_validation = db.query(EventMetadata).filter(
            or_(
                EventMetadata.validation_status == 'pending',
                EventMetadata.validation_status == 'failed'
            )
        ).count()
        
        # QA Queue statistics
        try:
            qa_manager = QAQueueManager(db)
            qa_stats = qa_manager.get_qa_stats()
            
            # High priority QA candidates
            high_priority_qa = qa_stats.get('high_priority_needs_qa', 0)
            
            # Source quality breakdown
            source_stats = qa_stats.get('source_quality', {})
            events_missing_sources = source_stats.get('no_sources', 0) + source_stats.get('one_source', 0)
            
            # Total QA backlog
            qa_backlog = qa_stats.get('estimated_qa_backlog', 0)
            
        except Exception as qa_error:
            logger.warning(f"Error getting QA stats: {qa_error}")
            high_priority_qa = 0
            events_missing_sources = 0
            qa_backlog = 0
        
        return {
            'total_events': total_events,
            'active_priorities': active_priorities,
            'staged_events_count': events_since_commit,
            'commit_progress': f"{events_since_commit}/{COMMIT_THRESHOLD}",
            'events_needing_validation': events_needing_validation,
            'qa_queue': {
                'high_priority_events': high_priority_qa,
                'missing_sources': events_missing_sources,
                'total_backlog': qa_backlog
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return {
            'total_events': 0,
            'active_priorities': 0,
            'staged_events_count': 0,
            'commit_progress': '0/10',
            'events_needing_validation': 0,
            'qa_queue': {
                'high_priority_events': 0,
                'missing_sources': 0,
                'total_backlog': 0
            }
        }

# ==================== QA QUEUE SYSTEM ====================

# Import QA system
from qa_queue_system import QAQueueManager

# MOVED TO routes/qa.py blueprint - 14 QA routes
# Lines 3446-4003 have been extracted to routes/qa.py
#
# Routes extracted:
# - GET  /api/qa/queue - QA queue with pagination and filtering
# - GET  /api/qa/next - Next highest priority event for QA
# - GET  /api/qa/stats - Comprehensive QA statistics
# - POST /api/qa/validate/<event_id> - Mark event as validated
# - POST /api/qa/enhance/<event_id> - Enhance event with improved content
# - GET  /api/qa/issues/<issue_type> - Events with specific issues
# - POST /api/qa/reject/<event_id> - Mark event as rejected
# - POST /api/qa/start/<event_id> - Mark event as in_progress
# - POST /api/qa/score - Calculate QA priority score
# - POST /api/qa/validation/initialize - Initialize validation audit trail
# - POST /api/qa/validation/reset - Reset validation audit trail
# - GET  /api/qa/rejected - Get rejected events for audit
# - POST /api/qa/batch/reserve - Reserve batch of events for QA
# - POST /api/qa/batch/release - Release expired QA reservations
#
# @app.route('/api/qa/queue')
# @cache_with_invalidation(timeout=120, key_prefix='qa_queue')
# def get_qa_queue():
#    """Get prioritized queue of events needing QA"""
#    db = get_db()
#    try:
#        # Parse query parameters
#        limit = min(int(request.args.get('limit', 50)), 100)
#        batch_size = int(request.args.get('batch_size', limit))  # Support batch_size parameter
#        offset = int(request.args.get('offset', 0))
#        min_importance = int(request.args.get('min_importance', 1))
#        include_validated = request.args.get('include_validated', 'false').lower() == 'true'
#        
#        # Use batch_size if provided, otherwise use limit
#        actual_limit = min(batch_size, limit)
#        
#        # Get QA queue
#        qa_manager = QAQueueManager(db)
#        qa_queue = qa_manager.get_qa_queue(
#            limit=actual_limit,
#            offset=offset,
#            min_importance=min_importance,
#            include_validated=include_validated
#        )
#        
#        return jsonify({
#            'qa_queue': qa_queue,
#            'count': len(qa_queue),
#            'limit': limit,
#            'offset': offset,
#            'filters': {
#                'min_importance': min_importance,
#                'include_validated': include_validated
#            }
#        })
#        
#    except Exception as e:
#        logger.error(f"Error getting QA queue: {e}")
#        return jsonify({'error': 'Failed to get QA queue'}), 500
#    finally:
#        db.close()
#
#@app.route('/api/qa/next')
#@cache_with_invalidation(timeout=60, key_prefix='qa_next')
#def get_next_qa_event():
#    """Get the next highest priority event for QA"""
#    db = get_db()
#    try:
#        min_importance = int(request.args.get('min_importance', 7))
#        
#        qa_manager = QAQueueManager(db)
#        next_event = qa_manager.get_next_qa_event(min_importance=min_importance)
#        
#        if next_event:
#            return jsonify(next_event)
#        else:
#            return jsonify({'message': 'No events available for QA'}), 404
#            
#    except Exception as e:
#        logger.error(f"Error getting next QA event: {e}")
#        return jsonify({'error': 'Failed to get next QA event'}), 500
#    finally:
#        db.close()
#
#@app.route('/api/qa/stats')
#@cache_with_invalidation(timeout=300, key_prefix='qa_stats')
#def get_qa_stats():
#    """Get comprehensive QA statistics"""
#    db = get_db()
#    try:
#        qa_manager = QAQueueManager(db)
#        stats = qa_manager.get_qa_stats()
#        
#        return jsonify(stats)
#        
#    except Exception as e:
#        logger.error(f"Error getting QA stats: {e}")
#        return jsonify({'error': 'Failed to get QA stats'}), 500
#    finally:
#        db.close()
#
#@app.route('/api/qa/validate/<event_id>', methods=['POST'])
#@require_api_key
#def mark_event_validated(event_id):
#    """Mark an event as validated with quality score"""
#    db = get_db()
#    try:
#        data = request.json or {}
#        quality_score = data.get('quality_score')
#        validation_notes = data.get('validation_notes', '')
#        created_by = data.get('created_by', 'qa-agent')
#        
#        if quality_score is None:
#            return jsonify({'error': 'quality_score is required'}), 400
#        
#        if not (0 <= quality_score <= 10):
#            return jsonify({'error': 'quality_score must be between 0 and 10'}), 400
#        
#        qa_manager = QAQueueManager(db)
#        success = qa_manager.mark_event_validated(
#            event_id=event_id,
#            quality_score=quality_score,
#            validation_notes=validation_notes,
#            created_by=created_by
#        )
#        
#        if success:
#            # Log the validation activity
#            activity = ActivityLog(
#                action='event_validated',
#                event_id=event_id,
#                agent=created_by,
#                details={
#                    'quality_score': quality_score,
#                    'validation_notes': validation_notes
#                }
#            )
#            db.add(activity)
#            db.commit()
#            
#            # Invalidate cache
#            cache.clear()
#            
#            return jsonify({
#                'status': 'success',
#                'event_id': event_id,
#                'quality_score': quality_score,
#                'validation_notes': validation_notes
#            })
#        else:
#            return jsonify({'error': 'Failed to mark event as validated'}), 500
#            
#    except Exception as e:
#        logger.error(f"Error validating event {event_id}: {e}")
#        return jsonify({'error': 'Failed to validate event'}), 500
#    finally:
#        db.close()
#
#@app.route('/api/qa/enhance/<event_id>', methods=['POST'])
#@require_api_key
#def enhance_event_with_qa(event_id):
#    """Enhance an event with improved content and record QA metadata"""
#    db = get_db()
#    try:
#        data = request.json or {}
#        enhanced_event = data.get('enhanced_event')
#        quality_score = data.get('quality_score')
#        validation_notes = data.get('validation_notes', '')
#        created_by = data.get('created_by', 'qa-agent')
#        
#        if not enhanced_event:
#            return jsonify({
#                'error': 'enhanced_event is required',
#                'help': 'POST body must include: {"enhanced_event": {...}, "quality_score": 8.5, "validation_notes": "..."}'
#            }), 400
#
#        if quality_score is None:
#            return jsonify({
#                'error': 'quality_score is required',
#                'help': 'Include quality_score (0-10) in POST body, e.g., "quality_score": 8.5'
#            }), 400
#
#        if not (0 <= quality_score <= 10):
#            return jsonify({
#                'error': 'quality_score must be between 0 and 10',
#                'received': quality_score,
#                'help': 'Use quality_score between 0-10, e.g., 8.5 for high-quality sources'
#            }), 400
#        
#        # Validate enhanced event structure
#        validation_result = validate_timeline_event(enhanced_event)
#        
#        if not validation_result['valid']:
#            return jsonify({
#                'error': 'Enhanced event validation failed',
#                'validation_errors': validation_result['errors']
#            }), 400
#        
#        # Ensure event ID matches
#        if enhanced_event.get('id') != event_id:
#            return jsonify({
#                'error': 'Event ID mismatch',
#                'url_event_id': event_id,
#                'enhanced_event_id': enhanced_event.get('id'),
#                'help': 'The enhanced_event.id must match the event_id in the URL'
#            }), 400
#
#        # Check if original event exists
#        original_event = db.query(TimelineEvent).filter_by(id=event_id).first()
#        if not original_event:
#            return jsonify({
#                'error': 'Original event not found',
#                'event_id': event_id,
#                'help': 'Event must exist in the database before enhancement. Check event ID format: YYYY-MM-DD--slug'
#            }), 404
#        
#        # Save enhanced event to filesystem
#        event_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
#                                     'timeline_data', 'events', f'{event_id}.json')
#        
#        try:
#            with open(event_file_path, 'w', encoding='utf-8') as f:
#                json.dump(enhanced_event, f, indent=2, ensure_ascii=False)
#        except Exception as e:
#            logger.error(f"Failed to save enhanced event to filesystem: {e}")
#            return jsonify({'error': 'Failed to save enhanced event'}), 500
#        
#        # Record QA metadata
#        qa_manager = QAQueueManager(db)
#        success = qa_manager.mark_event_validated(
#            event_id=event_id,
#            quality_score=quality_score,
#            validation_notes=validation_notes,
#            created_by=created_by
#        )
#        
#        if success:
#            # Log the enhancement activity
#            activity = ActivityLog(
#                action='event_enhanced',
#                event_id=event_id,
#                agent=created_by,
#                details={
#                    'quality_score': quality_score,
#                    'validation_notes': validation_notes,
#                    'enhancements': 'Event content and sources enhanced'
#                }
#            )
#            db.add(activity)
#            
#            # Update commit counter since we modified a file
#            global events_since_commit
#            events_since_commit += 1
#            
#            db.commit()
#            
#            # Invalidate cache
#            cache.clear()
#            
#            return jsonify({
#                'status': 'success',
#                'event_id': event_id,
#                'quality_score': quality_score,
#                'validation_notes': validation_notes,
#                'enhanced': True,
#                'file_updated': True
#            })
#        else:
#            return jsonify({'error': 'Failed to record QA metadata'}), 500
#            
#    except Exception as e:
#        logger.error(f"Error enhancing event {event_id}: {e}")
#        return jsonify({'error': 'Failed to enhance event'}), 500
#    finally:
#        db.close()
#
#@app.route('/api/qa/issues/<issue_type>')
#@cache_with_invalidation(timeout=180, key_prefix='qa_issues')
#def get_qa_candidates_by_issue(issue_type):
#    """Get events with specific QA issues"""
#    db = get_db()
#    try:
#        limit = min(int(request.args.get('limit', 20)), 50)
#        
#        qa_manager = QAQueueManager(db)
#        candidates = qa_manager.get_qa_candidates_by_issue(issue_type, limit)
#        
#        return jsonify({
#            'issue_type': issue_type,
#            'candidates': candidates,
#            'count': len(candidates),
#            'limit': limit
#        })
#        
#    except Exception as e:
#        logger.error(f"Error getting QA candidates for issue {issue_type}: {e}")
#        return jsonify({'error': 'Failed to get QA candidates'}), 500
#    finally:
#        db.close()
#
#@app.route('/api/qa/reject/<event_id>', methods=['POST'])
#@require_api_key
#def mark_event_rejected(event_id):
#    """Mark an event as rejected with detailed reasoning"""
#    db = get_db()
#    try:
#        data = request.json or {}
#        rejection_reason = data.get('rejection_reason', '')
#        created_by = data.get('created_by', 'qa-agent')
#        
#        if not rejection_reason.strip():
#            return jsonify({'error': 'rejection_reason is required and cannot be empty'}), 400
#        
#        qa_manager = QAQueueManager(db)
#        success = qa_manager.mark_event_rejected(
#            event_id=event_id,
#            rejection_reason=rejection_reason,
#            created_by=created_by
#        )
#        
#        if success:
#            # Log the rejection activity
#            activity = ActivityLog(
#                action='event_rejected',
#                event_id=event_id,
#                agent=created_by,
#                details={
#                    'rejection_reason': rejection_reason
#                }
#            )
#            db.add(activity)
#            db.commit()
#            
#            # Invalidate cache
#            cache.clear()
#            
#            return jsonify({
#                'status': 'success',
#                'event_id': event_id,
#                'rejection_reason': rejection_reason
#            }), 200
#        else:
#            return jsonify({'error': 'Failed to reject event'}), 500
#            
#    except Exception as e:
#        logger.error(f"Error rejecting event {event_id}: {e}")
#        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
#    finally:
#        db.close()
#
#@app.route('/api/qa/start/<event_id>', methods=['POST'])
#@require_api_key  
#def mark_event_in_progress(event_id):
#    """Mark an event as in_progress to prevent duplicate processing"""
#    db = get_db()
#    try:
#        data = request.json or {}
#        created_by = data.get('created_by', 'qa-agent')
#        agent_id = data.get('agent_id', created_by)
#        
#        qa_manager = QAQueueManager(db)
#        success = qa_manager.mark_event_in_progress(event_id, created_by, agent_id)
#        
#        if success:
#            # Log the activity
#            activity = ActivityLog(
#                action='event_started',
#                event_id=event_id,
#                agent=created_by,
#                details={
#                    'agent_id': agent_id,
#                    'status': 'in_progress'
#                }
#            )
#            db.add(activity)
#            db.commit()
#            
#            # Invalidate cache
#            cache.clear()
#            
#            return jsonify({
#                'status': 'success',
#                'event_id': event_id,
#                'assigned_to': agent_id,
#                'validation_status': 'in_progress'
#            }), 200
#        else:
#            return jsonify({'error': 'Failed to mark event as in_progress or already being processed'}), 400
#            
#    except Exception as e:
#        logger.error(f"Error marking event {event_id} as in_progress: {e}")
#        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
#    finally:
#        db.close()
#
#@app.route('/api/qa/score', methods=['POST'])
#def calculate_qa_score():
#    """Calculate QA priority score for event data"""
#    try:
#        data = request.json
#        if not data:
#            return jsonify({'error': 'Event data required'}), 400
#        
#        event_data = data.get('event', {})
#        metadata = data.get('metadata')
#        
#        # Create temporary QA manager (no DB needed for scoring)
#        qa_manager = QAQueueManager(None)
#        score, breakdown = qa_manager.calculate_qa_priority_score(event_data, metadata)
#        
#        return jsonify({
#            'qa_priority_score': score,
#            'score_breakdown': breakdown,
#            'event_id': event_data.get('id', 'unknown')
#        })
#        
#    except Exception as e:
#        logger.error(f"Error calculating QA score: {e}")
#        return jsonify({'error': 'Failed to calculate QA score'}), 500
#
## ==================== VALIDATION AUDIT TRAIL ENDPOINTS ====================
#
#@app.route('/api/qa/validation/initialize', methods=['POST'])
#@require_api_key
#def initialize_validation_audit_trail():
#    """Initialize metadata records for all events to create complete validation audit trail"""
#    
#    db = get_db()
#    try:
#        data = request.json or {}
#        created_by = data.get('created_by', 'api-init')
#        dry_run = data.get('dry_run', False)
#        
#        qa_manager = QAQueueManager(db)
#        result = qa_manager.initialize_validation_audit_trail(created_by, dry_run)
#        
#        # Invalidate QA-related caches if not dry run
#        if not dry_run:
#            cache.clear()
#        
#        return jsonify(result)
#        
#    except Exception as e:
#        logger.error(f"Error initializing validation audit trail: {e}")
#        return jsonify({'error': 'Failed to initialize validation audit trail'}), 500
#    finally:
#        if db:
#            db.close()
#
#@app.route('/api/qa/validation/reset', methods=['POST'])
#@require_api_key
#def reset_validation_audit_trail():
#    """Reset all validation records to pending status for complete re-validation"""
#    
#    db = get_db()
#    try:
#        data = request.json or {}
#        created_by = data.get('created_by', 'api-reset')
#        dry_run = data.get('dry_run', False)
#        
#        qa_manager = QAQueueManager(db)
#        result = qa_manager.reset_validation_audit_trail(created_by, dry_run)
#        
#        # Invalidate QA-related caches if not dry run
#        if not dry_run:
#            cache.clear()
#        
#        return jsonify(result)
#        
#    except Exception as e:
#        logger.error(f"Error resetting validation audit trail: {e}")
#        return jsonify({'error': 'Failed to reset validation audit trail'}), 500
#    finally:
#        if db:
#            db.close()
#
#@app.route('/api/qa/rejected')
#def get_rejected_events():
#    """Get rejected events for audit purposes"""
#    
#    db = None
#    try:
#        db = get_db()
#        qa_manager = QAQueueManager(db)
#        
#        # Get parameters
#        limit = min(int(request.args.get('limit', 50)), 200)
#        offset = int(request.args.get('offset', 0))
#        
#        # Get rejected events
#        rejected_events = qa_manager.get_rejected_events(limit=limit, offset=offset)
#        
#        return jsonify({
#            'rejected_events': rejected_events,
#            'count': len(rejected_events),
#            'limit': limit,
#            'offset': offset,
#            'filters': {
#                'validation_status': 'rejected'
#            }
#        })
#        
#    except Exception as e:
#        logger.error(f"Error getting rejected events: {e}")
#        return jsonify({'error': 'Failed to get rejected events'}), 500
#    finally:
#        if db:
#            db.close()
#
#@app.route('/api/qa/batch/reserve', methods=['POST'])
#@require_api_key
#def reserve_qa_batch():
#    """Reserve a batch of events for QA processing to prevent duplicate work"""
#    db = get_db()
#    try:
#        qa_manager = QAQueueManager(db)
#        
#        # Get request parameters
#        data = request.get_json() or {}
#        batch_size = min(int(data.get('batch_size', 5)), 20)  # Max 20 events per batch
#        agent_id = data.get('agent_id')
#        min_importance = int(data.get('min_importance', 1))
#        
#        if not agent_id:
#            agent_id = f"qa-agent-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:17]}"
#        
#        # Release any expired reservations first
#        expired_count = qa_manager.release_expired_qa_reservations()
#        if expired_count > 0:
#            logger.info(f"Released {expired_count} expired QA reservations before batch reservation")
#        
#        # Reserve batch of events
#        reserved_events = qa_manager.reserve_qa_batch(
#            batch_size=batch_size,
#            agent_id=agent_id,
#            min_importance=min_importance
#        )
#        
#        if not reserved_events:
#            return jsonify({
#                'message': 'No events available for QA batch reservation',
#                'error': 'queue_empty'
#            }), 404
#        
#        return jsonify({
#            'reserved_events': reserved_events,
#            'count': len(reserved_events),
#            'agent_id': agent_id,
#            'batch_size': batch_size,
#            'reservation_expires': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
#            'status': 'reserved'
#        })
#        
#    except Exception as e:
#        logger.error(f"Error reserving QA batch: {e}")
#        return jsonify({'error': 'Failed to reserve QA batch', 'message': str(e)}), 500
#    finally:
#        db.close()
#
#@app.route('/api/qa/batch/release', methods=['POST'])
#@require_api_key
#def release_expired_qa_reservations():
#    """Manually release expired QA reservations"""
#    db = get_db()
#    try:
#        qa_manager = QAQueueManager(db)
#        released_count = qa_manager.release_expired_qa_reservations()
#        
#        return jsonify({
#            'released_count': released_count,
#            'message': f'Released {released_count} expired QA reservations'
#        })
#        
#    except Exception as e:
#        logger.error(f"Error releasing expired QA reservations: {e}")
#        return jsonify({'error': 'Failed to release reservations', 'message': str(e)}), 500
#    finally:
#        db.close()


# ==================== VALIDATION RUNS SYSTEM ====================

@app.route('/api/validation-runs', methods=['GET'])
def list_validation_runs():
    """List all validation runs with optional filtering"""
    db = get_db()
    try:
        # Get query parameters
        status = request.args.get('status')  # active, completed, paused, cancelled
        run_type = request.args.get('type')  # random_sample, importance_focused, etc.
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = db.query(ValidationRun)
        
        if status:
            query = query.filter(ValidationRun.status == status)
        if run_type:
            query = query.filter(ValidationRun.run_type == run_type)
        
        # Order by creation date, newest first
        query = query.order_by(ValidationRun.created_date.desc())
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        validation_runs = query.offset(offset).limit(limit).all()
        
        # Convert to dict format
        runs_data = []
        for run in validation_runs:
            run_data = {
                'id': run.id,
                'run_name': run.run_name,
                'run_type': run.run_type,
                'status': run.status,
                'target_count': run.target_count,
                'actual_count': run.actual_count,
                'events_validated': run.events_validated,
                'events_remaining': run.events_remaining,
                'progress_percentage': run.progress_percentage,
                'created_date': run.created_date.isoformat() if run.created_date else None,
                'started_date': run.started_date.isoformat() if run.started_date else None,
                'completed_date': run.completed_date.isoformat() if run.completed_date else None,
                'created_by': run.created_by,
                'selection_criteria': run.selection_criteria
            }
            runs_data.append(run_data)
        
        return jsonify({
            'validation_runs': runs_data,
            'pagination': {
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing validation runs: {e}")
        return jsonify({'error': 'Failed to list validation runs'}), 500
    finally:
        db.close()

@app.route('/api/validation-runs', methods=['POST'])
@require_api_key
def create_validation_run():
    """Create a new validation run using different sampling strategies"""
    db = get_db()
    try:
        data = request.json or {}
        
        run_type = data.get('run_type', 'random_sample')
        created_by = data.get('created_by', 'api')
        
        calculator = ValidationRunCalculator(db)
        
        if run_type == 'random_sample':
            target_count = data.get('target_count', 50)
            min_importance = data.get('min_importance', 5)
            exclude_recent = data.get('exclude_recent_validations', True)
            
            validation_run = calculator.create_random_sample_run(
                target_count=target_count,
                min_importance=min_importance,
                exclude_recent_validations=exclude_recent
            )
            
        elif run_type == 'importance_focused':
            target_count = data.get('target_count', 30)
            min_importance = data.get('min_importance', 7)
            focus_unvalidated = data.get('focus_unvalidated', True)
            
            validation_run = calculator.create_importance_focused_run(
                target_count=target_count,
                min_importance=min_importance,
                focus_unvalidated=focus_unvalidated
            )
            
        elif run_type == 'date_range':
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            if not start_date or not end_date:
                return jsonify({'error': 'start_date and end_date required for date_range runs'}), 400
            
            target_count = data.get('target_count')  # None = all matching
            min_importance = data.get('min_importance', 5)
            
            validation_run = calculator.create_date_range_run(
                start_date=start_date,
                end_date=end_date,
                target_count=target_count,
                min_importance=min_importance
            )
            
        elif run_type == 'pattern_detection':
            pattern_keywords = data.get('pattern_keywords', [])
            if not pattern_keywords:
                return jsonify({'error': 'pattern_keywords required for pattern_detection runs'}), 400
            
            target_count = data.get('target_count', 40)
            pattern_description = data.get('pattern_description', '')
            
            validation_run = calculator.create_pattern_detection_run(
                pattern_keywords=pattern_keywords,
                target_count=target_count,
                pattern_description=pattern_description
            )
            
        elif run_type == 'source_quality':
            target_count = data.get('target_count', 30)
            min_importance = data.get('min_importance', 1)
            
            validation_run = calculator.create_source_quality_run(
                target_count=target_count,
                min_importance=min_importance
            )
            
        else:
            return jsonify({'error': f'Unknown run_type: {run_type}'}), 400
        
        # Update creator
        validation_run.created_by = created_by
        db.commit()
        
        # Return created run details
        return jsonify({
            'validation_run': {
                'id': validation_run.id,
                'run_name': validation_run.run_name,
                'run_type': validation_run.run_type,
                'status': validation_run.status,
                'target_count': validation_run.target_count,
                'actual_count': validation_run.actual_count,
                'events_remaining': validation_run.events_remaining,
                'created_date': validation_run.created_date.isoformat(),
                'created_by': validation_run.created_by,
                'selection_criteria': validation_run.selection_criteria
            }
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating validation run: {e}")
        return jsonify({'error': 'Failed to create validation run'}), 500
    finally:
        db.close()

@app.route('/api/validation-runs/<int:run_id>')
def get_validation_run(run_id):
    """Get detailed information about a specific validation run"""
    db = get_db()
    try:
        calculator = ValidationRunCalculator(db)
        stats = calculator.get_validation_run_stats(run_id)
        
        return jsonify(stats)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting validation run {run_id}: {e}")
        return jsonify({'error': 'Failed to get validation run'}), 500
    finally:
        db.close()

@app.route('/api/validation-runs/<int:run_id>/next')
def get_next_validation_event(run_id):
    """Get the next event to validate from a validation run"""
    db = get_db()
    try:
        validator_id = request.args.get('validator_id')
        
        # Require validator_id to prevent duplicate assignments
        if not validator_id:
            return jsonify({
                'error': 'validator_id parameter is required',
                'message': 'Must provide unique validator_id to prevent duplicate event assignments'
            }), 400
        
        calculator = ValidationRunCalculator(db)
        run_event = calculator.get_next_validation_event(run_id, validator_id)
        
        if not run_event:
            return jsonify({
                'message': 'No more events to validate in this run',
                'run_id': run_id
            }), 404
        
        # Get the full event data
        event = db.query(TimelineEvent).get(run_event.event_id)
        event_data = event.json_content.copy() if event.json_content else {}
        
        return jsonify({
            'run_event': {
                'id': run_event.id,
                'validation_run_id': run_event.validation_run_id,
                'event_id': run_event.event_id,
                'selection_reason': run_event.selection_reason,
                'selection_priority': run_event.selection_priority,
                'validation_status': run_event.validation_status,
                'assigned_validator': run_event.assigned_validator,
                'assigned_date': run_event.assigned_date.isoformat() if run_event.assigned_date else None,
                'high_priority': run_event.high_priority,
                'needs_attention': run_event.needs_attention
            },
            'event': event_data
        })
        
    except Exception as e:
        logger.error(f"Error getting next validation event: {e}")
        return jsonify({'error': 'Failed to get next validation event'}), 500
    finally:
        db.close()

@app.route('/api/validation-runs/<int:run_id>/events/<int:run_event_id>/complete', methods=['POST'])
@require_api_key
def complete_validation_run_event(run_id, run_event_id):
    """Mark a validation run event as completed"""
    db = get_db()
    try:
        data = request.json or {}
        
        status = data.get('status', 'completed')
        notes = data.get('notes', '')
        
        calculator = ValidationRunCalculator(db)
        run_event = calculator.complete_validation_run_event(run_event_id, status, notes)
        
        return jsonify({
            'run_event': {
                'id': run_event.id,
                'validation_status': run_event.validation_status,
                'completed_date': run_event.completed_date.isoformat() if run_event.completed_date else None,
                'validation_notes': run_event.validation_notes
            },
            'message': 'Validation run event completed successfully'
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error completing validation run event: {e}")
        return jsonify({'error': 'Failed to complete validation run event'}), 500
    finally:
        db.close()

@app.route('/api/validation-runs/<int:run_id>/requeue-needs-work', methods=['POST'])
@require_api_key
def requeue_needs_work_events(run_id):
    """Requeue events marked as 'needs_work' back to pending status for re-assignment"""
    db = get_db()
    try:
        calculator = ValidationRunCalculator(db)
        requeued_count = calculator.requeue_needs_work_events(run_id)
        
        return jsonify({
            'run_id': run_id,
            'requeued_count': requeued_count,
            'message': f'Successfully requeued {requeued_count} events that need more work'
        })
        
    except Exception as e:
        logger.error(f"Error requeuing needs-work events for run {run_id}: {e}")
        return jsonify({'error': 'Failed to requeue needs-work events'}), 500
    finally:
        db.close()

@app.route('/api/validation-logs', methods=['POST'])
@require_api_key
def create_validation_log():
    """Create a new validation log entry for an event"""
    db = get_db()
    try:
        data = request.json or {}
        
        # Required fields
        event_id = data.get('event_id')
        validator_type = data.get('validator_type')
        status = data.get('status')
        notes = data.get('notes')
        
        if not all([event_id, validator_type, status, notes]):
            return jsonify({'error': 'event_id, validator_type, status, and notes are required'}), 400
        
        # Create validation log
        validation_log = ValidationLog(
            event_id=event_id,
            validation_run_id=data.get('validation_run_id'),
            validator_type=validator_type,
            validator_id=data.get('validator_id'),
            status=status,
            confidence=data.get('confidence'),
            notes=notes,
            issues_found=data.get('issues_found'),
            sources_verified=data.get('sources_verified'),
            corrections_made=data.get('corrections_made'),
            time_spent_minutes=data.get('time_spent_minutes'),
            validation_criteria=data.get('validation_criteria')
        )
        
        db.add(validation_log)
        db.commit()
        
        # Store fields before session closes
        validation_log_data = {
            'id': validation_log.id,
            'event_id': validation_log.event_id,
            'validator_type': validation_log.validator_type,
            'validator_id': validation_log.validator_id,
            'status': validation_log.status,
            'validation_date': validation_log.validation_date.isoformat(),
            'notes': validation_log.notes,
            'confidence': validation_log.confidence,
            'issues_found': validation_log.issues_found,
            'sources_verified': validation_log.sources_verified,
            'corrections_made': validation_log.corrections_made,
            'time_spent_minutes': validation_log.time_spent_minutes,
            'validation_criteria': validation_log.validation_criteria,
            'validation_run_id': validation_log.validation_run_id
        }
        validation_log_id = validation_log.id
        
        # Write validation log to filesystem for persistence
        write_validation_log_to_filesystem(validation_log_data)
        
        # Auto-apply corrections if provided and status is validated
        corrections_applied = False
        if status == 'validated' and data.get('corrections_made') and data.get('auto_apply', True):
            try:
                corrections_applied = apply_validation_corrections(
                    event_id=event_id,
                    corrections=data.get('corrections_made'),
                    validator_id=data.get('validator_id', 'unknown'),
                    validation_log_id=validation_log_id
                )
            except Exception as e:
                logger.warning(f"Failed to apply corrections for event {event_id}: {e}")
        
        return jsonify({
            'validation_log': validation_log_data,
            'corrections_applied': corrections_applied,
            'message': 'Validation log created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating validation log: {e}")
        return jsonify({'error': 'Failed to create validation log'}), 500
    finally:
        db.close()

@app.route('/api/event-update-failures')
def list_event_update_failures():
    """List event update failures with optional filtering"""
    db = get_db()
    try:
        from models import EventUpdateFailure
        
        # Get query parameters
        event_id = request.args.get('event_id')
        failure_type = request.args.get('failure_type')
        validator_id = request.args.get('validator_id')
        resolved = request.args.get('resolved')
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = int(request.args.get('offset', 0))
        
        # Build query with filters
        query = db.query(EventUpdateFailure)
        
        if event_id:
            query = query.filter(EventUpdateFailure.event_id.like(f'%{event_id}%'))
        if failure_type:
            query = query.filter_by(failure_type=failure_type)
        if validator_id:
            query = query.filter_by(validator_id=validator_id)
        if resolved is not None:
            resolved_bool = resolved.lower() in ('true', '1', 'yes')
            query = query.filter_by(resolved=resolved_bool)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply ordering and pagination
        failures = query.order_by(EventUpdateFailure.failure_date.desc())\
                      .offset(offset)\
                      .limit(limit)\
                      .all()
        
        # Convert to dictionaries
        failure_dicts = []
        for failure in failures:
            failure_dict = {
                'id': failure.id,
                'event_id': failure.event_id,
                'validation_log_id': failure.validation_log_id,
                'failure_date': failure.failure_date.isoformat() if failure.failure_date else None,
                'failure_type': failure.failure_type,
                'error_message': failure.error_message,
                'stack_trace': failure.stack_trace,
                'validator_id': failure.validator_id,
                'attempted_corrections': failure.attempted_corrections,
                'file_path': failure.file_path,
                'file_exists': failure.file_exists,
                'file_permissions': failure.file_permissions,
                'retry_count': failure.retry_count,
                'resolved': failure.resolved,
                'resolution_notes': failure.resolution_notes,
                'resolved_date': failure.resolved_date.isoformat() if failure.resolved_date else None
            }
            failure_dicts.append(failure_dict)
        
        return jsonify({
            'event_update_failures': failure_dicts,
            'pagination': {
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing event update failures: {e}")
        return jsonify({'error': f'Failed to list event update failures: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/event-update-failures/stats')
def event_update_failure_stats():
    """Get statistics about event update failures"""
    db = get_db()
    try:
        from models import EventUpdateFailure
        from sqlalchemy import func, desc
        
        # Total failure counts
        total_failures = db.query(EventUpdateFailure).count()
        unresolved_failures = db.query(EventUpdateFailure).filter_by(resolved=False).count()
        resolved_failures = db.query(EventUpdateFailure).filter_by(resolved=True).count()
        
        # Failure types breakdown
        failure_type_stats = db.query(
            EventUpdateFailure.failure_type,
            func.count(EventUpdateFailure.id).label('count'),
            func.count(func.nullif(EventUpdateFailure.resolved, True)).label('unresolved_count')
        ).group_by(EventUpdateFailure.failure_type)\
         .order_by(desc('count'))\
         .all()
        
        # Most problematic events (multiple failures)
        problematic_events = db.query(
            EventUpdateFailure.event_id,
            func.count(EventUpdateFailure.id).label('failure_count')
        ).group_by(EventUpdateFailure.event_id)\
         .having(func.count(EventUpdateFailure.id) > 1)\
         .order_by(desc('failure_count'))\
         .limit(10)\
         .all()
        
        # Validators with most failures
        validator_failure_stats = db.query(
            EventUpdateFailure.validator_id,
            func.count(EventUpdateFailure.id).label('failure_count')
        ).group_by(EventUpdateFailure.validator_id)\
         .order_by(desc('failure_count'))\
         .limit(10)\
         .all()
        
        return jsonify({
            'overall_stats': {
                'total_failures': total_failures,
                'unresolved_failures': unresolved_failures,
                'resolved_failures': resolved_failures,
                'resolution_rate': (resolved_failures / total_failures * 100) if total_failures > 0 else 0
            },
            'failure_types': [
                {
                    'failure_type': ft.failure_type,
                    'count': ft.count,
                    'unresolved_count': ft.unresolved_count,
                    'resolution_rate': ((ft.count - ft.unresolved_count) / ft.count * 100) if ft.count > 0 else 0
                }
                for ft in failure_type_stats
            ],
            'problematic_events': [
                {
                    'event_id': pe.event_id,
                    'failure_count': pe.failure_count
                }
                for pe in problematic_events
            ],
            'validator_failure_stats': [
                {
                    'validator_id': vfs.validator_id,
                    'failure_count': vfs.failure_count
                }
                for vfs in validator_failure_stats
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting event update failure stats: {e}")
        return jsonify({'error': f'Failed to get failure stats: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/validation-logs')
def list_validation_logs():
    """List validation logs with optional filtering"""
    db = get_db()
    try:
        # Get query parameters
        event_id = request.args.get('event_id')
        validation_run_id = request.args.get('validation_run_id')
        validator_type = request.args.get('validator_type')
        status = request.args.get('status')
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = db.query(ValidationLog)
        
        if event_id:
            query = query.filter(ValidationLog.event_id == event_id)
        if validation_run_id:
            query = query.filter(ValidationLog.validation_run_id == int(validation_run_id))
        if validator_type:
            query = query.filter(ValidationLog.validator_type == validator_type)
        if status:
            query = query.filter(ValidationLog.status == status)
        
        # Order by validation date, newest first
        query = query.order_by(ValidationLog.validation_date.desc())
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        validation_logs = query.offset(offset).limit(limit).all()
        
        # Convert to dict format
        logs_data = []
        for log in validation_logs:
            log_data = {
                'id': log.id,
                'event_id': log.event_id,
                'validation_run_id': log.validation_run_id,
                'validator_type': log.validator_type,
                'validator_id': log.validator_id,
                'validation_date': log.validation_date.isoformat(),
                'status': log.status,
                'confidence': log.confidence,
                'notes': log.notes,
                'issues_found': log.issues_found,
                'sources_verified': log.sources_verified,
                'corrections_made': log.corrections_made,
                'time_spent_minutes': log.time_spent_minutes,
                'validation_criteria': log.validation_criteria
            }
            logs_data.append(log_data)
        
        return jsonify({
            'validation_logs': logs_data,
            'pagination': {
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing validation logs: {e}")
        return jsonify({'error': 'Failed to list validation logs'}), 500
    finally:
        db.close()


# ==================== STATIC ASSETS SERVING ====================

@app.route('/')
def timeline_viewer():
    """Serve the main timeline viewer application"""
    return send_file('templates/index.html')

@app.route('/viewer')
def timeline_viewer_alt():
    """Alternative route for timeline viewer"""
    return send_file('templates/index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static assets (CSS, JS, images)"""
    return send_from_directory('static', filename)

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    try:
        return send_from_directory('static/img', 'favicon.ico')
    except:
        # Return empty response if no favicon
        return '', 204

@app.route('/manifest.json')
def manifest():
    """Serve PWA manifest"""
    try:
        return send_from_directory('static', 'manifest.json')
    except:
        # Return basic manifest if none exists
        manifest_data = {
            "name": "Timeline Viewer",
            "short_name": "Timeline",
            "start_url": "/",
            "display": "standalone",
            "theme_color": "#000000",
            "background_color": "#ffffff"
        }
        return jsonify(manifest_data)

# ==================== STARTUP ====================

if __name__ == '__main__':
    PORT = int(os.environ.get('RESEARCH_MONITOR_PORT', 5555))
    
    # Sync validation logs from filesystem on startup
    sync_validation_logs_from_filesystem()
    
    # Start filesystem syncer
    syncer.start()
    
    logger.info(f"Research Monitor v2 starting on port {PORT}")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Events path: {EVENTS_PATH}")
    logger.info(f"Priorities path: {PRIORITIES_PATH}")
    logger.info(f"Validation logs path: {VALIDATION_LOGS_PATH}")
    logger.info(f"Commit threshold: {COMMIT_THRESHOLD} events")
    
    try:
        app.run(host='127.0.0.1', port=PORT, debug=False)
    finally:
        syncer.stop()