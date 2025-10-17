# Sprint 2 Progress Report

**Started**: 2025-10-16
**Status**: In Progress (Task 1 partially complete)

## Task 1: Consolidate Blueprint Helpers (2 hours) - IN PROGRESS

### Completed
- ✅ Created `research_monitor/blueprint_utils.py` (413 lines)
  - Database access: `get_db()`
  - Authentication: `require_api_key()` decorator
  - Activity logging: `log_activity()`
  - Caching: `cache_with_invalidation()`, `invalidate_cache()`
  - Response helpers: `success_response()`, `error_response()`
  - Pagination helpers: `paginate_query()`
  - Request helpers: `get_request_json()`, `get_query_params()`

- ✅ Updated 3/8 blueprint files to use shared utilities:
  - `routes/system.py` - Imports get_db, log_activity, success/error_response
  - `routes/priorities.py` - Imports get_db, log_activity, success/error_response
  - `routes/git.py` - Ready to import (backup exists)

### Remaining Work (1 hour)

Need to update 5 more blueprint files:
1. `routes/git.py` - Remove duplicate `get_db()` (restore from backup first)
2. `routes/timeline.py` - Remove duplicate `get_db()` and `get_cache()`
3. `routes/events.py` - Remove duplicate `get_db()` and `require_api_key()`
4. `routes/qa.py` - Remove duplicates: `get_db()`, `require_api_key()`, `cache_with_invalidation()`
5. `routes/validation_runs.py` - Remove duplicate `get_db()` and `require_api_key()`

### Update Pattern for Each File

For each blueprint file:

```python
# OLD (duplicated in each file):
def get_db():
    """Get database session from app_v2"""
    from research_monitor import app_v2
    return app_v2.get_db()

def require_api_key(f):
    """API key authentication decorator"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from research_monitor import app_v2
        api_key_decorator = app_v2.require_api_key
        return api_key_decorator(f)(*args, **kwargs)
    return decorated_function

# NEW (import from shared utilities):
from research_monitor.blueprint_utils import get_db, require_api_key, log_activity
```

### Code Reduction Impact

**Before**:
- 7 files × ~15 lines each = ~105 lines of duplicate code
- Maintenance nightmare (update in 7 places)

**After**:
- 1 file (blueprint_utils.py) with 413 lines of well-documented utilities
- All blueprints import from single source
- Easy to extend and maintain

### Testing Checklist

After updating each file:
- [ ] File imports successfully
- [ ] No NameError or ImportError
- [ ] Server restarts without errors
- [ ] `/api/server/health` responds correctly
- [ ] Endpoints in that blueprint still work

### Manual Update Steps

1. **Restore from backup** (if script attempted edits):
   ```bash
   cp research_monitor/routes/git.py.bak research_monitor/routes/git.py
   ```

2. **Edit imports section** - Add after existing imports:
   ```python
   # Import shared utilities
   from research_monitor.blueprint_utils import get_db, require_api_key, log_activity
   ```

3. **Remove duplicate function definitions**:
   - Delete `def get_db():` function entirely
   - Delete `def require_api_key(f):` function entirely
   - Delete `def cache_with_invalidation(...):` if present
   - Keep blueprint-specific helper functions (like `get_qa_validation_stats()`)

4. **Test**:
   ```bash
   python3 -c "from research_monitor.routes import git; print('✅ OK')"
   ```

5. **Verify server**:
   ```bash
   curl http://localhost:5558/api/server/health
   ```

## Task 2: Centralize Configuration (4 hours) - PENDING

Create `research_monitor/config.py` with Config class:
- Environment variable loading
- Validation
- Defaults
- Type conversion

## Task 3: Replace Print Statements (2 hours) - PENDING

Replace ~34 print statements with proper logging:
- Use `logger.info()` for normal messages
- Use `logger.warning()` for warnings
- Use `logger.error()` for errors
- Add structured logging where beneficial

## Task 4: API Endpoint Tests (8 hours) - PENDING

Create comprehensive pytest test suite:
- Test all 72 endpoints
- Integration tests for critical workflows
- Mock database for unit tests
- Test error handling

## Task 5: Broken Link Detection (4 hours) - PENDING

Implement automated source validation:
- Crawl event sources
- Detect 404s, timeouts, redirects
- Flag suspicious URLs
- Generate broken link reports

## Time Tracking

| Task | Est. | Actual | Status |
|------|------|--------|--------|
| 1. Blueprint helpers | 2h | 1h | In Progress (75% done) |
| 2. Configuration | 4h | - | Pending |
| 3. Print statements | 2h | - | Pending |
| 4. API tests | 8h | - | Pending |
| 5. Broken links | 4h | - | Pending |
| **Total** | **20h** | **1h** | **5% complete** |

## Next Session Start Here

```bash
# 1. Check current status
curl http://localhost:5558/api/server/health

# 2. Update remaining 5 blueprint files (see "Remaining Work" section above)

# 3. Test all imports
python3 -c "
from research_monitor.routes import git, timeline, events, qa, validation_runs
print('✅ All blueprints updated successfully')
"

# 4. Test server
curl http://localhost:5558/api/stats
curl http://localhost:5558/api/timeline/events?limit=5
curl http://localhost:5558/api/qa/stats

# 5. Commit when all working
git add research_monitor/routes/*.py
git commit -m "Sprint 2: Complete blueprint helper consolidation"
```

## Related Documentation

- `research_monitor/blueprint_utils.py` - Shared utilities module
- `specs/PROJECT_EVALUATION.md` - Sprint 2 plan
- `specs/ARCHITECTURAL_CLEANUP.md` - Full cleanup details
