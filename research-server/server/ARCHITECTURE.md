# Research Monitor Architecture & Usage Guide

## Overview

The Research Monitor is a **persistence and service layer** for the Kleptocracy Timeline project. It provides APIs that Claude Code can call via tools (Bash/curl) to orchestrate research, track priorities, and maintain data consistency between JSON files and SQLite database.

## Core Concept

**Claude Code is the orchestrator** - it makes all decisions and drives the workflow using tools. The Research Monitor is a passive service that:
- Maintains state and persistence
- Validates data
- Prevents duplicates
- Tracks progress
- Syncs files ↔ database

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Claude Code Session                    │
│                                                          │
│  Human ←→ Claude (makes decisions)                      │
│              ↓                                           │
│         Uses Tools:                                      │
│         • Bash (curl API calls)                         │
│         • Task (launch subagents)                       │
│         • Read/Write (files)                            │
└──────────────┬───────────────────────────────────────────┘
               │
               │ HTTP/JSON
               ▼
┌──────────────────────────────────────────────────────────┐
│              Research Monitor (Port 5555)                │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Flask API Layer                     │    │
│  │                                                  │    │
│  │  /api/priorities/next     → Next task to work   │    │
│  │  /api/events/search       → Find existing       │    │
│  │  /api/events/validate     → Check before save   │    │
│  │  /api/priorities/{id}     → Update status       │    │
│  │  /api/stats               → Progress metrics    │    │
│  └─────────────────┬────────────────────────────────┘    │
│                    │                                      │
│  ┌─────────────────▼────────────────────────────────┐    │
│  │           SQLite Database (Thread-Safe)          │    │
│  │                                                  │    │
│  │  • research_priorities  (tasks to complete)      │    │
│  │  • timeline_events      (validated events)       │    │
│  │  • research_logs        (activity tracking)      │    │
│  │  • metrics              (performance data)       │    │
│  └─────────────────┬────────────────────────────────┘    │
│                    │                                      │
│  ┌─────────────────▼────────────────────────────────┐    │
│  │            File System Sync Service              │    │
│  │                                                  │    │
│  │  • Watches timeline_data/events/*.json           │    │
│  │  • Watches research_priorities/*.json            │    │
│  │  • Auto-syncs changes to database                │    │
│  │  • Maintains consistency                         │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

## API Endpoints

### Research Priority Management

#### Get Next Priority
```bash
GET /api/priorities/next
```
Returns the highest priority pending research task.

**Response:**
```json
{
  "id": "RT-001-whig-propaganda",
  "title": "Research WHIG propaganda campaign",
  "description": "Investigate White House Iraq Group...",
  "priority": 9,
  "estimated_events": 5,
  "tags": ["whig", "iraq-war", "propaganda"]
}
```

#### Update Priority Status
```bash
PUT /api/priorities/{id}/status
```
Update the status of a research priority.

**Request:**
```json
{
  "status": "in_progress|completed|blocked",
  "actual_events": 3,
  "notes": "Found 3 events, need more sources for 4th"
}
```

#### Create New Priority
```bash
POST /api/priorities
```
Add a new research priority to the queue.

**Request:**
```json
{
  "title": "Research Halliburton no-bid contracts",
  "description": "Investigate contract awards...",
  "priority": 8,
  "estimated_events": 4,
  "tags": ["halliburton", "iraq-war", "corruption"]
}
```

### Timeline Event Management

#### Search Events
```bash
GET /api/events/search?q=halliburton&date_from=2003-01-01
```
Search existing events to avoid duplicates.

**Response:**
```json
{
  "count": 2,
  "events": [
    {
      "id": "2003-03-24--halliburton-no-bid-contract",
      "title": "Halliburton awarded $7B no-bid contract",
      "date": "2003-03-24",
      "importance": 8
    }
  ]
}
```

#### Validate Event
```bash
POST /api/events/validate
```
Validate an event before saving to filesystem.

**Request:**
```json
{
  "id": "2003-03-24--halliburton-contract",
  "date": "2003-03-24",
  "title": "Halliburton no-bid contract",
  "summary": "...",
  "sources": [...]
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": ["Similar event exists: 2003-03-24--halliburton-no-bid"],
  "duplicate": false
}
```

#### Record Event Creation
```bash
POST /api/events/created
```
Notify the monitor that an event was created (for tracking).

**Request:**
```json
{
  "id": "2003-03-24--halliburton-contract",
  "priority_id": "RT-004",
  "created_by": "timeline-researcher"
}
```

### Progress Tracking

#### Get Statistics
```bash
GET /api/stats
```
Get current progress and system statistics.

**Response:**
```json
{
  "priorities": {
    "total": 104,
    "pending": 67,
    "in_progress": 3,
    "completed": 34
  },
  "events": {
    "total": 1065,
    "created_today": 12,
    "created_week": 47
  },
  "research_velocity": {
    "events_per_day": 6.7,
    "priorities_per_week": 8.2
  }
}
```

#### Log Activity
```bash
POST /api/activity
```
Log research activity for monitoring.

**Request:**
```json
{
  "action": "research_started",
  "priority_id": "RT-001",
  "agent": "timeline-researcher",
  "details": "Researching WHIG propaganda"
}
```

## Usage Patterns

### 1. Basic Research Workflow

```bash
# 1. Get next priority from Research Monitor
priority=$(curl -s http://localhost:5555/api/priorities/next)

# 2. Mark as in-progress
curl -X PUT http://localhost:5555/api/priorities/$id/status \
  -d '{"status": "in_progress"}'

# 3. [Claude launches research subagent via Task tool]

# 4. Validate results before saving
curl -X POST http://localhost:5555/api/events/validate \
  -d @event.json

# 5. If valid, save to filesystem (monitor auto-syncs to DB)
# [Claude uses Write tool to save JSON]

# 6. Mark priority as completed
curl -X PUT http://localhost:5555/api/priorities/$id/status \
  -d '{"status": "completed", "actual_events": 3}'
```

### 2. Duplicate Prevention

```bash
# Before creating an event, check if it exists
existing=$(curl -s "http://localhost:5555/api/events/search?q=halliburton+no-bid&date=2003-03-24")

if [ $(echo $existing | jq '.count') -eq 0 ]; then
  # Safe to create new event
else
  # Event already exists, skip or update
fi
```

### 3. Progress Monitoring

```bash
# Check overall progress
curl http://localhost:5555/api/stats | jq '.priorities.pending'

# Log activity for tracking
curl -X POST http://localhost:5555/api/activity \
  -d '{"action": "pdf_processed", "file": "senate_report.pdf"}'
```

## Database Schema

### research_priorities
- `id` (TEXT PRIMARY KEY) - Unique identifier (RT-XXX-description)
- `title` (TEXT) - Brief title
- `description` (TEXT) - Detailed research description
- `priority` (INTEGER 1-10) - Priority score
- `status` (TEXT) - pending|in_progress|completed|blocked
- `estimated_events` (INTEGER) - Expected events to create
- `actual_events` (INTEGER) - Actual events created
- `tags` (JSON) - Array of tags
- `created_date` (TEXT) - When priority was created
- `updated_date` (TEXT) - Last status update
- `completion_date` (TEXT) - When completed

### timeline_events
- `id` (TEXT PRIMARY KEY) - Event identifier
- `date` (TEXT) - Event date (YYYY-MM-DD)
- `title` (TEXT) - Event title
- `summary` (TEXT) - Detailed summary
- `importance` (INTEGER 1-10) - Importance score
- `tags` (JSON) - Array of tags
- `sources` (JSON) - Array of source objects
- `created_at` (TIMESTAMP) - When added to database
- `created_by` (TEXT) - Which agent/process created it
- `validation_status` (TEXT) - Status of validation

### research_logs
- `id` (INTEGER PRIMARY KEY) - Auto-incrementing ID
- `timestamp` (TEXT) - When logged
- `action` (TEXT) - Action type
- `priority_id` (TEXT) - Related priority
- `event_id` (TEXT) - Related event
- `agent` (TEXT) - Which agent/tool
- `details` (JSON) - Additional data

## Security & Performance

### Authentication
- Single API key via header: `X-API-Key: <key>`
- Set via environment variable: `RESEARCH_MONITOR_API_KEY`
- Only required for write operations

### Thread Safety
- Uses thread-local database connections
- Each request gets its own connection
- No shared state between requests

### Rate Limiting
- Not needed for local single-user deployment
- Can handle 100+ requests/second
- SQLite can handle 2-24 writes/minute easily

### File Sync
- Watches filesystem for changes every 5 seconds
- Updates database when JSON files change
- Maintains consistency between files and DB

## Running the Service

```bash
# Start the Research Monitor
python3 research_cli.py server-start

# Or manually:
cd research_monitor
RESEARCH_MONITOR_PORT=5558 python3 app_v2.py

# Service runs on http://localhost:5558
# API available at http://localhost:5558/api/
```

## Environment Variables

```bash
# Optional configuration
export RESEARCH_MONITOR_PORT=5555
export RESEARCH_MONITOR_API_KEY=your-secret-key
export RESEARCH_DB_PATH=../unified_research.db
export TIMELINE_EVENTS_PATH=../timeline_data/events
export RESEARCH_PRIORITIES_PATH=../research_priorities
```

## Key Benefits

1. **Separation of Concerns** - Claude decides, Monitor persists
2. **Tool-Friendly** - Simple HTTP/JSON APIs for Bash/curl
3. **Consistency** - Single source of truth in SQLite
4. **Progress Tracking** - Know what's done and what's next
5. **Duplicate Prevention** - Search before creating
6. **Validation** - Check events before saving
7. **Real-time Updates** - WebSocket for live progress

## Summary

The Research Monitor is NOT an orchestrator - it's a service layer that Claude Code uses via tools to:
- Get the next task to work on
- Check if events already exist
- Validate data before saving
- Track progress and metrics
- Maintain consistency between files and database

Claude Code remains in full control, making all decisions and orchestrating the actual research work through subagents.