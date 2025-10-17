# Sprint 2 Progress Report

**Started**: 2025-10-16
**Status**: In Progress (Task 1 partially complete)

## Task 1: Consolidate Blueprint Helpers (2 hours) - ✅ COMPLETED

### Completed
- ✅ Created `research_monitor/blueprint_utils.py` (413 lines)
  - Database access: `get_db()`
  - Authentication: `require_api_key()` decorator
  - Activity logging: `log_activity()`
  - Caching: `cache_with_invalidation()`, `invalidate_cache()`
  - Response helpers: `success_response()`, `error_response()`
  - Pagination helpers: `paginate_query()`
  - Request helpers: `get_request_json()`, `get_query_params()`

- ✅ Updated all 8 blueprint files to use shared utilities:
  - `routes/system.py` - Imports get_db, log_activity, success/error_response
  - `routes/priorities.py` - Imports get_db, log_activity, success/error_response
  - `routes/git.py` - Imports get_db, log_activity, success/error_response
  - `routes/timeline.py` - Imports get_db (kept blueprint-specific get_cache)
  - `routes/events.py` - Imports get_db, require_api_key
  - `routes/qa.py` - Imports get_db, require_api_key, cache_with_invalidation
  - `routes/validation_runs.py` - Imports get_db, require_api_key

### Impact
- **Code Reduction**: Eliminated ~105 lines of duplicate code across 8 files
- **Maintainability**: Single source of truth for common utilities
- **Testing**: All blueprints import successfully and server endpoints verified working

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

## Task 2: Centralize Configuration (4 hours) - ✅ COMPLETED

### Completed
- ✅ Created enhanced `research_monitor/config.py` with Config class
  - Environment variable loading with defaults
  - Type conversion (int, Path, string)
  - Configuration validation (port range, thresholds, cache settings)
  - `to_flask_config()` method for Flask integration
  - Singleton pattern with `get_config()`
  - Safe `__repr__` and human-readable `summary()` methods
  - Backward compatibility with legacy functions

- ✅ Updated `research_monitor/app_v2.py` to use centralized config
  - Replaced scattered `os.environ.get()` calls with Config class
  - Removed duplicate configuration variables (API_KEY, DB_PATH, EVENTS_PATH, etc.)
  - Updated all references to use `config` or `app.config`
  - Simplified Flask app initialization

### Impact
- **Code Reduction**: Eliminated ~15 lines of duplicate environment variable loading
- **Single Source of Truth**: All configuration in one Config class
- **Better Validation**: Port range, threshold, and cache validation
- **Type Safety**: Proper type conversion with error handling
- **Maintainability**: Easy to add new config options
- **Testing**: Singleton pattern allows config reset for tests

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
| 1. Blueprint helpers | 2h | 2h | ✅ Completed |
| 2. Configuration | 4h | 3h | ✅ Completed |
| 3. Print statements | 2h | - | Pending |
| 4. API tests | 8h | - | Pending |
| 5. Broken links | 4h | - | Pending |
| **Total** | **20h** | **5h** | **25% complete** |

## Next Session Start Here

Tasks 1 & 2 complete! Ready for Task 3: Replace Print Statements (2 hours)

```bash
# 1. Check current status
curl http://localhost:5558/api/server/health

# 2. Find all print statements in research_monitor/
grep -r "print(" research_monitor/ --include="*.py" | wc -l

# 3. Replace print statements with proper logging
# - Use logger.info() for informational messages
# - Use logger.warning() for warnings
# - Use logger.error() for errors
# - Add structured logging where beneficial

# 4. Test server starts without print() calls
python3 research_cli.py server-restart
curl http://localhost:5558/api/server/health

# 5. Verify log output is cleaner and more structured
tail -f /tmp/research_monitor.log
```

## Related Documentation

- `research_monitor/blueprint_utils.py` - Shared utilities module
- `specs/PROJECT_EVALUATION.md` - Sprint 2 plan
- `specs/ARCHITECTURAL_CLEANUP.md` - Full cleanup details
