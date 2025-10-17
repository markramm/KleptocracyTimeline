"""
routes/timeline.py - Timeline Query and Metadata Endpoints

Provides read-only access to timeline events with:
- Pagination and filtering
- Date/year/actor-based queries
- Metadata extraction (actors, tags, sources)
- Advanced search and filtering

All routes are read-only (GET/POST for search).
"""
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import func, or_
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('timeline', __name__, url_prefix='/api/timeline')

def get_db():
    """Get database session from app_v2"""
    from research_monitor import app_v2
    return app_v2.get_db()

def get_cache():
    """Get cache from app config"""
    return current_app.config.get('CACHE')

# ==================== TIMELINE QUERY ENDPOINTS ====================

@bp.route('/events', methods=['GET'])
def get_timeline_events():
    """Get timeline events with pagination and filtering"""
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        # Pagination parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 5000)  # Max 5000 per page for loading all events

        # Filtering parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        importance_min = request.args.get('importance_min', type=int)
        importance_max = request.args.get('importance_max', type=int)
        search_text = request.args.get('search')

        # Build query
        query = db.query(TimelineEvent)

        # Apply filters
        if date_from:
            query = query.filter(TimelineEvent.date >= date_from)
        if date_to:
            query = query.filter(TimelineEvent.date <= date_to)
        if importance_min:
            query = query.filter(TimelineEvent.importance >= importance_min)
        if importance_max:
            query = query.filter(TimelineEvent.importance <= importance_max)

        # Full-text search if provided
        if search_text:
            search_query = f'%{search_text}%'
            query = query.filter(
                or_(
                    TimelineEvent.title.ilike(search_query),
                    TimelineEvent.summary.ilike(search_query)
                )
            )

        # Order by date descending
        query = query.order_by(TimelineEvent.date.desc())

        # Get total count for pagination
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        events = query.offset(offset).limit(per_page).all()

        # Convert to JSON format using the json_content field
        events_data = []
        for event in events:
            # Start with the full JSON content
            event_dict = event.json_content.copy() if event.json_content else {}

            # Add filesystem metadata
            event_dict.update({
                'file_path': event.file_path,
                'last_synced': event.last_synced.isoformat() if event.last_synced else None
            })

            events_data.append(event_dict)

        # Calculate pagination info
        pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < pages

        return jsonify({
            'events': events_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'prev_page': page - 1 if has_prev else None,
                'next_page': page + 1 if has_next else None
            },
            'filters_applied': {
                'date_from': date_from,
                'date_to': date_to,
                'importance_min': importance_min,
                'importance_max': importance_max,
                'search_text': search_text
            }
        })

    except Exception as e:
        logger.error(f"Error getting timeline events: {e}")
        return jsonify({'error': 'Failed to retrieve timeline events'}), 500
    finally:
        db.close()

@bp.route('/events/<event_id>', methods=['GET'])
def get_timeline_event(event_id):
    """Get a single timeline event by ID"""
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        event = db.query(TimelineEvent).filter_by(id=event_id).first()
        if not event:
            return jsonify({'error': 'Event not found'}), 404

        # Return full JSON content for single event
        event_dict = event.json_content.copy() if event.json_content else {}

        # Add filesystem metadata
        event_dict.update({
            'file_path': event.file_path,
            'last_synced': event.last_synced.isoformat() if event.last_synced else None
        })

        return jsonify(event_dict)

    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        return jsonify({'error': 'Failed to retrieve event'}), 500
    finally:
        db.close()

@bp.route('/events/date/<date>', methods=['GET'])
def get_timeline_events_by_date(date):
    """Get timeline events for a specific date"""
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        events = db.query(TimelineEvent).filter_by(date=date).order_by(TimelineEvent.importance.desc()).all()

        events_data = []
        for event in events:
            # Use full JSON content
            event_dict = event.json_content.copy() if event.json_content else {}
            events_data.append(event_dict)

        return jsonify({
            'date': date,
            'count': len(events_data),
            'events': events_data
        })

    except Exception as e:
        logger.error(f"Error getting events for date {date}: {e}")
        return jsonify({'error': 'Failed to retrieve events for date'}), 500
    finally:
        db.close()

@bp.route('/events/year/<int:year>', methods=['GET'])
def get_timeline_events_by_year(year):
    """Get timeline events for a specific year"""
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        # Filter events by year
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        events = db.query(TimelineEvent)\
            .filter(TimelineEvent.date >= start_date)\
            .filter(TimelineEvent.date <= end_date)\
            .order_by(TimelineEvent.date.desc())\
            .all()

        events_data = []
        for event in events:
            # Use full JSON content
            event_dict = event.json_content.copy() if event.json_content else {}
            events_data.append(event_dict)

        return jsonify({
            'year': year,
            'count': len(events_data),
            'events': events_data
        })

    except Exception as e:
        logger.error(f"Error getting events for year {year}: {e}")
        return jsonify({'error': 'Failed to retrieve events for year'}), 500
    finally:
        db.close()

