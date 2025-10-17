"""
routes/events.py - Event Search and Management Endpoints

Provides event discovery, validation, and creation:
- Research-focused queries (missing sources, validation queue, research candidates)
- Event validation and batch operations
- Filesystem-based event creation with commit orchestration
"""
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import text
from pathlib import Path
from typing import List, Tuple
import json
import logging

# Import shared utilities
from blueprint_utils import get_db, require_api_key

logger = logging.getLogger(__name__)

bp = Blueprint('events', __name__, url_prefix='/api/events')

def get_events_path():
    """Get events path from config (blueprint-specific helper)"""
    return current_app.config.get('EVENTS_PATH')

def get_priorities_path():
    """Get priorities path from config (blueprint-specific helper)"""
    return current_app.config.get('PRIORITIES_PATH')

def get_commit_threshold():
    """Get commit threshold from config (blueprint-specific helper)"""
    return current_app.config.get('COMMIT_THRESHOLD', 10)

# ==================== EVENT SEARCH APIS (Read from synced data) ====================

@bp.route('/search')
def search_events():
    """Search events using JSON queries and full-text search"""
    from models import TimelineEvent

    db = get_db()
    try:
        query_text = request.args.get('q', '')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = min(int(request.args.get('limit', 20)), 5000)

        # Use SQLite FTS if query provided
        if query_text:
            # Escape special characters for FTS5
            fts_query = query_text.replace('.', ' ').replace('-', ' ').replace(':', ' ')
            # For exact phrase matching with special chars, use LIKE fallback
            if any(char in query_text for char in ['.', ':', '/', '@']):
                # Use LIKE search for URLs and special content including JSON sources
                results = db.execute(text('''
                    SELECT e.id, e.date, e.title, e.summary, e.importance
                    FROM timeline_events e
                    WHERE e.title LIKE :query_pattern
                       OR e.summary LIKE :query_pattern
                       OR e.json_content LIKE :query_pattern
                    ORDER BY e.importance DESC
                    LIMIT :limit
                '''), {'query_pattern': f'%{query_text}%', 'limit': limit})
            else:
                # Use FTS5 for regular text search
                results = db.execute(text('''
                    SELECT e.id, e.date, e.title, e.summary, e.importance
                    FROM timeline_events e
                    JOIN events_fts ON events_fts.id = e.id
                    WHERE events_fts MATCH :query
                    ORDER BY rank
                    LIMIT :limit
                '''), {'query': fts_query, 'limit': limit})
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

@bp.route('/missing-sources')
def find_events_missing_sources():
    """Find events with missing or insufficient sources"""
    from models import TimelineEvent

    db = get_db()
    try:
        min_sources = int(request.args.get('min_sources', 2))
        limit = min(int(request.args.get('limit', 50)), 5000)

        # Query events and check their sources
        events = db.query(TimelineEvent).order_by(TimelineEvent.importance.desc()).all()

        missing_sources_events = []
        for event in events:
            if event.json_content:
                sources = event.json_content.get('sources', [])
                source_count = 0

                if isinstance(sources, list):
                    source_count = len(sources)
                elif isinstance(sources, dict):
                    source_count = 1
                elif sources:
                    source_count = 1

                if source_count < min_sources:
                    event_dict = event.json_content.copy()
                    event_dict['source_count'] = source_count
                    event_dict['sources_needed'] = min_sources - source_count
                    missing_sources_events.append(event_dict)

                    if len(missing_sources_events) >= limit:
                        break

        return jsonify({
            'events': missing_sources_events,
            'count': len(missing_sources_events),
            'criteria': {
                'min_sources': min_sources,
                'limit': limit
            }
        })

    finally:
        db.close()

@bp.route('/validation-queue')
def get_validation_queue():
    """Get events prioritized for validation by importance and source quality"""
    from models import TimelineEvent

    db = get_db()
    try:
        limit = min(int(request.args.get('limit', 20)), 5000)
        min_importance = int(request.args.get('min_importance', 6))
        max_sources = int(request.args.get('max_sources', 2))

        # Get events that are high importance but low source count
        events = db.query(TimelineEvent).order_by(TimelineEvent.importance.desc()).all()

        validation_queue = []
        for event in events:
            if event.json_content and event.importance >= min_importance:
                sources = event.json_content.get('sources', [])
                source_count = 0

                if isinstance(sources, list):
                    source_count = len(sources)
                elif isinstance(sources, dict):
                    source_count = 1
                elif sources:
                    source_count = 1

                if source_count <= max_sources:
                    event_dict = event.json_content.copy()
                    event_dict['source_count'] = source_count
                    event_dict['validation_priority'] = event.importance - source_count
                    validation_queue.append(event_dict)

                    if len(validation_queue) >= limit:
                        break

        # Sort by validation priority (importance minus source count)
        validation_queue.sort(key=lambda x: x.get('validation_priority', 0), reverse=True)

        return jsonify({
            'events': validation_queue,
            'count': len(validation_queue),
            'criteria': {
                'min_importance': min_importance,
                'max_sources': max_sources,
                'limit': limit
            }
        })

    finally:
        db.close()

