"""
routes/priorities.py - Research Priority Management

Provides research priority queue management with atomic reservation,
status tracking, and export capabilities. Research priorities are
database-authoritative.

Routes:
- POST /api/priorities/next - Atomically reserve next priority (prevents race conditions)
- GET /api/priorities/next - Get info about next priority without reserving
- PUT /api/priorities/<id>/start - Confirm starting work on reserved priority
- PUT /api/priorities/<id>/status - Update priority status and progress
- GET /api/priorities/export - Export valuable priorities for persistence
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
import logging
import time

# Import shared utilities
from blueprint_utils import get_db, log_activity, success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('priorities', __name__, url_prefix='/api/priorities')


@bp.route('/next', methods=['POST'])
def reserve_next_priority():
    """Atomically reserve the next priority for an agent (prevents race conditions)"""
    from models import ResearchPriority, ActivityLog

    # Check API key
    api_key = current_app.config.get('API_KEY')
    if api_key:
        provided_key = request.headers.get('X-API-Key')
        if provided_key != api_key:
            return jsonify({'error': 'Invalid or missing API key'}), 401

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


@bp.route('/next', methods=['GET'])
def get_next_priority_info():
    """Get info about next priority without reserving (for inspection only)"""
    from models import ResearchPriority

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


@bp.route('/<priority_id>/start', methods=['PUT'])
def confirm_priority_work(priority_id):
    """Confirm that agent is starting work on reserved priority"""
    from models import ResearchPriority, ActivityLog

    # Check API key
    api_key = current_app.config.get('API_KEY')
    if api_key:
        provided_key = request.headers.get('X-API-Key')
        if provided_key != api_key:
            return jsonify({'error': 'Invalid or missing API key'}), 401

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


@bp.route('/<priority_id>/status', methods=['PUT'])
def update_priority_status(priority_id):
    """Update priority status (database authoritative)"""
    from models import ResearchPriority, ActivityLog

    # Check API key
    api_key = current_app.config.get('API_KEY')
    if api_key:
        provided_key = request.headers.get('X-API-Key')
        if provided_key != api_key:
            return jsonify({'error': 'Invalid or missing API key'}), 401

    db = get_db()
    try:
        priority = db.query(ResearchPriority).filter_by(id=priority_id).first()
        if not priority:
            return jsonify({'error': 'Priority not found'}), 404

        data = request.json
        old_status = priority.status
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
            details={'old_status': old_status, 'new_status': data.get('status')}
        )
        db.add(activity)

        db.commit()
        return jsonify({'status': 'updated'})

    finally:
        db.close()


@bp.route('/export')
def export_priorities():
    """Export valuable priorities for persistence"""
    from models import ResearchPriority

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
