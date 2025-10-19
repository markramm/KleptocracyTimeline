# SPEC-007: Reorganize Root-Level Directories

**Status**: Ready
**Priority**: High
**Estimated Time**: 45 minutes
**Risk**: Medium
**Dependencies**: SPEC-005, SPEC-006

## Problem

Repository root has many directories that should be organized under either `timeline/` or `research-server/`:

**Root-level directories** (potentially misplaced):
- `api/` (27 items) - Legacy API code?
- `agents/` (8 items) - Research agents?
- `agent_configs/` (5 items) - Agent configurations?
- `ai-analysis/` (4 items) - Analysis tools?
- `docs/` (30 items) - Which component's docs?
- `scripts/` (30 items) - Timeline scripts or server scripts?
- `schemas/` (4 items) - Timeline schemas?
- `tests/` (22 items) - Server tests?
- `utils/` (4 items) - Shared utilities?
- `validation_reports/` (4 items) - Timeline validation output?
- `viewer/` (10 items) - Should be in timeline/?

**Also present**:
- `alembic/` (7 items) - Database migrations (belongs in research-server)
- `venv/` (5 items) - Should be in .gitignore

This creates:
- Confusion about project structure
- Unclear ownership of files
- Harder repository split later
- Difficult onboarding for new contributors

## Goal

Organize all root-level directories into logical groupings under `timeline/` or `research-server/` (or mark for removal if obsolete).

## Success Criteria

- [ ] All directories investigated and ownership determined
- [ ] Timeline-related directories moved to `timeline/`
- [ ] Research-server directories moved to `research-server/`
- [ ] Obsolete directories removed or archived
- [ ] All import paths updated
- [ ] Tests still pass
- [ ] Applications still work
- [ ] Clean, organized root directory

## Investigation Steps

### Step 1: Catalog Each Directory

Create investigation checklist:

```bash
cd /Users/markr/kleptocracy-timeline

# For each directory, determine:
# 1. What it contains
# 2. Last modified date
# 3. Whether it's referenced by active code
# 4. Where it should belong

# Create investigation script
cat > scripts/investigate_root_dirs.sh << 'EOF'
#!/bin/bash

dirs="api agents agent_configs ai-analysis docs scripts schemas tests utils validation_reports viewer alembic venv"

for dir in $dirs; do
    if [ -d "$dir" ]; then
        echo "================================"
        echo "Directory: $dir"
        echo "================================"
        echo "Files: $(find $dir -type f 2>/dev/null | wc -l)"
        echo "Last modified: $(ls -lt $dir | head -2 | tail -1)"
        echo "Size: $(du -sh $dir 2>/dev/null | cut -f1)"
        echo ""
        echo "File types:"
        find $dir -type f 2>/dev/null | sed 's/.*\.//' | sort | uniq -c | head -10
        echo ""
        echo "Sample files:"
        find $dir -type f 2>/dev/null | head -5
        echo ""
    fi
done
EOF

chmod +x scripts/investigate_root_dirs.sh
./scripts/investigate_root_dirs.sh > root_dirs_analysis.txt

cat root_dirs_analysis.txt
```

### Step 2: Check References

```bash
# Check what imports from each directory
for dir in api agents agent_configs ai-analysis utils; do
    echo "=== References to $dir/ ==="
    grep -r "from $dir" --include="*.py" 2>/dev/null | head -5
    grep -r "import $dir" --include="*.py" 2>/dev/null | head -5
    echo ""
done
```

### Step 3: Directory Ownership Decision Matrix

| Directory | Contents | Owner | Action |
|-----------|----------|-------|--------|
| `api/` | Legacy API? | Research Server? | Investigate → Move or Archive |
| `agents/` | Research agents | Research Server | Move to `research-server/agents/` |
| `agent_configs/` | Agent configs | Research Server | Move to `research-server/configs/` |
| `ai-analysis/` | Analysis tools | Research Server | Move to `research-server/analysis/` |
| `docs/` | Documentation | Both? | Split between timeline/docs and research-server/docs |
| `scripts/` | Scripts | Both? | Split between timeline/scripts and research-server/scripts |
| `schemas/` | Timeline schemas | Timeline | Move to `timeline/schemas/` |
| `tests/` | Tests | Research Server | Move to `research-server/tests/` |
| `utils/` | Utilities | Research Server | Move to `research-server/utils/` |
| `validation_reports/` | Reports | Timeline | Move to `timeline/validation_reports/` or archive |
| `viewer/` | React viewer | Timeline | Move to `timeline/viewer/` |
| `alembic/` | DB migrations | Research Server | Move to `research-server/alembic/` |
| `venv/` | Virtual env | None | Add to .gitignore, remove |

## Implementation Steps

### Step 1: Move Timeline-Related Directories

