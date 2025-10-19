# Kleptocracy Timeline - SpecKit Specifications

Comprehensive specifications for repository cleanup, split, and refactoring.

## 📋 Overview

This directory contains detailed SpecKit-style specifications for transforming the Kleptocracy Timeline from a monorepo prototype into production-ready, split repositories.

**Total Specs**: 13 specifications across 4 phases
**Estimated Time**: 18-36 hours of focused work

## 🎯 Quick Start

### What Are These Specs?

Each specification follows SpecKit format:
- **Problem**: What needs fixing
- **Goal**: Desired outcome
- **Success Criteria**: How to measure success
- **Implementation Steps**: Detailed commands and code
- **Validation**: How to verify it worked
- **Rollback**: How to undo if needed

### How to Use

1. **Read [SPEC_INDEX.md](SPEC_INDEX.md)** - Complete overview
2. **Start with Phase 1** - Critical cleanup before split
3. **Execute sequentially** - Each phase builds on previous
4. **Validate thoroughly** - Run tests after each spec

## 📁 Directory Structure

```
specs/
├── README.md                    # This file
├── SPEC_INDEX.md                # Complete index with dependencies
├── phase1-cleanup/              # Pre-split cleanup (2-4 hours)
│   ├── 001-move-tests-to-correct-location.md
│   ├── 002-consolidate-documentation.md
│   ├── 003-choose-static-site-generator.md
│   └── 004-fix-timeline-path-consistency.md
├── phase2-split/                # Repository split (1-2 hours)
│   ├── 001-create-timeline-data-repository.md
│   └── 002-create-research-server-repository.md
├── phase3-refactor/             # Code quality improvements (10-20 hours)
│   └── 001-extract-services-from-app.md
└── phase4-polish/               # Final polish (5-10 hours)
    └── 001-generate-openapi-documentation.md
```

## 🚀 Phase Overview

### Phase 1: Pre-Split Cleanup (Critical)

**Time**: 2-4 hours
**Must complete before split**

- SPEC-001: Move test files to correct location (15 min)
- SPEC-002: Consolidate duplicate documentation (30 min)
- SPEC-003: Choose one static site generator (1 hour)
- SPEC-004: Fix timeline path consistency (20 min)

**Why**: Clean up inconsistencies that would propagate to split repos

### Phase 2: Repository Split

**Time**: 1-2 hours
**Creates two separate repositories**

- SPEC-005: Create timeline data repository (1-2 hours)
- SPEC-006: Create research server repository (1 hour)

**Output**:
- `kleptocracy-timeline` - Public timeline data + viewer
- `timeline-research-server` - Research tools (API, CLI, MCP)

### Phase 3: Refactoring (Can be incremental)

**Time**: 10-20 hours
**Improves code quality in research server**

- SPEC-007: Extract services from app_v2.py (4-6 hours)
- More specs planned...

**Why**: Reduce app_v2.py from 4,708 lines to <500 lines

### Phase 4: Polish (Can be incremental)

**Time**: 5-10 hours
**Final quality improvements**

- SPEC-013: Generate OpenAPI documentation (2-3 hours)
- More specs planned...

**Why**: Production-ready documentation and tooling

## ⚡ Quick Commands

### Phase 1 (Execute in order)

```bash
# SPEC-001: Move tests
mv research-server/server/test_*.py research-server/tests/integration/
pytest research-server/tests/

# SPEC-002: Consolidate docs
mkdir -p research-server/docs
mv research-server/server/API_DOCUMENTATION.md research-server/docs/API.md
rm research-server/server/static/API_DOCUMENTATION.md

# SPEC-003: Remove Hugo
rm -rf timeline/content/ timeline/public/ timeline/hugo.toml

# SPEC-004: Fix paths
# (manual updates to documentation and config)
```

### Phase 2 (Repository split)

```bash
# SPEC-005: Create timeline repo
git subtree split -P timeline -b timeline-data-only
gh repo create kleptocracy-timeline --public

# SPEC-006: Create research server repo
git subtree split -P research-server -b research-server-only
gh repo create timeline-research-server --public
```

## 📖 Detailed Specs

### SPEC-001: Move Tests to Correct Location
**File**: [phase1-cleanup/001-move-tests-to-correct-location.md](phase1-cleanup/001-move-tests-to-correct-location.md)

Moves test files from `research-server/server/` to proper `tests/` directory.

**Impact**: Cleaner separation of production code and tests