@bp.route('/broken-links')
def find_broken_links():
    """Find events with potentially broken or inaccessible source links"""
    from models import TimelineEvent

    db = get_db()
    try:
        limit = min(int(request.args.get('limit', 50)), 5000)
        check_links = request.args.get('check_links', 'false').lower() == 'true'

        events = db.query(TimelineEvent).order_by(TimelineEvent.importance.desc()).all()

        broken_link_events = []
        for event in events:
            if event.json_content:
                sources = event.json_content.get('sources', [])
                if isinstance(sources, list):
                    suspicious_urls = []
                    for source in sources:
                        if isinstance(source, dict) and 'url' in source:
                            url = source['url']
                            # Skip if URL is None or not a string
                            if not url or not isinstance(url, str):
                                continue
                            # Basic checks for potentially broken links
                            if (url.startswith('http://example.com') or
                                url.startswith('https://example.com') or
                                url == 'TBD' or
                                url == 'internal-research' or
                                'internal-research-portal' in url):
                                suspicious_urls.append(url)

                    if suspicious_urls:
                        event_dict = event.json_content.copy()
                        event_dict['suspicious_urls'] = suspicious_urls
                        event_dict['suspicious_count'] = len(suspicious_urls)
                        broken_link_events.append(event_dict)

                        if len(broken_link_events) >= limit:
                            break

        return jsonify({
            'events': broken_link_events,
            'count': len(broken_link_events),
            'criteria': {
                'check_links': check_links,
                'limit': limit
            }
        })

    finally:
        db.close()

@bp.route('/research-candidates')
def get_research_candidates():
    """Get high-importance events with insufficient sources - ideal for research"""
    from models import TimelineEvent

    db = get_db()
    try:
        limit = min(int(request.args.get('limit', 20)), 5000)
        min_importance = int(request.args.get('min_importance', 7))
        max_sources = int(request.args.get('max_sources', 2))

        events = db.query(TimelineEvent).order_by(TimelineEvent.importance.desc()).all()

        research_candidates = []
        for event in events:
            if event.json_content and event.importance >= min_importance:
                sources = event.json_content.get('sources', [])
                source_count = 0

                if isinstance(sources, list):
                    source_count = len(sources)
                elif isinstance(sources, dict):
                    source_count = 1
                elif sources:
                    source_count = 1

                if source_count <= max_sources:
                    event_dict = event.json_content.copy()
                    event_dict['source_count'] = source_count
                    event_dict['research_priority'] = event.importance * 2 - source_count
                    research_candidates.append(event_dict)

                    if len(research_candidates) >= limit:
                        break

        # Sort by research priority
        research_candidates.sort(key=lambda x: x.get('research_priority', 0), reverse=True)

        return jsonify({
            'events': research_candidates,
            'count': len(research_candidates),
            'criteria': {
                'min_importance': min_importance,
                'max_sources': max_sources,
                'limit': limit
            }
        })

    finally:
        db.close()

@bp.route('/validate', methods=['POST'])
def validate_event():
    """Validate an event before saving with helpful error messages"""
    from models import TimelineEvent
    import app_v2

    try:
        event = request.json
        if not event:
            return jsonify({
                'valid': False,
                'errors': ['No event data provided'],
                'warnings': [],
                'fixed_event': None
            }), 400

        # Use built-in validation
        validation_result = app_v2.validate_timeline_event(event)
        errors = validation_result['errors']
        warnings = validation_result['warnings']
        fixed_event = validation_result['fixed_event']

        # Check for duplicates
        if event.get('id'):
            db = get_db()
            try:
                existing = db.query(TimelineEvent).filter_by(id=event['id']).first()
                if existing:
                    errors.append(f"Event {event['id']} already exists")
            finally:
                db.close()

        status_code = 400 if errors else 200
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'fixed_event': fixed_event
        }), status_code

    except Exception as e:
        return jsonify({
            'valid': False,
            'errors': [f'Validation error: {str(e)}'],
            'warnings': []
        }), 500

# ==================== COMMIT ORCHESTRATION ====================

def validate_single_event(event: dict, db) -> Tuple[List[str], dict]:
    """Validate a single event using built-in validator and return errors and fixed event"""
    from models import TimelineEvent
    import app_v2

    validation_result = app_v2.validate_timeline_event(event)

    errors = validation_result['errors'].copy()
    fixed_event = validation_result['fixed_event']

    # Check for duplicates by ID (only real error we can't fix)
    if fixed_event.get('id'):
        existing = db.query(TimelineEvent).filter_by(id=fixed_event['id']).first()
        if existing:
            errors.append(f"Event {fixed_event['id']} already exists")

    return errors, fixed_event

