# Kleptocracy Timeline - Claude Code Instructions

## System Architecture

### Research Monitor v2
The Research Monitor v2 (`research_monitor/app_v2.py`) is a Flask server that provides:
- **Filesystem-authoritative events**: Timeline events are read-only synced from JSON files
- **Database-authoritative research priorities**: Full CRUD operations on research tasks
- **Search capabilities**: Full-text search across 1,000+ timeline events
- **Commit orchestration**: Tracks when commits are needed but doesn't perform them

### Starting the Server
```bash
cd research_monitor
RESEARCH_MONITOR_PORT=5558 python3 app_v2.py &
```

## Key API Endpoints

### Search Events
```bash
# Search for events by keyword
curl "http://localhost:5558/api/events/search?q=Trump"
curl "http://localhost:5558/api/events/search?q=surveillance+FISA"
```

### Research Priorities
```bash
# Get next priority to research
curl "http://localhost:5558/api/priorities/next"

# Update priority status
curl -X PUT "http://localhost:5558/api/priorities/{id}/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress", "notes": "Research notes here"}'
```

### Event Creation
```bash
# Stage a new event
curl -X POST "http://localhost:5558/api/events/staged" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{
    "id": "YYYY-MM-DD--event-slug",
    "date": "YYYY-MM-DD",
    "title": "Event Title",
    "summary": "Detailed summary",
    "importance": 1-10,
    "tags": ["tag1", "tag2"]
  }'
```

### Commit Orchestration
```bash
# Check if commit is needed
curl "http://localhost:5558/api/commit/status"

# Reset counter after committing
curl -X POST "http://localhost:5558/api/commit/reset" \
  -H "X-API-Key: test-key"
```

## CRITICAL: Duplicate Detection Workflow

### Before Creating Any Event

1. **Search for exact duplicates by date and key terms**:
```bash
# Search by main actor/entity
curl "http://localhost:5558/api/events/search?q=Trump+crypto"
curl "http://localhost:5558/api/events/search?q=Musk+Starlink"

# Search by specific terms from the event
curl "http://localhost:5558/api/events/search?q=specific+company+name"
```

2. **Check events around the same date**:
```bash
# List events by browsing the filesystem
ls -la timeline_data/events/YYYY-MM-*.json

# Check specific date range
ls -la timeline_data/events/2025-01-*.json | grep -i keyword
```

3. **Search for related events**:
```bash
# Search for broader patterns
curl "http://localhost:5558/api/events/search?q=FISA+court"
curl "http://localhost:5558/api/events/search?q=no-bid+contract"
```

### Duplicate Detection Rules

**DO NOT CREATE** if:
- An event with the same date and similar title exists
- The core facts are already covered in an existing event
- It's a minor update to an existing story (add to the existing event instead)

**DO CREATE** if:
- It's a genuinely new development
- It reveals new information not in existing events
- It represents a significant escalation or change

### Event ID Format
Always use: `YYYY-MM-DD--descriptive-slug-here`
- Use the actual event date, not today's date
- Make slugs descriptive and searchable
- Keep slugs concise but meaningful

## Research Workflow

### 1. Get Next Priority
```bash
curl "http://localhost:5558/api/priorities/next"
```

### 2. Search for Existing Related Events
**ALWAYS DO THIS FIRST**
```bash
# Search broadly for the topic
curl "http://localhost:5558/api/events/search?q=topic+keywords"

# Search for specific actors
curl "http://localhost:5558/api/events/search?q=actor+name"

# Check the time period
ls -la timeline_data/events/YYYY-*.json
```

### 3. Research the Topic
- Use web search for current information
- Focus on credible sources
- Look for specific dates and verifiable facts

### 4. Create New Events (If Not Duplicates)
For each potential event:
1. Search for duplicates (see above)
2. If unique, create with proper format
3. Include importance score (1-10)
4. Add relevant tags

### 5. Update Priority Status
```bash
curl -X PUT "http://localhost:5558/api/priorities/{id}/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "actual_events": 3}'
```

### 6. Commit When Threshold Reached
The server tracks events and will signal when 10 events are staged:
```bash
# Check status
curl "http://localhost:5558/api/commit/status"

# If commit_needed is true, perform git operations:
cd /Users/markr/kleptocracy-timeline
git add timeline_data/events research_priorities
git commit -m "Add X researched events and update priorities"

# Reset the counter
curl -X POST "http://localhost:5558/api/commit/reset" -H "X-API-Key: test-key"
```

## Best Practices

### Event Quality
- **Importance scores**: 1-3 minor, 4-6 significant, 7-9 major, 10 critical
- **Summaries**: Provide context and explain significance
- **Sources**: Mention credible sources in summary when possible
- **Tags**: Use consistent tagging for better searchability

### Avoiding Duplicates
1. **Always search first** - Multiple searches are better than creating duplicates
2. **Check date ranges** - Events might be off by a day or two
3. **Search key actors** - "Trump", "Musk", "Thiel", etc.
4. **Search key terms** - Company names, program names, specific amounts

### Performance
- The database indexes over 1,000 events efficiently
- Full-text search is available via SQLite FTS5
- The server handles concurrent requests well
- Filesystem sync runs every 30 seconds

## Common Tasks

### Find Events by Actor
```bash
curl "http://localhost:5558/api/events/search?q=Cheney" | jq '.events[] | {date, title}'
```

### Find Events by Pattern
```bash
curl "http://localhost:5558/api/events/search?q=no-bid+contract" | jq '.count'
```

### Check System Stats
```bash
curl "http://localhost:5558/api/stats" | jq
```

### Export Priorities
```bash
curl "http://localhost:5558/api/priorities/export" > priorities_backup.json
```

## Troubleshooting

### Server Won't Start
- Check if port is in use: `lsof -i :5558`
- Kill existing process: `kill -9 <PID>`
- Use different port: `RESEARCH_MONITOR_PORT=5559 python3 app_v2.py`

### Database Corruption
```bash
cd /Users/markr/kleptocracy-timeline
rm -f unified_research.db unified_research.db-wal unified_research.db-shm
# Restart server - it will rebuild from filesystem
```

### Search Not Working
- Wait 30 seconds for filesystem sync
- Check server logs for errors
- Verify events are valid JSON

## Architecture Notes

The system uses a **hybrid architecture**:
- **Events**: Filesystem is authoritative (one-way sync to database)
- **Priorities**: Database is authoritative (can export to filesystem)
- **Search**: SQLite FTS5 for full-text search
- **Commits**: Server signals, orchestrator (you) performs

This design ensures:
- No data loss (filesystem is source of truth for events)
- Fast searching (database indexes)
- Clean separation of concerns (server manages data, orchestrator manages git)