### SPEC-002: Consolidate Documentation
**File**: [phase1-cleanup/002-consolidate-documentation.md](phase1-cleanup/002-consolidate-documentation.md)

Removes 3 copies of API documentation, creates single source in `docs/`.

**Impact**: Single source of truth, less confusion

### SPEC-003: Choose Static Site Generator
**File**: [phase1-cleanup/003-choose-static-site-generator.md](phase1-cleanup/003-choose-static-site-generator.md)

Removes Hugo, keeps React viewer. Reduces timeline dir from 759MB to ~50MB.

**Impact**: Simpler architecture, massive size reduction

### SPEC-004: Fix Timeline Path Consistency
**File**: [phase1-cleanup/004-fix-timeline-path-consistency.md](phase1-cleanup/004-fix-timeline-path-consistency.md)

Standardizes all references to `timeline/data/events/YYYY/`.

**Impact**: Consistent paths across all code and documentation

### SPEC-005: Create Timeline Data Repository
**File**: [phase2-split/001-create-timeline-data-repository.md](phase2-split/001-create-timeline-data-repository.md)

Extracts timeline data + viewer into separate public repository.

**Impact**: Public timeline data, independent deployment

### SPEC-006: Create Research Server Repository
**File**: [phase2-split/002-create-research-server-repository.md](phase2-split/002-create-research-server-repository.md)

Extracts research server (API, CLI, MCP) into separate repository.

**Impact**: Development tools separate from public data

### SPEC-007: Extract Services from app_v2.py
**File**: [phase3-refactor/001-extract-services-from-app.md](phase3-refactor/001-extract-services-from-app.md)

Refactors monolithic 4,708-line app_v2.py into service layer.

**Impact**: Cleaner architecture, testable business logic

### SPEC-013: Generate OpenAPI Documentation
**File**: [phase4-polish/001-generate-openapi-documentation.md](phase4-polish/001-generate-openapi-documentation.md)

Generates API docs automatically from code using OpenAPI 3.0.

**Impact**: Always up-to-date docs, interactive testing

## 🎓 How to Execute a Spec

Each spec includes:

1. **Problem Statement** - Why this change is needed
2. **Implementation Steps** - Exact commands to run
3. **Validation Steps** - How to verify it worked
4. **Rollback Plan** - How to undo if problems occur

Example workflow:

```bash
# 1. Read spec thoroughly
less specs/phase1-cleanup/001-move-tests-to-correct-location.md

# 2. Create feature branch
git checkout -b spec-001-move-tests

# 3. Execute implementation steps (from spec)
mv research-server/server/test_*.py research-server/tests/integration/

# 4. Run validation steps (from spec)
pytest research-server/tests/ -v

# 5. Commit if successful
git commit -m "SPEC-001: Move test files to correct location"
```

## ⚠️ Important Notes

### Dependencies

Specs must be executed in order within each phase:
- Phase 1: All specs sequentially
- Phase 2: SPEC-005 then SPEC-006
- Phase 3 & 4: Can be done in any order after Phase 2

### Rollback

Every spec includes rollback instructions. If something goes wrong:

```bash
# Check spec for rollback section
# Usually involves:
git checkout <files>  # Restore from git
git clean -fd         # Remove new files
```

### Testing

After EVERY spec:

```bash
# Run tests
pytest research-server/tests/ -v

# Start server (if relevant)
./research server-start
./research get-stats

# Verify no regressions
```

## 📊 Progress Tracking

Track progress by checking off specs in [SPEC_INDEX.md](SPEC_INDEX.md).

Update status column:
- **Ready** → **In Progress** → **Complete**

## 🤝 Contributing to Specs

If you find issues or improvements:

1. Note the spec number (e.g., SPEC-001)
2. Document the issue
3. Update the spec with fixes
4. Update SPEC_INDEX.md if dependencies change

## 🔗 Related Documentation

- [ARCHITECTURE_REVIEW.md](../ARCHITECTURE_REVIEW.md) - Detailed analysis
- [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) - Release preparation
- [INSTALLATION.md](../INSTALLATION.md) - Setup guide
- [IMPROVEMENTS_SUMMARY.md](../IMPROVEMENTS_SUMMARY.md) - Recent changes

## 📞 Questions?

- Open an issue referencing the spec number
- Tag as `question` or `spec-clarification`
- Include which step you're stuck on

## License

Specifications are CC0 (public domain) - use freely for your own projects.
