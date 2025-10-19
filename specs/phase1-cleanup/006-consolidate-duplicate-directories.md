# SPEC-006: Consolidate Duplicate Directories

**Status**: Ready
**Priority**: Medium
**Estimated Time**: 30 minutes
**Risk**: Medium
**Dependencies**: SPEC-005 (Remove Build Artifacts)

## Problem

Repository has duplicate directories serving similar purposes:

**Timeline Directories**:
- `timeline/` (13 items) - Current, cleaned up directory structure
- `timeline_data/` (31 items) - Legacy directory with old structure

**Research Server Directories**:
- `research-server/` (21 items) - Current, refactored structure
- `research_monitor/` (37 items) - Legacy directory with old code

This causes:
- Confusion about which directory is authoritative
- Risk of using outdated code
- Duplicated maintenance burden
- Larger repository size

## Goal

Remove legacy duplicate directories, keeping only current versions.

## Success Criteria

- [ ] Verified `timeline_data/` is truly obsolete
- [ ] Removed `timeline_data/` if obsolete
- [ ] Verified `research_monitor/` is truly obsolete
- [ ] Removed `research_monitor/` if obsolete
- [ ] All references updated to use current directories
- [ ] Tests still pass
- [ ] Server still works
- [ ] Documentation updated

## Investigation Steps

### Step 1: Compare timeline/ vs timeline_data/

```bash
cd /Users/markr/kleptocracy-timeline

# Check what's in timeline_data/
ls -la timeline_data/

# Check what's in timeline/
ls -la timeline/

# Compare event counts
find timeline_data/events -name "*.json" 2>/dev/null | wc -l
find timeline/data/events -name "*.json" 2>/dev/null | wc -l

# Check for unique files in timeline_data/
diff -rq timeline_data/ timeline/ 2>/dev/null | grep "Only in timeline_data"

# Check last modification dates
ls -lt timeline_data/ | head -5
ls -lt timeline/ | head -5
```

**Decision Points**:
- If `timeline_data/` has files not in `timeline/`, investigate why
- If `timeline_data/` is older and superseded, mark for removal
- If `timeline_data/` has unique data, migrate to `timeline/` first

### Step 2: Compare research-server/ vs research_monitor/

```bash
# Check what's in research_monitor/
ls -la research_monitor/

# Check what's in research-server/
ls -la research-server/

# Compare file counts
find research_monitor/ -name "*.py" | wc -l
find research-server/ -name "*.py" | wc -l

# Check for unique files
diff -rq research_monitor/ research-server/ 2>/dev/null | grep "Only in research_monitor"

# Check last modification dates
ls -lt research_monitor/ | head -5
ls -lt research-server/ | head -5
```

**Decision Points**:
- If `research_monitor/` has code not in `research-server/`, investigate
- If `research_monitor/` is legacy app_v1.py vs app_v2.py, mark for removal
- If `research_monitor/` has unique features, migrate to `research-server/` first

### Step 3: Check for Active References

```bash
# Check if anything imports from timeline_data/
grep -r "timeline_data" --include="*.py" --include="*.js" --include="*.md" \
  --exclude-dir="timeline_data" --exclude-dir="archive" | grep -v "^#"

# Check if anything imports from research_monitor/
grep -r "research_monitor" --include="*.py" --include="*.md" \
  --exclude-dir="research_monitor" --exclude-dir="archive" | grep -v "^#"
```

## Implementation Steps (Assuming Legacy Directories Are Obsolete)

### Step 1: Archive Legacy Directories

Before deletion, create archive:

```bash
# Create archive of legacy directories
tar -czf archive/legacy-directories-$(date +%Y%m%d).tar.gz \
  timeline_data/ research_monitor/

# Verify archive
tar -tzf archive/legacy-directories-$(date +%Y%m%d).tar.gz | head -20

# Archive should be created successfully
```

### Step 2: Remove timeline_data/

```bash
# Backup check: Verify timeline/ has all needed data
find timeline/data/events -name "*.json" | wc -l
# Should show 1,607 or similar

# Remove timeline_data/
rm -rf timeline_data/

# Verify removal
ls -la | grep timeline_data
# Should return nothing
```

### Step 3: Remove research_monitor/

```bash
# Backup check: Verify research-server/ has app_v2.py
ls -la research-server/server/app_v2.py
# Should exist

# Remove research_monitor/
rm -rf research_monitor/

# Verify removal
ls -la | grep research_monitor
# Should return nothing
```

### Step 4: Update Any Remaining References

```bash
# Check for any missed references
grep -r "timeline_data" --include="*.py" --include="*.md" \
  --exclude-dir="archive" | grep -v "^#" | head -20

grep -r "research_monitor" --include="*.py" --include="*.md" \
  --exclude-dir="archive" | grep -v "^#" | head -20

# Update any found references manually
```

### Step 5: Update Documentation

Update any documentation that references old directories:

```bash
# Check README files
grep -l "timeline_data\|research_monitor" *.md 2>/dev/null

# Update each file to use timeline/ and research-server/
```

