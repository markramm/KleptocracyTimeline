# Technical Plan: Extract Routes from app_v2.py

**Spec ID**: 001-extract-routes
**Created**: 2025-10-16
**Status**: Ready for Implementation
**Estimated Effort**: 12-16 hours

## Current State Analysis

### File Statistics
- **Total lines**: 4,649 (much larger than initial 1000+ estimate)
- **Total routes**: 72 endpoints
- **Route categories**: 10 distinct groups
- **Dependencies**: Flask, SQLite, multiple services

### Route Distribution
```
/api/events/*              16 routes  ~800 lines
/api/priorities/*           5 routes  ~300 lines
/api/timeline/*            16 routes  ~900 lines
/api/qa/*                  16 routes  ~1000 lines
/api/validation-runs/*     11 routes  ~600 lines
/api/validation-logs/*      2 routes  ~100 lines
/api/git/*                  2 routes  ~150 lines
/api/commit/*               2 routes  ~100 lines
/api/server/*               2 routes  ~100 lines
/api/cache/*                2 routes  ~50 lines
/api/research/*             1 route   ~50 lines
/api/activity/*             1 route   ~50 lines
/api/ (docs, openapi)       3 routes  ~150 lines
/ (root)                    1 route   ~50 lines
```

## Architecture Design

### Blueprint Strategy

We'll create Flask Blueprints for logical grouping of related endpoints:

```python
research_monitor/
├── app_v2.py                    # App initialization only (~300 lines)
│   ├── Flask app creation
│   ├── Configuration
│   ├── Database initialization
│   ├── Blueprint registration
│   └── Main execution block
│
└── routes/
    ├── __init__.py              # Blueprint registration helper
    ├── events.py                # Event CRUD and search (~800 lines)
    ├── priorities.py            # Research priority management (~300 lines)
    ├── timeline.py              # Timeline data access (~900 lines)
    ├── qa.py                    # QA validation system (~1000 lines)
    ├── validation_runs.py       # Validation run lifecycle (~700 lines)
    ├── git.py                   # Git integration (~150 lines)
    ├── system.py                # Server, cache, stats (~300 lines)
    └── docs.py                  # API documentation (~150 lines)
```

### Blueprint Design Pattern

Each blueprint module will follow this structure:

```python
"""
routes/[module].py - [Description]

Provides endpoints for [functionality]:
- List of main endpoints
- Purpose and use cases
"""

from flask import Blueprint, request, jsonify, current_app
from pathlib import Path
from typing import Dict, Any, List
import logging

# Create blueprint
bp = Blueprint('[name]', __name__, url_prefix='/api/[prefix]')

# Helper functions specific to this module
def _helper_function():
    """Private helper for this module only."""
    pass

# Route handlers
@bp.route('/endpoint')
def route_handler():
    """Docstring describing endpoint."""
    # Implementation
    pass
```

### Configuration Sharing

**Approach**: Use Flask's application context

```python
# In app_v2.py - store config in app.config
app.config['DB_PATH'] = DB_PATH
app.config['EVENTS_PATH'] = EVENTS_PATH
app.config['API_KEY'] = API_KEY

# In blueprints - access via current_app
from flask import current_app

def get_db():
    return current_app.config['DB_PATH']
```

### Shared Utilities

**Keep in app_v2.py (not in blueprints)**:
- `require_api_key()` decorator
- `db_connection()` context manager
- `sync_events_from_filesystem()` function
- `init_db()` function

**Why**: These are used across all blueprints and should remain centralized.

## Implementation Approach

### Phase 1: Preparation (1-2 hours)
1. Create `routes/` directory
2. Create `routes/__init__.py` with blueprint registration
3. Read and understand all current routes
4. Map dependencies for each route group

### Phase 2: Extract Blueprints (8-12 hours)

Extract in this order (least to most complex):

**2.1. Documentation Routes** (~30 min)
- `routes/docs.py`
- Routes: `/api/docs`, `/api/openapi.json`
- Dependencies: None (static responses)
- Risk: Low

