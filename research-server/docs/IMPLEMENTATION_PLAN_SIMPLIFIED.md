# Simplified Git-Sync Implementation Plan

**Status**: Practical Incremental Approach
**Date**: 2025-10-22
**Effort**: 2-3 days (vs 7-11 days for full rewrite)

## Key Simplifications

Based on user feedback:
1. ✅ **Markdown only** - Drop JSON support (all events already converted)
2. ✅ **Reuse existing database** - Keep timeline_events, event_metadata, etc.
3. ✅ **Defer multi-timeline** - No other timelines exist yet (add later)
4. ✅ **Manual sync** - On startup + user-triggered (no 30-second polling)

## Current vs Proposed

### Current (FilesystemSyncer):
```
Local Filesystem
    ↓ 30-second poll
Parse JSON/Markdown
    ↓
Update Database
```

### Proposed (GitSyncer):
```
Git Repository
    ↓ git pull (on startup + manual trigger)
Parse Markdown (Hugo/YAML frontmatter)
    ↓
Update Database (same structure)
```

## Implementation: Replace FilesystemSyncer with GitSyncer

### Step 1: Create GitSyncer (replaces FilesystemSyncer)

**New file**: `services/git_sync.py`

```python
"""
Git Syncer - Replaces FilesystemSyncer with git-based sync
Syncs timeline events from git repository on demand
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from services.git_service import GitService
from parsers.factory import EventParserFactory
from models import TimelineEvent, ActivityLog
from utils.event_normalizer import EventNormalizer

logger = logging.getLogger(__name__)


class GitSyncer:
    """Git-based event syncer - replaces filesystem polling"""

    def __init__(self, app, session_factory, git_service: GitService = None):
        """
        Initialize GitSyncer

        Args:
            app: Flask app instance (for config)
            session_factory: SQLAlchemy session factory
            git_service: GitService instance (creates default if None)
        """
        self.app = app
        self.Session = session_factory
        self.git_service = git_service or GitService()
        self.parser_factory = EventParserFactory()
        self.normalizer = EventNormalizer()

    def sync_from_git(self, pull_first: bool = True) -> Dict[str, Any]:
        """
        Sync events from git repository to database

        Args:
            pull_first: If True, git pull before syncing

        Returns:
            Dict with sync statistics
        """
        stats = {
            'success': False,
            'events_synced': 0,
            'events_added': 0,
            'events_updated': 0,
            'events_unchanged': 0,
            'errors': [],
            'git_pull': None
        }

        db = self.Session()
        try:
            # Pull latest from git
            if pull_first:
                pull_result = self.git_service.pull_latest()
                stats['git_pull'] = pull_result

                if not pull_result.get('success'):
                    stats['errors'].append(f"Git pull failed: {pull_result.get('error')}")
                    return stats

                logger.info(f"Git pull: {pull_result.get('new_commits', 0)} new commits")

            # Get events directory from git workspace
            events_path = self.git_service.workspace / 'timeline' / 'data' / 'events'

            if not events_path.exists():
                stats['errors'].append(f"Events path not found: {events_path}")
                return stats

            # Sync all markdown events
            for event_file in events_path.glob('*.md'):
                try:
                    # Skip README and other non-event files
                    if event_file.name.upper() in ('README.MD', 'INDEX.MD'):
                        continue

                    result = self._sync_event_file(db, event_file)

                    if result == 'added':
                        stats['events_added'] += 1
                    elif result == 'updated':
                        stats['events_updated'] += 1
                    elif result == 'unchanged':
                        stats['events_unchanged'] += 1

                    stats['events_synced'] += 1

                except Exception as e:
                    error_msg = f"Error syncing {event_file.name}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)

            # Commit database changes
            db.commit()

            # Log activity
            activity = ActivityLog(
                action='git_sync',
                agent='system',
                details={
                    'events_added': stats['events_added'],
                    'events_updated': stats['events_updated'],
                    'events_unchanged': stats['events_unchanged']
                }
            )
            db.add(activity)
            db.commit()

            stats['success'] = True
            logger.info(f"Git sync complete: +{stats['events_added']} ~{stats['events_updated']} ={stats['events_unchanged']}")

        except Exception as e:
            logger.error(f"Git sync error: {e}")
            stats['errors'].append(str(e))
            db.rollback()
        finally:
            db.close()

        return stats

    def _sync_event_file(self, db, event_file: Path) -> str:
        """
        Sync single event file to database

        Returns:
            'added', 'updated', or 'unchanged'
        """
        # Calculate file hash
        import hashlib
        with open(event_file, 'rb') as f:
            file_content = f.read()
            file_hash = hashlib.md5(file_content).hexdigest()

        # Extract event ID from filename
        event_id = event_file.stem

        # Check if exists
        existing = db.query(TimelineEvent).filter_by(id=event_id).first()

        # If exists and hash unchanged, skip
        if existing and existing.file_hash == file_hash:
            return 'unchanged'

        # Parse event (Markdown with YAML frontmatter)
        try:
            data = self.parser_factory.parse_event(event_file)
        except ValueError as e:
            raise ValueError(f"Parse error: {e}")

        # Normalize event data
        normalized_data = self.normalizer.normalize(data)

        # Create or update event
        if not existing:
            event = TimelineEvent(id=event_id)
            result = 'added'
        else:
            event = existing
            result = 'updated'

        # Update fields
        event.json_content = normalized_data
        event.date = normalized_data.get('date', '')
        event.title = normalized_data.get('title', '')
        event.summary = normalized_data.get('summary', '')
        event.importance = normalized_data.get('importance', 5)
        event.status = normalized_data.get('status', 'confirmed')
        event.file_path = str(event_file)
        event.file_hash = file_hash
        event.last_synced = datetime.now()

        if not existing:
            db.add(event)

        logger.debug(f"Synced {event_id} ({result})")

        return result

    def get_git_status(self) -> Dict[str, Any]:
        """Get current git repository status"""
        return self.git_service.get_status()

    def clone_or_update_repo(self) -> Dict[str, Any]:
        """Ensure git repository is cloned and up to date"""
        return self.git_service.clone_or_update()
```

