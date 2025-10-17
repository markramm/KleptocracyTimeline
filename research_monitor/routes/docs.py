"""
routes/docs.py - API Documentation Endpoints

Provides API documentation and OpenAPI specification endpoints.
No dependencies on database or external services - pure documentation routes.

Routes:
- GET /api/openapi.json - OpenAPI 3.0 specification
- GET /api/docs - API documentation overview
"""

from flask import Blueprint, jsonify, current_app
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('docs', __name__)


@bp.route('/api/openapi.json', methods=['GET'])
def get_openapi_spec():
    """Return OpenAPI 3.0 specification"""
    try:
        openapi_path = Path(__file__).parent.parent / 'openapi.json'
        with open(openapi_path, 'r') as f:
            spec = json.load(f)
        return jsonify(spec)
    except Exception as e:
        logger.error(f"Error loading OpenAPI spec: {e}")
        return jsonify({
            'error': 'OpenAPI specification not available',
            'message': str(e)
        }), 500


@bp.route('/api/docs', methods=['GET'])
def api_documentation():
    """Redirect to API documentation"""
    return jsonify({
        'documentation': {
            'markdown': '/static/API_DOCUMENTATION.md',
            'openapi': '/api/openapi.json',
            'interactive': 'Planned for future release'
        },
        'endpoints': {
            'events': [
                '/api/events/search',
                '/api/events/{id}',
                '/api/events/staged'
            ],
            'timeline': [
                '/api/timeline/events',
                '/api/timeline/actors',
                '/api/timeline/tags',
                '/api/timeline/sources'
            ],
            'visualization': [
                '/api/viewer/timeline-data',
                '/api/viewer/actor-network',
                '/api/viewer/tag-cloud'
            ],
            'statistics': [
                '/api/viewer/stats/overview',
                '/api/viewer/stats/actors',
                '/api/viewer/stats/patterns'
            ],
            'research': [
                '/api/priorities/next',
                '/api/priorities/{id}/status'
            ],
            'system': [
                '/api/server/health',
                '/api/stats',
                '/api/commit/status'
            ]
        }
    })