**2.2. System Routes** (~1 hour)
- `routes/system.py`
- Routes: `/api/server/*`, `/api/cache/*`, `/api/stats`, `/api/activity/*`
- Dependencies: Database, filesystem sync
- Risk: Low

**2.3. Git Integration Routes** (~30 min)
- `routes/git.py`
- Routes: `/api/git/*`, `/api/commit/*`
- Dependencies: Git services
- Risk: Low

**2.4. Priority Routes** (~1 hour)
- `routes/priorities.py`
- Routes: `/api/priorities/*`
- Dependencies: Database, research priorities
- Risk: Low-Medium

**2.5. Timeline Routes** (~2 hours)
- `routes/timeline.py`
- Routes: `/api/timeline/*`
- Dependencies: Database, events
- Risk: Medium (many routes, complex queries)

**2.6. Event Routes** (~2 hours)
- `routes/events.py`
- Routes: `/api/events/*`
- Dependencies: Database, validation, filesystem
- Risk: Medium (complex validation logic)

**2.7. QA Routes** (~2 hours)
- `routes/qa.py`
- Routes: `/api/qa/*`
- Dependencies: Database, validation, QA system
- Risk: Medium-High (complex workflow)

**2.8. Validation Run Routes** (~2 hours)
- `routes/validation_runs.py`
- Routes: `/api/validation-runs/*`, `/api/validation-logs/*`
- Dependencies: Database, validation system
- Risk: Medium-High (complex state management)

### Phase 3: Integration (1-2 hours)
1. Update `app_v2.py` to register all blueprints
2. Remove extracted route code from `app_v2.py`
3. Verify imports and dependencies
4. Test blueprint registration order

### Phase 4: Testing & Validation (2-3 hours)
1. Run full test suite
2. Test each endpoint manually via research_cli.py
3. Check for import cycles
4. Verify MyPy compliance
5. Performance testing

## Detailed Module Specifications

### routes/__init__.py

```python
"""
Blueprint registration helper for Research Monitor API.
"""

from flask import Flask

def register_blueprints(app: Flask) -> None:
    """
    Register all route blueprints with the Flask app.

    Args:
        app: Flask application instance
    """
    from research_monitor.routes import (
        docs,
        system,
        git,
        priorities,
        timeline,
        events,
        qa,
        validation_runs
    )

    # Register blueprints in order
    app.register_blueprint(docs.bp)
    app.register_blueprint(system.bp)
    app.register_blueprint(git.bp)
    app.register_blueprint(priorities.bp)
    app.register_blueprint(timeline.bp)
    app.register_blueprint(events.bp)
    app.register_blueprint(qa.bp)
    app.register_blueprint(validation_runs.bp)
```

### routes/events.py

**Responsibility**: Event CRUD, search, and discovery

**Routes**:
- `GET /api/events/search` - Full-text search
- `GET /api/events/missing-sources` - Events needing sources
- `GET /api/events/validation-queue` - Events for QA
- `GET /api/events/broken-links` - Events with broken URLs
- `GET /api/events/research-candidates` - High-priority events
- `POST /api/events/validate` - Validate event data
- `POST /api/events/batch` - Create multiple events
- `POST /api/events/staged` - Stage events for commit

**Dependencies**:
- Database connection
- Filesystem (EVENTS_PATH)
- Validation functions
- API key authentication

**Shared utilities needed**:
- `require_api_key` decorator
- `db_connection` context manager

### routes/priorities.py

**Responsibility**: Research priority management

**Routes**:
- `POST /api/priorities/next` - Get next priority
- `GET /api/priorities/next` - Alternative method
- `PUT /api/priorities/<id>/start` - Mark priority as started
- `PUT /api/priorities/<id>/status` - Update priority status
- `GET /api/priorities/export` - Export priorities

**Dependencies**:
- Database connection
- PRIORITIES_PATH
- API key authentication

### routes/timeline.py

**Responsibility**: Read-only timeline data access

