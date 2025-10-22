# Final Pre-Split Cleanup Report
**Date**: 2025-10-21
**Status**: Additional cleanup needed before repository split

---

## Executive Summary

After the initial cleanup that freed ~230MB, a comprehensive scan revealed additional items that should be cleaned up:

### Critical Issues Found
- **32MB** of scraped HTML sources being tracked in git (should not be)
- **14MB** of React build artifacts (should be gitignored)
- **4 duplicate/outdated scripts** in root directory
- **2 empty database files** in wrong locations
- **25 references** to old "timeline_data" path in Python code
- **1 duplicate MCP server file** (28KB)

### Total Additional Space to Free: ~48MB

---

## 🚨 Critical: Files That Should NOT Be in Git

### 1. timeline/data/events/.sources/ (32MB)
**Location**: `timeline/data/events/.sources/`
**Size**: 32MB
**Files**: 100+ scraped HTML files

**Contents**:
- Cached web scraper output (HTML files)
- `scraping_errors.log` (84KB)
- `scraping_progress.json`
- `metadata.json`

**Problem**: These are temporary scraper artifacts, not source data. They contain:
- Full HTML of scraped web pages
- Temporary logs and progress files
- Should be regenerated locally, not committed

**Action Required**:
```bash
# Add to .gitignore
echo "timeline/data/events/.sources/" >> .gitignore

# Remove from git (but keep locally if needed)
git rm -r --cached timeline/data/events/.sources/
```

---

## 🗑️ Build Artifacts to Delete

### 2. timeline/viewer/build/ (14MB)
**Location**: `timeline/viewer/build/`
**Size**: 14MB
**Files**: 23 files (React production build)

**Problem**: This is a build output directory that should be regenerated, not committed.

**Action Required**:
```bash
# Delete build directory
rm -rf timeline/viewer/build/

# Already in .gitignore, but verify
grep "viewer/build" .gitignore
```

### 3. timeline/viewer/coverage/
**Location**: `timeline/viewer/coverage/`
**Files**: Test coverage output

**Problem**: Test coverage reports should not be committed.

**Action Required**:
```bash
# Delete coverage directory
rm -rf timeline/viewer/coverage/

# Update .gitignore
echo "timeline/viewer/coverage/" >> .gitignore
```

---

## 📄 Root Directory Cleanup

### 4. Duplicate/Outdated Files in Root

#### Duplicate MCP Server (28KB)
- **File**: `mcp_timeline_server_v2.py`
- **Duplicate of**: `research-server/mcp/mcp_server.py` (identical, 669 lines)
- **Action**: Delete root copy, use research-server version

#### Outdated Scripts (Broken Paths)

