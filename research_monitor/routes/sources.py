"""
Source Validation Routes - API endpoints for validating source URLs
"""

from flask import Blueprint, request, jsonify
import logging

from research_monitor.blueprint_utils import get_db, success_response, error_response
from research_monitor.services.link_validator import LinkValidator

logger = logging.getLogger(__name__)

bp = Blueprint('sources', __name__, url_prefix='/api/sources')

# Initialize link validator
validator = LinkValidator(timeout=10, max_redirects=5)


@bp.route('/validate', methods=['GET'])
def validate_all_sources():
    """
    Validate all event sources

    Query params:
    - check_http: bool - Perform HTTP checks (default: false)
    - limit: int - Max events to check (default: 100)
    - min_importance: int - Only check events with importance >= this (default: 0)
    """
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        check_http = request.args.get('check_http', 'false').lower() == 'true'
        limit = min(int(request.args.get('limit', 100)), 5000)
        min_importance = int(request.args.get('min_importance', 0))

        query = db.query(TimelineEvent)

        if min_importance > 0:
            query = query.filter(TimelineEvent.importance >= min_importance)

        events = query.order_by(TimelineEvent.importance.desc()).limit(limit).all()

        # Convert to dicts
        event_dicts = [event.json_content for event in events if event.json_content]

        # Generate validation report
        report = validator.generate_report(event_dicts, check_http=check_http)

        return success_response({
            'report': report,
            'parameters': {
                'check_http': check_http,
                'limit': limit,
                'min_importance': min_importance,
                'events_checked': len(event_dicts)
            }
        })

    except ValueError as e:
        return error_response(f"Invalid parameter: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error validating sources: {e}", exc_info=True)
        return error_response(f"Failed to validate sources: {str(e)}", 500)
    finally:
        db.close()


@bp.route('/broken', methods=['GET'])
def get_broken_sources():
    """
    Get events with broken or suspicious sources

    Query params:
    - check_http: bool - Perform HTTP checks (default: false)
    - limit: int - Max events to return (default: 50)
    - severity: str - Filter by severity (critical, high, medium, low)
    - min_importance: int - Only check events with importance >= this (default: 0)
    """
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        check_http = request.args.get('check_http', 'false').lower() == 'true'
        limit = min(int(request.args.get('limit', 50)), 5000)
        severity_filter = request.args.get('severity', None)
        min_importance = int(request.args.get('min_importance', 0))

        query = db.query(TimelineEvent)

        if min_importance > 0:
            query = query.filter(TimelineEvent.importance >= min_importance)

        events = query.order_by(TimelineEvent.importance.desc()).all()

        broken_events = []
        for event in events:
            if not event.json_content:
                continue

            validation = validator.validate_event_sources(event.json_content, check_http=check_http)

            # Filter by severity if specified
            if severity_filter and validation['severity'] != severity_filter:
                continue

            # Only include events with issues
            if validation['invalid_sources'] > 0:
                event_data = event.json_content.copy()
                event_data['validation'] = validation
                broken_events.append(event_data)

                if len(broken_events) >= limit:
                    break

        return success_response({
            'events': broken_events,
            'count': len(broken_events),
            'parameters': {
                'check_http': check_http,
                'limit': limit,
                'severity': severity_filter,
                'min_importance': min_importance
            }
        })

    except ValueError as e:
        return error_response(f"Invalid parameter: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error getting broken sources: {e}", exc_info=True)
        return error_response(f"Failed to get broken sources: {str(e)}", 500)
    finally:
        db.close()


@bp.route('/check', methods=['POST'])
def check_specific_urls():
    """
    Check specific URLs for validity

    Request body:
    {
        "urls": ["url1", "url2", ...],
        "check_http": bool (optional, default: true)
    }
    """
    try:
        data = request.get_json()

        if not data or 'urls' not in data:
            return error_response("Missing 'urls' field in request body", 400)

        urls = data['urls']
        check_http = data.get('check_http', True)

        if not isinstance(urls, list):
            return error_response("'urls' must be a list", 400)

        if len(urls) > 100:
            return error_response("Maximum 100 URLs per request", 400)

        results = []
        for url in urls:
            validation = validator.validate_url(url, check_http=check_http)
            results.append(validation)

        # Summary statistics
        valid_count = sum(1 for r in results if r['valid'])
        invalid_count = len(results) - valid_count

        return success_response({
            'results': results,
            'summary': {
                'total': len(results),
                'valid': valid_count,
                'invalid': invalid_count,
                'check_http': check_http
            }
        })

    except Exception as e:
        logger.error(f"Error checking URLs: {e}", exc_info=True)
        return error_response(f"Failed to check URLs: {str(e)}", 500)


@bp.route('/event/<event_id>', methods=['GET'])
def validate_event_sources(event_id: str):
    """
    Validate sources for a specific event

    Query params:
    - check_http: bool - Perform HTTP checks (default: false)
    """
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        check_http = request.args.get('check_http', 'false').lower() == 'true'

        event = db.query(TimelineEvent).filter_by(id=event_id).first()

        if not event:
            return error_response(f"Event not found: {event_id}", 404)

        if not event.json_content:
            return error_response("Event has no content", 404)

        validation = validator.validate_event_sources(event.json_content, check_http=check_http)

        return success_response({
            'event_id': event_id,
            'validation': validation,
            'parameters': {
                'check_http': check_http
            }
        })

    except Exception as e:
        logger.error(f"Error validating event sources: {e}", exc_info=True)
        return error_response(f"Failed to validate event sources: {str(e)}", 500)
    finally:
        db.close()


@bp.route('/stats', methods=['GET'])
def get_validation_stats():
    """
    Get overall source validation statistics

    Query params:
    - check_http: bool - Perform HTTP checks (default: false)
    """
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        check_http = request.args.get('check_http', 'false').lower() == 'true'

        # Get all events
        events = db.query(TimelineEvent).all()
        event_dicts = [event.json_content for event in events if event.json_content]

        # Generate report
        report = validator.generate_report(event_dicts, check_http=check_http)

        # Calculate percentages
        total_sources = report['total_sources']
        stats = {
            'total_events': report['total_events'],
            'events_with_issues': report['events_with_issues'],
            'events_with_issues_percent': round(report['events_with_issues'] / report['total_events'] * 100, 2) if report['total_events'] > 0 else 0,
            'total_sources': total_sources,
            'valid_sources': report['valid_sources'],
            'valid_sources_percent': round(report['valid_sources'] / total_sources * 100, 2) if total_sources > 0 else 0,
            'invalid_sources': report['invalid_sources'],
            'invalid_sources_percent': round(report['invalid_sources'] / total_sources * 100, 2) if total_sources > 0 else 0,
            'suspicious_sources': report['suspicious_sources'],
            'suspicious_sources_percent': round(report['suspicious_sources'] / total_sources * 100, 2) if total_sources > 0 else 0,
            'severity_breakdown': report['severity_breakdown'],
            'check_http_enabled': check_http
        }

        return success_response({'stats': stats})

    except Exception as e:
        logger.error(f"Error getting validation stats: {e}", exc_info=True)
        return error_response(f"Failed to get validation stats: {str(e)}", 500)
    finally:
        db.close()