### Step 2: Update app_v2.py

Replace FilesystemSyncer with GitSyncer:

```python
# OLD (in app_v2.py)
from services.filesystem_sync import FilesystemSyncer
syncer = FilesystemSyncer(app, Session, sync_lock)
syncer.start()  # Starts 30-second polling thread

# NEW
from services.git_sync import GitSyncer
from services.git_service import GitService

git_service = GitService()  # Uses config from GitConfig
git_syncer = GitSyncer(app, Session, git_service)

# Sync on startup (no background thread)
startup_sync = git_syncer.sync_from_git(pull_first=True)
logger.info(f"Startup sync: {startup_sync['events_synced']} events")
```

### Step 3: Add Manual Sync Endpoint

```python
# Add to app_v2.py or routes/system.py

@app.route('/api/sync', methods=['POST'])
@require_api_key
def trigger_sync():
    """Manually trigger git sync"""
    try:
        # Optional: force git pull
        force_pull = request.json.get('pull', True) if request.json else True

        # Sync from git
        result = git_syncer.sync_from_git(pull_first=force_pull)

        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Sync completed',
                'events_added': result['events_added'],
                'events_updated': result['events_updated'],
                'events_unchanged': result['events_unchanged'],
                'total_synced': result['events_synced']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Sync failed',
                'errors': result['errors']
            }), 500

    except Exception as e:
        logger.error(f"Sync endpoint error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/git/status', methods=['GET'])
def git_status():
    """Get git repository status"""
    try:
        status = git_syncer.get_git_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500
```

### Step 4: Update Configuration

Ensure GitConfig is properly configured:

```python
# In .env or environment
TIMELINE_REPO_URL=https://github.com/markramm/KleptocracyTimeline
TIMELINE_BRANCH=main
TIMELINE_WORKSPACE=/tmp/timeline-workspace
GITHUB_TOKEN=<optional-for-private-repos>
```

### Step 5: Update Markdown Parser

Ensure parser handles Hugo-style frontmatter:

```python
# parsers/markdown_parser.py should already support this
# Format:
# ---
# id: YYYY-MM-DD--slug
# date: YYYY-MM-DD
# title: Event title
# actors:
#   - Actor 1
#   - Actor 2
# ---
#
# Event content in markdown...
```

## What Gets Deleted