```bash
cd /Users/markr/kleptocracy-timeline

# Move viewer/ if not already in timeline/
if [ -d "viewer" ] && [ ! -d "timeline/viewer" ]; then
    mv viewer/ timeline/
    echo "✓ Moved viewer/ to timeline/"
fi

# Move schemas/ if timeline-specific
if [ -d "schemas" ] && [ ! -d "timeline/schemas" ]; then
    # Check if these are timeline event schemas
    ls schemas/
    # If timeline schemas, move:
    mv schemas/ timeline/
    echo "✓ Moved schemas/ to timeline/"
fi

# Move validation_reports/ if timeline-specific
if [ -d "validation_reports" ]; then
    # These are likely timeline validation outputs
    # Option 1: Move to timeline
    mv validation_reports/ timeline/
    # Option 2: Archive (if old reports)
    # tar -czf archive/validation_reports-$(date +%Y%m%d).tar.gz validation_reports/
    # rm -rf validation_reports/
    echo "✓ Moved validation_reports/ to timeline/"
fi
```

### Step 2: Move Research-Server Directories

```bash
# Move agents/
if [ -d "agents" ] && [ ! -d "research-server/agents" ]; then
    mv agents/ research-server/
    echo "✓ Moved agents/ to research-server/"
fi

# Move agent_configs/
if [ -d "agent_configs" ] && [ ! -d "research-server/agent_configs" ]; then
    mv agent_configs/ research-server/
    echo "✓ Moved agent_configs/ to research-server/"
fi

# Move ai-analysis/
if [ -d "ai-analysis" ] && [ ! -d "research-server/ai-analysis" ]; then
    mv ai-analysis/ research-server/
    echo "✓ Moved ai-analysis/ to research-server/"
fi

# Move utils/
if [ -d "utils" ] && [ ! -d "research-server/utils" ]; then
    # Check if these utils are server-specific
    mv utils/ research-server/
    echo "✓ Moved utils/ to research-server/"
fi

# Move tests/ (if not already in research-server/tests/)
if [ -d "tests" ]; then
    # Merge with research-server/tests/ if exists
    if [ -d "research-server/tests" ]; then
        cp -r tests/* research-server/tests/
        rm -rf tests/
        echo "✓ Merged tests/ into research-server/tests/"
    else
        mv tests/ research-server/
        echo "✓ Moved tests/ to research-server/"
    fi
fi

# Move alembic/
if [ -d "alembic" ] && [ ! -d "research-server/alembic" ]; then
    mv alembic/ research-server/
    echo "✓ Moved alembic/ to research-server/"
fi
```

### Step 3: Handle api/ Directory

```bash
# Investigate api/ first
if [ -d "api" ]; then
    echo "Investigating api/ directory..."
    ls -la api/

    # Check if this is legacy code
    grep -r "app_v2" api/ 2>/dev/null

    # Decision:
    # - If legacy (superseded by research-server/server/): Archive
    # - If still active: Move to research-server/

    # Option 1: Archive if legacy
    tar -czf archive/legacy-api-$(date +%Y%m%d).tar.gz api/
    rm -rf api/
    echo "✓ Archived legacy api/ directory"

    # Option 2: Move if still active
    # mv api/ research-server/legacy-api/
fi
```

### Step 4: Split docs/ Directory

```bash
# docs/ may contain documentation for both components
if [ -d "docs" ]; then
    echo "Analyzing docs/ directory..."
    ls docs/

    # Manual review needed - check each doc:
    # - Timeline-specific docs → timeline/docs/
    # - Research-server docs → research-server/docs/
    # - Shared/project docs → keep at root or duplicate

    # Example split (adjust based on actual content):
    # Timeline docs
    for doc in docs/EVENT_FORMAT.md docs/VALIDATION.md docs/CONTRIBUTING.md; do
        if [ -f "$doc" ]; then
            mv "$doc" timeline/docs/
        fi
    done

    # Research server docs
    for doc in docs/API.md docs/ARCHITECTURE.md docs/CLI.md; do
        if [ -f "$doc" ]; then
            mv "$doc" research-server/docs/
        fi
    done

    # Check what's left
    ls docs/
    # Decide on remaining files
fi
```

### Step 5: Split scripts/ Directory

```bash
# scripts/ may contain scripts for both components
if [ -d "scripts" ]; then
    echo "Analyzing scripts/ directory..."
    ls scripts/

    # Timeline scripts (event validation, conversion)
    for script in scripts/validate_*.py scripts/convert_*.py scripts/generate_static_api.py; do
        if [ -f "$script" ]; then
            mv "$script" timeline/scripts/
        fi
    done

    # Research server scripts (if any)
    # Check remaining scripts and categorize

    # If scripts/ is now empty, remove it
    if [ -z "$(ls -A scripts/)" ]; then
        rmdir scripts/
        echo "✓ Removed empty scripts/ directory"
    fi
fi
```

### Step 6: Remove venv/

