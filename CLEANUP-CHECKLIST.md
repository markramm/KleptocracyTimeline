# Pre-Split Cleanup Checklist

**Purpose**: Clean up the repository before splitting into `kleptocracy-timeline` (events + viewer) and `kleptocracy-research` (research infrastructure) repositories.

**Date**: 2025-10-19

---

## ✅ Critical Cleanup (Must Do Before Split)

### 1. Remove Build Artifacts ✅ Ready
**Impact**: Reduces repo size, prevents confusion

```bash
# Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null

# Coverage reports
rm -rf htmlcov/ .coverage coverage.json research-server/htmlcov/ research-server/.coverage

# Node modules (if needed, can be reinstalled)
# rm -rf timeline/viewer/node_modules/

# Hugo build artifacts
rm -rf timeline/public/ timeline/resources/ timeline/.hugo_build.lock timeline/archetypes/
```

**Files to remove**: ~500MB of cache files

---

### 2. Remove Database Files ✅ Ready
**Impact**: Database should be regenerated from filesystem events

```bash
# Root database files (should be in research-server/)
rm -f unified_research.db unified_research.db-wal unified_research.db-shm

# Any other database files
find . -name "*.db" -o -name "*.db-wal" -o -name "*.db-shm" -o -name "*.sqlite" -o -name "*.sqlite3"
```

**Note**: Database is regenerated from timeline events automatically on server start.

**Files to remove**:
- `unified_research.db` (16MB)
- `unified_research.db-wal` (32KB)
- `unified_research.db-shm` (empty)

---

### 3. Remove Backup Files ✅ Ready
**Impact**: Cleans up development artifacts

```bash
# Backup files from editing
find . -name "*.backup" -delete
find . -name "*.bak" -delete
find . -name "*.old" -delete
find . -name "*~" -delete

# Specific files found:
rm -f research-server/server/enhanced_event_validator.py.bak
rm -f research-server/server/app_v2.py.backup
rm -f README.md.backup
```

**Files to remove**: ~20 backup files in timeline/data/events/ and research-server/

---

### 4. Commit Pending Changes ✅ Ready
**Impact**: Clean git state before split

**Current status** (from `git status`):
- Modified files: ~15 test files, config files
- Deleted files: ~10 event files (old formats/duplicates)

```bash
# Review changes
git status
git diff

# Commit SPEC-008 Phase 9 work
git add research-server/tests/e2e/test_e2e.py
git add SPEC-008-PHASE-9-SUMMARY.md
git add SPEC-008-FINAL-REPORT.md

# Review deleted event files (ensure intentional)
git status | grep "deleted:"

# Create comprehensive commit
git commit -m "SPEC-008 Phase 9: Fix E2E tests against live server

- Fixed 7 API contract mismatches in E2E tests
- E2E test suite now 100% passing (10/10 tests)
- Updated SPEC-008 documentation with final results
- Achieved 82.2% overall pass rate (212/258 tests)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 📋 Important Cleanup (Recommended Before Split)

### 5. Review and Update Documentation 🔍 Review Needed
**Impact**: Ensures accurate documentation for both repos

**Timeline Repository Docs** (stays in kleptocracy-timeline):
- `timeline/README.md` - Timeline-specific guide
- `timeline/docs/EVENT_FORMAT.md` - Event format documentation
- Root `README.md` - Update for timeline-only repo after split

**Research Server Docs** (moves to kleptocracy-research):
- `research-server/README.md` - Research server guide
- `research-server/docs/` - API documentation
- `CLAUDE.md` - Research workflow instructions (update paths)

**Shared Docs** (decide where to keep):
- `SPEC-*.md` files - Implementation specifications
- Development documentation

**Action Items**:
```bash
# Review and update main README for timeline repo
# TODO: Create separate README for research repo
# TODO: Update CLAUDE.md paths for split repos
```

---

### 6. Clean Up Test Artifacts 🔍 Review Needed
**Impact**: Removes temporary test data

```bash
# Test database files (if any in test directories)
find research-server/tests -name "*.db" -o -name "*.sqlite"

