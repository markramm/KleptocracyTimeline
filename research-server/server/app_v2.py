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
from parsers.factory import EventParserFactory
from services.git_sync import GitSyncer
from services.git_service import GitService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__,
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')

# Load centralized configuration
from config import get_config
config = get_config()

# Apply configuration to Flask app
app.config.update(config.to_flask_config())

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

# Store cache in app.config for blueprint access
app.config['CACHE'] = cache

# Database setup using centralized config
engine = init_database(config.db_path)
Session = scoped_session(sessionmaker(bind=engine))

# Current session tracking
current_session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
events_since_commit = 0
sync_lock = threading.Lock()

# Create git syncer (replaces FilesystemSyncer)
git_service = GitService()
git_syncer = GitSyncer(app, Session, git_service)

def require_api_key(f):
    """Decorator to require API key for write operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = app.config.get('API_KEY')
        if api_key:
            provided_key = request.headers.get('X-API-Key')
            if provided_key != api_key:
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
# Extracted to services/filesystem_sync.py - instantiated after app initialization

def write_validation_log_to_filesystem(validation_log_data: dict):
    """Write validation log to filesystem for persistence"""
    try:
        # Ensure validation logs directory exists
        validation_logs_path = app.config.get('VALIDATION_LOGS_PATH')
        validation_logs_path.mkdir(parents=True, exist_ok=True)

        # Create filename with timestamp and ID
        timestamp = validation_log_data['validation_date'].replace(':', '-').replace('.', '-')
        filename = f"validation-log-{validation_log_data['id']}-{timestamp}.json"
        file_path = validation_logs_path / filename
        
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
        validation_logs_path = app.config.get('VALIDATION_LOGS_PATH')
        if validation_logs_path.exists():
            for json_file in validation_logs_path.glob('validation-log-*.json'):
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
    Supports both JSON and Markdown (.md) event formats
    """
    import traceback
    from pathlib import Path

    event_file = None
    events_dir = Path(__file__).parent.parent.parent / 'timeline' / 'data' / 'events'

    try:
        # Find event file - check both .md and .json extensions
        for ext in ['.md', '.json']:
            exact_file = events_dir / f"{event_id}{ext}"
            if exact_file.exists():
                event_file = exact_file
                break

        # If exact match not found, search for files containing the event ID
        if not event_file:
            for pattern in ['*.md', '*.json']:
                for file_path in events_dir.glob(pattern):
                    if event_id in file_path.name:
                        event_file = file_path
                        break
                if event_file:
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
                file_path=str(events_dir / f"{event_id}.*")
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
        
        # Read current event data with error handling - supports both JSON and Markdown
        try:
            # Use EventParserFactory to read the file (auto-detects format)
            parser_factory = EventParserFactory()
            event_data = parser_factory.parse_event(event_file)
        except Exception as parse_error:
            error_msg = f"Error parsing event file: {parse_error}"
            log_update_failure(
                event_id=event_id,
                validation_log_id=validation_log_id,
                validator_id=validator_id,
                failure_type="parse_error",
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
        
        # Write updated event data with error handling - supports both JSON and Markdown
        try:
            # Create backup before writing
            backup_content = None
            try:
                with open(event_file, 'r') as f:
                    backup_content = f.read()
            except:
                pass  # If we can't backup, still try to write

            # Write in the appropriate format based on file extension
            if event_file.suffix == '.md':
                # Write markdown with frontmatter
                import frontmatter

                # Extract summary for markdown body
                summary = event_data.get('summary', '')

                # Prepare frontmatter metadata (exclude summary)
                metadata = {k: v for k, v in event_data.items() if k != 'summary'}

                # Create frontmatter post
                post = frontmatter.Post(summary, **metadata)

                with open(event_file, 'w', encoding='utf-8') as f:
                    f.write(frontmatter.dumps(post))
            else:
                # Write JSON
                with open(event_file, 'w') as f:
                    json.dump(event_data, f, indent=2)

            # Verify the write was successful by reading back
            try:
                parser_factory = EventParserFactory()
                verification_data = parser_factory.parse_event(event_file)
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
from routes import register_blueprints
register_blueprints(app)

# ==================== RESEARCH PRIORITY APIS (Database Authoritative) ====================
# MOVED TO routes/priorities.py blueprint
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

@app.route('/api/sync', methods=['POST'])
@require_api_key
def trigger_sync():
    """
    Manually trigger git sync

    POST body (optional):
    {
        "pull": true  // Whether to git pull before syncing (default: true)
    }

    Returns:
        Sync statistics
    """
    try:
        # Optional: force git pull
        pull_first = request.json.get('pull', True) if request.json else True

        logger.info(f"Manual sync triggered (pull_first={pull_first})")

        # Sync from git
        result = git_syncer.sync_from_git(pull_first=pull_first)

        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Sync completed',
                'events_added': result['events_added'],
                'events_updated': result['events_updated'],
                'events_unchanged': result['events_unchanged'],
                'total_synced': result['events_synced'],
                'errors': result['errors'] if result['errors'] else None
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Sync failed',
                'errors': result['errors']
            }), 500

    except Exception as e:
        logger.error(f"Sync endpoint error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/git/status', methods=['GET'])
def git_status():
    """
    Get git repository status

    Returns:
        Git status information (current commit, branch, etc.)
    """
    try:
        status = git_syncer.get_git_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Git status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== TIMELINE VIEWER API ENDPOINTS ====================
# MOVED TO routes/timeline.py blueprint - 12 timeline routes
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
    # Sync validation logs from filesystem on startup
    sync_validation_logs_from_filesystem()

    # Sync events from git repository on startup
    logger.info("Syncing events from git repository...")
    startup_sync = git_syncer.sync_from_git(pull_first=True)

    if startup_sync['success']:
        logger.info(
            f"Startup sync complete: {startup_sync['events_synced']} events "
            f"(+{startup_sync['events_added']} ~{startup_sync['events_updated']})"
        )
    else:
        logger.error(f"Startup sync failed: {startup_sync['errors']}")

    logger.info(f"Research Monitor v2 starting on port {config.port}")
    logger.info(f"Database: {config.db_path}")
    logger.info(f"Events path: {config.events_path}")
    logger.info(f"Priorities path: {config.priorities_path}")
    logger.info(f"Validation logs path: {config.validation_logs_path}")
    logger.info(f"Commit threshold: {config.commit_threshold} events")

    app.run(host='127.0.0.1', port=config.port, debug=False)