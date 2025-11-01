# Architecture V2: Git-Authoritative with Database Cache

**Status**: Revised Proposal (Based on User Feedback)
**Date**: 2025-10-22
**Priority**: High - Fundamental simplification with practical workflow

## Executive Summary

Use **git as the authoritative source**, but maintain **SQLite as a local cache and working set**. This enables:
- Fast search/queries via cached database
- Batch workflow: accumulate changes, review, then commit as a set
- Multi-timeline federation (judicial, state, local, international, military)
- Clean separation: cache for reads, git for authoritative storage

## Revised Architecture

### Data Flow:
```
Timeline Git Repos (multiple sources)
    ↓ (git clone/pull)
Git Workspace (local clones)
    ↓ (parse on pull)
SQLite Cache (fast reads, working set)
    ↓ (API queries)
Research Monitor API
    ↓
Agents/Researchers

Changes flow back:
Working Set (uncommitted changes in DB)
    ↓ (review & batch)
Git Commit (authoritative record)
    ↓ (push/PR)
Remote Git Repos
    ↓ (pull updates cache)
SQLite Cache refreshed
```

### Key Principles:

1. **Git is Authoritative**: Repository is source of truth
2. **Database is Cache**: Rebuilt from git on pull, indexed for fast queries
3. **Working Set**: Uncommitted changes accumulate in database
4. **Batch Commits**: Review changes, then commit set to git
5. **Multi-Timeline**: Support multiple specialized timeline repositories

## Database Redesign

### Tables by Purpose:

#### **Cache Tables** (rebuilt from git)
```sql
-- Timeline events cached from git (read-only mirror)
CREATE TABLE timeline_events_cache (
    id TEXT PRIMARY KEY,
    source_repo TEXT NOT NULL,           -- Which timeline repo
    date TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    importance INTEGER,
    json_content TEXT,
    file_path TEXT,
    git_commit_hash TEXT,                -- Last git commit that modified this
    git_commit_author TEXT,
    git_commit_date TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_source_repo (source_repo),
    INDEX idx_date (date),
    INDEX idx_importance (importance)
);

-- Full-text search index on cache
CREATE VIRTUAL TABLE events_fts USING fts5(
    id, title, summary, actors, tags, sources,
    content='timeline_events_cache'
);
```

#### **Working Set Tables** (uncommitted changes)
```sql
-- Events pending commit to git
CREATE TABLE working_set_events (
    id TEXT PRIMARY KEY,
    target_repo TEXT NOT NULL,           -- Which timeline to commit to
    operation TEXT NOT NULL,             -- 'create', 'update', 'delete'
    event_data TEXT NOT NULL,            -- JSON event data
    created_by TEXT,                     -- Agent/researcher ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed BOOLEAN DEFAULT FALSE,
    review_notes TEXT,
    commit_group TEXT,                   -- Batch multiple events into one commit
    INDEX idx_target_repo (target_repo),
    INDEX idx_commit_group (commit_group)
);

-- Audit trail of what's pending
CREATE TABLE working_set_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'        -- 'pending', 'committed', 'rejected'
);
```

#### **Metadata Tables** (workflow state)
```sql
-- Research priorities (unchanged)
CREATE TABLE research_priorities (...);

-- Validation runs (unchanged)
CREATE TABLE validation_runs (...);

-- QA reservations (unchanged)
CREATE TABLE qa_reservations (...);

-- Activity logs (unchanged)
CREATE TABLE activity_logs (...);

-- Multi-timeline registry
CREATE TABLE timeline_repos (
    id TEXT PRIMARY KEY,                 -- e.g., 'main', 'judicial', 'military'
    repo_url TEXT NOT NULL,
    branch TEXT DEFAULT 'main',
    workspace_path TEXT,
    last_pull TIMESTAMP,
    sync_enabled BOOLEAN DEFAULT TRUE,
    display_name TEXT,                   -- "Judicial Capture Timeline"
    description TEXT
);
```

## Workflow Examples

### Workflow 1: Research Agent Creates Events (Batch)