@bp.route('/batch', methods=['POST'])
@require_api_key
def batch_create_events():
    """Create multiple events with validation and error handling"""
    from models import EventMetadata, ResearchSession, ActivityLog
    import app_v2

    db = get_db()
    try:
        data = request.json
        events = data.get('events', [])
        priority_id = data.get('priority_id')

        if not events:
            return jsonify({'error': 'No events provided'}), 400

        results = []
        successful_events = 0
        failed_events = 0
        EVENTS_PATH = get_events_path()

        for i, event in enumerate(events):
            event_result = {
                'index': i,
                'event_id': event.get('id', f'event-{i}'),
                'status': 'success',
                'errors': [],
                'warnings': []
            }

            try:
                # Validate and fix event using enhanced validator
                validation_errors, fixed_event = validate_single_event(event, db)
                if validation_errors:
                    event_result['status'] = 'failed'
                    event_result['errors'] = validation_errors
                    failed_events += 1
                    results.append(event_result)
                    continue

                # Use the fixed event (validator handles ID generation, type fixing, etc.)
                event_result['event_id'] = fixed_event['id']

                # Save fixed event to filesystem
                event_path = EVENTS_PATH / f"{fixed_event['id']}.json"
                with open(event_path, 'w') as f:
                    json.dump(fixed_event, f, indent=2)

                # Create metadata
                metadata = EventMetadata(
                    event_id=fixed_event['id'],
                    created_by=request.headers.get('User-Agent', 'claude-code'),
                    research_priority_id=priority_id,
                    validation_status='validated'
                )
                db.add(metadata)

                # Log activity
                activity = ActivityLog(
                    action='event_batched',
                    event_id=event['id'],
                    priority_id=priority_id,
                    agent=request.headers.get('User-Agent', 'claude-code')
                )
                db.add(activity)

                successful_events += 1
                app_v2.events_since_commit += 1

            except Exception as e:
                event_result['status'] = 'failed'
                event_result['errors'].append(f'System error: {str(e)}')
                failed_events += 1

            results.append(event_result)

        # Update session tracking
        session = db.query(ResearchSession).filter_by(session_id=app_v2.current_session_id).first()
        if not session:
            session = ResearchSession(
                session_id=app_v2.current_session_id,
                commit_threshold=get_commit_threshold(),
                events_created=0,
                priorities_completed=0
            )
            db.add(session)

        session.events_created = (session.events_created or 0) + successful_events

        db.commit()

        # Check if we should trigger a commit
        if app_v2.events_since_commit >= get_commit_threshold():
            trigger_commit()

        return jsonify({
            'status': 'completed',
            'successful_events': successful_events,
            'failed_events': failed_events,
            'total_events': len(events),
            'events_since_commit': app_v2.events_since_commit,
            'results': results
        })

    except Exception as e:
        logger.error(f"Batch event creation failed: {e}")
        return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500
    finally:
        db.close()

@bp.route('/staged', methods=['POST'])
@require_api_key
def stage_event():
    """Stage an event for the next commit"""
    from models import EventMetadata, ResearchSession, ActivityLog
    import app_v2

    db = get_db()
    try:
        data = request.json
        priority_id = data.get('priority_id')

        # Validate and fix event using enhanced validator
        validation_errors, fixed_event = validate_single_event(data, db)

        # Only reject if there are truly unfixable errors (like duplicates)
        # Type conversion errors and missing fields are auto-fixed
        unfixable_errors = [err for err in validation_errors if 'already exists' in err]
        if unfixable_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': unfixable_errors
            }), 400

        # Use fixed event
        event_id = fixed_event['id']
        EVENTS_PATH = get_events_path()

        # Save fixed event to filesystem
        event_path = EVENTS_PATH / f"{event_id}.json"
        with open(event_path, 'w') as f:
            json.dump(fixed_event, f, indent=2)

        # Create metadata
        metadata = EventMetadata(
            event_id=event_id,
            created_by=request.headers.get('User-Agent', 'claude-code'),
            research_priority_id=priority_id,
            validation_status='pending'
        )
        db.add(metadata)

        # Update session tracking
        session = db.query(ResearchSession).filter_by(session_id=app_v2.current_session_id).first()
        if not session:
            session = ResearchSession(
                session_id=app_v2.current_session_id,
                commit_threshold=get_commit_threshold(),
                events_created=0,
                priorities_completed=0
            )
            db.add(session)

        session.events_created = (session.events_created or 0) + 1
        app_v2.events_since_commit += 1

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
        if app_v2.events_since_commit >= get_commit_threshold():
            trigger_commit()

        return jsonify({'status': 'staged', 'events_since_commit': app_v2.events_since_commit})

    finally:
        db.close()

def trigger_commit():
    """Orchestrate a git commit with new events and updated priorities"""
    from models import ResearchPriority, ResearchSession
    import app_v2
    from datetime import datetime

    db = get_db()
    try:
        PRIORITIES_PATH = get_priorities_path()

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
        session = db.query(ResearchSession).filter_by(session_id=app_v2.current_session_id).first()
        if session:
            session.last_commit = datetime.now()

        db.commit()

        # Log for orchestrator to see
        logger.info(f"COMMIT THRESHOLD REACHED: {app_v2.events_since_commit} events ready for commit")
        logger.info(f"Exported {len(priorities)} priorities marked as export_worthy")
        logger.info("Orchestrator should perform: git add timeline_data/events research_priorities && git commit")

        # Reset counter
        app_v2.events_since_commit = 0

    finally:
        db.close()
