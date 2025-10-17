# Specification: Extract Routes from app_v2.py

**Spec ID**: 001-extract-routes
**Created**: 2025-10-16
**Status**: Draft (Example - Not Yet Implemented)
**Priority**: Medium (Deferred from Phase 2)

## Problem Statement

The Research Monitor API (`research_monitor/app_v2.py`) currently contains all Flask routes in a single monolithic file of 1000+ lines. This creates several issues:

- **Maintainability**: Difficult to locate and modify specific route logic
- **Testing**: Hard to test routes in isolation
- **Collaboration**: Merge conflicts when multiple developers work on different endpoints
- **Code Organization**: Violates Single Responsibility Principle

## Current State

### File Structure
```
research_monitor/
├── app_v2.py              # 1000+ lines - ALL routes defined here
├── models.py              # Database models
├── validation_functions.py
└── services/
    ├── git_service.py
    ├── timeline_sync.py
    └── pr_builder.py
```

### Route Categories in app_v2.py
1. **Event routes** (~200 lines): `/api/events/*`
2. **Priority routes** (~150 lines): `/api/priorities/*`
3. **Search routes** (~100 lines): `/api/search/*`
4. **QA routes** (~150 lines): `/api/qa/*`
5. **Validation run routes** (~200 lines): `/api/validation-runs/*`
6. **System routes** (~100 lines): `/api/server/*`, `/api/stats`
7. **Git integration routes** (~100 lines): `/api/git/*`

### Dependencies
- Uses Flask app instance directly
- Shares global configuration (DB_PATH, API_KEY, etc.)
- Imports services (EventService, ValidationService, etc.)
- Returns JSON responses with consistent error handling

## Desired State

### Modular Route Structure
```
research_monitor/
├── app_v2.py              # Reduced to ~200 lines - app initialization only
├── routes/
│   ├── __init__.py        # Blueprint registration
│   ├── events.py          # Event CRUD operations
│   ├── priorities.py      # Research priority management
│   ├── search.py          # Search endpoints
│   ├── qa.py              # QA validation endpoints
│   ├── validation_runs.py # Validation run system
│   ├── system.py          # Server status, stats, health
│   └── git.py             # Git integration endpoints
├── models.py
├── validation_functions.py
└── services/
    └── ...
```

### Each Route Module
- Defines a Flask Blueprint
- Contains 100-200 lines (manageable size)
- Focused on single responsibility
- Independently testable
- Clear documentation

## Success Criteria

### Functional Requirements
1. **Zero Functionality Change**: All existing endpoints work exactly as before
2. **All Tests Pass**: Existing test suite passes without modification
3. **API Compatibility**: All API clients work without changes
4. **Performance**: No degradation in response times

### Code Quality Requirements
1. **Modularity**: Each route module <200 lines
2. **Documentation**: Each blueprint has docstring explaining purpose
3. **Type Safety**: Maintains 100% MyPy compliance
4. **Imports**: Clean import structure, no circular dependencies

### Testing Requirements
1. **Existing tests**: All pass without modification
2. **New tests**: Add blueprint registration tests
3. **Coverage**: Maintain or improve test coverage
4. **Integration**: Verify all endpoints via research_cli.py

## Non-Goals

This refactoring explicitly does NOT:
- ❌ Change any API endpoint paths or responses
- ❌ Modify database schema or models
- ❌ Add new features or endpoints
- ❌ Change authentication or authorization logic
- ❌ Refactor services layer (separate task)
- ❌ Update frontend/viewer (no API changes)

## Implementation Constraints

### Must Maintain
- Existing error handling patterns
- JSON response format
- API key authentication
- Database connection handling
- Logging and monitoring

### Must Not Break
- CLI tools (research_cli.py, research_client.py)
- Pre-commit hooks
- Existing automation scripts
- Production deployments

## Acceptance Tests

### 1. Endpoint Availability
```bash
# All endpoints respond correctly
python3 research_cli.py server-start
python3 research_cli.py get-stats          # ✓ Should work
python3 research_cli.py search-events --query "test"  # ✓ Should work
python3 research_cli.py get-next-priority  # ✓ Should work
```

### 2. Test Suite
```bash
# All tests pass
python3 -m unittest discover -s tests -v
# Expected: 221 tests, 220 passing (99.5%)
```

### 3. Type Safety
```bash
# No new MyPy errors
mypy research_monitor/app_v2.py research_monitor/routes/
# Expected: 0 errors
```

### 4. Import Check
```bash
# No circular dependencies
python3 -c "from research_monitor.app_v2 import app; print('OK')"
# Expected: OK (no import errors)
```

### 5. Server Startup
```bash
# Server starts cleanly
python3 research_monitor/app_v2.py
# Expected: "Running on http://127.0.0.1:5558" (no errors)
```

## Dependencies

### Prerequisite Work
- None (can start immediately)

### Blocking Issues
- None identified

### Related Work
- Phase 2: Git service layer (already complete)
- Future: Service layer refactoring (separate spec)

## Risks and Mitigations

### Risk 1: Import Cycles
**Impact**: High
**Likelihood**: Medium
**Mitigation**:
- Careful blueprint registration order
- Shared configuration in separate config module
- Import services at function level if needed

### Risk 2: Global State
**Impact**: Medium
**Likelihood**: Low
**Mitigation**:
- Document shared state (db connection, API key)
- Pass app instance to blueprints
- Use Flask's `current_app` when appropriate

### Risk 3: Test Brittleness
**Impact**: Medium
**Likelihood**: Low
**Mitigation**:
- Run full test suite after each module extraction
- Don't modify tests unless necessary
- Add smoke tests for blueprint registration

## Timeline Estimate

- **Specification**: 1 hour (this document)
- **Planning**: 2 hours (technical approach, task breakdown)
- **Implementation**: 4-6 hours (extract and test each module)
- **Testing**: 2 hours (comprehensive validation)
- **Documentation**: 1 hour (update CLAUDE.md, comments)
- **Total**: ~10-12 hours of focused work

## Stakeholders

- **Primary**: Project maintainers
- **Affected**: AI coding assistants (need updated CLAUDE.md)
- **Informed**: Future contributors

## Open Questions

1. **Blueprint naming convention**: Singular (event) or plural (events)?
   - **Decision**: Plural to match route paths (`/api/events`)

2. **Configuration sharing**: Module-level or app-level config?
   - **Decision**: Use Flask app.config, access via current_app

3. **Error handling**: Centralized decorator or per-route?
   - **Decision**: Keep existing per-route pattern for now

## References

- **Current code**: `research_monitor/app_v2.py`
- **Flask Blueprints**: https://flask.palletsprojects.com/blueprints/
- **Project standards**: `.specify/memory/constitution.md`

---

**Next Steps**: Create `plan.md` with detailed implementation approach using `/speckit.plan`.