```python
# Agent researches topic, creates 10 events
for event_data in research_results:
    # Add to working set (not committed yet)
    db.execute("""
        INSERT INTO working_set_events (id, target_repo, operation, event_data, created_by)
        VALUES (?, 'main', 'create', ?, 'research-agent-1')
    """, (event_id, json.dumps(event_data)))

# Return to agent: "10 events added to working set"
# NO git commit yet - changes accumulate

# Later: Researcher reviews working set
pending_events = db.query(WorkingSetEvent).filter_by(reviewed=False).all()

# Researcher approves batch
for event in approved_batch:
    event.reviewed = True
    event.commit_group = "research-batch-20250122"

# NOW commit to git as a batch
git_service.create_branch("research-batch-20250122")
for event in approved_batch:
    file_path = git_service.write_event(event.id, event.event_data)

git_service.commit(
    message=f"Research: {len(approved_batch)} events on Trump crypto",
    author="research-agent-1"
)
git_service.push()
git_service.create_pr("Research batch: 10 new events")

# Mark as committed in working set
db.execute("""
    UPDATE working_set_events
    SET status = 'committed'
    WHERE commit_group = 'research-batch-20250122'
""")

# Pull updates to refresh cache
git_service.pull_latest()
refresh_cache_from_git()
```

### Workflow 2: QA Agent Enhances Event

```python
# 1. Read from cache (fast)
event = db.query(TimelineEventsCache).filter_by(id=event_id).first()

# 2. Agent enhances event
enhanced = qa_agent.validate_and_enhance(event.json_content)

# 3. Add to working set (not committed yet)
db.add(WorkingSetEvent(
    id=event_id,
    target_repo='main',
    operation='update',
    event_data=json.dumps(enhanced),
    created_by='qa-agent-5'
))

# 4. When QA batch complete, commit together
# (Same batch commit workflow as above)
```

### Workflow 3: Multi-Timeline Integration

```python
# Configure multiple timeline repos
db.execute("""
    INSERT INTO timeline_repos (id, repo_url, display_name) VALUES
    ('main', 'github.com/markramm/KleptocracyTimeline', 'Federal Kleptocracy'),
    ('judicial', 'github.com/org/JudicialCapture', 'Judicial Capture'),
    ('military', 'github.com/org/MilitaryTimeline', 'Military-Industrial'),
    ('state-ny', 'github.com/org/NYStateCorruption', 'New York State')
""")

# Sync all timelines
for repo in db.query(TimelineRepo).all():
    git_service = GitService(repo.repo_url, repo.workspace_path)
    git_service.pull_latest()
    refresh_cache_from_git(repo.id)  # Updates timeline_events_cache

# Search across all timelines
results = db.execute("""
    SELECT * FROM events_fts
    WHERE events_fts MATCH ?
""", (query,))

# Filter by specific timeline
ny_events = db.query(TimelineEventsCache).filter_by(source_repo='state-ny').all()

# Cross-timeline analysis
connections = db.execute("""
    SELECT
        m.id as federal_event,
        s.id as state_event
    FROM timeline_events_cache m
    JOIN timeline_events_cache s
        ON json_extract(m.json_content, '$.actors') LIKE '%' || json_extract(s.json_content, '$.actors[0]') || '%'
    WHERE m.source_repo = 'main'
      AND s.source_repo = 'state-ny'
""")
```

### Workflow 4: Review & Commit Batch

```python
# View pending changes (web UI or CLI)
GET /api/working-set/pending
→ Returns all uncommitted events grouped by creator

# Review specific batch
GET /api/working-set/by-creator/research-agent-1
→ Show 10 pending events with diffs

# Approve batch
POST /api/working-set/commit
{
    "event_ids": ["2025-01-15--event1", "2025-01-15--event2", ...],
    "commit_message": "Research: Trump crypto dealings (10 events)",
    "target_branch": "research-batch-20250122",
    "create_pr": true
}

# Server commits to git and refreshes cache
→ Git commit created
→ PR created on GitHub
→ Cache refreshed
→ Working set marked as committed
```

## Cache Refresh Strategy

