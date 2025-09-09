# Research Priorities API

A JSON-file based research management system that mirrors the timeline events structure, providing both local editability and API access through SQLite caching.

## Architecture

### 📁 **JSON Files as Source of Truth**
- `research_priorities/` directory contains canonical JSON files
- Each file represents one research thread with complete metadata
- Files are version-controlled and locally editable
- Automatic sync to SQLite database for API performance

### 🗄️ **SQLite Mirror Database**
- `research_priorities.db` provides fast API queries
- Auto-reloads JSON files every 5 minutes
- Change detection prevents unnecessary updates
- Full-text search across all research threads

### 🔄 **Two-Way Sync Design**
- **Read**: SQLite serves API requests with sub-second response times
- **Write**: Updates can modify JSON files directly
- **Commit**: Changes to JSON files can be committed to git
- **Reload**: API endpoint forces immediate sync from files

## JSON File Structure

### Research Priority Schema
```json
{
  "id": "RT-001-unique-identifier",
  "title": "Research Thread Title",
  "description": "Detailed research plan and objectives",
  "priority": 9,
  "status": "pending|in_progress|completed|blocked|abandoned",
  "category": "constitutional-crisis|intelligence-manipulation|etc",
  "tags": ["tag1", "tag2", "tag3"],
  "estimated_events": 3,
  "actual_events": 0,
  "created_date": "2025-01-05",
  "updated_date": "2025-01-05",
  "completion_date": null,
  "triggered_by": ["event-id-1", "event-id-2"],
  "key_sources": [
    {
      "title": "Source Name",
      "type": "government-report|court-records|etc",
      "credibility": 9,
      "why": "Why this source is valuable",
      "url": "https://example.com",
      "author": "Author Name"
    }
  ],
  "expected_outcomes": [
    "Outcome description 1",
    "Outcome description 2"
  ],
  "connections": [
    {
      "to": "RT-002-related-thread",
      "type": "precursor|related|dependent",
      "description": "How threads relate"
    }
  ],
  "actors_to_investigate": ["Actor 1", "Actor 2"],
  "time_period": "2001-2003",
  "constitutional_issues": ["Fourth Amendment", "separation of powers"],
  "estimated_importance": 8,
  "research_notes": "Additional context and findings"
}
```

### Completed Research Example
```json
{
  "id": "RT-COMPLETED-plame-leak",
  "status": "completed",
  "completion_date": "2025-01-05",
  "events_created": [
    {
      "event_id": "2003-07-14--plame-cia-identity-leaked",
      "event_title": "Valerie Plame's CIA Identity Leaked",
      "event_date": "2003-07-14",
      "created_date": "2025-01-05"
    }
  ],
  "outcomes_achieved": [
    "Documented systematic retaliation against Iraq War critics",
    "Revealed executive branch obstruction of justice"
  ]
}
```

## API Endpoints

### Research Priorities Server (Port 5175)

#### Search & Query
- `GET /api/research-priorities/search?q=query&limit=20` - Full-text search
- `GET /api/research-priorities/RT-001-thread-id` - Get specific thread
- `GET /api/research-priorities/status/pending?limit=20` - Filter by status
- `GET /api/research-priorities/stats` - Database statistics

#### Management
- `GET /api/research-priorities/reload` - Force reload from JSON files

### Example API Calls
```bash
# Search for surveillance-related research
curl "http://127.0.0.1:5175/api/research-priorities/search?q=surveillance"

# Get high-priority pending research
curl "http://127.0.0.1:5175/api/research-priorities/status/pending?limit=5"

# Get complete details for specific thread
curl "http://127.0.0.1:5175/api/research-priorities/RT-001-whig-propaganda-campaign"

# Force reload from files
curl "http://127.0.0.1:5175/api/research-priorities/reload"
```

## Database Schema

### Core Tables
- **`research_priorities`** - Main research threads
- **`research_sources`** - Key sources for each thread
- **`research_events_created`** - Timeline events created from research
- **`research_connections`** - Relationships between threads
- **`research_actors`** - Actors to investigate
- **`research_outcomes`** - Expected vs achieved outcomes

