# Research Monitor v2 API Documentation

## Overview

The Research Monitor v2 API provides comprehensive access to timeline events, research priorities, and analytical data for the Kleptocracy Timeline project. The API is designed to support both research workflow automation and timeline visualization applications.

**Base URL**: `http://localhost:5558/api`

## Authentication

Most read-only endpoints require no authentication. Write operations require an API key:
- Header: `X-API-Key: <your-api-key>`
- Test key: `test-key`

## Response Format

All API responses follow a consistent JSON format:

```json
{
  "success": true,
  "data": {...},
  "count": 10,
  "total": 1866,
  "page": 1,
  "per_page": 50,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

Error responses:
```json
{
  "success": false,
  "error": "Error message",
  "code": 400
}
```

## Core Event Endpoints

### Search Events
`GET /api/events/search`

Search timeline events with full-text search and filtering.

**Parameters:**
- `q` (string): Search query for full-text search
- `limit` (integer): Number of results to return (default: 50, max: 200)
- `offset` (integer): Number of results to skip (default: 0)
- `start_date` (string): Filter events after this date (YYYY-MM-DD)
- `end_date` (string): Filter events before this date (YYYY-MM-DD)
- `min_importance` (integer): Filter events with importance >= this value
- `max_importance` (integer): Filter events with importance <= this value
- `tags` (string): Comma-separated list of tags to filter by
- `actors` (string): Comma-separated list of actors to filter by

**Example:**
```bash
curl "http://localhost:5558/api/events/search?q=Trump&limit=10&min_importance=7"
```

### Get Event by ID
`GET /api/events/{event_id}`

Retrieve a specific event by its ID.

**Example:**
```bash
curl "http://localhost:5558/api/events/2025-01-20--trump-inauguration"
```

### Create Staged Event
`POST /api/events/staged`

Create a new event that will be written to filesystem on next commit.

**Headers:** `X-API-Key: <api-key>`

**Request Body:**
```json
{
  "id": "2025-01-15--example-event",
  "date": "2025-01-15",
  "title": "Example Event Title",
  "summary": "Detailed event summary with context and significance",
  "importance": 7,
  "tags": ["corruption", "corporate-capture"],
  "actors": ["Actor Name"],
  "sources": [
    {
      "url": "https://example.com/article",
      "title": "Source Article Title"
    }
  ]
}
```

## Timeline Viewer Endpoints

### Get Timeline Events
`GET /api/timeline/events`

Optimized endpoint for timeline visualization with pagination and filtering.

**Parameters:**
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Events per page (default: 50, max: 200)
- `start_date` (string): Filter events after this date
- `end_date` (string): Filter events before this date
- `importance_min` (integer): Minimum importance level
- `importance_max` (integer): Maximum importance level
- `tags` (string): Comma-separated tags filter
- `actors` (string): Comma-separated actors filter

**Response includes pagination metadata:**
```json
{
  "events": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1866,
    "pages": 38,
    "has_next": true,
    "has_prev": false
  }
}
```

### Get Event by ID (Timeline)
`GET /api/timeline/events/{event_id}`

Get a single event with related events.

### Get Events by Date
`GET /api/timeline/events/date/{date}`

Get all events for a specific date (YYYY-MM-DD).

## Timeline Metadata Endpoints

### Get All Actors
`GET /api/timeline/actors`

Returns all unique actors in the timeline with event counts.

**Parameters:**
- `min_events` (integer): Filter actors with at least this many events
- `limit` (integer): Maximum number of actors to return

**Response:**
```json
{
  "actors": [
    {"name": "Donald Trump", "event_count": 156},
    {"name": "Dick Cheney", "event_count": 89}
  ]
}
```

### Get All Tags
`GET /api/timeline/tags`

Returns all unique tags with usage counts.

### Get All Sources
`GET /api/timeline/sources`

Returns all unique source domains with usage counts.

### Get Date Range
`GET /api/timeline/date-range`

Returns the earliest and latest event dates in the timeline.

## Timeline Filtering and Search

### Advanced Filter
`GET /api/timeline/filter`

Advanced filtering with multiple criteria and sorting options.

**Parameters:**
- `actors[]` (array): Multiple actor names
- `tags[]` (array): Multiple tag names
- `date_from` (string): Start date
- `date_to` (string): End date
- `importance_min` (integer): Minimum importance
- `importance_max` (integer): Maximum importance
- `sort_by` (string): Sort field (date, importance, title)
- `sort_order` (string): Sort direction (asc, desc)

### Advanced Search
`POST /api/timeline/search`

Advanced search with complex query options.

**Request Body:**
```json
{
  "query": "search terms",
  "filters": {
    "date_range": ["2020-01-01", "2025-01-01"],
    "actors": ["Trump", "Cheney"],
    "tags": ["corruption"],
    "importance_range": [7, 10]
  },
  "sort": {
    "field": "date",
    "order": "desc"
  },
  "limit": 50,
  "offset": 0
}
```

## Viewer-Specific Data Endpoints

### Timeline Data
`GET /api/viewer/timeline-data`

Optimized data format for timeline visualization components.

**Parameters:**
- `granularity` (string): Time grouping (day, week, month, year)
- `format` (string): Response format (standard, compact, viz)

### Actor Network
`GET /api/viewer/actor-network`

Network graph data showing relationships between actors.

**Parameters:**
- `min_connections` (integer): Minimum shared events for connection
- `max_actors` (integer): Maximum actors in network
- `time_window` (string): Time period to analyze

**Response:**
```json
{
  "nodes": [
    {"id": "Trump", "label": "Donald Trump", "size": 156, "group": "political"}
  ],
  "edges": [
    {"source": "Trump", "target": "Cheney", "weight": 12}
  ]
}
```

### Tag Cloud
`GET /api/viewer/tag-cloud`

Tag frequency data for tag cloud visualization.

**Parameters:**
- `min_frequency` (integer): Minimum tag usage count
- `max_tags` (integer): Maximum tags to return

## Statistics Endpoints

### Overall Statistics
`GET /api/viewer/stats/overview`

High-level timeline statistics.

**Response:**
```json
{
  "total_events": 1866,
  "total_actors": 423,
  "total_tags": 89,
  "date_range": {
    "earliest": "1971-08-23",
    "latest": "2025-01-20"
  },
  "avg_importance": 6.2,
  "events_by_decade": {...}
}
```

### Events by Time Period
`GET /api/viewer/stats/events-by-period`

Event distribution over time.

**Parameters:**
- `period` (string): Grouping period (year, month, day)
- `start_date` (string): Start date for analysis
- `end_date` (string): End date for analysis

### Actor Statistics
`GET /api/viewer/stats/actors`

Statistics about actors in the timeline.

### Tag Statistics
`GET /api/viewer/stats/tags`

Statistics about tag usage.

### Importance Distribution
`GET /api/viewer/stats/importance`

Distribution of event importance scores.

### Timeline Patterns
`GET /api/viewer/stats/patterns`

Analyze patterns and trends in the timeline data.

## Research Priority Endpoints

### Get Next Priority
`GET /api/priorities/next`

Get the next research priority to work on.

**Parameters:**
- `agent_id` (string): Agent identifier for reservation
- `categories[]` (array): Filter by priority categories

### Update Priority Status
`PUT /api/priorities/{priority_id}/status`

Update the status of a research priority.

**Headers:** `X-API-Key: <api-key>`

**Request Body:**
```json
{
  "status": "in_progress",
  "notes": "Started researching this topic",
  "estimated_events": 5
}
```

### Get All Priorities
`GET /api/priorities`

List all research priorities with filtering.

**Parameters:**
- `status` (string): Filter by status (pending, in_progress, completed)
- `category` (string): Filter by category
- `priority_min` (integer): Minimum priority level
- `limit` (integer): Maximum results to return

## System Endpoints

### Health Check
`GET /api/health`

Check API health and database connectivity.

### Statistics
`GET /api/stats`

Overall system statistics.

### Reload Data
`GET /api/reload`

Force reload of timeline events from filesystem.

### Commit Status
`GET /api/commit/status`

Check if a commit is needed (10+ staged events).

### Reset Commit Counter
`POST /api/commit/reset`

Reset the staged events counter after committing.

**Headers:** `X-API-Key: <api-key>`

## Error Codes

- **400 Bad Request**: Invalid parameters or malformed request
- **401 Unauthorized**: Missing or invalid API key
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

## Rate Limiting

- **Read endpoints**: 100 requests per minute
- **Write endpoints**: 20 requests per minute
- **Search endpoints**: 30 requests per minute

## Caching

Response caching is enabled for read-only endpoints:
- **Timeline data**: 5 minutes
- **Statistics**: 10 minutes
- **Metadata**: 30 minutes

Cache headers indicate cache status and expiration.

## Python Client

Use the official Python client for easier integration:

```python
from research_monitor.research_client import ResearchMonitorClient

client = ResearchMonitorClient(base_url="http://localhost:5558")
events = client.search_events("Trump crypto", limit=10)
analysis = client.analyze_actor("Donald Trump")
stats = client.get_timeline_stats()
```

See `research_client.py` for full client documentation.

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
`GET /api/openapi.json`

Interactive documentation (Swagger UI) is planned for a future release.