# Test output files
find research-server/tests -name "test_output_*" -delete
find research-server/tests -name "temp_*" -delete
```

---

### 7. Update .gitignore for Split 🔍 Review Needed
**Impact**: Ensures proper ignore patterns for each repo

**Timeline repo .gitignore** (simplified):
```gitignore
# Focus on timeline/viewer artifacts
node_modules/
.next/
build/
*.log
.DS_Store
.env.local
```

**Research repo .gitignore** (comprehensive):
```gitignore
# Keep existing Python, database, test patterns
__pycache__/
*.pyc
*.db
*.db-wal
*.db-shm
.pytest_cache/
.coverage
htmlcov/
.env
```

---

### 8. Archive Deprecated Code ✅ Already Done
**Impact**: Moved deprecated tests to archive

**Status**: ✅ Complete
- Deprecated tests in `research-server/tests/deprecated/`
- Migration guide in `research-server/tests/deprecated/README.md`

---

## 🔧 Optional Cleanup (Nice to Have)

### 9. Consolidate Event File Formats 🔍 Review Needed
**Impact**: Ensure consistent event format

**Current state**:
- Mix of `.json` and `.md` event files
- Both formats supported by parser

**Options**:
1. Keep both formats (current approach - flexible)
2. Migrate all to `.md` format (better for manual editing)
3. Migrate all to `.json` format (better for programmatic access)

**Recommendation**: Keep both formats, document in `EVENT_FORMAT.md`

---

### 10. Remove Empty/Placeholder Directories 🔍 Review Needed

```bash
# Find empty directories
find . -type d -empty

# Review and remove if not needed
```

---

### 11. Optimize Event Data 🔍 Review Needed
**Impact**: Ensure data quality before split

**Action Items**:
```bash
# Run validation
python3 research-server/cli/research_cli.py qa-stats

# Check for:
# - Events with insufficient sources
# - Events with broken links
# - Events with missing required fields
```

**Status from recent validation**:
- 1,582 total events
- 0 validated (validation system not fully utilized yet)
- Consider running validation pass before split

---

### 12. Clean Up Scripts Directory 🔍 Review Needed

```bash
# Review scripts in both repos
ls -la timeline/scripts/
ls -la research-server/scripts/

# Move scripts to appropriate repo:
# - Event conversion/validation → timeline repo
# - Research/QA scripts → research repo
```

---

## 📊 Size Analysis Before Cleanup

```bash
# Current repo size
du -sh .

# Timeline directory
du -sh timeline/

# Research server directory
du -sh research-server/

# Database files
du -sh *.db*

# Build artifacts
du -sh htmlcov/ .pytest_cache/ __pycache__/
```

---

## 🎯 Recommended Cleanup Order

1. **Commit current work** (SPEC-008 Phase 9)
2. **Remove build artifacts** (Python cache, coverage reports)
3. **Remove database files** (will regenerate)
4. **Remove backup files** (.bak, .backup, .old)
5. **Review and update documentation**
6. **Run final test suite** (ensure 82.2% pass rate maintained)
7. **Create pre-split checkpoint commit**
8. **Proceed with repository split**

---

## ✅ Verification Checklist

Before splitting, verify:

- [ ] All SPEC-008 work committed
- [ ] Build artifacts removed
- [ ] Database files removed (or moved to research-server/)
- [ ] Backup files cleaned up
- [ ] Documentation updated
- [ ] Test suite passing (82.2% pass rate)
- [ ] Git status clean (no uncommitted changes)
- [ ] .gitignore updated for split repos

---

## 📝 Post-Cleanup Actions

After cleanup, before split:

1. Create final checkpoint:
```bash
git add .
git commit -m "Pre-split cleanup: Remove build artifacts and prepare for repository split"
```

2. Tag the pre-split state:
```bash
git tag -a pre-split-cleanup -m "Pre-split cleanup complete - ready for repo split"
```

3. Push to remote:
```bash
git push origin repository-restructure-prototype
git push --tags
```

---

## 📂 Expected Repository Sizes After Split

**kleptocracy-timeline** (events + viewer):
- `timeline/` directory
- Event data (~1,600 files)
- React viewer
- Documentation
- **Estimated size**: ~50-100MB (without node_modules)

**kleptocracy-research** (research infrastructure):
- `research-server/` directory
- Flask API, CLI, MCP server
- Test suite (258 tests)
- Documentation
- **Estimated size**: ~20-50MB

---

## 🚀 Ready for Split When:

✅ All cleanup tasks marked "Critical" are complete
✅ Documentation reviewed and updated
✅ Test suite passing
✅ Git state clean
✅ Pre-split tag created

---

**Next Step**: Execute cleanup commands and verify results before proceeding with repository split.
