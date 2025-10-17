"""
Source Validation Routes - API endpoints for validating source URLs and quality
"""

from flask import Blueprint, request, jsonify
import logging

from blueprint_utils import get_db, success_response, error_response
from services.link_validator import LinkValidator
from services.source_quality import SourceQualityClassifier

logger = logging.getLogger(__name__)

bp = Blueprint('sources', __name__, url_prefix='/api/sources')

# Initialize validators
validator = LinkValidator(timeout=10, max_redirects=5)
quality_classifier = SourceQualityClassifier()


@bp.route('/validate', methods=['GET'])
def validate_all_sources():
    """
    Validate all event sources

    Query params:
    - check_http: bool - Perform HTTP checks (default: false)
    - limit: int - Max events to check (default: 100)
    - min_importance: int - Only check events with importance >= this (default: 0)
    """
    from models import TimelineEvent

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
    from models import TimelineEvent

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
    from models import TimelineEvent

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
    from models import TimelineEvent

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


# === Source Quality Endpoints ===

@bp.route('/quality/stats', methods=['GET'])
def get_quality_stats():
    """
    Get overall source quality statistics

    Query params:
    - min_importance: int - Only analyze events with importance >= this (default: 0)
    """
    from models import TimelineEvent

    db = get_db()
    try:
        min_importance = int(request.args.get('min_importance', 0))

        query = db.query(TimelineEvent)
        if min_importance > 0:
            query = query.filter(TimelineEvent.importance >= min_importance)

        events = query.all()
        event_dicts = [event.json_content for event in events if event.json_content]

        # Analyze all events
        quality_levels = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        tier_counts = {1: 0, 2: 0, 3: 0}
        total_quality_score = 0
        events_with_issues = 0

        for event_dict in event_dicts:
            classification = quality_classifier.classify_event_sources(event_dict)
            quality_levels[classification['quality_level']] += 1
            tier_counts[1] += classification['tier_1_count']
            tier_counts[2] += classification['tier_2_count']
            tier_counts[3] += classification['tier_3_count']
            total_quality_score += classification['quality_score']
            if classification['issues']:
                events_with_issues += 1

        total_events = len(event_dicts)
        total_sources = sum(tier_counts.values())
        avg_quality_score = total_quality_score / total_events if total_events > 0 else 0

        stats = {
            'total_events': total_events,
            'total_sources': total_sources,
            'average_quality_score': round(avg_quality_score, 2),
            'quality_distribution': {
                level: {
                    'count': count,
                    'percent': round(count / total_events * 100, 1) if total_events > 0 else 0
                }
                for level, count in quality_levels.items()
            },
            'tier_distribution': {
                f'tier_{tier}': {
                    'count': count,
                    'percent': round(count / total_sources * 100, 1) if total_sources > 0 else 0
                }
                for tier, count in tier_counts.items()
            },
            'events_with_issues': events_with_issues,
            'events_with_issues_percent': round(
                events_with_issues / total_events * 100, 1
            ) if total_events > 0 else 0,
            'classifier_stats': quality_classifier.get_statistics()
        }

        return success_response({'stats': stats})

    except ValueError as e:
        return error_response(f"Invalid parameter: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error getting quality stats: {e}", exc_info=True)
        return error_response(f"Failed to get quality stats: {str(e)}", 500)
    finally:
        db.close()


@bp.route('/quality/low', methods=['GET'])
def get_low_quality_events():
    """
    Get events with low source quality

    Query params:
    - max_score: float - Maximum quality score (default: 5.0)
    - min_importance: int - Minimum importance (default: 0)
    - limit: int - Max events to return (default: 50)
    """
    from models import TimelineEvent

    db = get_db()
    try:
        max_score = float(request.args.get('max_score', 5.0))
        min_importance = int(request.args.get('min_importance', 0))
        limit = min(int(request.args.get('limit', 50)), 500)

        query = db.query(TimelineEvent)
        if min_importance > 0:
            query = query.filter(TimelineEvent.importance >= min_importance)

        events = query.order_by(TimelineEvent.importance.desc()).all()

        low_quality_events = []
        for event in events:
            if not event.json_content:
                continue

            classification = quality_classifier.classify_event_sources(event.json_content)

            if classification['quality_score'] <= max_score:
                event_data = event.json_content.copy()
                event_data['quality_analysis'] = {
                    'quality_score': classification['quality_score'],
                    'quality_level': classification['quality_level'],
                    'tier_1_count': classification['tier_1_count'],
                    'tier_2_count': classification['tier_2_count'],
                    'tier_3_count': classification['tier_3_count'],
                    'issues': classification['issues']
                }
                low_quality_events.append(event_data)

                if len(low_quality_events) >= limit:
                    break

        return success_response({
            'events': low_quality_events,
            'count': len(low_quality_events),
            'parameters': {
                'max_score': max_score,
                'min_importance': min_importance,
                'limit': limit
            }
        })

    except ValueError as e:
        return error_response(f"Invalid parameter: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error getting low quality events: {e}", exc_info=True)
        return error_response(f"Failed to get low quality events: {str(e)}", 500)
    finally:
        db.close()


@bp.route('/quality/event/<event_id>', methods=['GET'])
def analyze_event_quality(event_id: str):
    """
    Analyze source quality for a specific event
    """
    from models import TimelineEvent

    db = get_db()
    try:
        event = db.query(TimelineEvent).filter_by(id=event_id).first()

        if not event:
            return error_response(f"Event not found: {event_id}", 404)

        if not event.json_content:
            return error_response("Event has no content", 404)

        classification = quality_classifier.classify_event_sources(event.json_content)

        # Get recommendations
        suggestions = []
        if classification['tier_1_count'] == 0:
            suggestions.append("Add at least one tier-1 source (major news, government, academic)")
        if classification['tier_3_count'] > classification['tier_1_count'] + classification['tier_2_count']:
            suggestions.append("Reduce tier-3 sources, add more tier-1 or tier-2 sources")
        if classification['total_sources'] < 2:
            suggestions.append("Add more sources - minimum 2 recommended")
        if classification['total_sources'] < 3:
            suggestions.append("Add one more source for better credibility (3+ recommended)")

        return success_response({
            'event_id': event_id,
            'quality_analysis': classification,
            'suggestions': suggestions
        })

    except Exception as e:
        logger.error(f"Error analyzing event quality: {e}", exc_info=True)
        return error_response(f"Failed to analyze event quality: {str(e)}", 500)
    finally:
        db.close()


@bp.route('/quality/tier/<int:tier>', methods=['GET'])
def get_tier_outlets(tier: int):
    """
    Get list of outlets in a specific quality tier

    Path params:
    - tier: Quality tier (1, 2, or 3)
    """
    try:
        if tier not in [1, 2, 3]:
            return error_response("Tier must be 1, 2, or 3", 400)

        if tier == 1:
            outlets = list(quality_classifier.TIER_1_OUTLETS)
        elif tier == 2:
            outlets = list(quality_classifier.TIER_2_OUTLETS)
        else:
            outlets = list(quality_classifier.TIER_3_OUTLETS)

        return success_response({
            'tier': tier,
            'outlet_count': len(outlets),
            'outlets': sorted(outlets)
        })

    except Exception as e:
        logger.error(f"Error getting tier outlets: {e}", exc_info=True)
        return error_response(f"Failed to get tier outlets: {str(e)}", 500)