### Delete FilesystemSyncer:
- ✅ `services/filesystem_sync.py` (242 lines)
- ✅ 30-second polling thread
- ✅ sync_lock threading primitives
- ✅ seed_priorities() from filesystem (keep in database)

### Keep Everything Else:
- ✅ Database structure (timeline_events, event_metadata, etc.)
- ✅ All API endpoints
- ✅ Validation system
- ✅ QA system
- ✅ Research priorities

## Migration Steps

### Phase 1: Add GitSyncer (1 day)
1. Create `services/git_sync.py` with GitSyncer class
2. Add to app_v2.py (don't delete FilesystemSyncer yet)
3. Test: `git_syncer.sync_from_git()` works

### Phase 2: Switch Over (1 day)
1. Replace FilesystemSyncer with GitSyncer in app_v2.py
2. Add manual sync endpoint
3. Test: Startup sync works, manual sync works
4. Verify: No JSON files are being synced (Markdown only)

### Phase 3: Cleanup (0.5 days)
1. Delete `services/filesystem_sync.py`
2. Remove sync_lock, threading imports
3. Remove FilesystemSyncer references
4. Update documentation

**Total: 2-3 days**

## Benefits

### Immediate:
- ✅ Remove 30-second polling overhead
- ✅ Explicit sync control (on startup + manual)
- ✅ Direct git integration (pull latest)
- ✅ ~242 lines deleted (FilesystemSyncer)

### Enables Future:
- ✅ Working set (stage changes before commit)
- ✅ Multi-timeline (when other timelines exist)
- ✅ Git write operations (commit events back)

## Testing Plan

### Test 1: Initial Clone & Sync
```bash
# Remove existing database and workspace
rm unified_research.db
rm -rf /tmp/timeline-workspace

# Start server (should clone repo and sync)
python3 app_v2.py

# Verify: All markdown events loaded
sqlite3 unified_research.db "SELECT COUNT(*) FROM timeline_events"
# Should match number of .md files
```

### Test 2: Manual Sync
```bash
# Make change to timeline repo (outside server)
cd /path/to/KleptocracyTimeline
# ... edit an event ...
git add . && git commit -m "Update event"
git push

# Trigger manual sync
curl -X POST http://localhost:5558/api/sync \
  -H "X-API-Key: test-key"

# Verify: Event updated in database
```

### Test 3: Startup Sync
```bash
# Stop server
# Make changes to remote repo
# Start server
python3 app_v2.py

# Verify: Startup log shows sync occurred
# Verify: Changes reflected in database
```

## Comparison: Old vs New

| Aspect | FilesystemSyncer | GitSyncer |
|--------|------------------|-----------|
| **Sync Trigger** | 30-second polling | On demand |
| **Source** | Local filesystem | Git repository |
| **Updates** | Continuous | Startup + manual |
| **Code** | 242 lines | ~180 lines |
| **Threading** | Background thread | No threading |
| **Format** | JSON + Markdown | Markdown only |
| **Git Awareness** | No | Yes (pull, status) |

## Risk Mitigation

### Risk 1: Startup Sync Slow
- **Mitigation**: Git pull is fast (<1 sec for no changes)
- **Fallback**: Make startup sync async, return immediately

### Risk 2: Manual Sync Conflicts
- **Mitigation**: GitService handles pull conflicts
- **Handling**: Return error, user resolves in git

### Risk 3: Parse Errors
- **Mitigation**: Same parser as before (already tested)
- **Handling**: Log errors, continue with other events

## Open Questions

1. **Auto-sync on PR merge**: Add GitHub webhook for automatic sync?
2. **Sync frequency**: Just startup + manual, or also periodic (every 5 min)?
3. **Conflict handling**: What if local changes exist when pulling?

## Recommendation

**Proceed with simplified git-sync implementation**:
- Much less risk than full rewrite
- Reuses existing database structure
- Incremental improvement (delete FilesystemSyncer)
- Enables future enhancements (working set, write operations)

**Estimated effort**: 2-3 days vs 7-11 days for full hybrid cache

---

**Next Steps**:
1. Create `services/git_sync.py` with GitSyncer class
2. Test alongside existing FilesystemSyncer
3. Switch over when confirmed working
4. Delete FilesystemSyncer
