# Kleptocracy Timeline - Comprehensive Improvement Plan

**Created**: 2025-10-16
**Status**: Draft
**Target Completion**: 2025-11-30 (6 weeks)
**Priority**: HIGH

---

## Table of Contents

1. [Current State Assessment](#current-state-assessment)
2. [Strategic Goals](#strategic-goals)
3. [Success Metrics](#success-metrics)
4. [Implementation Phases](#implementation-phases)
5. [Detailed Action Items](#detailed-action-items)
6. [Risk Assessment](#risk-assessment)
7. [Resource Requirements](#resource-requirements)
8. [Timeline](#timeline)

---

## Current State Assessment

### Code Quality Baseline (as of 2025-10-16)

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| **Overall Grade** | B+ (7.76/10) | A (9.0/10) | +1.24 |
| **Type Hints Coverage** | ~30% | 80%+ | +50% |
| **Test Coverage** | Unknown* | 80%+ | N/A |
| **Passing Tests** | 93/117 (79.5%) | 110+/117 (94%+) | +17 tests |
| **Code Duplication** | ~15% (estimated) | <5% | -10% |
| **Technical Debt Hours** | ~60 hours | <20 hours | -40 hours |

*Need to generate coverage report

### Component Health

| Component | Lines | Grade | Issues | Priority |
|-----------|-------|-------|--------|----------|
| research_cli.py | 830 | 8.5/10 | Type hints, hardcoded keys | MEDIUM |
| research_client.py | 1,143 | 8.0/10 | Type hints, long file | MEDIUM |
| **app_v2.py** | **4,650** | **7.0/10** | **Too large, needs splitting** | **CRITICAL** |
| qa_queue_system.py | 700+ | 8.0/10 | Type hints | MEDIUM |
| React Viewer | 40 components | 8.5/10 | Minor ESLint issues | LOW |
| Testing Infrastructure | 12 test files | 7.5/10 | Coverage gaps, 19 failures | HIGH |

### Architecture Concerns

**Critical Issues** 🔴:
1. **app_v2.py is 4,650 lines** - Should be split into modules
2. **No test coverage metrics** - Can't measure quality objectively
3. **19 test failures** - Pre-existing validation issues
4. **Hardcoded credentials** - Development keys should use env vars

**Major Issues** 🟡:
5. Type hints coverage only ~30%
6. Limited API documentation
7. Code duplication across similar functions
8. No performance monitoring/profiling

**Minor Issues** 🟢:
9. Some deprecated datetime usage (mostly fixed)
10. ESLint warnings in viewer
11. Inconsistent error handling patterns

---

## Strategic Goals

### 1. Code Quality Excellence (Target: A Grade)

**Objectives**:
- Increase type hints coverage to 80%+
- Reduce code duplication to <5%
- Fix all critical linting issues
- Improve documentation coverage

**Success Criteria**:
- MyPy passes with strict mode
- Pylint score >9.0/10
- All components score 8.5+/10

### 2. Robust Testing Infrastructure (Target: 80%+ Coverage)

**Objectives**:
- Generate baseline coverage report
- Increase test coverage to 80%+
- Fix all 19 pre-existing test failures
- Add integration tests for critical paths

**Success Criteria**:
- 110+ tests passing (94%+)
- Coverage ≥80% for core modules
- Zero critical path gaps

### 3. Scalable Architecture (Target: Modular Design)

**Objectives**:
- Split app_v2.py into logical modules
- Implement proper dependency injection
- Create clear module boundaries
- Document architectural decisions

**Success Criteria**:
- No file >1,000 lines
- Clear separation of concerns
- Architecture diagram documented

### 4. Production Readiness (Target: Enterprise-Grade)

**Objectives**:
- Remove all hardcoded credentials
- Add comprehensive error handling
- Implement monitoring and logging
- Create deployment documentation

**Success Criteria**:
- Zero hardcoded secrets
- Structured logging throughout
- Production deployment guide

---

## Success Metrics

### Key Performance Indicators (KPIs)

| KPI | Baseline | Week 2 | Week 4 | Week 6 (Target) |
|-----|----------|--------|--------|-----------------|
| Code Quality Grade | B+ (7.76) | B+ (8.0) | A- (8.5) | **A (9.0)** |
| Type Hints % | 30% | 50% | 70% | **80%+** |
| Test Coverage % | Unknown | 60% | 75% | **80%+** |
| Tests Passing | 93/117 | 100/120 | 110/125 | **110+/117** |
| Largest File (lines) | 4,650 | 3,000 | 1,500 | **<1,000** |
| MyPy Errors | ~200 (est.) | 100 | 20 | **0** |
| Pylint Score | 7.5/10 (est.) | 8.0/10 | 8.5/10 | **9.0+/10** |

### Quality Gates

**Cannot proceed to next phase without**:
- ✅ All critical tests passing
- ✅ No regression in existing functionality
- ✅ Documentation updated for all changes
- ✅ Code review completed (self-review for solo projects)

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2) - 20 hours

**Focus**: Testing infrastructure and baseline metrics

**Goals**:
- ✅ Generate test coverage report
- ✅ Fix all 19 pre-existing test failures
- ✅ Set up MyPy and Pylint configurations
- ✅ Document baseline metrics

**Deliverables**:
1. Coverage report showing current state
2. All tests passing (110+/117)
3. MyPy/Pylint configs in place
4. Baseline metrics documented

**Success Criteria**:
- Coverage report generated (target: >50%)
- Zero critical test failures
- CI/CD pipeline validates type hints

---

### Phase 2: Architecture Refactoring + Git Service Layer (Week 2-4) - 30 hours

**Focus**: Split app_v2.py, build Git service layer, prepare for multi-tenant architecture

**Strategic Direction**:
- Replace filesystem sync (~500 lines) with clean Git operations
- Enable multi-tenant support (work with forks and alternative timelines)
- Prepare for future extraction into separate repository
- See `GIT_SERVICE_DESIGN.md` for complete architecture

**Goals**:
- ✅ Design modular architecture for app_v2.py
- ✅ Split into routes/, services/, models/ modules
- ✅ **Build Git service layer (GitService, TimelineSyncService, PRBuilderService)**
- ✅ **Replace filesystem sync with PR-based workflow**
- ✅ **Add multi-tenant configuration (repo URL, branch)**
- ✅ Implement dependency injection
- ✅ Update all imports and tests

**Deliverables**:
1. Architecture diagram (modules and dependencies)
2. app_v2.py split into 8-10 files
3. **Git service layer with PR creation capability**
4. **Multi-tenant configuration system**
5. **CLI commands: `git-pull`, `create-pr`, `git-status`**
6. All tests still passing
7. Updated documentation

**Success Criteria**:
- No file >1,000 lines
- Clear module boundaries
- **Filesystem sync removed (~500 lines eliminated)**
- **Can create PRs programmatically**
- **Can work with fork via environment variables**
- All tests passing
- No functionality regression

**Proposed Structure**:
```
research_monitor/
├── app_v2.py                 # Main app (200 lines - config, initialization)
├── routes/
│   ├── __init__.py
│   ├── events.py            # Event endpoints (300-400 lines)
│   ├── priorities.py        # Priority endpoints (250-300 lines)
│   ├── validation.py        # Validation endpoints (400-500 lines)
│   ├── qa.py               # QA system endpoints (300-400 lines)
│   ├── git.py              # Git operations endpoints (200-300 lines) **NEW**
│   └── monitoring.py       # Health/stats endpoints (150-200 lines)
├── services/
│   ├── __init__.py
│   ├── git_service.py      # Core Git operations (clone, pull, push) **NEW**
│   ├── timeline_sync.py    # Import/export coordination **NEW**
│   ├── pr_builder.py       # GitHub PR creation **NEW**
│   ├── search.py           # Search service (300-400 lines)
│   ├── validation.py       # Validation logic (400-500 lines)
│   └── qa_queue.py         # QA queue management (300-400 lines)
├── core/
│   ├── __init__.py
│   ├── config.py           # Multi-tenant configuration **ENHANCED**
│   ├── git_config.py       # Git-specific settings **NEW**
│   ├── database.py         # Database session management
│   └── auth.py             # API key authentication
├── models/
│   ├── sync_status.py      # Track git sync operations **NEW**
│   └── ... (existing models)
└── utils/
    ├── __init__.py
    ├── logging.py          # Structured logging
    └── errors.py           # Custom exceptions
```

**New CLI Commands** (Phase 2):
```bash
# Import from git
research_cli.py git-pull              # Pull latest from timeline repo
research_cli.py git-status            # Check sync status

# Export to git
research_cli.py create-pr             # Create PR with validated events
research_cli.py create-pr --events "event-1,event-2"

# Multi-tenant configuration
research_cli.py git-config --repo https://github.com/alice/fork
research_cli.py git-config --show
```

**Workflow Transformation**:
```
BEFORE (Complex):
├─ Filesystem sync every 30s
├─ Commit threshold tracking
├─ Manual git commands
└─ ~500 lines of sync logic

AFTER (Simple):
├─ Database authoritative
├─ Explicit git operations (pull/PR)
├─ Programmatic PR creation
└─ Clean service boundaries
```

---

### Phase 3: Type Safety & Code Quality (Week 3-5) - 20 hours

**Focus**: Add type hints and improve code quality

**Goals**:
- ✅ Add type hints to all functions (target: 80%+)
- ✅ Fix all MyPy errors in strict mode
- ✅ Improve Pylint score to 9.0+/10
- ✅ Reduce code duplication

**Deliverables**:
1. Type hints for all public APIs
2. MyPy passes in strict mode
3. Pylint score ≥9.0/10
4. Refactored duplicate code

**Success Criteria**:
- Type hint coverage ≥80%
- Zero MyPy errors
- Pylint score ≥9.0/10
- Code duplication <5%

---

### Phase 4: Testing & Production Readiness (Week 4-6) - 15 hours

**Focus**: Increase test coverage and production hardening

**Goals**:
- ✅ Increase test coverage to 80%+
- ✅ Add integration tests for critical paths
- ✅ Remove hardcoded credentials
- ✅ Add monitoring and structured logging

**Deliverables**:
1. Test coverage ≥80%
2. Integration test suite
3. Environment variable configuration
4. Monitoring dashboard
5. Production deployment guide

**Success Criteria**:
- Coverage ≥80% for core modules
- All critical paths tested
- Zero hardcoded secrets
- Production-ready deployment docs

---

## Detailed Action Items

### Phase 1: Foundation

#### 1.1 Generate Test Coverage Report (2 hours)

**Tasks**:
```bash
# Install coverage tools
pip install pytest-cov coverage

# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term

# Analyze results
coverage report --skip-covered
coverage html
```

**Deliverables**:
- `htmlcov/index.html` - Interactive coverage report
- Coverage baseline documented in TESTING.md

**Success Criteria**: Coverage report shows >50% baseline

---

#### 1.2 Fix Pre-Existing Test Failures (8 hours)

**Current Failures**: 19 tests failing

**Root Causes**:
1. **Event status validation** (15 tests) - Invalid status values in timeline events
2. **KeyError: 'id'** (5 tests) - Test fixtures missing event IDs
3. **Schema validation** - Status field validation too strict

**Tasks**:

**Task 1.2.1**: Fix event status validation (4 hours)
```python
# Current validation (too strict)
VALID_STATUSES = ['confirmed', 'alleged', 'developing', 'speculative']

# Proposed (allow more statuses from actual events)
VALID_STATUSES = [
    'confirmed', 'alleged', 'developing', 'speculative',
    'validated', 'reported', 'investigated', 'disputed',
    'contested', 'predicted', 'verified', 'enhanced'
]
```

**Task 1.2.2**: Fix test fixtures (2 hours)
- Update test event fixtures to include 'id' field
- Ensure all required fields present
- Add validation tests for new status values

**Task 1.2.3**: Update validation logic (2 hours)
- Make status validation configurable
- Separate internal validation from public API validation
- Document valid status values

**Success Criteria**: All 117 tests passing

---

#### 1.3 Set Up Type Checking (3 hours)

**Tasks**:

**Task 1.3.1**: Create mypy.ini configuration
```ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False  # Start permissive, tighten later
ignore_missing_imports = True

[mypy-tests.*]
ignore_errors = True
```

**Task 1.3.2**: Create .pylintrc configuration
```ini
[MASTER]
init-hook='import sys; sys.path.append(".")'

[MESSAGES CONTROL]
disable=C0111,  # missing-docstring (too noisy initially)
        C0103,  # invalid-name (allow short names)
        R0913   # too-many-arguments (refactor later)

[FORMAT]
max-line-length=120
```

**Task 1.3.3**: Run baseline checks
```bash
mypy research_cli.py research_client.py research_api.py
pylint research_cli.py research_client.py research_api.py --score=yes
```

**Deliverables**:
- mypy.ini
- .pylintrc
- Baseline type checking/linting report

**Success Criteria**: Baseline report generated, no blocking errors

---

#### 1.4 Document Baseline Metrics (2 hours)

**Tasks**:
1. Create METRICS.md with current state
2. Set up tracking spreadsheet or dashboard
3. Define quality gates for each phase

**Deliverables**: METRICS.md with baseline data

---

### Phase 2: Architecture Refactoring

#### 2.1 Design Modular Architecture (4 hours)

**Tasks**:

**Task 2.1.1**: Create architecture diagram (2 hours)
- Document current app_v2.py structure
- Design proposed module structure
- Identify dependencies and data flow
- Review and validate design

**Task 2.1.2**: Plan migration strategy (2 hours)
- Identify minimal breaking changes
- Plan incremental refactoring
- Design backwards compatibility layer
- Create rollback plan

**Deliverables**:
- architecture_diagram.md (or .png)
- migration_plan.md
- module_dependencies.md

---

#### 2.2 Split app_v2.py into Modules (15 hours)

**Incremental Approach** (to maintain working state):

**Step 1**: Extract configuration (2 hours)
```python
# Create research_monitor/core/config.py
class Config:
    TIMELINE_DIR = Path(__file__).parent.parent.parent / 'timeline_data' / 'events'
    DATABASE_URL = 'sqlite:///unified_research.db'
    API_KEY = os.environ.get('RESEARCH_MONITOR_API_KEY', None)
    # ... all config
```

**Step 2**: Extract route blueprints (6 hours)
```python
# Create routes/events.py
from flask import Blueprint
events_bp = Blueprint('events', __name__)

@events_bp.route('/api/events', methods=['GET'])
def get_events():
    # Moved from app_v2.py
    ...
```

**Step 3**: Extract services (4 hours)
```python
# Create services/event_sync.py
class EventSyncService:
    def __init__(self, db_session, timeline_dir):
        self.db = db_session
        self.timeline_dir = timeline_dir

    def sync_events(self):
        # Moved from app_v2.py
        ...
```

**Step 4**: Update main app (2 hours)
```python
# Simplified app_v2.py
from flask import Flask
from routes import events_bp, priorities_bp, validation_bp
from core.config import Config
from core.database import init_db

app = Flask(__name__)
app.config.from_object(Config)

# Register blueprints
app.register_blueprint(events_bp)
app.register_blueprint(priorities_bp)
app.register_blueprint(validation_bp)

# ... minimal startup code
```

**Step 5**: Update all tests (1 hour)
```python
# Update imports
from research_monitor.routes.events import events_bp
from research_monitor.services.event_sync import EventSyncService
```

**Success Criteria**:
- All tests passing after each step
- No functionality regression
- app_v2.py reduced to <500 lines
- All modules <1,000 lines

---

#### 2.3 Implement Dependency Injection (3 hours)

**Tasks**:

**Task 2.3.1**: Create dependency container (2 hours)
```python
# core/dependencies.py
from dataclasses import dataclass
from sqlalchemy.orm import Session

@dataclass
class Dependencies:
    db_session: Session
    config: Config
    event_sync_service: EventSyncService
    search_service: SearchService
    validation_service: ValidationService
```

**Task 2.3.2**: Update routes to use DI (1 hour)
```python
from flask import current_app, g

def get_deps() -> Dependencies:
    if 'deps' not in g:
        g.deps = current_app.config['DEPENDENCIES']
    return g.deps

@events_bp.route('/api/events')
def get_events():
    deps = get_deps()
    events = deps.event_sync_service.get_all_events()
    return jsonify(events)
```

**Success Criteria**: Services decoupled, easily testable

---

#### 2.4 Documentation Update (3 hours)

**Tasks**:
1. Update CLAUDE.md with new structure
2. Create architecture documentation
3. Update API documentation
4. Add module-level docstrings

**Deliverables**:
- Updated CLAUDE.md
- architecture/DESIGN.md
- Module docstrings

---

### Phase 3: Type Safety & Code Quality

#### 3.1 Add Type Hints (12 hours)

**Approach**: File-by-file, starting with most-used modules

**Priority Order**:
1. research_client.py (4 hours) - Most used
2. research_api.py (2 hours)
3. research_monitor/models.py (2 hours)
4. research_monitor/routes/*.py (2 hours)
5. research_monitor/services/*.py (2 hours)

**Example Transformation**:
```python
# Before
def search(self, query='', **filters):
    params = {'q': query}
    params.update(filters)
    return self._request('GET', '/api/events/search', params=params)

# After
def search(self, query: str = '', **filters: Any) -> Dict[str, Any]:
    """
    Search timeline events with full-text search and filters

    Args:
        query: Full-text search query
        **filters: Additional filters (start_date, end_date, actor, tag)

    Returns:
        Dictionary containing:
            - events: List of matching events
            - count: Total number of matches
            - query: Original query

    Raises:
        HTTPError: If API request fails
    """
    params: Dict[str, str] = {'q': query}
    params.update(filters)
    return self._request('GET', '/api/events/search', params=params)
```

**Success Criteria**: Type hint coverage ≥80%

---

#### 3.2 Fix MyPy Errors (4 hours)

**Tasks**:
1. Run mypy with strict mode incrementally
2. Fix type errors file-by-file
3. Add type: ignore comments where necessary (with justification)
4. Document any Any types with TODO comments

**Success Criteria**: MyPy passes with zero errors

---

#### 3.3 Improve Pylint Score (2 hours)

**Common Issues to Fix**:
- Missing docstrings
- Too many arguments (refactor)
- Too many local variables (extract functions)
- Inconsistent naming

**Success Criteria**: Pylint score ≥9.0/10

---

#### 3.4 Reduce Code Duplication (2 hours)

**Tasks**:
1. Run pylint/radon for duplication detection
2. Extract common patterns into utilities
3. Create shared base classes where appropriate

**Example**:
```python
# Before: Duplicated in multiple files
def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# After: Shared utility
# utils/validation.py
def validate_date_format(date_str: str, format: str = '%Y-%m-%d') -> bool:
    """Validate date string matches format"""
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False
```

**Success Criteria**: Code duplication <5%

---

### Phase 4: Testing & Production Readiness

#### 4.1 Increase Test Coverage (8 hours)

**Target Coverage**:
- research_client.py: 90%+
- research_api.py: 85%+
- research_monitor/routes/: 80%+
- research_monitor/services/: 80%+

**Tasks**:

**Task 4.1.1**: Add unit tests for uncovered functions (4 hours)
```python
# tests/test_event_sync_service.py
def test_sync_events_creates_new_event(mock_db, mock_filesystem):
    service = EventSyncService(mock_db, mock_filesystem)
    service.sync_events()
    assert mock_db.query(Event).count() == 1

def test_sync_events_updates_existing_event(mock_db, mock_filesystem):
    # ... existing event in DB, modified on filesystem
    service = EventSyncService(mock_db, mock_filesystem)
    service.sync_events()
    assert event.summary == "Updated summary"
```

**Task 4.1.2**: Add integration tests (2 hours)
```python
# tests/integration/test_api_flow.py
def test_full_research_workflow(test_client):
    # Create priority
    priority = test_client.post('/api/priorities', json={...})

    # Get next priority
    next_priority = test_client.get('/api/priorities/next')

    # Create event
    event = test_client.post('/api/events', json={...})

    # Update priority
    updated = test_client.put(f'/api/priorities/{priority["id"]}', ...)

    # Verify complete workflow
    assert updated['status'] == 'completed'
```

**Task 4.1.3**: Add edge case tests (2 hours)
- Invalid input handling
- Error conditions
- Boundary conditions

**Success Criteria**: Coverage ≥80% for all core modules

---

#### 4.2 Remove Hardcoded Credentials (2 hours)

**Tasks**:

**Task 4.2.1**: Create .env.example (1 hour)
```bash
# .env.example
RESEARCH_MONITOR_API_KEY=your-secure-api-key-here
RESEARCH_MONITOR_PORT=5558
DATABASE_URL=sqlite:///unified_research.db
TIMELINE_DIR=./timeline_data/events
LOG_LEVEL=INFO
```

**Task 4.2.2**: Update code to use env vars (1 hour)
```python
# Before
API_KEY = "test-key"

# After
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get('RESEARCH_MONITOR_API_KEY')
if not API_KEY:
    raise ValueError("RESEARCH_MONITOR_API_KEY environment variable required")
```

**Task 4.2.3**: Update documentation
- Add .env setup instructions to README.md
- Document all required env vars
- Add security best practices

**Success Criteria**: Zero hardcoded credentials in codebase

---

#### 4.3 Add Monitoring & Logging (3 hours)

**Tasks**:

**Task 4.3.1**: Implement structured logging (2 hours)
```python
# utils/logging.py
import logging
import json
from datetime import datetime, timezone

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str, message: str, **context):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'message': message,
            'context': context
        }
        self.logger.log(getattr(logging, level.upper()), json.dumps(log_entry))
```

**Task 4.3.2**: Add request/response logging middleware (1 hour)
```python
@app.before_request
def log_request():
    g.start_time = time.time()
    logger.info('request_started',
                method=request.method,
                path=request.path)

@app.after_request
def log_response(response):
    duration = time.time() - g.start_time
    logger.info('request_completed',
                method=request.method,
                path=request.path,
                status=response.status_code,
                duration_ms=duration * 1000)
    return response
```

**Success Criteria**: All requests logged with timing

---

#### 4.4 Production Deployment Guide (2 hours)

**Tasks**:
1. Create deployment checklist
2. Document production setup
3. Add health check endpoints
4. Create troubleshooting guide

**Deliverables**:
- DEPLOYMENT.md
- TROUBLESHOOTING.md
- Production-ready health checks

---

## Risk Assessment

### High Risks 🔴

**Risk 1: Breaking Changes During Refactoring**
- **Probability**: Medium
- **Impact**: High
- **Mitigation**:
  - Incremental refactoring with tests at each step
  - Comprehensive test coverage before changes
  - Git branches for major refactors
  - Rollback plan documented

**Risk 2: Test Coverage Reveals Major Bugs**
- **Probability**: Medium
- **Impact**: Medium-High
- **Mitigation**:
  - Fix bugs as discovered
  - Prioritize critical path bugs
  - Document known issues
  - Plan bug fix sprints

### Medium Risks 🟡

**Risk 3: Type Hints Break Existing Code**
- **Probability**: Low-Medium
- **Impact**: Medium
- **Mitigation**:
  - Add type hints incrementally
  - Use type: ignore for complex types initially
  - Run tests after each file update
  - Use gradual typing approach

**Risk 4: Performance Degradation**
- **Probability**: Low
- **Impact**: Medium
- **Mitigation**:
  - Benchmark critical paths before/after
  - Profile code for bottlenecks
  - Keep performance tests in CI/CD

### Low Risks 🟢

**Risk 5: Documentation Becomes Stale**
- **Probability**: Medium
- **Impact**: Low
- **Mitigation**:
  - Update docs with code changes
  - Automated doc generation where possible
  - Regular doc reviews

---

## Resource Requirements

### Time Investment

| Phase | Estimated Hours | Developer Effort |
|-------|-----------------|------------------|
| Phase 1: Foundation | 20 hours | 1 week (part-time) |
| Phase 2: Architecture | 25 hours | 1.5 weeks (part-time) |
| Phase 3: Type Safety | 20 hours | 1 week (part-time) |
| Phase 4: Production | 15 hours | 1 week (part-time) |
| **Total** | **80 hours** | **6 weeks (part-time)** |

**Full-time equivalent**: ~2 weeks of focused work

### Tools & Dependencies

**Required**:
- pytest-cov (test coverage)
- mypy (type checking)
- pylint (linting)
- python-dotenv (env vars)
- coverage (coverage reporting)

**Optional**:
- radon (code complexity metrics)
- bandit (security scanning)
- black (code formatting)
- pre-commit (git hooks)

**Installation**:
```bash
pip install pytest-cov mypy pylint python-dotenv coverage radon bandit black pre-commit
```

---

## Timeline

### Week 1-2: Foundation Phase
- **Week 1**: Coverage report, fix test failures
- **Week 2**: Type checking setup, baseline metrics

**Milestone**: All tests passing, baseline established

### Week 2-4: Architecture Phase
- **Week 2-3**: Design architecture, start splitting app_v2.py
- **Week 4**: Complete refactoring, dependency injection

**Milestone**: Modular architecture, all tests passing

### Week 3-5: Type Safety Phase
- **Week 3-4**: Add type hints to core modules
- **Week 5**: Fix MyPy errors, improve Pylint score

**Milestone**: 80%+ type coverage, MyPy clean

### Week 4-6: Production Readiness
- **Week 4-5**: Increase test coverage, add integration tests
- **Week 6**: Remove hardcoded credentials, add monitoring

**Milestone**: Production-ready, 80%+ coverage

---

## Success Validation

### Phase Completion Checklist

#### Phase 1: Foundation ✅
- [ ] Coverage report generated (>50% baseline)
- [ ] All 117 tests passing
- [ ] MyPy/Pylint configs in place
- [ ] Baseline metrics documented

#### Phase 2: Architecture ✅
- [ ] Architecture diagram created
- [ ] app_v2.py split into modules (<1,000 lines each)
- [ ] All tests passing
- [ ] Documentation updated

#### Phase 3: Type Safety ✅
- [ ] Type hint coverage ≥80%
- [ ] MyPy passes (zero errors)
- [ ] Pylint score ≥9.0/10
- [ ] Code duplication <5%

#### Phase 4: Production ✅
- [ ] Test coverage ≥80%
- [ ] Zero hardcoded credentials
- [ ] Structured logging implemented
- [ ] Deployment guide complete

### Final Acceptance Criteria

**Code Quality**:
- ✅ Overall grade: A (9.0/10)
- ✅ Type hints: 80%+
- ✅ MyPy: Zero errors
- ✅ Pylint: 9.0+/10

**Testing**:
- ✅ Coverage: 80%+
- ✅ Tests passing: 110+/117 (94%+)
- ✅ Integration tests: Complete

**Architecture**:
- ✅ No file >1,000 lines
- ✅ Clear module boundaries
- ✅ Documented design

**Production**:
- ✅ Zero hardcoded secrets
- ✅ Structured logging
- ✅ Deployment docs
- ✅ Health checks

---

## Appendix

### A. Useful Commands

**Testing**:
```bash
# Run all tests with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_research_client.py -v

# Run with verbose output
pytest -vv -s
```

**Type Checking**:
```bash
# Check single file
mypy research_cli.py

# Check all files
mypy .

# Strict mode
mypy --strict research_client.py
```

**Linting**:
```bash
# Check file
pylint research_cli.py

# Check all Python files
pylint **/*.py

# Generate score
pylint research_cli.py --score=yes
```

**Coverage**:
```bash
# Generate HTML report
coverage html

# Show missing lines
coverage report --show-missing

# Focus on specific module
coverage report --include="research_monitor/*"
```

### B. Quality Metrics Tracking Template

Create a spreadsheet or use this table to track progress:

| Week | Tests Passing | Coverage % | Type Hints % | MyPy Errors | Pylint Score | Grade |
|------|---------------|------------|--------------|-------------|--------------|-------|
| 0 (Baseline) | 93/117 | Unknown | 30% | ~200 | 7.5 | B+ |
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | 110+/117 | 80%+ | 80%+ | 0 | 9.0+ | A |

### C. References

- **Python Type Hints**: https://docs.python.org/3/library/typing.html
- **MyPy Documentation**: https://mypy.readthedocs.io/
- **Pytest Coverage**: https://pytest-cov.readthedocs.io/
- **Flask Blueprints**: https://flask.palletsprojects.com/en/2.3.x/blueprints/
- **Dependency Injection in Python**: https://python-dependency-injector.ets-labs.org/

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-16 | Claude Code | Initial comprehensive improvement plan |

---

**Next Steps**: Review this plan, adjust priorities as needed, and begin Phase 1: Foundation.