### On Git Pull:
```python
def refresh_cache_from_git(repo_id: str):
    """Rebuild cache from git workspace"""
    git_service = GitService.for_repo(repo_id)

    # Get all event files
    events_path = git_service.workspace / 'timeline/data/events'

    # Start transaction
    db.begin()

    # Delete old cache for this repo
    db.execute("DELETE FROM timeline_events_cache WHERE source_repo = ?", (repo_id,))

    # Parse and cache all events
    for event_file in events_path.glob('*.{json,md}'):
        event_data = parse_event(event_file)

        # Get git metadata for this file
        git_info = git_service.get_file_history(event_file)

        db.execute("""
            INSERT INTO timeline_events_cache
            (id, source_repo, date, title, summary, importance, json_content,
             git_commit_hash, git_commit_author, git_commit_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_data['id'], repo_id, event_data['date'],
            event_data['title'], event_data.get('summary'),
            event_data.get('importance', 5), json.dumps(event_data),
            git_info['commit_hash'], git_info['author'], git_info['date']
        ))

    # Rebuild FTS5 index
    db.execute("INSERT INTO events_fts(events_fts) VALUES('rebuild')")

    db.commit()
    logger.info(f"Refreshed cache for repo '{repo_id}': {count} events")
```

### When to Refresh:
1. **On startup**: Sync all configured timeline repos
2. **On explicit pull**: API endpoint to refresh specific repo
3. **After commit**: Refresh after pushing changes
4. **Periodic**: Optional background sync (configurable, default off)
5. **Webhook**: GitHub webhook triggers refresh on main repo push

## API Design

### Read Operations (from cache)
```python
# Fast - uses SQLite cache
GET  /api/events?repo=main&actor=Trump
GET  /api/events/search?q=crypto&repos=main,judicial
GET  /api/events/{event_id}?include_git_history=true

# Cross-timeline queries
GET  /api/timelines                           # List all configured timelines
GET  /api/timelines/{repo_id}/events          # Events from specific timeline
GET  /api/analysis/cross-timeline?actor=Koch  # Find actor across all timelines
```

### Working Set Operations
```python
# Accumulate changes
POST /api/working-set/events                  # Add event to working set
PUT  /api/working-set/events/{event_id}       # Update pending event
DELETE /api/working-set/events/{event_id}     # Remove from working set

# Review workflow
GET  /api/working-set/pending                 # All uncommitted changes
GET  /api/working-set/by-creator/{agent_id}   # Changes by specific agent
POST /api/working-set/review                  # Mark events as reviewed

# Commit to git
POST /api/working-set/commit                  # Batch commit to git
POST /api/working-set/commit-pr               # Create PR for batch
```

### Git Sync Operations
```python
# Manual sync control
POST /api/repos/{repo_id}/pull                # Pull latest from git
POST /api/repos/{repo_id}/refresh-cache       # Rebuild cache from workspace
GET  /api/repos/{repo_id}/status              # Git status for repo

# Multi-timeline management
POST /api/repos                               # Register new timeline repo
GET  /api/repos                               # List all configured repos
PUT  /api/repos/{repo_id}/config              # Update repo config
```

## Benefits Over Current Architecture

### 1. **Performance**
- ✅ Fast queries via SQLite cache (no 30-second lag)
- ✅ Full-text search via FTS5
- ✅ No filesystem polling overhead

### 2. **Workflow**
- ✅ Batch commits (accumulate → review → commit)
- ✅ Working set for staging changes
- ✅ Review before commit
- ✅ Natural PR workflow for human review

### 3. **Multi-Timeline**
- ✅ Multiple repos in same database
- ✅ Cross-timeline queries
- ✅ Unified search across all timelines
- ✅ Timeline-specific filtering

### 4. **Git Integration**
- ✅ Git as authoritative source
- ✅ Full history via git log
- ✅ Proper attribution in commits
- ✅ Git metadata in cache (author, date, hash)

### 5. **Simplicity**
- ✅ No FilesystemSyncer (delete 242 lines)
- ✅ No 30-second polling
- ✅ No commit orchestration complexity
- ✅ Clear data flow: git → cache → API

## Migration Path

### Phase 1: Add Cache Layer (2-3 days)
- Create `timeline_events_cache` table
- Create `working_set_events` table
- Add `refresh_cache_from_git()` function
- Test cache refresh performance

### Phase 2: Dual-Mode Operation (2 days)
- APIs read from cache (fallback to old table)
- Verify cache matches old database
- Performance benchmarks

### Phase 3: Working Set API (2-3 days)
- Implement working set endpoints
- Add review workflow
- Batch commit to git functionality

### Phase 4: Multi-Timeline Support (2-3 days)
- Add `timeline_repos` table
- Multi-repo sync
- Cross-timeline queries

### Phase 5: Cut Over & Cleanup (1-2 days)
- Switch all APIs to cache
- Delete `FilesystemSyncer`
- Remove old `timeline_events` table
- Delete sync logic from app_v2.py

