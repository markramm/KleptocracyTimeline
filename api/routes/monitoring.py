"""
Monitoring API routes blueprint
"""

from flask import Blueprint, jsonify, current_app
from datetime import datetime, timezone
import os
from pathlib import Path

monitoring_bp = Blueprint('monitoring', __name__)


@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'timeline-api',
        'version': '1.0.0'
    })


@monitoring_bp.route('/status', methods=['GET'])
def get_status():
    """Get system status"""
    event_service = current_app.services['event_service']
    database_service = current_app.services['database_service']
    
    # Count events
    events = event_service.get_all_events()
    
    # Get recent activity
    recent_activity = database_service.get_validation_history()[:5]
    
    # Check filesystem
    timeline_dir = Path(current_app.config['TIMELINE_DIR'])
    
    return jsonify({
        'status': 'operational',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'statistics': {
            'total_events': len(events),
            'timeline_directory': str(timeline_dir),
            'timeline_exists': timeline_dir.exists(),
            'database_url': current_app.config['DATABASE_URL'].split('/')[-1],  # Just filename
        },
        'recent_activity': recent_activity,
        'configuration': {
            'debug': current_app.config.get('DEBUG', False),
            'testing': current_app.config.get('TESTING', False),
            'api_port': current_app.config.get('API_PORT', 5000)
        }
    })


@monitoring_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get application metrics"""
    event_service = current_app.services['event_service']
    validation_service = current_app.services['validation_service']
    
    events = event_service.get_all_events()
    
    # Calculate metrics
    total_events = len(events)
    valid_events = 0
    total_score = 0
    total_actors = 0
    total_sources = 0
    total_tags = set()
    
    for event in events:
        result = validation_service.validate_event(event)
        if result['valid']:
            valid_events += 1
        total_score += result['score']
        
        # Count entities
        total_actors += len(event.get('actors', []))
        total_sources += len(event.get('sources', []))
        total_tags.update(event.get('tags', []))
    
    return jsonify({
        'events': {
            'total': total_events,
            'valid': valid_events,
            'invalid': total_events - valid_events,
            'average_score': total_score / total_events if total_events else 0
        },
        'entities': {
            'total_actors': total_actors,
            'average_actors_per_event': total_actors / total_events if total_events else 0,
            'total_sources': total_sources,
            'average_sources_per_event': total_sources / total_events if total_events else 0,
            'unique_tags': len(total_tags)
        },
        'validation': {
            'pass_rate': valid_events / total_events if total_events else 0,
            'average_score': total_score / total_events if total_events else 0
        },
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@monitoring_bp.route('/config', methods=['GET'])
def get_config():
    """Get current configuration (non-sensitive)"""
    return jsonify({
        'environment': 'development' if current_app.config.get('DEBUG') else 'production',
        'timeline_directory': str(current_app.config.get('TIMELINE_DIR')),
        'api_port': current_app.config.get('API_PORT', 5000),
        'cors_origins': current_app.config.get('CORS_ORIGINS', '*'),
        'testing': current_app.config.get('TESTING', False),
        'debug': current_app.config.get('DEBUG', False)
    })


@monitoring_bp.route('/services', methods=['GET'])
def get_services():
    """Get status of all services"""
    services_status = {}
    
    # Check each service
    for service_name, service in current_app.services.items():
        try:
            # Try to use the service
            if service_name == 'event_service':
                # Try to count events
                service.get_all_events()
                services_status[service_name] = 'operational'
            elif service_name == 'validation_service':
                # Try to validate empty event
                service.validate_event({})
                services_status[service_name] = 'operational'
            elif service_name == 'file_service':
                # Try to list files
                service.list_files(Path('.'))
                services_status[service_name] = 'operational'
            elif service_name == 'database_service':
                # Try to get history
                service.get_validation_history()
                services_status[service_name] = 'operational'
            else:
                services_status[service_name] = 'unknown'
        except Exception as e:
            services_status[service_name] = f'error: {str(e)}'
    
    return jsonify({
        'services': services_status,
        'all_operational': all(s == 'operational' for s in services_status.values()),
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@monitoring_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({'pong': True, 'timestamp': datetime.now(timezone.utc).isoformat()})