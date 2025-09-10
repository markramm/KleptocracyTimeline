"""
Events API routes blueprint
"""

from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any

events_bp = Blueprint('events', __name__)


@events_bp.route('/', methods=['GET'])
def get_events():
    """Get all events or search events"""
    event_service = current_app.services['event_service']
    
    # Check for search query
    query = request.args.get('q')
    field = request.args.get('field')
    
    if query:
        events = event_service.search_events(query, field)
    else:
        events = event_service.get_all_events()
    
    return jsonify({
        'events': events,
        'count': len(events)
    })


@events_bp.route('/<event_id>', methods=['GET'])
def get_event(event_id: str):
    """Get a specific event by ID"""
    event_service = current_app.services['event_service']
    event = event_service.get_event_by_id(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    return jsonify(event)


@events_bp.route('/', methods=['POST'])
def create_event():
    """Create a new event"""
    event_service = current_app.services['event_service']
    validation_service = current_app.services['validation_service']
    database_service = current_app.services['database_service']
    
    event_data = request.get_json()
    
    if not event_data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate event
    validation_result = validation_service.validate_event(event_data)
    
    if not validation_result['valid']:
        return jsonify({
            'error': 'Validation failed',
            'validation': validation_result
        }), 400
    
    # Create event
    success, result = event_service.create_event(event_data)
    
    if success:
        # Log validation
        database_service.log_validation(
            event_data.get('id', 'unknown'),
            validation_result['score'],
            len(validation_result['errors'])
        )
        # Log activity
        database_service.log_activity('event_created', event_data.get('id'))
        
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@events_bp.route('/<event_id>', methods=['PUT'])
def update_event(event_id: str):
    """Update an existing event"""
    event_service = current_app.services['event_service']
    validation_service = current_app.services['validation_service']
    database_service = current_app.services['database_service']
    
    event_data = request.get_json()
    
    if not event_data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate event
    validation_result = validation_service.validate_event(event_data)
    
    if not validation_result['valid']:
        return jsonify({
            'error': 'Validation failed',
            'validation': validation_result
        }), 400
    
    # Update event
    success, result = event_service.update_event(event_id, event_data)
    
    if success:
        # Log validation
        database_service.log_validation(
            event_id,
            validation_result['score'],
            len(validation_result['errors'])
        )
        # Log activity
        database_service.log_activity('event_updated', event_id)
        
        return jsonify(result)
    else:
        return jsonify(result), 404


@events_bp.route('/<event_id>', methods=['DELETE'])
def delete_event(event_id: str):
    """Delete an event"""
    event_service = current_app.services['event_service']
    database_service = current_app.services['database_service']
    
    success, result = event_service.delete_event(event_id)
    
    if success:
        # Log activity
        database_service.log_activity('event_deleted', event_id)
        return jsonify(result)
    else:
        return jsonify(result), 404


@events_bp.route('/batch', methods=['POST'])
def batch_create_events():
    """Create multiple events in batch"""
    event_service = current_app.services['event_service']
    validation_service = current_app.services['validation_service']
    database_service = current_app.services['database_service']
    
    data = request.get_json()
    events = data.get('events', [])
    
    if not events:
        return jsonify({'error': 'No events provided'}), 400
    
    results = []
    created_count = 0
    failed_count = 0
    
    for event_data in events:
        # Validate event
        validation_result = validation_service.validate_event(event_data)
        
        if validation_result['valid']:
            success, result = event_service.create_event(event_data)
            if success:
                created_count += 1
                results.append({
                    'id': event_data.get('id'),
                    'status': 'created',
                    'validation_score': validation_result['score']
                })
                # Log validation
                database_service.log_validation(
                    event_data.get('id', 'unknown'),
                    validation_result['score'],
                    len(validation_result['errors'])
                )
            else:
                failed_count += 1
                results.append({
                    'id': event_data.get('id'),
                    'status': 'failed',
                    'error': result.get('error')
                })
        else:
            failed_count += 1
            results.append({
                'id': event_data.get('id'),
                'status': 'validation_failed',
                'errors': validation_result['errors']
            })
    
    # Log activity
    database_service.log_activity(
        'batch_create',
        f'Created: {created_count}, Failed: {failed_count}'
    )
    
    return jsonify({
        'created': created_count,
        'failed': failed_count,
        'results': results
    }), 201 if created_count > 0 else 400