**Total: 9-13 days**

## Success Metrics

### Before:
- Sync lag: 30 seconds
- Single timeline: local filesystem only
- Commit workflow: awkward orchestration
- Code: 1,884 lines app_v2.py + 242 lines sync

### After:
- Sync lag: On-demand (instant when needed)
- Multiple timelines: federated across repos
- Commit workflow: batch with review
- Code: ~1,600 lines app_v2.py (delete sync)
- Net: ~400 line reduction + better architecture

## Open Questions

1. **Cache Invalidation**: How aggressive? On every pull or periodic?
2. **Working Set Size**: Limit to N events per agent? Time-based expiry?
3. **Multi-Timeline Search**: Weighted by timeline or treat equally?
4. **Conflict Resolution**: How to handle concurrent edits in working set?
5. **Timeline Discovery**: Manual registration or auto-discover from org?

## Recommendation

**Proceed with hybrid cache architecture** - it combines the best of both approaches:
- Git authoritative (clean, auditable, collaborative)
- Database cache (fast queries, working set, multi-timeline)
- Batch workflow (review before commit)

This architecture supports your vision of:
✅ Multi-timeline federation
✅ Batch review workflow
✅ Fast search across all timelines
✅ Clean git-centric collaborative workflow

---

**Next Steps**:
1. Get approval for hybrid cache approach
2. Implement Phase 1: Cache layer
3. Performance test with 1,580 events
4. Add working set functionality
5. Test multi-timeline support


## Deterministic Formatting for Clean Git Diffs

### The Problem

Bad diffs make review impossible:
```diff
- {"actors": ["Trump", "Musk", "Thiel"], "tags": ["corruption", "crypto"]}
+ {"tags": ["crypto", "corruption"], "actors": ["Musk", "Trump", "Thiel"]}
```
This looks like everything changed, but it's just reordering.

### The Solution: Stable, Deterministic Formatting

#### 1. **Alphabetical Sorting for Lists**

All list fields sorted alphabetically for stable diffs:

```python
def normalize_event(event: dict) -> dict:
    """Normalize event for deterministic serialization"""
    normalized = event.copy()
    
    # Sort all list fields alphabetically
    if 'actors' in normalized:
        normalized['actors'] = sorted(normalized['actors'])
    
    if 'tags' in normalized:
        normalized['tags'] = sorted(normalized['tags'])
    
    # Sources: sort by tier first, then alphabetically by title
    if 'sources' in normalized:
        normalized['sources'] = sorted(
            normalized['sources'],
            key=lambda s: (s.get('tier', 99), s.get('title', ''))
        )
    
    return normalized
```

**Good diff when actor added**:
```diff
  "actors": [
+   "Kushner, Jared",
    "Musk, Elon",
    "Trump, Donald"
  ]
```

#### 2. **Consistent JSON Formatting**

Use Python's `json.dumps` with consistent settings:

```python
def write_event_file(event_id: str, data: dict) -> Path:
    """Write event with deterministic formatting"""
    
    # Normalize data
    normalized = normalize_event(data)
    
    # Write with consistent formatting
    event_path = events_dir / f"{event_id}.json"
    with open(event_path, 'w', encoding='utf-8') as f:
        json.dump(
            normalized,
            f,
            indent=2,              # 2-space indent (GitHub default)
            sort_keys=True,        # Sort object keys alphabetically
            ensure_ascii=False,    # Allow unicode characters
            separators=(',', ': ') # Consistent spacing
        )
        f.write('\n')  # Trailing newline (POSIX standard)
    
    return event_path
```

#### 3. **Field Ordering in JSON**

Use OrderedDict or Python 3.7+ dict ordering guarantee:

```python
from collections import OrderedDict

def order_event_fields(event: dict) -> OrderedDict:
    """Order fields for consistent diffs"""
    ordered = OrderedDict()
    
    # Standard field order
    field_order = [
        'id',
        'date',
        'title',
        'summary',
        'importance',
        'status',
        'actors',
        'tags',
        'sources',
        'related_events',
        'notes'
    ]
    
    # Add fields in defined order
    for field in field_order:
        if field in event:
            ordered[field] = event[field]
    
    # Add any extra fields at end (sorted)
    extra_fields = sorted(set(event.keys()) - set(field_order))
    for field in extra_fields:
        ordered[field] = event[field]
    
    return ordered
```