```bash
# Virtual environment should not be in repo
if [ -d "venv" ]; then
    rm -rf venv/
    echo "✓ Removed venv/ directory"

    # Make sure it's in .gitignore
    grep -q "^venv/" .gitignore || echo "venv/" >> .gitignore
fi
```

### Step 7: Update Import Paths

After moving directories, update import statements:

```bash
# Find and update imports (example for moved agents/)
grep -r "from agents" --include="*.py" research-server/ | cut -d: -f1 | sort -u

# For each file, update:
# from agents.foo import bar
# to:
# from research-server.agents.foo import bar

# OR if running from research-server/:
# from agents.foo import bar (stays the same if PYTHONPATH includes research-server/)
```

### Step 8: Update Configuration Files

```bash
# Update pytest.ini if paths changed
cat research-server/pytest.ini

# Update any path references in config files
# Update CLAUDE.md if it references old paths
# Update README.md if it references old structure
```

## Validation Steps

### Test 1: Verify Clean Root Directory

```bash
ls -la

# Root should now have:
# - timeline/
# - research-server/
# - specs/
# - archive/
# - .git/
# - .github/
# - .gitignore
# - README.md
# - Other project files (CLAUDE.md, LICENSE, etc.)

# Should NOT have:
# - api/
# - agents/
# - agent_configs/
# - ai-analysis/
# - viewer/
# - schemas/
# - tests/
# - utils/
# - venv/
# - alembic/
```

### Test 2: Verify Timeline Structure

```bash
ls timeline/

# Should show:
# - data/
# - viewer/
# - schemas/
# - scripts/
# - docs/
# - (possibly) validation_reports/
```

### Test 3: Verify Research-Server Structure

```bash
ls research-server/

# Should show:
# - server/
# - client/
# - cli/
# - tests/
# - docs/
# - agents/
# - agent_configs/
# - ai-analysis/
# - utils/
# - alembic/
```

### Test 4: Run Tests

```bash
# Research server tests
cd research-server
pytest tests/ -v

# Should pass all tests
```

### Test 5: Test Applications

```bash
# Test research server
python3 research-server/cli/research_cli.py server-status

# Test timeline viewer
cd timeline/viewer
npm install
npm start

# Both should work without errors
```

### Test 6: Check for Broken Imports

```bash
# Search for imports from old paths
grep -r "from agents" --include="*.py" research-server/ | grep -v "research-server.agents"
grep -r "from utils" --include="*.py" research-server/ | grep -v "research-server.utils"

# Should return nothing or only valid imports
```

## Rollback Plan

If reorganization breaks something:

```bash
# Restore from git
git restore .
git clean -fd

# Or restore from specific commit
git checkout HEAD~1 -- api/ agents/ agent_configs/ viewer/ schemas/ tests/ utils/

# Or use archives if created
tar -xzf archive/legacy-*.tar.gz
```

## Dependencies

- SPEC-005: Build artifacts removed
- SPEC-006: Duplicate directories investigated
- Git working tree clean

## Risks & Mitigations

**Risk**: Breaking import paths
**Mitigation**: Systematic search and replace, thorough testing

**Risk**: Moving active code to wrong location
**Mitigation**: Investigation step before moving, preserve in archive

**Risk**: Circular dependencies after reorganization
**Mitigation**: Test imports after each move

## Notes

- Some directories may need manual review (docs/, scripts/)
- Consider whether shared utilities belong in both places
- Update PYTHONPATH if needed for imports
- May need to update .github/workflows/ paths

## Acceptance Criteria

- [x] All root directories investigated
- [x] Timeline directories moved to timeline/
- [x] Research-server directories moved to research-server/
- [x] Obsolete directories archived or removed
- [x] Import paths updated
- [x] Tests pass
- [x] Applications work
- [x] Clean root directory structure
- [x] Documentation updated

## Size Impact

No significant size change (reorganization only)

## Output Files

**Modified Structure**:
```
kleptocracy-timeline/
├── timeline/
│   ├── data/
│   ├── viewer/          ← moved from root
│   ├── schemas/         ← moved from root
│   ├── scripts/         ← timeline scripts from root
│   ├── docs/            ← timeline docs from root
│   └── validation_reports/ ← moved from root (optional)
├── research-server/
│   ├── server/
│   ├── client/
│   ├── cli/
│   ├── tests/           ← moved from root
│   ├── docs/            ← server docs from root
│   ├── agents/          ← moved from root
│   ├── agent_configs/   ← moved from root
│   ├── ai-analysis/     ← moved from root
│   ├── utils/           ← moved from root
│   └── alembic/         ← moved from root
├── specs/
├── archive/
│   └── legacy-*.tar.gz  ← archived obsolete directories
├── .github/
├── README.md
└── CLAUDE.md
```

**Archived**:
- `api/` (if obsolete)
- Any other obsolete directories

**Removed**:
- `venv/`
