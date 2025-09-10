"""
Validation API routes blueprint
"""

from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any

validation_bp = Blueprint('validation', __name__)


@validation_bp.route('/validate', methods=['POST'])
def validate_event():
    """Validate a single event"""
    validation_service = current_app.services['validation_service']
    
    event_data = request.get_json()
    
    if not event_data:
        return jsonify({'error': 'No data provided'}), 400
    
    validation_result = validation_service.validate_event(event_data)
    
    return jsonify(validation_result)


@validation_bp.route('/validate/batch', methods=['POST'])
def validate_batch():
    """Validate multiple events"""
    validation_service = current_app.services['validation_service']
    database_service = current_app.services['database_service']
    
    data = request.get_json()
    events = data.get('events', [])
    
    if not events:
        return jsonify({'error': 'No events provided'}), 400
    
    batch_result = validation_service.validate_batch(events)
    
    # Log activity
    database_service.log_activity(
        'batch_validation',
        f'Validated {len(events)} events, {batch_result["valid_events"]} valid'
    )
    
    return jsonify(batch_result)


@validation_bp.route('/validate/all', methods=['GET'])
def validate_all_events():
    """Validate all events in the timeline"""
    event_service = current_app.services['event_service']
    validation_service = current_app.services['validation_service']
    database_service = current_app.services['database_service']
    
    # Get all events
    events = event_service.get_all_events()
    
    if not events:
        return jsonify({
            'error': 'No events found',
            'total_events': 0
        })
    
    # Validate batch
    batch_result = validation_service.validate_batch(events)
    
    # Log each validation
    for event, result in zip(events, batch_result['results']):
        database_service.log_validation(
            event.get('id', 'unknown'),
            result['score'],
            result['error_count']
        )
    
    # Log activity
    database_service.log_activity(
        'full_validation',
        f'Validated all {len(events)} events'
    )
    
    return jsonify(batch_result)


@validation_bp.route('/history', methods=['GET'])
def get_validation_history():
    """Get validation history"""
    database_service = current_app.services['database_service']
    
    event_id = request.args.get('event_id')
    history = database_service.get_validation_history(event_id)
    
    return jsonify({
        'history': history,
        'count': len(history)
    })


@validation_bp.route('/score/<event_id>', methods=['GET'])
def get_event_score(event_id: str):
    """Get validation score for a specific event"""
    event_service = current_app.services['event_service']
    validation_service = current_app.services['validation_service']
    
    event = event_service.get_event_by_id(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    validation_result = validation_service.validate_event(event)
    
    return jsonify({
        'event_id': event_id,
        'score': validation_result['score'],
        'valid': validation_result['valid'],
        'error_count': len(validation_result['errors'])
    })


@validation_bp.route('/stats', methods=['GET'])
def get_validation_stats():
    """Get validation statistics"""
    event_service = current_app.services['event_service']
    validation_service = current_app.services['validation_service']
    
    events = event_service.get_all_events()
    
    if not events:
        return jsonify({
            'total_events': 0,
            'valid_events': 0,
            'invalid_events': 0,
            'average_score': 0
        })
    
    valid_count = 0
    total_score = 0
    error_distribution = {}
    
    for event in events:
        result = validation_service.validate_event(event)
        if result['valid']:
            valid_count += 1
        total_score += result['score']
        
        # Track error types
        for error in result['errors']:
            error_type = error.split(':')[0] if ':' in error else error
            error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
    
    return jsonify({
        'total_events': len(events),
        'valid_events': valid_count,
        'invalid_events': len(events) - valid_count,
        'average_score': total_score / len(events) if events else 0,
        'validation_rate': valid_count / len(events) if events else 0,
        'error_distribution': error_distribution
    })


@validation_bp.route('/fix/<event_id>', methods=['POST'])
def fix_event(event_id: str):
    """Apply suggested fixes to an event"""
    event_service = current_app.services['event_service']
    validation_service = current_app.services['validation_service']
    database_service = current_app.services['database_service']
    
    event = event_service.get_event_by_id(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Get validation result with suggestions
    validation_result = validation_service.validate_event(event)
    
    if validation_result['valid']:
        return jsonify({
            'message': 'Event is already valid',
            'score': validation_result['score']
        })
    
    # Apply automatic fixes where possible
    fixed_event = event.copy()
    fixes_applied = []
    
    for suggestion in validation_result['suggestions']:
        if 'Convert sources to new format' in suggestion:
            # Convert legacy source format
            if isinstance(event.get('sources', []), list) and event['sources']:
                if isinstance(event['sources'][0], str):
                    fixed_event['sources'] = [
                        {'title': f'Source {i+1}', 'url': url}
                        for i, url in enumerate(event['sources'])
                    ]
                    fixes_applied.append('Converted sources to new format')
        
        if 'Add more actors' in suggestion:
            # Can't automatically add actors
            fixes_applied.append('Manual fix required: Add more actors')
        
        if 'Provide at least 2 sources' in suggestion:
            # Can't automatically add sources
            fixes_applied.append('Manual fix required: Add more sources')
    
    # Update event if fixes were applied
    if any('Manual' not in fix for fix in fixes_applied):
        success, result = event_service.update_event(event_id, fixed_event)
        
        if success:
            # Revalidate
            new_validation = validation_service.validate_event(fixed_event)
            
            # Log activity
            database_service.log_activity(
                'event_fixed',
                f'{event_id}: {", ".join(fixes_applied)}'
            )
            
            return jsonify({
                'message': 'Fixes applied',
                'fixes_applied': fixes_applied,
                'old_score': validation_result['score'],
                'new_score': new_validation['score'],
                'valid': new_validation['valid']
            })
    
    return jsonify({
        'message': 'Some fixes require manual intervention',
        'fixes_applied': fixes_applied,
        'suggestions': validation_result['suggestions']
    })