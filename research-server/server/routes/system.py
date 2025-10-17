"""
routes/system.py - System Management and Server Control

Provides server management, statistics, cache control, activity monitoring,
and static file serving endpoints.

Routes:
- POST /api/server/shutdown - Graceful server shutdown
- GET /api/server/health - Health check
- GET /api/stats - System statistics
- POST /api/cache/clear - Clear cache
- GET /api/cache/stats - Cache statistics
- GET /api/activity/recent - Recent activity
- GET /api/research/session - Research session status
- GET / - Main timeline viewer
- GET /viewer - Alternative timeline viewer route
- GET /static/<path> - Static assets
- GET /favicon.ico - Favicon
- GET /manifest.json - PWA manifest
"""

from flask import Blueprint, jsonify, request, current_app, send_file, send_from_directory
from datetime import datetime, timezone
from sqlalchemy import or_
import logging
import os
import signal
import time
import threading

# Import shared utilities
from blueprint_utils import get_db, log_activity, success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('system', __name__)


def get_current_summary(db):
    """Get current research status summary with QA queue stats"""
    import app_v2
    from models import TimelineEvent, EventMetadata, ResearchPriority
    from qa_queue import QAQueueManager

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
            'staged_events_count': app_v2.events_since_commit,
            'commit_progress': f"{app_v2.events_since_commit}/{app_v2.COMMIT_THRESHOLD}",
            'events_needing_validation': events_needing_validation,
            'qa_queue': {
                'high_priority_events': high_priority_qa,
                'missing_sources': events_missing_sources,
                'total_backlog': qa_backlog
            }
        }
    except Exception as e:
        logger.error(f"Error getting current summary: {e}")
        return {}


@bp.route('/api/server/shutdown', methods=['POST'])
def graceful_shutdown():
    """Gracefully shutdown the Research Monitor server"""
    import app_v2

    # Check API key
    api_key = current_app.config.get('API_KEY')
    if api_key:
        provided_key = request.headers.get('X-API-Key')
        if provided_key != api_key:
            return jsonify({'error': 'Invalid or missing API key'}), 401

    try:
        # Stop the filesystem sync thread
        if app_v2.syncer:
            app_v2.syncer.stop()
            logger.info("Filesystem sync thread stopped")

        # Close database connections
        try:
            app_v2.Session.remove()
            app_v2.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.warning(f"Error closing database connections: {e}")

        # Schedule Flask server shutdown
        def shutdown_server():
            time.sleep(1)  # Give response time to be sent
            try:
                os.kill(os.getpid(), signal.SIGTERM)
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
        threading.Thread(target=shutdown_server).start()

        return jsonify({
            'status': 'shutting_down',
            'message': 'Research Monitor server is shutting down gracefully'
        })

    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Shutdown error: {str(e)}'
        }), 500


@bp.route('/api/server/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    import app_v2
    from sqlalchemy import text

    db = get_db()
    try:
        # Test database connection
        db.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    finally:
        db.close()

    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'session_id': app_v2.current_session_id,
        'events_since_commit': app_v2.events_since_commit,
        'timestamp': datetime.now().isoformat()
    })


@bp.route('/api/stats')
def get_stats():
    """Get system statistics"""
    import app_v2
    from models import TimelineEvent, EventMetadata, ResearchPriority

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
                'id': app_v2.current_session_id,
                'events_since_commit': app_v2.events_since_commit,
                'commit_threshold': app_v2.COMMIT_THRESHOLD
            }
        }
        return jsonify(stats)

    finally:
        db.close()


@bp.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached responses (admin endpoint)"""
    try:
        cache = current_app.config.get('CACHE')
        if cache:
            cache.clear()
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return jsonify({'error': 'Failed to clear cache'}), 500


@bp.route('/api/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics"""
    try:
        return jsonify({
            'cache_type': current_app.config.get('CACHE_TYPE', 'simple'),
            'default_timeout': current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
            'threshold': current_app.config.get('CACHE_THRESHOLD', 1000),
            'status': 'active'
        })
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return jsonify({'error': 'Failed to get cache stats'}), 500


@bp.route('/api/activity/recent', methods=['GET'])
def get_recent_activity():
    """Get recent research activity for monitoring dashboard"""
    from models import ActivityLog

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


@bp.route('/api/research/session', methods=['GET'])
def get_session_status():
    """Get current research session metrics"""
    import app_v2
    from models import ResearchSession, ResearchPriority, EventMetadata

    db = get_db()
    try:
        # Get current session
        session = db.query(ResearchSession).filter_by(session_id=app_v2.current_session_id).first()

        if not session:
            # Create default session if none exists
            session = ResearchSession(
                session_id=app_v2.current_session_id,
                commit_threshold=app_v2.COMMIT_THRESHOLD,
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
            'session_id': app_v2.current_session_id,
            'session_start': session.created_at.isoformat() + 'Z' if session.created_at else None,
            'events_this_session': session.events_created or 0,
            'priorities_completed': session.priorities_completed or 0,
            'commit_threshold': session.commit_threshold,
            'events_since_commit': app_v2.events_since_commit,
            'quality_trend': quality_trend,
            'active_priorities': active_priorities
        })

    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': 'Failed to get session status'}), 500
    finally:
        db.close()


# Static file serving routes
@bp.route('/')
def timeline_viewer():
    """Serve the main timeline viewer application"""
    return send_file('templates/index.html')


@bp.route('/viewer')
def timeline_viewer_alt():
    """Alternative route for timeline viewer"""
    return send_file('templates/index.html')


@bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static assets (CSS, JS, images)"""
    return send_from_directory('static', filename)


@bp.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    try:
        return send_from_directory('static/img', 'favicon.ico')
    except:
        # Return empty response if no favicon
        return '', 204


@bp.route('/manifest.json')
def manifest():
    """Serve PWA manifest"""
    try:
        return send_from_directory('static', 'manifest.json')
    except:
        # Return empty response if no manifest
        return '', 204
