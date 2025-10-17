# Task Breakdown: Extract Routes from app_v2.py

**Spec ID**: 001-extract-routes
**Created**: 2025-10-16
**Status**: Ready for Implementation

## Task Checklist

### Phase 1: Preparation (1-2 hours)

- [ ] **Task 1.1**: Create routes/ directory structure
  ```bash
  mkdir -p research_monitor/routes
  touch research_monitor/routes/__init__.py
  ```

- [ ] **Task 1.2**: Read and understand current app_v2.py structure
  - [ ] Review all 72 routes and their dependencies
  - [ ] Identify shared utilities to keep in app_v2.py
  - [ ] Map which routes belong to which blueprint

- [ ] **Task 1.3**: Create blueprint registration helper
  - [ ] Implement `research_monitor/routes/__init__.py`
  - [ ] Add `register_blueprints(app)` function
  - [ ] Document blueprint registration order

### Phase 2: Extract Blueprints (8-12 hours)

#### 2.1. Documentation Routes (30 min)

- [ ] **Task 2.1.1**: Create routes/docs.py
  - [ ] Extract `/api/docs` route
  - [ ] Extract `/api/openapi.json` route
  - [ ] Add module docstring
  - [ ] Create blueprint with url_prefix

- [ ] **Task 2.1.2**: Test docs blueprint
  - [ ] Import blueprint in app_v2.py
  - [ ] Register blueprint
  - [ ] Test endpoints respond correctly
  - [ ] Remove old route code from app_v2.py

#### 2.2. System Routes (1 hour)

- [ ] **Task 2.2.1**: Create routes/system.py
  - [ ] Extract `/api/server/health` route
  - [ ] Extract `/api/server/shutdown` route
  - [ ] Extract `/api/stats` route
  - [ ] Extract `/api/cache/stats` route
  - [ ] Extract `/api/cache/clear` route
  - [ ] Extract `/api/activity/recent` route
  - [ ] Extract `/api/research/session` route
  - [ ] Extract `/` root route
  - [ ] Update config access to use `current_app.config`
  - [ ] Import shared utilities from app_v2

- [ ] **Task 2.2.2**: Test system blueprint
  - [ ] Register blueprint in app_v2.py
  - [ ] Test all system endpoints
  - [ ] Verify server management works
  - [ ] Remove old route code from app_v2.py

#### 2.3. Git Integration Routes (30 min)

- [ ] **Task 2.3.1**: Create routes/git.py
  - [ ] Extract `/api/git/pull` route
  - [ ] Extract `/api/git/status` route
  - [ ] Extract `/api/commit/reset` route
  - [ ] Extract `/api/commit/status` route
  - [ ] Update config access patterns
  - [ ] Import git service dependencies

- [ ] **Task 2.3.2**: Test git blueprint
  - [ ] Register blueprint in app_v2.py
  - [ ] Test git operations
  - [ ] Test commit counter
  - [ ] Remove old route code from app_v2.py

#### 2.4. Priority Routes (1 hour)

- [ ] **Task 2.4.1**: Create routes/priorities.py
  - [ ] Extract `POST /api/priorities/next` route
  - [ ] Extract `GET /api/priorities/next` route
  - [ ] Extract `PUT /api/priorities/<id>/start` route
  - [ ] Extract `PUT /api/priorities/<id>/status` route
  - [ ] Extract `GET /api/priorities/export` route
  - [ ] Update database connection usage
  - [ ] Import authentication decorator

- [ ] **Task 2.4.2**: Test priorities blueprint
  - [ ] Register blueprint in app_v2.py
  - [ ] Test priority management workflow
  - [ ] Test with research_cli.py commands
  - [ ] Remove old route code from app_v2.py

#### 2.5. Timeline Routes (2 hours)

- [ ] **Task 2.5.1**: Create routes/timeline.py
  - [ ] Extract `GET /api/timeline/events` route
  - [ ] Extract `GET /api/timeline/events/<id>` route
  - [ ] Extract `GET /api/timeline/events/date/<date>` route
  - [ ] Extract `GET /api/timeline/events/year/<year>` route
  - [ ] Extract `GET /api/timeline/events/actor/<actor>` route
  - [ ] Extract `GET /api/timeline/actors` route
  - [ ] Extract `GET /api/timeline/tags` route
  - [ ] Extract `GET /api/timeline/sources` route
  - [ ] Extract `GET /api/timeline/date-range` route
  - [ ] Extract `GET /api/timeline/actor/<actor>/timeline` route
  - [ ] Extract remaining timeline routes
  - [ ] Update database queries
  - [ ] Ensure read-only access pattern