**Routes**:
- `GET /api/timeline/events` - List all events
- `GET /api/timeline/events/<id>` - Get single event
- `GET /api/timeline/events/date/<date>` - Events by date
- `GET /api/timeline/events/year/<year>` - Events by year
- `GET /api/timeline/events/actor/<actor>` - Events by actor
- `GET /api/timeline/actors` - List all actors
- `GET /api/timeline/tags` - List all tags
- `GET /api/timeline/sources` - List all sources
- `GET /api/timeline/date-range` - Events in date range
- `GET /api/timeline/actor/<actor>/timeline` - Actor timeline

**Dependencies**:
- Database connection
- Read-only access (no authentication needed for most)

### routes/qa.py

**Responsibility**: QA validation workflow

**Routes**:
- `GET /api/qa/queue` - Get QA queue
- `GET /api/qa/next` - Get next QA item
- `GET /api/qa/stats` - QA statistics
- `GET /api/qa/issues/<type>` - Get specific issues
- `GET /api/qa/rejected` - Get rejected events
- `POST /api/qa/validate/<id>` - Validate event
- `POST /api/qa/reject/<id>` - Reject event
- `POST /api/qa/enhance/<id>` - Enhance event
- `POST /api/qa/start/<id>` - Start QA on event
- `POST /api/qa/score` - Calculate QA score
- `POST /api/qa/batch/reserve` - Reserve batch
- `POST /api/qa/batch/release` - Release batch
- `POST /api/qa/validation/initialize` - Initialize validation
- `POST /api/qa/validation/reset` - Reset validation

**Dependencies**:
- Database connection
- QA queue system
- Validation functions
- API key authentication

### routes/validation_runs.py

**Responsibility**: Validation run lifecycle management

**Routes**:
- `GET /api/validation-runs` - List validation runs
- `POST /api/validation-runs` - Create validation run
- `GET /api/validation-runs/<id>` - Get validation run
- `GET /api/validation-runs/<id>/next` - Get next event
- `POST /api/validation-runs/<id>/events/<event_id>/complete` - Complete event
- `POST /api/validation-runs/<id>/requeue-needs-work` - Requeue events
- `GET /api/validation-logs` - List validation logs
- `POST /api/validation-logs` - Create validation log
- `GET /api/event-update-failures` - List update failures
- `GET /api/event-update-failures/stats` - Failure statistics

**Dependencies**:
- Database connection
- Validation run tables
- API key authentication

### routes/git.py

**Responsibility**: Git integration operations

**Routes**:
- `POST /api/git/pull` - Pull latest changes
- `POST /api/git/status` - Get git status
- `POST /api/commit/reset` - Reset commit counter
- `GET /api/commit/status` - Get commit status

**Dependencies**:
- Git service layer
- Database connection
- API key authentication

### routes/system.py

**Responsibility**: Server management and system information

**Routes**:
- `GET /api/server/health` - Health check
- `POST /api/server/shutdown` - Graceful shutdown
- `GET /api/stats` - System statistics
- `GET /api/cache/stats` - Cache statistics
- `POST /api/cache/clear` - Clear cache
- `GET /api/activity/recent` - Recent activity
- `GET /api/research/session` - Research session info
- `GET /` - Root endpoint

**Dependencies**:
- Database connection
- Filesystem sync
- Cache management

### routes/docs.py

**Responsibility**: API documentation

**Routes**:
- `GET /api/openapi.json` - OpenAPI spec
- `GET /api/docs` - Swagger UI

**Dependencies**:
- None (static or generated content)

## Migration Strategy

### Code Movement Pattern

For each blueprint:

1. **Create blueprint file**:
```python
from flask import Blueprint
bp = Blueprint('events', __name__, url_prefix='/api/events')
```

2. **Copy route handler**:
```python
@bp.route('/search')
def search_events():
    # Exact same implementation
    pass
```

3. **Update app.config access**:
```python
# OLD (in app_v2.py)
DB_PATH = os.environ.get('...')

# NEW (in blueprint)
from flask import current_app
db_path = current_app.config['DB_PATH']
```

