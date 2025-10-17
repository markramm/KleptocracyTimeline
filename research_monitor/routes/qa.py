"""
routes/qa.py - Quality Assurance Workflow Endpoints

Provides comprehensive QA workflow for timeline events:
- QA queue management and prioritization
- Event validation and enhancement
- Batch processing support
- Validation audit trail management
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timezone, timedelta
import os
import json
import logging

# Import shared utilities
from research_monitor.blueprint_utils import get_db, require_api_key, cache_with_invalidation

logger = logging.getLogger(__name__)

bp = Blueprint('qa', __name__, url_prefix='/api/qa')

def get_cache():
    """Get cache from config (blueprint-specific helper)"""
    return current_app.config.get('CACHE')

# ==================== QA QUEUE ENDPOINTS ====================

@bp.route('/queue')
@cache_with_invalidation(timeout=120, key_prefix='qa_queue')
def get_qa_queue():
    """Get prioritized queue of events needing QA"""
    from research_monitor.qa_queue_system import QAQueueManager

    db = get_db()
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 100)
        batch_size = int(request.args.get('batch_size', limit))  # Support batch_size parameter
        offset = int(request.args.get('offset', 0))
        min_importance = int(request.args.get('min_importance', 1))
        include_validated = request.args.get('include_validated', 'false').lower() == 'true'

        # Use batch_size if provided, otherwise use limit
        actual_limit = min(batch_size, limit)

        # Get QA queue
        qa_manager = QAQueueManager(db)
        qa_queue = qa_manager.get_qa_queue(
            limit=actual_limit,
            offset=offset,
            min_importance=min_importance,
            include_validated=include_validated
        )

        return jsonify({
            'qa_queue': qa_queue,
            'count': len(qa_queue),
            'limit': limit,
            'offset': offset,
            'filters': {
                'min_importance': min_importance,
                'include_validated': include_validated
            }
        })

    except Exception as e:
        logger.error(f"Error getting QA queue: {e}")
        return jsonify({'error': 'Failed to get QA queue'}), 500
    finally:
        db.close()

@bp.route('/next')
@cache_with_invalidation(timeout=60, key_prefix='qa_next')
def get_next_qa_event():
    """Get the next highest priority event for QA"""
    from research_monitor.qa_queue_system import QAQueueManager

    db = get_db()
    try:
        min_importance = int(request.args.get('min_importance', 7))

        qa_manager = QAQueueManager(db)
        next_event = qa_manager.get_next_qa_event(min_importance=min_importance)

        if next_event:
            return jsonify(next_event)
        else:
            return jsonify({'message': 'No events available for QA'}), 404

    except Exception as e:
        logger.error(f"Error getting next QA event: {e}")
        return jsonify({'error': 'Failed to get next QA event'}), 500
    finally:
        db.close()

@bp.route('/stats')
@cache_with_invalidation(timeout=300, key_prefix='qa_stats')
def get_qa_stats():
    """Get comprehensive QA statistics"""
    from research_monitor.qa_queue_system import QAQueueManager

    db = get_db()
    try:
        qa_manager = QAQueueManager(db)
        stats = qa_manager.get_qa_stats()

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error getting QA stats: {e}")
        return jsonify({'error': 'Failed to get QA stats'}), 500
    finally:
        db.close()

# ==================== EVENT VALIDATION ENDPOINTS ====================

@bp.route('/validate/<event_id>', methods=['POST'])
@require_api_key
def mark_event_validated(event_id):
    """Mark an event as validated with quality score"""
    from research_monitor.qa_queue_system import QAQueueManager
    from research_monitor.models import ActivityLog

    db = get_db()
    try:
        data = request.json or {}
        quality_score = data.get('quality_score')
        validation_notes = data.get('validation_notes', '')
        created_by = data.get('created_by', 'qa-agent')

        if quality_score is None:
            return jsonify({'error': 'quality_score is required'}), 400

        if not (0 <= quality_score <= 10):
            return jsonify({'error': 'quality_score must be between 0 and 10'}), 400

        qa_manager = QAQueueManager(db)
        success = qa_manager.mark_event_validated(
            event_id=event_id,
            quality_score=quality_score,
            validation_notes=validation_notes,
            created_by=created_by
        )

        if success:
            # Log the validation activity
            activity = ActivityLog(
                action='event_validated',
                event_id=event_id,
                agent=created_by,
                details={
                    'quality_score': quality_score,
                    'validation_notes': validation_notes
                }
            )
            db.add(activity)
            db.commit()

            # Invalidate cache
            cache = get_cache()
            if cache:
                cache.clear()

            return jsonify({
                'status': 'success',
                'event_id': event_id,
                'quality_score': quality_score,
                'validation_notes': validation_notes
            })
        else:
            return jsonify({'error': 'Failed to mark event as validated'}), 500

    except Exception as e:
        logger.error(f"Error validating event {event_id}: {e}")
        return jsonify({'error': 'Failed to validate event'}), 500
    finally:
        db.close()

@bp.route('/enhance/<event_id>', methods=['POST'])
@require_api_key
def enhance_event_with_qa(event_id):
    """Enhance an event with improved content and record QA metadata"""
    from research_monitor.qa_queue_system import QAQueueManager
    from research_monitor.models import TimelineEvent, ActivityLog
    from research_monitor import app_v2

    db = get_db()
    try:
        data = request.json or {}
        enhanced_event = data.get('enhanced_event')
        quality_score = data.get('quality_score')
        validation_notes = data.get('validation_notes', '')
        created_by = data.get('created_by', 'qa-agent')

        if not enhanced_event:
            return jsonify({
                'error': 'enhanced_event is required',
                'help': 'POST body must include: {"enhanced_event": {...}, "quality_score": 8.5, "validation_notes": "..."}'
            }), 400

        if quality_score is None:
            return jsonify({
                'error': 'quality_score is required',
                'help': 'Include quality_score (0-10) in POST body, e.g., "quality_score": 8.5'
            }), 400

        if not (0 <= quality_score <= 10):
            return jsonify({
                'error': 'quality_score must be between 0 and 10',
                'received': quality_score,
                'help': 'Use quality_score between 0-10, e.g., 8.5 for high-quality sources'
            }), 400

        # Validate enhanced event structure
        validation_result = app_v2.validate_timeline_event(enhanced_event)

        if not validation_result['valid']:
            return jsonify({
                'error': 'Enhanced event validation failed',
                'validation_errors': validation_result['errors']
            }), 400

        # Ensure event ID matches
        if enhanced_event.get('id') != event_id:
            return jsonify({
                'error': 'Event ID mismatch',
                'url_event_id': event_id,
                'enhanced_event_id': enhanced_event.get('id'),
                'help': 'The enhanced_event.id must match the event_id in the URL'
            }), 400

        # Check if original event exists
        original_event = db.query(TimelineEvent).filter_by(id=event_id).first()
        if not original_event:
            return jsonify({
                'error': 'Original event not found',
                'event_id': event_id,
                'help': 'Event must exist in the database before enhancement. Check event ID format: YYYY-MM-DD--slug'
            }), 404

        # Save enhanced event to filesystem
        event_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                     'timeline_data', 'events', f'{event_id}.json')

        try:
            with open(event_file_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_event, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save enhanced event to filesystem: {e}")
            return jsonify({'error': 'Failed to save enhanced event'}), 500

        # Record QA metadata
        qa_manager = QAQueueManager(db)
        success = qa_manager.mark_event_validated(
            event_id=event_id,
            quality_score=quality_score,
            validation_notes=validation_notes,
            created_by=created_by
        )

        if success:
            # Log the enhancement activity
            activity = ActivityLog(
                action='event_enhanced',
                event_id=event_id,
                agent=created_by,
                details={
                    'quality_score': quality_score,
                    'validation_notes': validation_notes,
                    'enhancements': 'Event content and sources enhanced'
                }
            )
            db.add(activity)

            # Update commit counter since we modified a file
            app_v2.events_since_commit += 1

            db.commit()

            # Invalidate cache
            cache = get_cache()
            if cache:
                cache.clear()

            return jsonify({
                'status': 'success',
                'event_id': event_id,
                'quality_score': quality_score,
                'validation_notes': validation_notes,
                'enhanced': True,
                'file_updated': True
            })
        else:
            return jsonify({'error': 'Failed to record QA metadata'}), 500

    except Exception as e:
        logger.error(f"Error enhancing event {event_id}: {e}")
        return jsonify({'error': 'Failed to enhance event'}), 500
    finally:
        db.close()

@bp.route('/issues/<issue_type>')
@cache_with_invalidation(timeout=180, key_prefix='qa_issues')
def get_qa_candidates_by_issue(issue_type):
    """Get events with specific QA issues"""
    from research_monitor.qa_queue_system import QAQueueManager

    db = get_db()
    try:
        limit = min(int(request.args.get('limit', 20)), 50)

        qa_manager = QAQueueManager(db)
        candidates = qa_manager.get_qa_candidates_by_issue(issue_type, limit)

        return jsonify({
            'issue_type': issue_type,
            'candidates': candidates,
            'count': len(candidates),
            'limit': limit
        })

    except Exception as e:
        logger.error(f"Error getting QA candidates for issue {issue_type}: {e}")
        return jsonify({'error': 'Failed to get QA candidates'}), 500
    finally:
        db.close()

@bp.route('/reject/<event_id>', methods=['POST'])
@require_api_key
def mark_event_rejected(event_id):
    """Mark an event as rejected with detailed reasoning"""
    from research_monitor.qa_queue_system import QAQueueManager
    from research_monitor.models import ActivityLog

    db = get_db()
    try:
        data = request.json or {}
        rejection_reason = data.get('rejection_reason', '')
        created_by = data.get('created_by', 'qa-agent')

        if not rejection_reason.strip():
            return jsonify({'error': 'rejection_reason is required and cannot be empty'}), 400

        qa_manager = QAQueueManager(db)
        success = qa_manager.mark_event_rejected(
            event_id=event_id,
            rejection_reason=rejection_reason,
            created_by=created_by
        )

        if success:
            # Log the rejection activity
            activity = ActivityLog(
                action='event_rejected',
                event_id=event_id,
                agent=created_by,
                details={
                    'rejection_reason': rejection_reason
                }
            )
            db.add(activity)
            db.commit()

            # Invalidate cache
            cache = get_cache()
            if cache:
                cache.clear()

            return jsonify({
                'status': 'success',
                'event_id': event_id,
                'rejection_reason': rejection_reason
            }), 200
        else:
            return jsonify({'error': 'Failed to reject event'}), 500

    except Exception as e:
        logger.error(f"Error rejecting event {event_id}: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    finally:
        db.close()

@bp.route('/start/<event_id>', methods=['POST'])
@require_api_key
def mark_event_in_progress(event_id):
    """Mark an event as in_progress to prevent duplicate processing"""
    from research_monitor.qa_queue_system import QAQueueManager
    from research_monitor.models import ActivityLog

    db = get_db()
    try:
        data = request.json or {}
        created_by = data.get('created_by', 'qa-agent')
        agent_id = data.get('agent_id', created_by)

        qa_manager = QAQueueManager(db)
        success = qa_manager.mark_event_in_progress(event_id, created_by, agent_id)

        if success:
            # Log the activity
            activity = ActivityLog(
                action='event_started',
                event_id=event_id,
                agent=created_by,
                details={
                    'agent_id': agent_id,
                    'status': 'in_progress'
                }
            )
            db.add(activity)
            db.commit()

            # Invalidate cache
            cache = get_cache()
            if cache:
                cache.clear()

            return jsonify({
                'status': 'success',
                'event_id': event_id,
                'assigned_to': agent_id,
                'validation_status': 'in_progress'
            }), 200
        else:
            return jsonify({'error': 'Failed to mark event as in_progress or already being processed'}), 400

    except Exception as e:
        logger.error(f"Error marking event {event_id} as in_progress: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    finally:
        db.close()

@bp.route('/score', methods=['POST'])
def calculate_qa_score():
    """Calculate QA priority score for event data"""
    from research_monitor.qa_queue_system import QAQueueManager

    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Event data required'}), 400

        event_data = data.get('event', {})
        metadata = data.get('metadata')

        # Create temporary QA manager (no DB needed for scoring)
        qa_manager = QAQueueManager(None)
        score, breakdown = qa_manager.calculate_qa_priority_score(event_data, metadata)

        return jsonify({
            'qa_priority_score': score,
            'score_breakdown': breakdown,
            'event_id': event_data.get('id', 'unknown')
        })

    except Exception as e:
        logger.error(f"Error calculating QA score: {e}")
        return jsonify({'error': 'Failed to calculate QA score'}), 500

# ==================== VALIDATION AUDIT TRAIL ENDPOINTS ====================

@bp.route('/validation/initialize', methods=['POST'])
@require_api_key
def initialize_validation_audit_trail():
    """Initialize metadata records for all events to create complete validation audit trail"""
    from research_monitor.qa_queue_system import QAQueueManager

    db = get_db()
    try:
        data = request.json or {}
        created_by = data.get('created_by', 'api-init')
        dry_run = data.get('dry_run', False)

        qa_manager = QAQueueManager(db)
        result = qa_manager.initialize_validation_audit_trail(created_by, dry_run)

        # Invalidate QA-related caches if not dry run
        if not dry_run:
            cache = get_cache()
            if cache:
                cache.clear()

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error initializing validation audit trail: {e}")
        return jsonify({'error': 'Failed to initialize validation audit trail'}), 500
    finally:
        if db:
            db.close()

@bp.route('/validation/reset', methods=['POST'])
@require_api_key
def reset_validation_audit_trail():
    """Reset all validation records to pending status for complete re-validation"""
    from research_monitor.qa_queue_system import QAQueueManager

    db = get_db()
    try:
        data = request.json or {}
        created_by = data.get('created_by', 'api-reset')
        dry_run = data.get('dry_run', False)

        qa_manager = QAQueueManager(db)
        result = qa_manager.reset_validation_audit_trail(created_by, dry_run)

        # Invalidate QA-related caches if not dry run
        if not dry_run:
            cache = get_cache()
            if cache:
                cache.clear()

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error resetting validation audit trail: {e}")
        return jsonify({'error': 'Failed to reset validation audit trail'}), 500
    finally:
        if db:
            db.close()

@bp.route('/rejected')
def get_rejected_events():
    """Get rejected events for audit purposes"""
    from research_monitor.qa_queue_system import QAQueueManager

    db = None
    try:
        db = get_db()
        qa_manager = QAQueueManager(db)

        # Get parameters
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = int(request.args.get('offset', 0))

        # Get rejected events
        rejected_events = qa_manager.get_rejected_events(limit=limit, offset=offset)

        return jsonify({
            'rejected_events': rejected_events,
            'count': len(rejected_events),
            'limit': limit,
            'offset': offset,
            'filters': {
                'validation_status': 'rejected'
            }
        })

    except Exception as e:
        logger.error(f"Error getting rejected events: {e}")
        return jsonify({'error': 'Failed to get rejected events'}), 500
    finally:
        if db:
            db.close()

# ==================== BATCH PROCESSING ENDPOINTS ====================

@bp.route('/batch/reserve', methods=['POST'])
@require_api_key
def reserve_qa_batch():
    """Reserve a batch of events for QA processing to prevent duplicate work"""
    from research_monitor.qa_queue_system import QAQueueManager

    db = get_db()
    try:
        qa_manager = QAQueueManager(db)

        # Get request parameters
        data = request.get_json() or {}
        batch_size = min(int(data.get('batch_size', 5)), 20)  # Max 20 events per batch
        agent_id = data.get('agent_id')
        min_importance = int(data.get('min_importance', 1))

        if not agent_id:
            agent_id = f"qa-agent-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:17]}"

        # Release any expired reservations first
        expired_count = qa_manager.release_expired_qa_reservations()
        if expired_count > 0:
            logger.info(f"Released {expired_count} expired QA reservations before batch reservation")

        # Reserve batch of events
        reserved_events = qa_manager.reserve_qa_batch(
            batch_size=batch_size,
            agent_id=agent_id,
            min_importance=min_importance
        )

        if not reserved_events:
            return jsonify({
                'message': 'No events available for QA batch reservation',
                'error': 'queue_empty'
            }), 404

        return jsonify({
            'reserved_events': reserved_events,
            'count': len(reserved_events),
            'agent_id': agent_id,
            'batch_size': batch_size,
            'reservation_expires': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            'status': 'reserved'
        })

    except Exception as e:
        logger.error(f"Error reserving QA batch: {e}")
        return jsonify({'error': 'Failed to reserve QA batch', 'message': str(e)}), 500
    finally:
        db.close()

@bp.route('/batch/release', methods=['POST'])
@require_api_key
def release_expired_qa_reservations():
    """Manually release expired QA reservations"""
    from research_monitor.qa_queue_system import QAQueueManager

    db = get_db()
    try:
        qa_manager = QAQueueManager(db)
        released_count = qa_manager.release_expired_qa_reservations()

        return jsonify({
            'released_count': released_count,
            'message': f'Released {released_count} expired QA reservations'
        })

    except Exception as e:
        logger.error(f"Error releasing expired QA reservations: {e}")
        return jsonify({'error': 'Failed to release reservations', 'message': str(e)}), 500
    finally:
        db.close()