- [ ] **Task 2.5.2**: Test timeline blueprint
  - [ ] Register blueprint in app_v2.py
  - [ ] Test all timeline query endpoints
  - [ ] Test search functionality
  - [ ] Verify performance
  - [ ] Remove old route code from app_v2.py

#### 2.6. Event Routes (2 hours)

- [ ] **Task 2.6.1**: Create routes/events.py
  - [ ] Extract `GET /api/events/search` route
  - [ ] Extract `GET /api/events/missing-sources` route
  - [ ] Extract `GET /api/events/validation-queue` route
  - [ ] Extract `GET /api/events/broken-links` route
  - [ ] Extract `GET /api/events/research-candidates` route
  - [ ] Extract `POST /api/events/validate` route
  - [ ] Extract `POST /api/events/batch` route
  - [ ] Extract `POST /api/events/staged` route
  - [ ] Extract remaining event routes
  - [ ] Update filesystem access via config
  - [ ] Import validation functions
  - [ ] Import authentication decorator

- [ ] **Task 2.6.2**: Test events blueprint
  - [ ] Register blueprint in app_v2.py
  - [ ] Test event search
  - [ ] Test event creation
  - [ ] Test validation
  - [ ] Test with research_cli.py
  - [ ] Remove old route code from app_v2.py

#### 2.7. QA Routes (2 hours)

- [ ] **Task 2.7.1**: Create routes/qa.py
  - [ ] Extract `GET /api/qa/queue` route
  - [ ] Extract `GET /api/qa/next` route
  - [ ] Extract `GET /api/qa/stats` route
  - [ ] Extract `GET /api/qa/issues/<type>` route
  - [ ] Extract `GET /api/qa/rejected` route
  - [ ] Extract `POST /api/qa/validate/<id>` route
  - [ ] Extract `POST /api/qa/reject/<id>` route
  - [ ] Extract `POST /api/qa/enhance/<id>` route
  - [ ] Extract `POST /api/qa/start/<id>` route
  - [ ] Extract `POST /api/qa/score` route
  - [ ] Extract `POST /api/qa/batch/reserve` route
  - [ ] Extract `POST /api/qa/batch/release` route
  - [ ] Extract `POST /api/qa/validation/initialize` route
  - [ ] Extract `POST /api/qa/validation/reset` route
  - [ ] Update QA system dependencies
  - [ ] Import validation functions

- [ ] **Task 2.7.2**: Test QA blueprint
  - [ ] Register blueprint in app_v2.py
  - [ ] Test QA queue workflow
  - [ ] Test validation/rejection
  - [ ] Test batch operations
  - [ ] Test with research_cli.py QA commands
  - [ ] Remove old route code from app_v2.py

#### 2.8. Validation Run Routes (2 hours)

- [ ] **Task 2.8.1**: Create routes/validation_runs.py
  - [ ] Extract `GET /api/validation-runs` route
  - [ ] Extract `POST /api/validation-runs` route
  - [ ] Extract `GET /api/validation-runs/<id>` route
  - [ ] Extract `GET /api/validation-runs/<id>/next` route
  - [ ] Extract `POST /api/validation-runs/<id>/events/<event_id>/complete` route
  - [ ] Extract `POST /api/validation-runs/<id>/requeue-needs-work` route
  - [ ] Extract `GET /api/validation-logs` route
  - [ ] Extract `POST /api/validation-logs` route
  - [ ] Extract `GET /api/event-update-failures` route
  - [ ] Extract `GET /api/event-update-failures/stats` route
  - [ ] Update validation run logic
  - [ ] Import database dependencies

- [ ] **Task 2.8.2**: Test validation_runs blueprint
  - [ ] Register blueprint in app_v2.py
  - [ ] Test validation run creation
  - [ ] Test event assignment
  - [ ] Test completion workflow
  - [ ] Test with research_cli.py validation commands
  - [ ] Remove old route code from app_v2.py

