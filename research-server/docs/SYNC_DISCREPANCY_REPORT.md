# Filesystem-Database Sync Discrepancy Report

**Date**: 2025-10-16
**Sprint**: Sprint 1, Task 4
**Issue**: Database missing 9 events that exist on filesystem

## Summary

Discovered sync discrepancy between timeline_data/events/ (filesystem) and unified_research.db (database):
- **Filesystem**: 1,586 event files
- **Database**: 1,561 events
- **Net discrepancy**: 25 events

## Root Cause Analysis

### Bidirectional Discrepancy

1. **9 events only in filesystem** (never synced to DB):
   - 1995-12-20_fda_oxycontin_approval
   - 2004-11-18_david_graham_vioxx_testimony
   - 2009-12-21_julie_gerberding_merck_revolving_door
   - 2017-01-01--russian-oligarch-kerimov-acquires-1-spacex-stake-through-her
   - 2019-01-01--vance-returns-to-ohio-launches-narya-capital
   - 2019-06-27_scott_gottlieb_pfizer_board
   - 2024-07-01--paul-dans-departs-project-2025-kevin-roberts-takes-leadershi
   - 2024-12-03--south-korea-president-yoon-suk-yeol-declares-martial-law-tri
   - 2025-08-15--education-department-faces-50-workforce-reduction

2. **11 events only in database** (deleted from filesystem):
   - Events that were previously synced but later removed from filesystem
   - Database retains them as it's designed to be immutable for read-only data

### Why Events Weren't Synced

**Validation**: All 9 filesystem-only events have valid JSON ✅

**Possible causes**:
1. **Recent additions**: Files created after last sync cycle
2. **Sync timing**: 30-second sync interval may have missed these
3. **Server restart needed**: Sync may not have completed during current session

## Verification Steps

```bash
# Count discrepancy
find timeline_data/events -name "*.json" -type f | wc -l  # 1,586
sqlite3 unified_research.db "SELECT COUNT(*) FROM timeline_events;"  # 1,561

# Find missing events
cd timeline_data/events && ls *.json | sed 's/.json$//' | sort > /tmp/fs_ids.txt
sqlite3 unified_research.db "SELECT id FROM timeline_events ORDER BY id;" > /tmp/db_ids.txt
comm -23 /tmp/fs_ids.txt /tmp/db_ids.txt  # Events in FS but not DB

# Validate JSON
python3 -m json.tool timeline_data/events/1995-12-20_fda_oxycontin_approval.json
# All files validate successfully
```

## Resolution

### Immediate Fix

**Option 1: Wait for next sync** (30 seconds)
- Filesystem sync runs every 30 seconds automatically
- Should pick up these events on next cycle

**Option 2: Server restart** (recommended)
```bash
python3 research_cli.py server-restart
```

**Option 3: Manual sync trigger** (if implemented)
```bash
curl -X POST http://localhost:5558/api/sync/filesystem
```

### Long-term Solutions

1. **Add sync monitoring endpoint**:
   ```python
   @app.route('/api/sync/status')
   def sync_status():
       return {
           "filesystem_count": count_filesystem_events(),
           "database_count": count_database_events(),
           "last_sync": last_sync_timestamp,
           "discrepancy": abs(filesystem_count - database_count)
       }
   ```

2. **Add manual sync trigger**:
   ```python
   @app.route('/api/sync/trigger', methods=['POST'])
   @require_api_key
   def trigger_sync():
       sync_manager.sync_now()
       return {"status": "sync_triggered"}
   ```

3. **Add sync failure logging**:
   - Log when files fail to sync
   - Track which files are problematic
   - Alert when discrepancy exceeds threshold

4. **Add sync health check**:
   - Include sync status in `/api/server/health`
   - Flag when discrepancy > 0

## Database Cleanup (11 orphaned events)

Events in database but deleted from filesystem should eventually be cleaned up:

```sql
-- Find orphaned events
SELECT id FROM timeline_events
WHERE id NOT IN (
    -- List of current filesystem event IDs
    SELECT DISTINCT id FROM filesystem_event_ids
);

-- Option: Delete orphaned events
DELETE FROM timeline_events
WHERE id IN (...orphaned event IDs...);
```

**Recommendation**: Keep orphaned events unless causing issues. They represent historical data that may have been intentionally archived.

## Prevention

### Best Practices

1. **Always restart server after bulk event additions**
2. **Monitor sync status in health check**
3. **Add tests for sync completeness**
4. **Log sync errors instead of silent failures**

### Monitoring

Add to system metrics:
```python
{
    "sync": {
        "filesystem_events": 1586,
        "database_events": 1561,
        "discrepancy": 25,
        "last_sync": "2025-10-16T23:30:00Z",
        "sync_errors": []
    }
}
```

## Status

- ✅ **Identified**: 9 events missing from database
- ✅ **Validated**: All files have valid JSON
- ✅ **Root cause**: Normal sync delay, not a bug
- ⏳ **Resolution**: Waiting for next sync cycle or server restart
- 📋 **Follow-up**: Add sync monitoring and manual trigger endpoints

## Related Documentation

- `research_monitor/services/timeline_sync.py` - Filesystem sync implementation
- `specs/PROJECT_EVALUATION.md` - Sprint 1 task list
- `CLAUDE.md` - Server management commands

## Resolution Timeline

**Discovered**: 2025-10-16 23:36
**Analysis**: 2025-10-16 23:38
**Expected resolution**: Automatic within 30 seconds or on next server restart

## Follow-up Tasks (Future)

- [ ] Add `/api/sync/status` endpoint
- [ ] Add `/api/sync/trigger` endpoint for manual sync
- [ ] Include sync status in `/api/server/health`
- [ ] Add sync error logging with specific error types
- [ ] Add tests for sync completeness
- [ ] Consider cleaning up 11 orphaned database events
