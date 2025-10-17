"""
Validation Runs Blueprint

Validation run lifecycle management, validation logs, and event update failure tracking.

Routes:
- GET  /api/validation-runs - List validation runs with filtering
- POST /api/validation-runs - Create new validation run
- GET  /api/validation-runs/<run_id> - Get validation run details
- GET  /api/validation-runs/<run_id>/next - Get next event to validate
- POST /api/validation-runs/<run_id>/events/<run_event_id>/complete - Complete validation
- POST /api/validation-runs/<run_id>/requeue-needs-work - Requeue needs-work events
- POST /api/validation-logs - Create validation log
- GET  /api/validation-logs - List validation logs
- GET  /api/event-update-failures - List event update failures
- GET  /api/event-update-failures/stats - Failure statistics
"""

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func, desc
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('validation_runs', __name__, url_prefix='/api')


def get_db():
    """Get database session from app_v2 module"""
    from research_monitor import app_v2
    return app_v2.get_db()


def require_api_key(f):
    """API key authentication decorator"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        from research_monitor import app_v2
        # Get the actual decorator from app_v2 and apply it
        api_key_decorator = app_v2.require_api_key
        return api_key_decorator(f)(*args, **kwargs)

    return decorated_function


# ==================== VALIDATION RUNS ====================

@bp.route('/validation-runs', methods=['GET'])
def list_validation_runs():
    """List all validation runs with optional filtering"""
    from research_monitor.models import ValidationRun

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


@bp.route('/validation-runs', methods=['POST'])
@require_api_key
def create_validation_run():
    """Create a new validation run using different sampling strategies"""
    from research_monitor.validation_run_calculator import ValidationRunCalculator

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


@bp.route('/validation-runs/<int:run_id>')
def get_validation_run(run_id):
    """Get detailed information about a specific validation run"""
    from research_monitor.validation_run_calculator import ValidationRunCalculator

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


@bp.route('/validation-runs/<int:run_id>/next')
def get_next_validation_event(run_id):
    """Get the next event to validate from a validation run"""
    from research_monitor.validation_run_calculator import ValidationRunCalculator
    from research_monitor.models import TimelineEvent

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


@bp.route('/validation-runs/<int:run_id>/events/<int:run_event_id>/complete', methods=['POST'])
@require_api_key
def complete_validation_run_event(run_id, run_event_id):
    """Mark a validation run event as completed"""
    from research_monitor.validation_run_calculator import ValidationRunCalculator

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


@bp.route('/validation-runs/<int:run_id>/requeue-needs-work', methods=['POST'])
@require_api_key
def requeue_needs_work_events(run_id):
    """Requeue events marked as 'needs_work' back to pending status for re-assignment"""
    from research_monitor.validation_run_calculator import ValidationRunCalculator

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


# ==================== VALIDATION LOGS ====================

@bp.route('/validation-logs', methods=['POST'])
@require_api_key
def create_validation_log():
    """Create a new validation log entry for an event"""
    from research_monitor.models import ValidationLog
    from research_monitor import app_v2

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
        app_v2.write_validation_log_to_filesystem(validation_log_data)

        # Auto-apply corrections if provided and status is validated
        corrections_applied = False
        if status == 'validated' and data.get('corrections_made') and data.get('auto_apply', True):
            try:
                corrections_applied = app_v2.apply_validation_corrections(
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


@bp.route('/validation-logs')
def list_validation_logs():
    """List validation logs with optional filtering"""
    from research_monitor.models import ValidationLog

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


# ==================== EVENT UPDATE FAILURES ====================

@bp.route('/event-update-failures')
def list_event_update_failures():
    """List event update failures with optional filtering"""
    from research_monitor.models import EventUpdateFailure

    db = get_db()
    try:
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


@bp.route('/event-update-failures/stats')
def event_update_failure_stats():
    """Get statistics about event update failures"""
    from research_monitor.models import EventUpdateFailure

    db = get_db()
    try:
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