@bp.route('/events/actor/<actor>', methods=['GET'])
def get_timeline_events_by_actor(actor):
    """Get timeline events involving a specific actor"""
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        # Search for events containing the actor in the JSON content
        events = db.query(TimelineEvent)\
            .filter(TimelineEvent.json_content.contains(actor))\
            .order_by(TimelineEvent.date.desc())\
            .all()

        events_data = []
        for event in events:
            # Use full JSON content
            event_dict = event.json_content.copy() if event.json_content else {}
            events_data.append(event_dict)

        return jsonify({
            'actor': actor,
            'count': len(events_data),
            'events': events_data
        })

    except Exception as e:
        logger.error(f"Error getting events for actor {actor}: {e}")
        return jsonify({'error': 'Failed to retrieve events for actor'}), 500
    finally:
        db.close()

@bp.route('/actor/<actor>/timeline')
def get_actor_timeline(actor):
    """Get chronological timeline of all events for a specific actor"""
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        limit = min(int(request.args.get('limit', 100)), 500)

        # Search for events containing the actor
        events = db.query(TimelineEvent)\
            .filter(TimelineEvent.json_content.contains(actor))\
            .order_by(TimelineEvent.date.asc())\
            .limit(limit)\
            .all()

        timeline_events = []
        for event in events:
            if event.json_content:
                # Verify actor is actually in the actors list, not just mentioned
                actors = event.json_content.get('actors', [])
                if isinstance(actors, list) and any(actor.lower() in str(a).lower() for a in actors):
                    event_dict = {
                        'date': event.date,
                        'id': event.id,
                        'title': event.title,
                        'summary': event.summary,
                        'importance': event.importance,
                        'actors': actors,
                        'tags': event.json_content.get('tags', [])
                    }
                    timeline_events.append(event_dict)

        # Group by year for easier navigation
        timeline_by_year = {}
        for event in timeline_events:
            year = event['date'][:4]
            if year not in timeline_by_year:
                timeline_by_year[year] = []
            timeline_by_year[year].append(event)

        return jsonify({
            'actor': actor,
            'events': timeline_events,
            'events_by_year': timeline_by_year,
            'total_events': len(timeline_events),
            'date_range': {
                'earliest': timeline_events[0]['date'] if timeline_events else None,
                'latest': timeline_events[-1]['date'] if timeline_events else None
            }
        })

    finally:
        db.close()

# ==================== TIMELINE METADATA ENDPOINTS ====================

@bp.route('/actors', methods=['GET'])
def get_timeline_actors():
    """Get all unique actors mentioned in timeline events"""
    from research_monitor.models import TimelineEvent

    cache = get_cache()
    if cache:
        cache_key = 'timeline_actors'
        cached_result = cache.get(cache_key)
        if cached_result:
            return jsonify(cached_result)

    db = get_db()
    try:
        # Get all events and extract actors from JSON content
        events = db.query(TimelineEvent).all()
        actors_set = set()

        for event in events:
            if event.json_content and 'actors' in event.json_content:
                actors = event.json_content.get('actors', [])
                if isinstance(actors, list):
                    for actor in actors:
                        if isinstance(actor, str) and actor.strip():
                            actors_set.add(actor.strip())

        # Convert to sorted list
        actors_list = sorted(list(actors_set))

        result = {
            'actors': actors_list,
            'count': len(actors_list)
        }

        # Cache for 10 minutes
        if cache:
            cache.set(cache_key, result, timeout=600)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting timeline actors: {e}")
        return jsonify({'error': 'Failed to retrieve actors'}), 500
    finally:
        db.close()

@bp.route('/tags', methods=['GET'])
def get_timeline_tags():
    """Get all unique tags used in timeline events"""
    from research_monitor.models import TimelineEvent

    cache = get_cache()
    if cache:
        cache_key = 'timeline_tags'
        cached_result = cache.get(cache_key)
        if cached_result:
            return jsonify(cached_result)

    db = get_db()
    try:
        # Get all events and extract tags from JSON content
        events = db.query(TimelineEvent).all()
        tags_set = set()

        for event in events:
            if event.json_content and 'tags' in event.json_content:
                tags = event.json_content.get('tags', [])
                if isinstance(tags, list):
                    for tag in tags:
                        if isinstance(tag, str) and tag.strip():
                            tags_set.add(tag.strip())

        # Convert to sorted list
        tags_list = sorted(list(tags_set))

        result = {
            'tags': tags_list,
            'count': len(tags_list)
        }

        # Cache for 10 minutes
        if cache:
            cache.set(cache_key, result, timeout=600)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting timeline tags: {e}")
        return jsonify({'error': 'Failed to retrieve tags'}), 500
    finally:
        db.close()