4. **Keep shared utilities in app_v2.py**:
```python
# These stay in app_v2.py
def require_api_key(f):
    # decorator implementation

def db_connection():
    # context manager implementation
```

5. **Import shared utilities in blueprint**:
```python
from research_monitor.app_v2 import require_api_key, db_connection
```

### Import Management

**Circular Import Prevention**:
- Blueprints import from app_v2.py (shared utilities only)
- app_v2.py imports from routes/ (blueprints only)
- Shared utilities have no Flask context dependencies

**Import Order**:
1. Standard library
2. Third-party (Flask, etc.)
3. Local app modules (models, services)
4. Shared utilities from app_v2.py

## Testing Strategy

### Unit Testing Approach
- Existing tests should work without modification
- Tests import from app_v2.py (Flask app instance)
- Blueprint registration happens in app initialization
- No test changes required

### Integration Testing
```python
# Test that blueprints are registered
def test_blueprints_registered():
    from research_monitor.app_v2 import app
    blueprint_names = [bp.name for bp in app.blueprints.values()]
    assert 'events' in blueprint_names
    assert 'qa' in blueprint_names
    # ... etc
```

### Endpoint Testing
Use existing research_cli.py for smoke testing:
```bash
python3 research_cli.py get-stats
python3 research_cli.py search-events --query "test"
python3 research_cli.py get-next-priority
python3 research_cli.py qa-queue --limit 5
```

## Rollback Strategy

If issues arise:
1. **Git Revert**: Single atomic commit, easy to revert
2. **Feature Flag**: Could add `USE_BLUEPRINTS` env var if needed
3. **Staged Rollout**: Test each blueprint before moving to next

## Type Safety Preservation

All modules must maintain MyPy compliance:

```python
# Type hints for route handlers
@bp.route('/search')
def search_events() -> Response:
    """Search timeline events."""
    query: str = request.args.get('query', '')
    results: List[Dict[str, Any]] = search_db(query)
    return jsonify(results)
```

## Performance Considerations

**Blueprint Registration Cost**: Negligible (one-time at startup)

**Import Time**: Possible slight increase, but:
- Happens once at startup
- Modular imports might be faster (lazy loading potential)
- Measured impact should be <100ms

**Runtime Performance**: Zero impact (same route handlers, different organization)

## Documentation Updates

After refactoring:

1. **CLAUDE.md**: Update with new structure
2. **README.md**: Mention modular architecture
3. **METRICS.md**: Document refactoring completion
4. **Docstrings**: Each blueprint gets module docstring

## Success Metrics

- ✅ All 221 tests pass
- ✅ Zero MyPy errors
- ✅ All 72 endpoints respond correctly
- ✅ Server startup time < 2 seconds
- ✅ No circular imports
- ✅ app_v2.py reduced from 4649 to ~300 lines
- ✅ Each blueprint module < 1000 lines
- ✅ Code organization score improved

## Risk Mitigation

### Risk: Import Cycles
**Mitigation**:
- Shared utilities stay in app_v2.py
- No Flask app instance in shared utilities
- Blueprint registration happens last

### Risk: Configuration Access
**Mitigation**:
- Use Flask's current_app.config pattern
- Document config access pattern clearly
- Test config availability in each blueprint

### Risk: Test Breakage
**Mitigation**:
- Run full test suite after each blueprint
- Don't modify test code unless necessary
- Keep app instance import path same

## Timeline

- **Day 1 (4 hours)**: Phases 1-2.3 (setup + simple blueprints)
- **Day 2 (6 hours)**: Phases 2.4-2.7 (complex blueprints)
- **Day 3 (4 hours)**: Phase 2.8 + Phase 3 (validation runs + integration)
- **Day 4 (2 hours)**: Phase 4 (testing + documentation)

**Total**: 16 hours estimated, could be faster with focus

## Next Steps

After completing this plan:
1. Create `tasks.md` with checklist
2. Execute task-by-task
3. Test after each blueprint
4. Commit when all tests pass

---

**This plan is ready for task breakdown using `/speckit.tasks`**