#### 4. **Source Normalization**

Consistent source formatting:

```python
def normalize_source(source: dict) -> dict:
    """Normalize source for stable diffs"""
    return OrderedDict([
        ('url', source['url']),
        ('title', source.get('title', '')),
        ('publisher', source.get('publisher', '')),
        ('date', source.get('date', '')),
        ('tier', source.get('tier', 2)),
        ('archive_url', source.get('archive_url', ''))
    ])

# Sources sorted by: tier (ascending), then title (alphabetical)
sources = sorted(
    [normalize_source(s) for s in event['sources']],
    key=lambda s: (s['tier'], s['title'])
)
```

### Example: Clean Diff After QA Enhancement

**Before (agent-created)**:
```json
{
  "id": "2025-01-15--trump-crypto-deal",
  "date": "2025-01-15",
  "title": "Trump announces crypto partnership",
  "summary": "Basic summary",
  "importance": 7,
  "actors": ["Trump, Donald"],
  "tags": ["crypto"],
  "sources": [
    {
      "url": "https://example.com/article",
      "title": "News article",
      "tier": 2
    }
  ]
}
```

**After (QA enhanced)**:
```json
{
  "id": "2025-01-15--trump-crypto-deal",
  "date": "2025-01-15",
  "title": "Trump announces crypto partnership",
  "summary": "Enhanced summary with more context and details",
  "importance": 8,
  "actors": ["Musk, Elon", "Trump, Donald"],
  "tags": ["conflicts-of-interest", "crypto"],
  "sources": [
    {
      "archive_url": "https://archive.org/...",
      "date": "2025-01-15",
      "publisher": "Reuters",
      "tier": 1,
      "title": "Trump crypto deal details",
      "url": "https://reuters.com/article"
    },
    {
      "date": "2025-01-15",
      "publisher": "Example News",
      "tier": 2,
      "title": "News article",
      "url": "https://example.com/article"
    }
  ]
}
```

**Git diff**:
```diff
   "summary": "Enhanced summary with more context and details",
-  "importance": 7,
+  "importance": 8,
   "actors": [
+    "Musk, Elon",
     "Trump, Donald"
   ],
   "tags": [
+    "conflicts-of-interest",
     "crypto"
   ],
   "sources": [
+    {
+      "archive_url": "https://archive.org/...",
+      "date": "2025-01-15",
+      "publisher": "Reuters",
+      "tier": 1,
+      "title": "Trump crypto deal details",
+      "url": "https://reuters.com/article"
+    },
     {
+      "date": "2025-01-15",
+      "publisher": "Example News",
       "tier": 2,
       "title": "News article",
       "url": "https://example.com/article"
     }
   ]
```

**Clear changes**:
- ✅ Summary enhanced
- ✅ Importance increased 7→8
- ✅ Actor added: Musk
- ✅ Tag added: conflicts-of-interest
- ✅ Tier-1 source added (Reuters)
- ✅ Original source enhanced with metadata

### Alternative: Markdown Format for Better Diffs

Consider Markdown instead of JSON for even cleaner diffs:

**events/2025-01-15--trump-crypto-deal.md**:
```markdown
---
id: 2025-01-15--trump-crypto-deal
date: 2025-01-15
title: Trump announces crypto partnership
importance: 8
status: validated
actors:
  - Musk, Elon
  - Trump, Donald
tags:
  - conflicts-of-interest
  - crypto
sources:
  - url: https://reuters.com/article
    title: Trump crypto deal details
    publisher: Reuters
    date: 2025-01-15
    tier: 1
    archive_url: https://archive.org/...
  - url: https://example.com/article
    title: News article
    publisher: Example News
    date: 2025-01-15
    tier: 2
---

Enhanced summary with more context and details.

## Background

Additional context goes here...

## Significance

Why this matters...
```

**Markdown diff is even cleaner**:
```diff
 ---
 date: 2025-01-15
 title: Trump announces crypto partnership
-importance: 7
+importance: 8
+status: validated
 actors:
+  - Musk, Elon
   - Trump, Donald
 tags:
+  - conflicts-of-interest
   - crypto
 sources:
+  - url: https://reuters.com/article
+    title: Trump crypto deal details
+    publisher: Reuters
+    tier: 1
   - url: https://example.com/article
     title: News article
     tier: 2
 ---

-Basic summary
+Enhanced summary with more context and details.
+
+## Background
+
+Additional context goes here...
```