### Full-Text Search
- **`research_priorities_fts`** - FTS5 virtual table for fast searching

## Current Research Threads

### ✅ Completed (1)
- **Valerie Plame Identity Leak Investigation** (2 events created)

### 📋 Pending High-Priority (4)
1. **White House Iraq Group (WHIG)** - Priority 9
2. **FISA Court Resistance** - Priority 9  
3. **Telecom-NSA Financial Networks** - Priority 8
4. **Enron-Cheney Connection** - Priority 8

### 📊 Statistics
- **4 total threads** (1 completed, 3 pending)
- **2 events created** from research
- **8.7 average pending priority**
- **4 categories**: constitutional-crisis, intelligence-manipulation, judicial-override, surveillance-industrial-complex

## Workflow Integration

### Research Planner Subagent
1. **Analyzes** completed timeline events
2. **Generates** new research threads as JSON files
3. **Updates** existing threads based on findings
4. **Maps** connections between related research

### Timeline Event Creation
1. **Triggered by** research priorities
2. **Documented in** events_created array
3. **Updates** actual_events count
4. **Links back** to research thread ID

### Priority Management
- **P0 (Critical)**: Constitutional crises, war crimes (Priority 9-10)
- **P1 (High)**: Major corruption, systemic capture (Priority 7-8)
- **P2 (Medium)**: Policy manipulation, conflicts of interest (Priority 5-6)
- **P3 (Low)**: Supporting details, minor scandals (Priority 1-4)

## Benefits Over Previous System

### ✅ **Local Editability**
- JSON files can be edited directly in any text editor
- Changes are immediately version-controlled in git
- No database corruption issues from complex updates

### ✅ **API Performance** 
- SQLite provides sub-second query responses
- Full-text search across all research content
- Complex filtering and aggregation queries

### ✅ **Data Durability**
- JSON files are canonical source of truth
- Database can be rebuilt from files at any time
- Easy backup and migration

### ✅ **Integration Ready**
- Same pattern as timeline events system
- Compatible with existing research workflow
- Subagent-friendly API design

## Usage Examples

### Creating New Research Priority
```bash
# Create new JSON file in research_priorities/
cat > research_priorities/RT-005-new-thread.json << 'EOF'
{
  "id": "RT-005-new-thread",
  "title": "New Research Thread",
  "description": "Research objectives...",
  "priority": 7,
  "status": "pending",
  "category": "category-name",
  "tags": ["tag1", "tag2"],
  "estimated_events": 2,
  "created_date": "2025-01-05"
}
EOF

# API will auto-detect and load within 5 minutes
# Or force immediate reload:
curl "http://127.0.0.1:5175/api/research-priorities/reload"
```

### Updating Research Status
```bash
# Edit JSON file directly
sed -i 's/"status": "pending"/"status": "in_progress"/' research_priorities/RT-001-whig-propaganda-campaign.json

# Commit changes to git
git add research_priorities/RT-001-whig-propaganda-campaign.json
git commit -m "Start WHIG research investigation"
```

### Querying Research State
```python
import requests

# Get all high-priority pending research
response = requests.get('http://127.0.0.1:5175/api/research-priorities/status/pending?limit=10')
priorities = response.json()['priorities']

# Filter by priority >= 8
high_priority = [p for p in priorities if p['priority'] >= 8]

# Launch research subagents for top priorities
for priority in high_priority[:3]:
    print(f"Research: {priority['title']} (Priority: {priority['priority']})")
```

## Future Enhancements

### Planned Features
- **Research assignment** to specific subagents
- **Progress tracking** with percentage completion
- **Source validation** and credibility scoring
- **Network visualization** of research connections
- **Automated priority adjustment** based on findings

The Research Priorities API provides a robust foundation for managing complex historical research at scale while maintaining the flexibility of local file editing and the performance of database queries.