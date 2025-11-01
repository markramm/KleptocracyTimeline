# Architecture Redesign: Git-Centric Research Monitor

**Status**: Proposal
**Date**: 2025-10-22
**Priority**: High - Fundamental simplification

## Executive Summary

Redesign Research Monitor to use git repository as the single source of truth, eliminating the database mirror, filesystem sync complexity, and 30-second lag. This reduces code by ~440 lines net and enables proper multi-tenant, collaborative workflows.

## Problem Statement

### Current Architecture is Overly Complex:
```
Timeline Repo → FilesystemSyncer (30s poll) → SQLite Mirror → API → Agents
```

**Issues**:
- Dual source of truth (files + database)
- 242 lines of sync logic we just extracted
- 30-second lag between file changes and API visibility
- Awkward commit orchestration (server tracks but doesn't commit)
- No git history/attribution in API responses
- Not multi-tenant ready

## Proposed Architecture

### Simple Git-Centric Flow:
```
Timeline Repo (GitHub) → git clone/pull → Workspace → Direct Read/Write → API → Agents
```

**Benefits**:
- Single source of truth (git only)
- No sync lag - instant updates
- Proper attribution (every change is a commit)
- Full git history available
- Multi-tenant ready (workspace per repo)
- Natural PR-based review workflow

## Key Design Decisions

### 1. Events: Read from Git, Write via Git Commits

**Read Path**:
```python
# Current (database)
event = db.query(TimelineEvent).filter_by(id=event_id).first()

# Proposed (git)
event = git_service.read_event(event_id)  # Parses JSON from workspace
```

**Write Path**:
```python
# Current (filesystem + orchestrated commit)
write_event_file(event_data)
events_since_commit += 1
# Wait for threshold, then signal orchestrator

# Proposed (direct git commit)
git_service.write_event(event_id, event_data, author="agent-5")
git_service.commit(f"Add: {event_id} by agent-5")
git_service.push()  # or create_pr()
```

### 2. Database: Metadata Only

**Keep**:
- Research Priorities (workflow state)
- Validation Runs (batch tracking)
- Validation Logs (audit trail)
- QA Reservations (prevent concurrent work)
- Activity Logs (system events)

**Remove**:
- `timeline_events` table (~1,580 rows mirrored)
- `events_fts` (full-text search index)
- `event_metadata` (can be in event file or separate)
- File hash tracking
- Last synced timestamps

### 3. Search Strategy

**Option A: Git Grep** (Simple)
```python
# Fast for 1,580 events
result = subprocess.run(['git', 'grep', '-i', query, '--', 'timeline/data/events/'])
```

**Option B: In-Memory Cache** (Faster)
```python
# Load all events on startup, refresh on pull
events_cache = {event_id: parse_event(path) for path in event_files}
# Search in memory
results = [e for e in events_cache.values() if query in e['title']]
```

**Option C: SQLite FTS5** (Keep search only)
```python
# Rebuild FTS5 index after pull
# Keep search fast, but don't mirror all event data
```

**Recommendation**: Start with Option B (simple in-memory cache for 1,580 events)

### 4. Concurrent Edit Handling

**Strategy: Branch Per Batch**
```python
# Research batch creates branch
git_service.create_branch(f"research-batch-{timestamp}")

# All events in batch go to this branch
for event in batch:
    git_service.write_event(event_id, data)
    git_service.commit(f"Add: {event_id}")

# Create PR when batch complete
git_service.create_pr("Research batch: 10 new events")
```

**Benefits**:
- No concurrent edit conflicts (each batch on own branch)
- Natural review workflow
- Git handles merge conflicts if needed

## Implementation Plan

### Phase 1: Add Git Read Operations (1-2 days)

**Add to GitService**:
```python
def read_event(event_id: str) -> dict:
    """Read and parse event from git workspace"""

def list_events(filters: dict = None) -> List[dict]:
    """List all events with optional filtering"""

def search_events(query: str) -> List[dict]:
    """Search events by text query"""
```

**Test in parallel** with existing database reads

### Phase 2: Add Git Write Operations (1-2 days)

**Add to GitService**:
```python
def write_event(event_id: str, data: dict, author: str = None) -> Path:
    """Write event file to workspace"""

def delete_event(event_id: str, author: str = None):
    """Archive event (move to archive/)"""

def commit_and_push(message: str, files: List[Path] = None):
    """Commit changes and push to remote"""
```

**Test**: Create events via API, verify git commits

### Phase 3: Switch APIs to Git (2-3 days)

**Update Routes**:
- `routes/events.py`: Read from git instead of database
- `routes/timeline.py`: Read from git instead of database
- `routes/qa.py`: Read from git, write via git commits

**Keep database** for:
- QA reservations (prevent concurrent work)
- Validation run tracking
- Activity logs

### Phase 4: Remove Database Mirror (1 day)

**Delete**:
- `services/filesystem_sync.py` (242 lines)
- `models.py`: TimelineEvent, EventMetadata
- `app_v2.py`: Sync logic, events_since_commit tracking
- Database initialization for events table
- FTS5 index creation

**Net code reduction**: ~440 lines

### Phase 5: Optimize & Polish (1-2 days)

**Add**:
- In-memory event cache for fast search
- Cache invalidation on git pull
- Batch commit optimization
- Error handling for git failures
- Metrics (cache hits, git operations)

## Workflow Examples

### Workflow 1: Research Agent Creates 10 Events

```python
# 1. Create branch for batch
git_service.create_branch("research-batch-20250122-143022")

# 2. Add events
for event_data in research_results:
    git_service.write_event(event_data['id'], event_data, author="research-agent-1")
    git_service.commit(f"Add: {event_data['id']} - {event_data['title'][:50]}")

# 3. Push and create PR
git_service.push("research-batch-20250122-143022")
pr_url = git_service.create_pr(
    title="Research: 10 events on Trump crypto dealings",
    body="Research priority RP-145 completed. See commit history for details."
)

# 4. Return PR URL to agent
return {"status": "success", "pr_url": pr_url, "events_created": 10}
```

### Workflow 2: QA Agent Validates Event

```python
# 1. Get next event from git (reserve in database)
event = git_service.read_event(event_id)
db.add(QAReservation(event_id=event_id, agent="qa-agent-5"))

# 2. Agent enhances event
enhanced_event = qa_agent.validate_and_enhance(event)

# 3. Write back with git commit
git_service.write_event(event_id, enhanced_event, author="qa-agent-5")
git_service.commit(f"QA: Enhanced {event_id} - added sources, improved summary")
git_service.push()  # Direct push for trusted QA agents

# 4. Log validation
db.add(ValidationLog(event_id=event_id, agent="qa-agent-5", quality_score=9.0))
```

### Workflow 3: Researcher Reviews PR

```
1. GitHub PR shows: "Research: 10 events on Trump crypto dealings"
2. Researcher sees clean git diff for each event file
3. GitHub review UI allows inline comments
4. Researcher merges PR → events immediately live
5. Local Research Monitor pulls latest
```

## Risk Mitigation

### Risk 1: Search Performance
- **Mitigation**: In-memory cache for 1,580 events (~5MB RAM)
- **Fallback**: Keep SQLite FTS5 for search only

### Risk 2: Git Operation Failures
- **Mitigation**: Wrap all git operations in try/catch
- **Rollback**: Git reset on failed commits
- **Monitoring**: Log all git operations

### Risk 3: Concurrent Writes
- **Mitigation**: Branch per batch strategy
- **Database**: QA reservation system prevents concurrent work on same event

### Risk 4: Migration Complexity
- **Mitigation**: Phased rollout (5 phases above)
- **Parallel Operation**: Phase 1-2 test git operations without switching over
- **Rollback Plan**: Keep database mirror until Phase 4 proves stable

## Success Metrics

### Before (Current):
- app_v2.py: 1,884 lines (after Phase 1 cleanup)
- FilesystemSyncer: 242 lines
- Sync lag: 30 seconds
- Code complexity: High (dual source of truth)

### After (Git-Centric):
- app_v2.py: ~1,500 lines (remove sync logic)
- FilesystemSyncer: Deleted
- Sync lag: 0 seconds (direct git)
- Code complexity: Low (single source of truth)
- Net reduction: ~440 lines + massive conceptual simplification

## Questions for Discussion

1. **Search Performance**: Start with in-memory cache or keep FTS5?
2. **PR vs Direct Push**: Require PR review for all agents or trust QA agents?
3. **Event Format**: Keep JSON or migrate to Markdown for better git diffs?
4. **Multi-Tenant**: Support multiple timeline repos from day 1 or add later?
5. **Caching Strategy**: How aggressive? Invalidation on every pull?

## Recommendation

**Proceed with git-centric redesign** - the conceptual simplification and workflow improvements far outweigh the implementation effort (7-10 days). The current sync-based architecture is fighting against git's natural strengths.

**Start with Phase 1** (git read operations) immediately to validate performance before committing to full migration.

---

**Next Steps**:
1. ✅ Get approval for architectural direction
2. Implement Phase 1: Git read operations
3. Performance test with 1,580 events
4. If performance good → proceed with Phases 2-5
5. If performance issues → adjust strategy (FTS5, caching)