### Implementation: Normalization Pipeline

```python
class EventNormalizer:
    """Ensure deterministic event formatting for clean git diffs"""
    
    def __init__(self):
        self.field_order = [
            'id', 'date', 'title', 'summary', 'importance',
            'status', 'actors', 'tags', 'sources', 'related_events'
        ]
    
    def normalize(self, event: dict) -> OrderedDict:
        """Normalize event for deterministic serialization"""
        normalized = OrderedDict()
        
        # Add fields in standard order
        for field in self.field_order:
            if field in event:
                normalized[field] = self._normalize_field(field, event[field])
        
        # Add any extra fields (sorted alphabetically)
        extra = sorted(set(event.keys()) - set(self.field_order))
        for field in extra:
            normalized[field] = self._normalize_field(field, event[field])
        
        return normalized
    
    def _normalize_field(self, field: str, value: Any) -> Any:
        """Normalize specific field types"""
        if field in ('actors', 'tags'):
            # Sort lists alphabetically
            return sorted(value) if isinstance(value, list) else value
        
        elif field == 'sources':
            # Sort sources by tier, then title
            if isinstance(value, list):
                return sorted(
                    [self._normalize_source(s) for s in value],
                    key=lambda s: (s.get('tier', 99), s.get('title', ''))
                )
            return value
        
        elif field == 'related_events':
            # Sort related event IDs
            return sorted(value) if isinstance(value, list) else value
        
        else:
            return value
    
    def _normalize_source(self, source: dict) -> OrderedDict:
        """Normalize source for stable diffs"""
        # Standard source field order
        source_order = ['url', 'title', 'publisher', 'date', 'tier', 'archive_url']
        normalized = OrderedDict()
        
        for field in source_order:
            if field in source:
                normalized[field] = source[field]
        
        return normalized

# Usage in git service
normalizer = EventNormalizer()

def write_event(event_id: str, data: dict):
    """Write event with deterministic formatting"""
    normalized = normalizer.normalize(data)
    event_path = workspace / f'timeline/data/events/{event_id}.json'
    
    with open(event_path, 'w', encoding='utf-8') as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)
        f.write('\n')  # Trailing newline
```

### Pre-Commit Hook for Enforcement

Add pre-commit hook to enforce formatting:

```python
# .git/hooks/pre-commit
#!/usr/bin/env python3
"""Enforce deterministic event formatting"""

import json
import sys
from pathlib import Path

def check_event_formatting(file_path):
    """Verify event has deterministic formatting"""
    with open(file_path) as f:
        content = f.read()
    
    # Parse and re-serialize
    event = json.loads(content)
    normalized = normalizer.normalize(event)
    canonical = json.dumps(normalized, indent=2, ensure_ascii=False) + '\n'
    
    if content != canonical:
        print(f"ERROR: {file_path} not properly formatted")
        print("Run: python scripts/normalize_events.py")
        return False
    
    return True

# Check all staged event files
staged_events = [
    f for f in Path('timeline/data/events').glob('*.json')
    if f.is_file()
]

if not all(check_event_formatting(f) for f in staged_events):
    sys.exit(1)
```

### Benefits

1. **Clean Diffs**: Only actual changes shown, not formatting
2. **Easy Review**: Reviewers see exactly what was added/changed
3. **Merge Friendly**: Sorted lists reduce merge conflicts
4. **Consistent**: All events follow same formatting rules
5. **Automated**: Pre-commit hook enforces standards

### Migration

```python
# Normalize all existing events
def normalize_all_events():
    """One-time normalization of all existing events"""
    normalizer = EventNormalizer()
    events_dir = Path('timeline/data/events')
    
    for event_file in events_dir.glob('*.json'):
        with open(event_file) as f:
            event = json.load(f)
        
        # Normalize
        normalized = normalizer.normalize(event)
        
        # Write back with deterministic formatting
        with open(event_file, 'w', encoding='utf-8') as f:
            json.dump(normalized, f, indent=2, ensure_ascii=False)
            f.write('\n')
        
        print(f"Normalized: {event_file.name}")

# Run once to normalize existing timeline
normalize_all_events()

# Commit normalized versions
git add timeline/data/events/*.json
git commit -m "Normalize all events for deterministic formatting"
```