## Validation Steps

### Test 1: Verify Directories Removed

```bash
# Check timeline_data removed
ls timeline_data 2>/dev/null
# Should show "No such file or directory"

# Check research_monitor removed
ls research_monitor 2>/dev/null
# Should show "No such file or directory"

# Check archive created
ls -lh archive/legacy-directories-*.tar.gz
# Should show archive file with reasonable size
```

### Test 2: Verify Current Directories Work

```bash
# Test timeline events exist
find timeline/data/events -name "*.json" | wc -l
# Should show 1,607+ events

# Test research server exists
ls research-server/server/app_v2.py
# Should exist

# Test research server structure
ls research-server/
# Should show: server/, client/, cli/, tests/, docs/
```

### Test 3: Run Tests

```bash
# Run research server tests
cd research-server
pytest tests/ -v

# Should pass all tests
```

### Test 4: Start Server

```bash
# Start research server
python3 research-server/cli/research_cli.py server-status

# Should show server status or offer to start
```

### Test 5: Check Viewer

```bash
# Test viewer exists and has dependencies
ls timeline/viewer/package.json
# Should exist

cd timeline/viewer
npm install
npm start
# Should start without errors
```

## Alternative: Investigate First (If Uncertain)

If uncertain about removing directories, investigate first:

### Investigation Script

Create `scripts/investigate_duplicates.py`:

```python
#!/usr/bin/env python3
"""
Compare duplicate directories to determine if they're truly obsolete.
"""
import os
from pathlib import Path
from datetime import datetime

def compare_directories(dir1, dir2):
    """Compare two directories and report differences."""
    print(f"\n{'='*60}")
    print(f"Comparing: {dir1} vs {dir2}")
    print(f"{'='*60}\n")

    d1 = Path(dir1)
    d2 = Path(dir2)

    if not d1.exists():
        print(f"❌ {dir1} does not exist")
        return

    if not d2.exists():
        print(f"❌ {dir2} does not exist")
        return

    # File counts
    files1 = list(d1.rglob("*"))
    files2 = list(d2.rglob("*"))

    print(f"📁 {dir1}: {len(files1)} files")
    print(f"📁 {dir2}: {len(files2)} files")

    # Modification times
    if files1:
        newest1 = max(f.stat().st_mtime for f in files1 if f.is_file())
        print(f"⏰ {dir1} last modified: {datetime.fromtimestamp(newest1)}")

    if files2:
        newest2 = max(f.stat().st_mtime for f in files2 if f.is_file())
        print(f"⏰ {dir2} last modified: {datetime.fromtimestamp(newest2)}")

    # Size
    size1 = sum(f.stat().st_size for f in files1 if f.is_file())
    size2 = sum(f.stat().st_size for f in files2 if f.is_file())

    print(f"💾 {dir1}: {size1 / 1024 / 1024:.1f} MB")
    print(f"💾 {dir2}: {size2 / 1024 / 1024:.1f} MB")

    return {
        "dir1": str(d1),
        "dir2": str(d2),
        "files1": len(files1),
        "files2": len(files2),
        "size1_mb": size1 / 1024 / 1024,
        "size2_mb": size2 / 1024 / 1024
    }

# Compare pairs
compare_directories("timeline_data", "timeline")
compare_directories("research_monitor", "research-server")
```

Run investigation:

```bash
python3 scripts/investigate_duplicates.py
```

## Rollback Plan

If removal causes issues:

```bash
# Extract from archive
tar -xzf archive/legacy-directories-$(date +%Y%m%d).tar.gz

# Or restore from git
git restore timeline_data/ research_monitor/

# Or restore from previous commit
git checkout HEAD~1 -- timeline_data/ research_monitor/
```

## Dependencies

- SPEC-005 completed (build artifacts removed for clearer comparison)
- Git working tree clean (to easily revert if needed)

## Risks & Mitigations

**Risk**: Removing directory with unique data
**Mitigation**: Archive before removal, investigate thoroughly first

**Risk**: Breaking active imports
**Mitigation**: Check for references before removal

**Risk**: Losing historical context
**Mitigation**: Monorepo preserved as pre-split history

## Notes

- Original monorepo will be preserved, so nothing is permanently lost
- Archives created as additional safety net
- Investigation step is optional but recommended if uncertain
- Can remove one directory at a time (timeline_data first, then research_monitor)

## Acceptance Criteria

- [x] Investigated both directory pairs
- [x] Determined which are obsolete
- [x] Created archives of legacy directories
- [x] Removed obsolete directories
- [x] Updated all references
- [x] Tests pass
- [x] Server works
- [x] Viewer works
- [x] Documentation updated

## Size Impact

Expected repository size reduction: 50-100MB (varies based on duplicate content)

## Output Files

**Created**:
- `archive/legacy-directories-YYYYMMDD.tar.gz` - Archive of removed directories

**Removed** (if obsolete):
- `timeline_data/` - Legacy timeline directory
- `research_monitor/` - Legacy research server directory

**Updated**:
- Any documentation referencing old directories
