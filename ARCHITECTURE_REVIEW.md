# Architecture & Design Review
## Kleptocracy Timeline - Comprehensive Analysis

**Review Date**: October 2025
**Current State**: Repository restructure prototype branch
**Target**: Two-repository split for production release

---

## Executive Summary

### Critical Issues (Must Fix)
1. **Monolithic app_v2.py** (4,708 lines) - needs decomposition
2. **Missing timeline/data/events/** - path inconsistency
3. **Test files in production code** - wrong location
4. **Duplicate API documentation** - 3 copies
5. **No schema migrations** - Alembic not in use
6. **CLI/API/MCP overlap** - three ways to do same thing

### High Priority (Should Fix)
1. **No dependency injection** - tight coupling throughout
2. **Inconsistent error handling** - mix of patterns
3. **Missing integration tests** for validation runs
4. **No API versioning** - breaking changes will hurt
5. **Database in multiple locations** - confusion risk

### Recommendations
1. **Split repository NOW** - defer further refactoring until after split
2. **Extract services from app_v2.py** - create proper service layer
3. **Consolidate docs** - single source of truth
4. **Add CI/CD** - automated testing and validation

---

## Component Analysis

### 1. Timeline Component (759MB)

#### Current Structure
```
timeline/
├── data/events/           # 1,607 JSON event files (core data)
├── content/events/        # Hugo markdown (1,552+ files) - REDUNDANT?
├── viewer/                # React application
├── scripts/               # Python utilities
├── schemas/               # JSON schemas
├── public/                # Hugo static output
└── docs/                  # Documentation
```

#### Issues

**Critical:**
- ❌ **Dual event storage** - both `data/events/` (JSON) and `content/events/` (Markdown Hugo)
- ❌ **759MB size** - too large for what should be data + simple viewer
- ❌ **Path confusion** - CLAUDE.md references `timeline/data/events` but viewer may use `content/events`
- ❌ **No clear single source of truth** - which format is authoritative?

**High Priority:**
- ⚠️ **No event versioning** - can't track changes over time
- ⚠️ **No data migrations** - schema changes will break existing data
- ⚠️ **Scripts duplicated** - both in `timeline/scripts/` and `research-server/scripts/`
- ⚠️ **Hugo + React** - two static site generators (confusion)

**Medium Priority:**
- 📝 Schemas should be in JSON Schema format, validate on commit
- 📝 No automated validation in pre-commit hooks
- 📝 Event IDs not enforced (manual naming)

#### Recommendations

**For Timeline Repository:**
```
timeline-data/
├── events/                    # SINGLE source of truth (JSON)
│   ├── YYYY/                 # Year-based organization
│   │   └── YYYY-MM-DD--slug.json
│   └── .schema/              # Event schema versions
│       └── v1.0.json
├── viewer/                    # React static viewer
│   ├── src/
│   ├── public/
│   └── package.json
├── scripts/                   # Validation & conversion tools
│   ├── validate.py
│   ├── convert_to_markdown.py
│   └── generate_static_api.py
├── .github/
│   └── workflows/
│       ├── validate-events.yml
│       └── deploy-viewer.yml
└── docs/
    ├── EVENT_FORMAT.md
    ├── CONTRIBUTING.md
    └── CHANGELOG.md
```

**Changes:**
1. ✅ **Remove Hugo** - use only React viewer
2. ✅ **Single event format** - JSON as source, generate Markdown if needed
3. ✅ **Year-based directories** - `/events/2024/`, `/events/2023/`, etc.
4. ✅ **Schema versioning** - track format changes
5. ✅ **Pre-commit validation** - enforce schema on commit
6. ✅ **Automated tests** - validate all events in CI

---

### 2. Research Server Component (66MB)

#### Current Structure
```
research-server/
├── server/
│   ├── app_v2.py          # 4,708 lines - MONOLITHIC
│   ├── routes/            # 8 blueprint files
│   ├── services/          # Business logic
│   ├── parsers/           # Event format parsers
│   ├── core/              # Core utilities
│   └── test_*.py          # Tests in WRONG location
├── client/
│   └── research_client.py # 1,143 lines - API wrapper
├── cli/
│   └── research_cli.py    # 1,127 lines - CLI interface
├── mcp/                   # MCP server
├── tests/                 # Proper test location
└── docs/
```

#### Issues

**Critical:**
- ❌ **app_v2.py is 4,708 lines** - should be <500 lines (just Flask app setup)
- ❌ **Test files in server/** - `test_app_v2.py`, `test_integration.py`, etc. should be in `tests/`
- ❌ **No separation of concerns** - routes, business logic, and data access mixed
- ❌ **95+ API endpoints** - no clear versioning or deprecation strategy
- ❌ **Three interfaces (CLI/API/MCP)** - overlap and inconsistency

**High Priority:**
- ⚠️ **No dependency injection** - everything tightly coupled
- ⚠️ **Inconsistent error handling** - some routes use error_response(), some return tuples
- ⚠️ **No request validation** - manual field checking in each route
- ⚠️ **Database queries in routes** - should be in repository layer
- ⚠️ **Global state** (`events_since_commit`, `current_session_id`) - not thread-safe

**Medium Priority:**
- 📝 No API versioning (`/api/v1/...`)
- 📝 No OpenAPI/Swagger docs
- 📝 Mixed sync model (filesystem authoritative for events, DB for priorities)
- 📝 Alembic configured but not used
- 📝 Config scattered (config.py, environment, hardcoded)

#### Recommendations

**Restructure app_v2.py:**
```python
# app_v2.py - Should be ~200 lines
from flask import Flask
from config import get_config
from extensions import db, cache, cors
from blueprints import register_blueprints
from services.filesystem_sync import FilesystemSyncService

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or get_config())

    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)
    cors.init_app(app)

    # Register blueprints
    register_blueprints(app)

    # Start background services
    sync_service = FilesystemSyncService(app)
    sync_service.start()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=app.config['PORT'])
```

**Extract Services:**
```
services/
├── __init__.py
├── event_service.py          # Event CRUD, validation
├── priority_service.py       # Research priority management
├── validation_service.py     # Validation runs
├── filesystem_sync.py        # File → DB sync
├── search_service.py         # Full-text search
└── qa_service.py             # Quality assurance
```

**Repository Pattern:**
```
repositories/
├── __init__.py
├── event_repository.py       # timeline_events table
├── priority_repository.py    # research_priorities table
├── validation_repository.py  # validation_runs table
└── base_repository.py        # Common query methods
```

**Move Tests:**
```bash
# Move all test_*.py from server/ to tests/
mv research-server/server/test_*.py research-server/tests/integration/
```

**API Versioning:**
```python
# Current: /api/events
# New:     /api/v1/events

blueprints/
├── v1/
│   ├── __init__.py
│   ├── events.py
│   ├── priorities.py
│   └── validation.py
└── v2/              # Future breaking changes
    └── ...
```

---

## Repository Split Strategy

### Option A: Clean Split (Recommended)

**Timeline Data Repository**
```
kleptocracy-timeline/
├── events/
│   └── YYYY/
│       └── *.json
├── viewer/              # React app
├── schemas/
├── scripts/            # Validation only
├── .github/workflows/  # CI for validation
└── README.md
```
**Size**: ~10-20MB (JSON events + viewer)
**License**: CC0 (data) + MIT (code)
**Users**: General public, researchers

**Research Server Repository**
```
timeline-research-server/
├── src/
│   ├── api/            # Flask REST API
│   ├── cli/            # CLI tool
│   ├── mcp/            # MCP server
│   ├── services/       # Business logic
│   ├── repositories/   # Data access
│   └── models/         # DB models
├── tests/              # All tests here
├── docs/               # API documentation
├── .github/workflows/  # CI for testing
└── requirements.txt
```
**Size**: ~5-10MB (code only, no data)
**License**: MIT
**Users**: AI agents, researchers, developers

### Option B: Monorepo with Clear Boundaries

```
kleptocracy-project/
├── packages/
│   ├── timeline-data/     # Data + viewer (independent)
│   └── research-server/   # Server (depends on nothing)
├── docs/                  # Shared docs
└── tools/                 # Shared scripts
```

**Recommendation**: **Option A** - Clearer separation, easier permissions, better for public data sharing

---

## Code Quality Issues

### 1. Inconsistent Error Handling

**Current (Mixed Patterns):**
```python
# Pattern 1: Tuple return
@app.route('/api/events')
def get_events():
    if error:
        return jsonify({'error': 'msg'}), 400
    return jsonify(data)

# Pattern 2: Helper function
@app.route('/api/priorities')
def get_priorities():
    if error:
        return error_response('msg', 400)
    return success_response(data)

# Pattern 3: Exception
@app.route('/api/search')
def search():
    if error:
        abort(400, description='msg')
```

**Recommended (Consistent):**
```python
# Use global error handlers + exceptions
from exceptions import ValidationError, NotFoundError

@app.route('/api/events')
def get_events():
    event = event_service.get_event(id)
    if not event:
        raise NotFoundError(f"Event {id} not found")
    return success_response(event)

# Global handler
@app.errorhandler(NotFoundError)
def handle_not_found(error):
    return error_response(str(error), 404)
```

### 2. No Dependency Injection

**Current (Tightly Coupled):**
```python
@app.route('/api/events')
def get_events():
    db = get_db()  # Creates session
    events = db.query(TimelineEvent).all()  # Direct query
    db.close()
    return jsonify([e.to_dict() for e in events])
```

**Recommended (Dependency Injection):**
```python
# Inject service
@events_bp.route('/')
@inject
def get_events(event_service: EventService):
    events = event_service.get_all()
    return success_response(events)
```

### 3. No Request Validation

**Current (Manual Validation):**
```python
@app.route('/api/events', methods=['POST'])
def create_event():
    data = request.json or {}

    # Manual validation
    if 'id' not in data:
        return error_response('Missing id'), 400
    if 'date' not in data:
        return error_response('Missing date'), 400
    # ... 20 more fields
```

**Recommended (Schema Validation):**
```python
from marshmallow import Schema, fields, validate

class EventSchema(Schema):
    id = fields.Str(required=True, validate=validate.Regexp(r'^\d{4}-\d{2}-\d{2}--[\w-]+$'))
    date = fields.Date(required=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    importance = fields.Int(required=True, validate=validate.Range(min=1, max=10))
    # ... rest of schema

@events_bp.route('/', methods=['POST'])
@validate_request(EventSchema)
def create_event(validated_data):
    event = event_service.create(validated_data)
    return success_response(event, 201)
```

### 4. Database Access in Routes

**Current (Bad):**
```python
@app.route('/api/events/<event_id>')
def get_event(event_id):
    db = get_db()
    event = db.query(TimelineEvent).filter_by(id=event_id).first()
    db.close()
    if not event:
        return error_response('Not found'), 404
    return success_response(event.to_dict())
```

**Recommended (Service Layer):**
```python
# Route (thin)
@events_bp.route('/<event_id>')
@inject
def get_event(event_id: str, event_service: EventService):
    event = event_service.get_by_id(event_id)
    return success_response(event)

# Service (business logic)
class EventService:
    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo

    def get_by_id(self, event_id: str) -> dict:
        event = self.event_repo.find_by_id(event_id)
        if not event:
            raise NotFoundError(f"Event {event_id} not found")
        return event.to_dict()

# Repository (data access)
class EventRepository:
    def find_by_id(self, event_id: str) -> Optional[TimelineEvent]:
        return self.db.query(TimelineEvent).filter_by(id=event_id).first()
```

---

## Test Quality Issues

### Current Test Organization

**Problems:**
1. ❌ Test files in `server/` directory (should be in `tests/`)
2. ❌ 207 tests collected but 1 error during collection
3. ❌ No integration tests for validation runs system
4. ❌ Tests depend on running server (not isolated)
5. ❌ No test fixtures for common scenarios

**Test Coverage Gaps:**
- ❌ Validation runs (newly added, untested)
- ❌ Filesystem sync service
- ❌ Error handling paths
- ❌ Concurrent operations (race conditions)
- ❌ Edge cases (invalid data, missing files)

### Recommended Test Structure

```
tests/
├── unit/                          # Fast, isolated tests
│   ├── services/
│   │   ├── test_event_service.py
│   │   ├── test_priority_service.py
│   │   └── test_validation_service.py
│   ├── repositories/
│   │   └── test_event_repository.py
│   └── utils/
│       └── test_validators.py
├── integration/                   # Tests with database
│   ├── test_api_events.py
│   ├── test_api_validation_runs.py
│   └── test_filesystem_sync.py
├── e2e/                          # End-to-end workflows
│   ├── test_research_workflow.py
│   └── test_qa_workflow.py
├── fixtures/                      # Shared test data
│   ├── events.py
│   ├── priorities.py
│   └── database.py
└── conftest.py                   # Pytest configuration
```

### Missing Tests (High Priority)

1. **Validation Runs System**
```python
def test_validation_run_unique_distribution():
    """Ensure two validators never get same event"""
    run = create_validation_run(target_count=10)
    event1 = get_next_event(run_id=run.id, validator="agent-1")
    event2 = get_next_event(run_id=run.id, validator="agent-2")
    assert event1.id != event2.id

def test_validation_run_requeue():
    """Ensure needs_work events can be requeued"""
    # ... test implementation
```

2. **Concurrent Access**
```python
def test_concurrent_event_creation():
    """Ensure no duplicate events from concurrent requests"""
    # Use threading to simulate concurrent requests
```

3. **Filesystem Sync**
```python
def test_filesystem_sync_detects_changes():
    """Ensure file changes sync to database"""
    # Create event file
    # Wait for sync
    # Verify in database
```

---

## Documentation Issues

### Current Documentation (Scattered)

**Problems:**
1. ❌ **3 copies of API docs** (server/, server/static/, README references)
2. ❌ **ARCHITECTURE.md outdated** (references port 5555, should be 5558)
3. ❌ **No OpenAPI/Swagger** - manual doc maintenance
4. ❌ **CLAUDE.md is comprehensive** but not user-facing
5. ❌ **Missing: DEVELOPMENT.md** (setup for contributors)

### Documentation Inventory

**Root Level:**
- ✅ README.md - Good overview
- ✅ INSTALLATION.md - Comprehensive
- ✅ RELEASE_CHECKLIST.md - Thorough
- ✅ IMPROVEMENTS_SUMMARY.md - Current
- ✅ CLAUDE.md - Excellent (for AI agents)
- ❌ CONTRIBUTING.md - Missing
- ❌ CHANGELOG.md - Missing
- ❌ CODE_OF_CONDUCT.md - Missing (if public)

**research-server/**
- ✅ README.md - Needs update for CLI wrapper
- ✅ server/ARCHITECTURE.md - Needs update (port, structure)
- ❌ server/API_DOCUMENTATION.md - Duplicate (keep one)
- ❌ server/static/API_DOCUMENTATION.md - Duplicate (remove)
- ❌ DEVELOPMENT.md - Missing

**timeline/**
- ✅ README.md - Good
- ❌ docs/EVENT_FORMAT.md - Incomplete
- ❌ docs/CONTRIBUTING.md - Missing
- ❌ docs/VALIDATION.md - Missing

### Recommended Documentation

**For Repository Split:**

**Timeline Data Repo:**
```
docs/
├── README.md                 # Overview, quick start
├── EVENT_FORMAT.md           # Complete format specification
├── CONTRIBUTING.md           # How to add events
├── VALIDATION.md             # Schema validation rules
├── VIEWER_DEPLOYMENT.md      # Deploy React viewer
└── CHANGELOG.md              # Version history
```

**Research Server Repo:**
```
docs/
├── README.md                 # Overview, installation
├── API.md                    # API reference (or OpenAPI)
├── ARCHITECTURE.md           # System design
├── DEVELOPMENT.md            # Setup for development
├── DEPLOYMENT.md             # Production deployment
├── CLI.md                    # CLI reference
├── MCP.md                    # MCP server usage
└── CHANGELOG.md              # Version history
```

### Generate OpenAPI Docs

**Recommended:**
```python
# Use flask-smorest or flask-restx
from flask_smorest import Api, Blueprint

api = Api(app, spec_kwargs={
    'title': 'Timeline Research API',
    'version': 'v1',
    'openapi_version': '3.0.2'
})

# Auto-generates docs at /api/docs
```

---

## Database & Schema Issues

### Current Issues

1. **Alembic Not Used**
   - Alembic configured but no migrations
   - Schema changes require manual database recreation
   - No version history

2. **No Schema Versioning**
   - Events don't track which schema version
   - Can't migrate old events to new schema
   - Breaking changes will orphan data

3. **Inconsistent Sync Model**
   - Events: filesystem → database (one-way)
   - Priorities: database → filesystem (manual export)
   - Confusing mental model

4. **Global Variables**
   ```python
   # Not thread-safe!
   events_since_commit = 0
   current_session_id = f"session-{datetime.now()...}"
   ```

### Recommendations

**1. Use Alembic Migrations**
```bash
# Create migration for current schema
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Future schema changes
alembic revision -m "Add validation_score to events"
# Edit migration file
alembic upgrade head
```

**2. Add Schema Version to Events**
```json
{
  "schema_version": "1.0",
  "id": "2025-01-15--event",
  "date": "2025-01-15",
  "title": "Event Title",
  ...
}
```

**3. Consistent Sync Model**

**Option A: Filesystem Authoritative (Current)**
- Keep filesystem as source of truth
- Database is read-only cache for search
- Document clearly in ARCHITECTURE.md

**Option B: Database Authoritative**
- Database is source of truth
- Filesystem is export target
- Changes must go through API

**Recommendation**: **Option A** for timeline data (Git history valuable), **Option B** for research server data

**4. Remove Global State**
```python
# Instead of global variables, use database
class ResearchSession:
    session_id = Column(String, primary_key=True)
    events_since_commit = Column(Integer, default=0)
    commit_threshold = Column(Integer)
    created_at = Column(DateTime)

# Access via session
def increment_commit_counter(session_id):
    session = db.query(ResearchSession).filter_by(session_id=session_id).first()
    session.events_since_commit += 1
    db.commit()
```

---

## Priority Fix List

### Critical (Must Fix Before Release)

1. **Move test files**
   ```bash
   mv research-server/server/test_*.py research-server/tests/integration/
   ```

2. **Fix app_v2.py monolith**
   - Extract services (event_service.py, priority_service.py, etc.)
   - Move routes to blueprints (already partially done)
   - Reduce to <500 lines (just app factory)

3. **Consolidate documentation**
   - Remove duplicate API_DOCUMENTATION.md
   - Create single source in docs/
   - Update ARCHITECTURE.md (port 5558, current structure)

4. **Timeline data path consistency**
   - Decide: `data/events/` or `content/events/`?
   - Update all references
   - Remove duplicate if needed

5. **Remove Hugo or React (not both)**
   - If keeping Hugo: remove React viewer
   - If keeping React: remove Hugo (recommended)

### High Priority (Should Fix Soon)

6. **Add dependency injection**
   - Use flask-injector or similar
   - Decouple services from routes

7. **Add request validation**
   - Use marshmallow or pydantic
   - Validate all POST/PUT requests

8. **API versioning**
   - Add /api/v1/ prefix
   - Plan for /api/v2/ breaking changes

9. **Use Alembic migrations**
   - Create initial migration
   - Document migration process

10. **Add integration tests for validation runs**
    - Test unique distribution
    - Test all completion statuses
    - Test concurrent access

11. **Consistent error handling**
    - Use global exception handlers
    - Define custom exceptions
    - Remove mixed patterns

12. **Generate OpenAPI docs**
    - Use flask-smorest
    - Auto-generate from code
    - Remove manual API docs

### Medium Priority (Nice to Have)

13. **Event schema versioning**
    - Add schema_version field
    - Document migration path

14. **Remove global state**
    - Store session data in database
    - Make thread-safe

15. **Improve test organization**
    - Split into unit/integration/e2e
    - Add shared fixtures
    - Add coverage reporting

16. **Add pre-commit hooks**
    - Validate event schemas
    - Run linters
    - Run tests

17. **Add CI/CD**
    - GitHub Actions for tests
    - Auto-deploy on merge
    - Automated releases

---

## Repository Split Action Plan

### Phase 1: Preparation (Before Split)

1. ✅ Clean up (RELEASE_CHECKLIST.md tasks)
2. ✅ Move tests to correct location
3. ✅ Consolidate documentation
4. ✅ Fix critical bugs (already done)
5. ✅ Decide on timeline data format (JSON primary)

### Phase 2: Split Execution

1. **Create timeline-data repository**
   ```bash
   # Extract timeline/ with history
   git subtree split -P timeline -b timeline-only

   # Create new repo
   gh repo create kleptocracy-timeline --public
   git push timeline-only main
   ```

2. **Create research-server repository**
   ```bash
   # Extract research-server/ with history
   git subtree split -P research-server -b research-only

   # Create new repo
   gh repo create timeline-research-server --public
   git push research-only main
   ```

3. **Update cross-references**
   - Timeline README → link to research server
   - Research server README → link to timeline data
   - Update CLAUDE.md with new repo structure

### Phase 3: Post-Split Refactoring

1. **Timeline repo:**
   - Remove Hugo (keep React viewer only)
   - Add pre-commit validation hooks
   - Add CI for event validation
   - Deploy viewer to GitHub Pages

2. **Research server repo:**
   - Extract services from app_v2.py
   - Add dependency injection
   - Add OpenAPI docs
   - Add comprehensive tests
   - Add CI/CD

### Phase 4: Documentation & Release

1. **Create releases**
   - Tag v1.0.0 in both repos
   - Write release notes
   - Update all documentation

2. **Add contributing guides**
   - CONTRIBUTING.md for both repos
   - CODE_OF_CONDUCT.md
   - Issue templates
   - PR templates

---

## Conclusion

### Current State: B- (Good but needs work)

**Strengths:**
- ✅ Comprehensive data (1,607 events)
- ✅ Working API (95+ endpoints)
- ✅ Good CLI wrapper
- ✅ Validation runs system functional
- ✅ Documentation improving

**Weaknesses:**
- ❌ Monolithic app_v2.py
- ❌ Scattered tests
- ❌ No schema migrations
- ❌ Inconsistent patterns
- ❌ Two competing static site generators

### Recommended Approach

**DO NOW (Before Split):**
1. Move test files
2. Consolidate docs
3. Choose one static site generator
4. Fix path inconsistencies

**DO AFTER SPLIT:**
1. Refactor app_v2.py
2. Add proper service layer
3. Add dependency injection
4. Add comprehensive tests
5. Generate OpenAPI docs

**Rationale:** Don't delay the split for perfect refactoring. Split first (clearer boundaries), then refactor each repo independently.

### Expected Timeline

- **Phase 1 (Preparation)**: 2-4 hours
- **Phase 2 (Split)**: 1-2 hours
- **Phase 3 (Refactoring)**: 10-20 hours
- **Phase 4 (Polish)**: 5-10 hours

**Total**: 18-36 hours of focused work

### Success Criteria

**Minimum Viable Split:**
- ✅ Two repositories with clean history
- ✅ All tests passing in both repos
- ✅ Documentation updated and accurate
- ✅ No broken cross-references
- ✅ CLI/API functional in research server
- ✅ Viewer deployed for timeline data

**Ideal State (Post-Refactoring):**
- ✅ app_v2.py < 500 lines
- ✅ Service layer extracted
- ✅ 80%+ test coverage
- ✅ OpenAPI documentation
- ✅ CI/CD in both repos
- ✅ Schema migrations working
