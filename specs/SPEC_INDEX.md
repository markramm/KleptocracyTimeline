# Specification Index

Complete list of all specifications for repository cleanup, split, and refactoring.

## Phase 1: Pre-Split Cleanup (3-5 hours)

Critical tasks to prepare repository for splitting.

| Spec | Title | Priority | Time | Status |
|------|-------|----------|------|--------|
| [SPEC-001](phase1-cleanup/001-move-tests-to-correct-location.md) | Move Test Files to Correct Location | Critical | 15 min | Complete ✅ |
| [SPEC-002](phase1-cleanup/002-consolidate-documentation.md) | Consolidate Duplicate Documentation | Critical | 30 min | Complete ✅ |
| [SPEC-003](phase1-cleanup/003-choose-static-site-generator.md) | Choose One Static Site Generator | Critical | 1 hour | Complete ✅ |
| [SPEC-004](phase1-cleanup/004-fix-timeline-path-consistency.md) | Fix Timeline Path Consistency | Critical | 20 min | Complete ✅ |
| [SPEC-005](phase1-cleanup/005-remove-build-artifacts.md) | Remove Build Artifacts | Low | 5 min | Ready |
| [SPEC-006](phase1-cleanup/006-consolidate-duplicate-directories.md) | Consolidate Duplicate Directories | Medium | 30 min | Ready |
| [SPEC-007](phase1-cleanup/007-reorganize-root-directories.md) | Reorganize Root-Level Directories | High | 45 min | Ready |
| [SPEC-008](phase1-cleanup/008-update-gitignore.md) | Update .gitignore | Low | 10 min | Ready |

**Total Phase 1**: ~3.5 hours

## Phase 2: Repository Split (1-2 hours)

**Note**: Deferred until ready. Will use clean git history and rename to "Capture Cascade Timeline".

Extract components into separate repositories.

| Spec | Title | Priority | Time | Status |
|------|-------|----------|------|--------|
| [SPEC-009](phase2-split/001-create-timeline-data-repository.md) | Create Timeline Data Repository | Critical | 1-2 hours | Deferred |
| [SPEC-010](phase2-split/002-create-research-server-repository.md) | Create Research Server Repository | Critical | 1 hour | Deferred |

**Total Phase 2**: ~2 hours

## Phase 3: Refactoring (10-20 hours)

Improve code quality and architecture in separated repositories.

| Spec | Title | Priority | Time | Status |
|------|-------|----------|------|--------|
| [SPEC-011](phase3-refactor/001-extract-services-from-app.md) | Extract Services from app_v2.py | High | 4-6 hours | Ready |
| SPEC-012 | Add Dependency Injection | High | 2-3 hours | Planned |
| SPEC-013 | Add Request Validation Layer | High | 2-3 hours | Planned |
| SPEC-014 | API Versioning (v1/ prefix) | Medium | 1-2 hours | Planned |
| SPEC-015 | Implement Repository Pattern | Medium | 3-4 hours | Planned |
| SPEC-016 | Add Alembic Migrations | Medium | 2 hours | Planned |

**Total Phase 3**: ~15 hours

## Phase 4: Polish & Documentation (5-10 hours)

Final quality improvements and documentation.

| Spec | Title | Priority | Time | Status |
|------|-------|----------|------|--------|
| [SPEC-017](phase4-polish/001-generate-openapi-documentation.md) | Generate OpenAPI Documentation | Medium | 2-3 hours | Ready |
| SPEC-018 | Add Comprehensive Test Suite | High | 3-4 hours | Planned |
| SPEC-019 | Setup CI/CD Pipelines | Medium | 2 hours | Planned |
| SPEC-020 | Add Pre-commit Hooks | Low | 1 hour | Planned |
| SPEC-021 | Create Contributing Guidelines | Low | 1 hour | Planned |

**Total Phase 4**: ~8 hours

## Total Estimated Time

| Phase | Time |
|-------|------|
| Phase 1: Pre-Split Cleanup | 3-5 hours |
| Phase 2: Repository Split | 1-2 hours (Deferred) |
| Phase 3: Refactoring | 10-20 hours |
| Phase 4: Polish | 5-10 hours |
| **Total** | **19-37 hours** |

## Execution Order

### Phase 1: Pre-Split Cleanup (Do Before Repository Split)
1. ✅ SPEC-001 → ✅ SPEC-002 → ✅ SPEC-003 → ✅ SPEC-004 (Critical cleanup - COMPLETE)
2. SPEC-005 → SPEC-006 → SPEC-007 → SPEC-008 (Additional cleanup - READY)

### Phase 2: Repository Split (Deferred)
- SPEC-009 → SPEC-010 (Will use clean git history)
- Rename to "Capture Cascade Timeline"

### Phase 3 & 4: Can Do Anytime After Split
- SPEC-011 onwards
- Independent improvements
- Can be done incrementally

## Dependencies

```
✅ SPEC-001 (Move Tests)
    ↓
✅ SPEC-002 (Consolidate Docs)
    ↓
✅ SPEC-003 (Remove Hugo) → ✅ SPEC-004 (Fix Paths)
    ↓
SPEC-005 (Remove Artifacts) → SPEC-006 (Consolidate Dirs)
    ↓
SPEC-007 (Reorganize Root) → SPEC-008 (Update .gitignore)
    ↓
SPEC-009 (Timeline Repo) ← ← ← ← ← Phase 1 Complete
    ↓
SPEC-010 (Research Repo) ← ← ← ← ← Phase 2 Complete
    ↓
[Phase 3 & 4: Can be done in any order]
```

## Quick Reference

### Phase 1 Commands

```bash
# SPEC-001
mv research-server/server/test_*.py research-server/tests/integration/

# SPEC-002
mv research-server/server/API_DOCUMENTATION.md research-server/docs/API.md
rm research-server/server/static/API_DOCUMENTATION.md

# SPEC-003
rm -rf timeline/content/ timeline/public/ timeline/hugo.toml

# SPEC-004
grep -r "timeline_data/events" . | # Update all references
```

### Phase 2 Commands

```bash
# SPEC-005
git subtree split -P timeline -b timeline-data-only
gh repo create kleptocracy-timeline --public

# SPEC-006
git subtree split -P research-server -b research-server-only
gh repo create timeline-research-server --public
```

## Status Legend

- **Ready**: Specification complete, can be executed
- **Planned**: Specification outlined but not detailed
- **In Progress**: Currently being worked on
- **Complete**: Executed and validated

## Notes

- All specs use SpecKit format (Problem, Goal, Success Criteria, Implementation Steps)
- Each spec includes validation steps and rollback plan
- Estimated times are for focused work
- Phase 3 & 4 specs can be done incrementally (not all at once)
- Some specs (SPEC-008+) are outlined but need detailed implementation steps

## Next Actions

1. Execute Phase 1 specs (SPEC-001 through SPEC-004)
2. Validate all changes with tests
3. Commit changes
4. Execute Phase 2 split (SPEC-005, SPEC-006)
5. Plan Phase 3 & 4 execution based on priorities