**build_static_site.sh**:
- References old `api/` directory (doesn't exist)
- References old `timeline_data/` path (now `timeline/data/`)
- **Status**: OUTDATED
- **Action**: Delete or update paths

**validate_new_events.sh**:
- References `timeline_data/events` (now `timeline/data/events`)
- **Status**: OUTDATED
- **Action**: Delete or update paths

**run_tests.sh**:
- References `research_monitor` (now `research-server`)
- References `api` (doesn't exist)
- **Status**: OUTDATED
- **Action**: Delete or update paths

#### Empty/Minimal Files

**package-lock.json** (99 bytes):
- Empty lockfile with no corresponding `package.json` in root
- Actual `package.json` is in `timeline/viewer/`
- **Action**: Delete

**.DS_Store** (8KB):
- macOS metadata file
- **Action**: Delete (already in .gitignore)

---

## 🗄️ Database Files to Delete

### 5. Empty Database Files

**research-server/server/unified_research.db** (0 bytes):
- Empty database file
- Gets regenerated from timeline events on server start
- **Action**: Delete

**timeline/viewer/unified_research.db** (0 bytes):
- Empty database file in wrong location
- Viewer shouldn't have its own database
- **Action**: Delete

---

## 🧹 Cache Files to Delete

### 6. Root .pytest_cache/
**Location**: `.pytest_cache/`
**Problem**: Test cache directory in root
**Action**: Delete (already in .gitignore, but exists)

---

## 📝 Code Quality Issues

### 7. Outdated Path References

**25 references to "timeline_data" in research-server/**:
- Old path structure was `timeline_data/events`
- New path structure is `timeline/data/events`

**Files affected** (partial list):
- Various Python modules in `research-server/`
- Need systematic find/replace

**Action**: Update all references from `timeline_data` to `timeline/data`

---

## 📊 Cleanup Action Plan

### Phase 1: Critical Deletions (~48MB freed)

```bash
# 1. Remove scraped sources from git (32MB)
git rm -r --cached timeline/data/events/.sources/
echo "timeline/data/events/.sources/" >> .gitignore

# 2. Delete build artifacts (14MB)
rm -rf timeline/viewer/build/
rm -rf timeline/viewer/coverage/

# 3. Delete empty databases (0 bytes but cleanup)
rm -f research-server/server/unified_research.db
rm -f timeline/viewer/unified_research.db

# 4. Delete root duplicates/outdated files
rm -f mcp_timeline_server_v2.py
rm -f package-lock.json
rm -f .DS_Store
rm -rf .pytest_cache/

# 5. Delete or update outdated scripts
rm -f build_static_site.sh
rm -f validate_new_events.sh
rm -f run_tests.sh
# OR update their paths if still needed
```

### Phase 2: Update .gitignore

```bash
# Add missing patterns to .gitignore
cat >> .gitignore << 'EOF'

# Scraped source cache
timeline/data/events/.sources/

# React viewer coverage
timeline/viewer/coverage/

# Root-level cache and metadata
.DS_Store
package-lock.json
EOF
```

### Phase 3: Code Updates (Optional)

```bash
# Update old path references
find research-server -name "*.py" -type f -exec sed -i '' 's/timeline_data/timeline\/data/g' {} +
```

---

## 🎯 Impact Summary

### Space to Free
| Category | Size | Files |
|----------|------|-------|
| Scraped sources | 32MB | 100+ |
| Build artifacts | 14MB | 30+ |
| Duplicate MCP | 28KB | 1 |
| Outdated scripts | ~15KB | 3 |
| Cache/metadata | ~10KB | 3 |
| **TOTAL** | **~48MB** | **~140** |

### Repository Size After Cleanup
| Component | Current | After Cleanup |
|-----------|---------|---------------|
| timeline/ | 490MB | ~458MB (remove .sources/) |
| research-server/ | 3.6MB | 3.6MB (no change) |
| Root files | ~100KB | ~50KB |
| **Total working** | ~494MB | **~462MB** |

### Benefits
1. ✅ **No scraped HTML in git** - Reduces repo bloat
2. ✅ **No build artifacts** - Proper separation of source/build
3. ✅ **Clean root directory** - Only necessary files
4. ✅ **Updated paths** - No references to old structure
5. ✅ **Ready for split** - Clean separation possible

---

## ✅ Pre-Split Checklist (Updated)

- [x] Archive development docs (~230MB) ✅ **COMPLETED**
- [x] Remove experimental code (108MB) ✅ **COMPLETED**
- [x] Delete backup files (115MB) ✅ **COMPLETED**
- [ ] **Remove scraped sources from git (32MB)** ⚠️ **NEEDED**
- [ ] **Delete build artifacts (14MB)** ⚠️ **NEEDED**
- [ ] **Delete duplicate/outdated root files** ⚠️ **NEEDED**
- [ ] **Update .gitignore** ⚠️ **NEEDED**
- [ ] **Optional: Update old path references** (25 files)

---

## 🚀 Recommended Execution

### Quick Clean (5 minutes) - Critical Issues Only

```bash
# Remove from git but keep locally
git rm -r --cached timeline/data/events/.sources/

# Delete build artifacts
rm -rf timeline/viewer/build/ timeline/viewer/coverage/

# Delete duplicates/outdated
rm -f mcp_timeline_server_v2.py package-lock.json .DS_Store
rm -rf .pytest_cache/
rm -f research-server/server/unified_research.db timeline/viewer/unified_research.db

# Delete outdated scripts
rm -f build_static_site.sh validate_new_events.sh run_tests.sh

# Update .gitignore
cat >> .gitignore << 'EOF'
# Scraped source cache
timeline/data/events/.sources/
# React viewer coverage
timeline/viewer/coverage/
EOF

# Commit
git add -A
git commit -m "Second cleanup pass: Remove build artifacts, scraped sources, and outdated files

- Remove 32MB of scraped HTML from git tracking
- Delete 14MB of React build artifacts
- Remove duplicate mcp_timeline_server_v2.py (use research-server/mcp/ version)
- Delete outdated scripts with wrong paths (build_static_site.sh, etc.)
- Remove empty database files
- Update .gitignore to prevent re-addition

Frees ~48MB additional space for clean repository split."
```

---

## 📚 Files to Keep in Archive

If you want to preserve the scraped sources locally but not in git:

```bash
# Before running git rm, copy to archive
mkdir -p archive/scraped-sources-20251021
cp -r timeline/data/events/.sources/ archive/scraped-sources-20251021/

# Then proceed with git rm
git rm -r --cached timeline/data/events/.sources/
```

---

## 🔍 Post-Cleanup Verification

After cleanup, verify:

```bash
# Check repository size
du -sh timeline/ research-server/

# Verify clean working directory
git status

# Confirm test suite still passes
cd research-server && python3 -m pytest

# Verify .gitignore working
git status timeline/data/events/.sources/  # Should show "ignored"
```

---

**Next Actions**: Execute Phase 1 cleanup to prepare for final repository split.

**Estimated time**: 5-10 minutes
**Risk**: Low (all deletions are safe, files can be regenerated)
**Benefit**: Cleaner repository, faster clones, proper separation of concerns