@bp.route('/sources', methods=['GET'])
def get_timeline_sources():
    """Get all unique sources/outlets used in timeline events"""
    from research_monitor.models import TimelineEvent

    cache = get_cache()
    if cache:
        cache_key = 'timeline_sources'
        cached_result = cache.get(cache_key)
        if cached_result:
            return jsonify(cached_result)

    db = get_db()
    try:
        # Get all events and extract sources from JSON content
        events = db.query(TimelineEvent).all()
        outlets_set = set()

        for event in events:
            if event.json_content and 'sources' in event.json_content:
                sources = event.json_content.get('sources', [])
                if isinstance(sources, list):
                    for source in sources:
                        if isinstance(source, dict) and 'outlet' in source:
                            outlet = source.get('outlet', '').strip()
                            if outlet:
                                outlets_set.add(outlet)

        # Convert to sorted list
        outlets_list = sorted(list(outlets_set))

        result = {
            'sources': outlets_list,
            'count': len(outlets_list)
        }

        # Cache for 10 minutes
        if cache:
            cache.set(cache_key, result, timeout=600)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting timeline sources: {e}")
        return jsonify({'error': 'Failed to retrieve sources'}), 500
    finally:
        db.close()

@bp.route('/date-range', methods=['GET'])
def get_timeline_date_range():
    """Get the date range of all timeline events"""
    from research_monitor.models import TimelineEvent

    cache = get_cache()
    if cache:
        cache_key = 'timeline_date_range'
        cached_result = cache.get(cache_key)
        if cached_result:
            return jsonify(cached_result)

    db = get_db()
    try:
        # Get min and max dates
        result_row = db.query(
            func.min(TimelineEvent.date).label('min_date'),
            func.max(TimelineEvent.date).label('max_date'),
            func.count(TimelineEvent.id).label('total_events')
        ).first()

        result = {
            'date_range': {
                'min_date': result_row.min_date,
                'max_date': result_row.max_date
            },
            'total_events': result_row.total_events
        }

        # Cache for 10 minutes
        if cache:
            cache.set(cache_key, result, timeout=600)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting timeline date range: {e}")
        return jsonify({'error': 'Failed to retrieve date range'}), 500
    finally:
        db.close()

# ==================== TIMELINE FILTERING AND SEARCH ENDPOINTS ====================

@bp.route('/filter', methods=['GET'])
def filter_timeline_events():
    """Advanced filtering of timeline events with multiple criteria"""
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        # Get filter parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        importance_min = request.args.get('importance_min', type=int)
        importance_max = request.args.get('importance_max', type=int)
        actors = request.args.getlist('actor')
        tags = request.args.getlist('tag')
        sources = request.args.getlist('source')
        search_text = request.args.get('search')

        # Pagination
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 200)

        # Build base query
        query = db.query(TimelineEvent)

        # Apply filters
        if date_from:
            query = query.filter(TimelineEvent.date >= date_from)
        if date_to:
            query = query.filter(TimelineEvent.date <= date_to)
        if importance_min:
            query = query.filter(TimelineEvent.importance >= importance_min)
        if importance_max:
            query = query.filter(TimelineEvent.importance <= importance_max)

        # Actor filtering - check if any of the specified actors appear in JSON content
        if actors:
            actor_conditions = []
            for actor in actors:
                actor_conditions.append(TimelineEvent.json_content.contains(actor))
            query = query.filter(or_(*actor_conditions))

        # Tag filtering - check if any of the specified tags appear in JSON content
        if tags:
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(TimelineEvent.json_content.contains(tag))
            query = query.filter(or_(*tag_conditions))

        # Source filtering - check if any of the specified sources appear in JSON content
        if sources:
            source_conditions = []
            for source in sources:
                source_conditions.append(TimelineEvent.json_content.contains(source))
            query = query.filter(or_(*source_conditions))

        # Text search across title and summary
        if search_text:
            search_query = f'%{search_text}%'
            query = query.filter(
                or_(
                    TimelineEvent.title.ilike(search_query),
                    TimelineEvent.summary.ilike(search_query)
                )
            )

        # Order by date descending
        query = query.order_by(TimelineEvent.date.desc())

        # Get total count for pagination
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        events = query.offset(offset).limit(per_page).all()

        # Convert to JSON format
        events_data = []
        for event in events:
            event_dict = event.json_content.copy() if event.json_content else {}
            event_dict.update({
                'file_path': event.file_path,
                'last_synced': event.last_synced.isoformat() if event.last_synced else None
            })
            events_data.append(event_dict)

        # Calculate pagination info
        pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < pages

        return jsonify({
            'events': events_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'prev_page': page - 1 if has_prev else None,
                'next_page': page + 1 if has_next else None
            },
            'filters_applied': {
                'date_from': date_from,
                'date_to': date_to,
                'importance_min': importance_min,
                'importance_max': importance_max,
                'actors': actors,
                'tags': tags,
                'sources': sources,
                'search_text': search_text
            }
        })

    except Exception as e:
        logger.error(f"Error filtering timeline events: {e}")
        return jsonify({'error': 'Failed to filter events'}), 500
    finally:
        db.close()

