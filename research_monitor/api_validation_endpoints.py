"""
API Validation Endpoints - Strict validation for event submissions
To be integrated into app_v2.py or used as app_v3.py
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import json
from event_validator import EventValidator

# Create validation blueprint
validation_bp = Blueprint('validation', __name__)

# Initialize validator
validator = EventValidator()

@validation_bp.route('/api/events/validate', methods=['POST'])
def validate_event_endpoint():
    """
    Validate an event without saving it
    Returns validation results and suggestions
    """
    try:
        event = request.json
        
        if not event:
            return jsonify({
                'success': False,
                'error': 'No event data provided'
            }), 400
        
        # Perform validation
        is_valid, errors, metadata = validator.validate_event(event)
        
        # Get fix suggestions
        suggestions = validator.suggest_fixes(event, errors) if errors else {}
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'validation_score': metadata['validation_score'],
            'errors': errors,
            'metadata': metadata,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@validation_bp.route('/api/events/submit-validated', methods=['POST'])
def submit_validated_event():
    """
    Submit an event with strict validation
    Event is rejected if validation score < 0.7
    """
    try:
        event = request.json
        
        if not event:
            return jsonify({
                'success': False,
                'error': 'No event data provided'
            }), 400
        
        # Validate the event
        is_valid, errors, metadata = validator.validate_event(event)
        
        # Check validation score threshold
        min_score = 0.7
        if metadata['validation_score'] < min_score:
            return jsonify({
                'success': False,
                'error': f'Validation score {metadata["validation_score"]:.2f} below minimum {min_score}',
                'validation_errors': errors,
                'suggestions': validator.suggest_fixes(event, errors)
            }), 400
        
        # Check for critical errors
        critical_errors = [e for e in errors if any(
            critical in e.lower() for critical in ['missing required', 'invalid date', 'empty required']
        )]
        
        if critical_errors:
            return jsonify({
                'success': False,
                'error': 'Critical validation errors found',
                'critical_errors': critical_errors,
                'all_errors': errors,
                'suggestions': validator.suggest_fixes(event, errors)
            }), 400
        
        # Add validation metadata to event
        event['validation_status'] = 'validated' if is_valid else 'partial'
        event['validation_score'] = metadata['validation_score']
        event['last_validated'] = datetime.now(timezone.utc).isoformat()
        event['validation_metadata'] = metadata
        
        # In production: Save to database
        # db.session.add(event)
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event submitted successfully',
            'event_id': event.get('id'),
            'validation_score': metadata['validation_score'],
            'warnings': errors if errors else []
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@validation_bp.route('/api/events/<event_id>/enhance', methods=['POST'])
def request_event_enhancement(event_id):
    """
    Add an event to the validation/enhancement queue
    """
    try:
        data = request.json or {}
        
        priority = data.get('priority', 5)
        reason = data.get('reason', 'Manual enhancement request')
        validation_type = data.get('type', 'full')  # full, sources, actors, dates, enhance
        
        # In production: Add to validation queue
        queue_entry = {
            'event_id': event_id,
            'added_at': datetime.now(timezone.utc).isoformat(),
            'priority': priority,
            'validation_type': validation_type,
            'reason': reason,
            'status': 'pending'
        }
        
        # In production: Save to database
        # db.session.add(EventValidationQueue(**queue_entry))
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Event {event_id} added to enhancement queue',
            'queue_entry': queue_entry
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@validation_bp.route('/api/validation/queue', methods=['GET'])
def get_validation_queue():
    """
    Get events in the validation queue
    """
    try:
        # In production: Query from database
        # queue = db.session.query(EventValidationQueue)\
        #     .filter_by(status='pending')\
        #     .order_by(EventValidationQueue.priority.desc())\
        #     .limit(10)\
        #     .all()
        
        # Demo response
        queue = []
        
        return jsonify({
            'success': True,
            'queue_size': len(queue),
            'events': queue
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@validation_bp.route('/api/validation/stats', methods=['GET'])
def get_validation_stats():
    """
    Get validation statistics
    """
    try:
        # In production: Query from database
        stats = {
            'total_events': 1298,
            'validated_events': 0,
            'partial_validated': 0,
            'unvalidated': 1298,
            'average_score': 0.0,
            'queue_size': 0,
            'enhancements_today': 0,
            'enhancements_total': 0
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@validation_bp.route('/api/events/<event_id>/validation-history', methods=['GET'])
def get_event_validation_history(event_id):
    """
    Get validation history for a specific event
    """
    try:
        # In production: Query from database
        # history = db.session.query(ValidationHistory)\
        #     .filter_by(event_id=event_id)\
        #     .order_by(ValidationHistory.timestamp.desc())\
        #     .all()
        
        history = []
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'history_count': len(history),
            'history': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def register_validation_endpoints(app):
    """
    Register validation endpoints with the Flask app
    """
    app.register_blueprint(validation_bp)
    print("✅ Validation endpoints registered")
    
    # Add validation info to root endpoint
    @app.route('/api/validation/info')
    def validation_info():
        return jsonify({
            'validation_enabled': True,
            'minimum_score': 0.7,
            'required_fields': EventValidator.REQUIRED_FIELDS,
            'valid_statuses': EventValidator.VALID_STATUSES,
            'endpoints': [
                '/api/events/validate',
                '/api/events/submit-validated',
                '/api/events/<id>/enhance',
                '/api/validation/queue',
                '/api/validation/stats',
                '/api/events/<id>/validation-history'
            ]
        })