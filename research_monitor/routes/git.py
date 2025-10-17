"""
routes/git.py - Git Integration and Commit Tracking

Provides commit orchestration tracking endpoints. The Research Monitor tracks
when commits are needed but delegates actual git operations to the orchestrator.

Routes:
- GET /api/commit/status - Check if commit is needed with QA metadata
- POST /api/commit/reset - Reset commit counter after orchestrator commits
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('git', __name__)


def get_db():
    """Get database session from app_v2"""
    from research_monitor import app_v2
    return app_v2.get_db()


def get_qa_validation_stats(db):
    """Get QA validation statistics for commit metadata"""
    from research_monitor.models import EventMetadata

    try:
        # Count events by validation status
        validation_counts = db.query(
            EventMetadata.validation_status,
            func.count(EventMetadata.event_id)
        ).group_by(EventMetadata.validation_status).all()

        # Convert to dictionary
        stats = {}
        total_events = 0
        for status, count in validation_counts:
            stats[status or 'pending'] = count
            total_events += count

        # Ensure all statuses are represented
        for status in ['pending', 'validated', 'rejected']:
            if status not in stats:
                stats[status] = 0

        # Calculate recent validation activity (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)

        recent_validations = db.query(EventMetadata).filter(
            EventMetadata.validation_date >= recent_cutoff,
            EventMetadata.validation_status.in_(['validated', 'rejected'])
        ).count()

        return {
            'total_events_with_metadata': total_events,
            'validation_breakdown': stats,
            'recent_validations_24h': recent_validations,
            'validation_rate': round((stats['validated'] + stats['rejected']) / max(total_events, 1) * 100, 1)
        }

    except Exception as e:
        logger.error(f"Error getting QA validation stats: {e}")
        return {
            'total_events_with_metadata': 0,
            'validation_breakdown': {'pending': 0, 'validated': 0, 'rejected': 0},
            'recent_validations_24h': 0,
            'validation_rate': 0.0
        }


@bp.route('/api/commit/status')
def get_commit_status():
    """Check if a commit is needed with QA validation metadata"""
    from research_monitor import app_v2

    db = get_db()

    try:
        # Get QA validation statistics
        qa_stats = get_qa_validation_stats(db)

        # Basic commit status
        commit_status = {
            'events_since_commit': app_v2.events_since_commit,
            'threshold': app_v2.COMMIT_THRESHOLD,
            'commit_needed': app_v2.events_since_commit >= app_v2.COMMIT_THRESHOLD,
            'session_id': app_v2.current_session_id
        }

        # Add QA validation metadata
        commit_status['qa_validation'] = qa_stats

        # Add suggested commit message components
        if commit_status['commit_needed']:
            validated_count = qa_stats['validation_breakdown']['validated']
            rejected_count = qa_stats['validation_breakdown']['rejected']
            pending_count = qa_stats['validation_breakdown']['pending']

            commit_status['suggested_commit_message'] = {
                'title': f"Add {app_v2.events_since_commit} researched events with QA validation",
                'qa_summary': f"QA Status: {validated_count} validated, {rejected_count} rejected, {pending_count} pending review",
                'validation_rate': f"Overall validation rate: {qa_stats['validation_rate']}%"
            }

        return jsonify(commit_status)

    finally:
        db.close()


@bp.route('/api/commit/reset', methods=['POST'])
def reset_commit_counter():
    """Reset the commit counter after orchestrator performs commit"""
    from research_monitor import app_v2

    # Check API key
    api_key = current_app.config.get('API_KEY')
    if api_key:
        provided_key = request.headers.get('X-API-Key')
        if provided_key != api_key:
            return jsonify({'error': 'Invalid or missing API key'}), 401

    app_v2.events_since_commit = 0
    logger.info("Commit counter reset by orchestrator")
    return jsonify({'status': 'reset', 'events_since_commit': 0})