### Phase 3: Integration (1-2 hours)

- [ ] **Task 3.1**: Update app_v2.py
  - [ ] Remove all extracted route code
  - [ ] Keep shared utilities (require_api_key, db_connection, etc.)
  - [ ] Import register_blueprints from routes
  - [ ] Call register_blueprints(app) after app creation
  - [ ] Verify app.config contains all needed values

- [ ] **Task 3.2**: Verify imports
  - [ ] Check for circular import issues
  - [ ] Ensure all blueprints import correctly
  - [ ] Verify shared utilities accessible from blueprints
  - [ ] Test import order

- [ ] **Task 3.3**: Update documentation
  - [ ] Update CLAUDE.md with new structure
  - [ ] Document blueprint organization
  - [ ] Update architecture notes
  - [ ] Add import guidelines

### Phase 4: Testing & Validation (2-3 hours)

- [ ] **Task 4.1**: Automated testing
  - [ ] Run full test suite: `python3 -m unittest discover -s tests -v`
  - [ ] Verify 221 tests still pass
  - [ ] Check test coverage: `coverage run -m unittest discover`
  - [ ] Ensure coverage maintained or improved

- [ ] **Task 4.2**: Type safety
  - [ ] Run MyPy on all route modules
  - [ ] Fix any type errors
  - [ ] Verify 100% MyPy compliance
  - [ ] Check for any new warnings

- [ ] **Task 4.3**: Integration testing via CLI
  - [ ] Test server start: `python3 research_cli.py server-start`
  - [ ] Test server status: `python3 research_cli.py server-status`
  - [ ] Test stats: `python3 research_cli.py get-stats`
  - [ ] Test search: `python3 research_cli.py search-events --query "test"`
  - [ ] Test priorities: `python3 research_cli.py get-next-priority`
  - [ ] Test QA: `python3 research_cli.py qa-queue --limit 5`
  - [ ] Test validation runs: `python3 research_cli.py validation-runs-list`

- [ ] **Task 4.4**: Performance testing
  - [ ] Measure server startup time (should be <2s)
  - [ ] Test search response time
  - [ ] Verify no performance degradation
  - [ ] Check memory usage

- [ ] **Task 4.5**: Pre-commit hooks
  - [ ] Verify all pre-commit hooks pass
  - [ ] Test JSON validation
  - [ ] Test API generation
  - [ ] Ensure no regressions

### Phase 5: Documentation & Commit (1 hour)

- [ ] **Task 5.1**: Update METRICS.md
  - [ ] Document refactoring completion
  - [ ] Note lines of code reduction (4649 → ~300)
  - [ ] List all 8 blueprints created
  - [ ] Update code organization metrics

- [ ] **Task 5.2**: Update CLAUDE.md
  - [ ] Document new routes/ structure
  - [ ] Update architecture section
  - [ ] Add blueprint organization notes
  - [ ] Include import guidelines

- [ ] **Task 5.3**: Final verification
  - [ ] All tests passing
  - [ ] Zero MyPy errors
  - [ ] All 72 endpoints responding
  - [ ] Server starts cleanly
  - [ ] No circular imports

- [ ] **Task 5.4**: Commit changes
  - [ ] Stage all changes: `git add research_monitor/`
  - [ ] Review diff carefully
  - [ ] Create comprehensive commit message
  - [ ] Reference spec: "Implements spec 001-extract-routes"
  - [ ] Push to branch

## Success Metrics

At completion, verify:
- ✅ All 221 tests pass
- ✅ Zero MyPy errors
- ✅ All 72 endpoints respond correctly
- ✅ Server startup time < 2 seconds
- ✅ No circular imports
- ✅ app_v2.py reduced from 4649 to ~300 lines
- ✅ Each blueprint module < 1000 lines
- ✅ Code organization score improved

## Rollback Plan

If issues arise at any phase:
1. **Git revert**: Single atomic commit per blueprint
2. **Incremental rollback**: Revert only problematic blueprint
3. **Emergency**: Full revert to pre-refactoring state

## Notes

- Test after EACH blueprint extraction (don't batch)
- Keep commits atomic per blueprint if possible
- Document any deviations from plan
- Update this file with actual time spent per phase
- Mark tasks complete as you go

---

**Ready to implement using `/speckit.implement` workflow**