@bp.route('/search', methods=['POST'])
def search_timeline_events():
    """Full-text search with advanced options"""
    from research_monitor.models import TimelineEvent

    db = get_db()
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No search data provided'}), 400

        query_text = data.get('query', '').strip()
        if not query_text:
            return jsonify({'error': 'No search query provided'}), 400

        # Search options
        search_fields = data.get('fields', ['title', 'summary'])  # title, summary, actors, tags
        case_sensitive = data.get('case_sensitive', False)
        exact_match = data.get('exact_match', False)

        # Additional filters
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        importance_min = data.get('importance_min')
        importance_max = data.get('importance_max')

        # Pagination
        page = data.get('page', 1)
        per_page = min(data.get('per_page', 50), 200)

        # Build search query
        query = db.query(TimelineEvent)

        # Apply date filters first
        if date_from:
            query = query.filter(TimelineEvent.date >= date_from)
        if date_to:
            query = query.filter(TimelineEvent.date <= date_to)
        if importance_min:
            query = query.filter(TimelineEvent.importance >= importance_min)
        if importance_max:
            query = query.filter(TimelineEvent.importance <= importance_max)

        # Build search conditions based on fields
        search_conditions = []

        if exact_match:
            # Exact match search
            for field in search_fields:
                if field == 'title':
                    if case_sensitive:
                        search_conditions.append(TimelineEvent.title.contains(query_text))
                    else:
                        search_conditions.append(TimelineEvent.title.ilike(f'%{query_text}%'))
                elif field == 'summary':
                    if case_sensitive:
                        search_conditions.append(TimelineEvent.summary.contains(query_text))
                    else:
                        search_conditions.append(TimelineEvent.summary.ilike(f'%{query_text}%'))
                elif field in ['actors', 'tags', 'sources']:
                    # Search in JSON content for these fields
                    search_conditions.append(TimelineEvent.json_content.contains(query_text))
        else:
            # Fuzzy/partial match search
            search_pattern = f'%{query_text}%'
            for field in search_fields:
                if field == 'title':
                    if case_sensitive:
                        search_conditions.append(TimelineEvent.title.contains(query_text))
                    else:
                        search_conditions.append(TimelineEvent.title.ilike(search_pattern))
                elif field == 'summary':
                    if case_sensitive:
                        search_conditions.append(TimelineEvent.summary.contains(query_text))
                    else:
                        search_conditions.append(TimelineEvent.summary.ilike(search_pattern))
                elif field in ['actors', 'tags', 'sources']:
                    # Search in JSON content
                    if case_sensitive:
                        search_conditions.append(TimelineEvent.json_content.contains(query_text))
                    else:
                        # For JSON content, we need to do case-insensitive search differently
                        search_conditions.append(TimelineEvent.json_content.ilike(search_pattern))

        # Apply search conditions (OR logic)
        if search_conditions:
            query = query.filter(or_(*search_conditions))

        # Order by relevance (for now, just date desc)
        query = query.order_by(TimelineEvent.date.desc())

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        events = query.offset(offset).limit(per_page).all()

        # Convert to JSON format
        events_data = []
        for event in events:
            event_dict = event.json_content.copy() if event.json_content else {}
            event_dict.update({
                'file_path': event.file_path,
                'last_synced': event.last_synced.isoformat() if event.last_synced else None
            })
            events_data.append(event_dict)

        # Calculate pagination info
        pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < pages

        return jsonify({
            'query': query_text,
            'events': events_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'prev_page': page - 1 if has_prev else None,
                'next_page': page + 1 if has_next else None
            },
            'search_options': {
                'fields': search_fields,
                'case_sensitive': case_sensitive,
                'exact_match': exact_match,
                'filters': {
                    'date_from': date_from,
                    'date_to': date_to,
                    'importance_min': importance_min,
                    'importance_max': importance_max
                }
            }
        })

    except Exception as e:
        logger.error(f"Error searching timeline events: {e}")
        return jsonify({'error': 'Failed to search events'}), 500
    finally:
        db.close()
