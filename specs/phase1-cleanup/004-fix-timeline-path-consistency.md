# SPEC-004: Fix Timeline Path Consistency

**Status**: Ready
**Priority**: Critical
**Estimated Time**: 20 minutes
**Risk**: Low
**Dependencies**: SPEC-003 (static site generator choice)

## Problem

Documentation and code reference inconsistent paths for timeline events:

- CLAUDE.md references: `timeline/data/events/`
- Hugo uses: `timeline/content/events/`
- Research server config: `../../timeline/data/events`
- Some scripts may use hardcoded paths

After Hugo removal (SPEC-003), need to ensure all references point to the canonical location.

## Goal

Establish single canonical path for timeline events and update all references.

## Success Criteria

- [ ] All documentation references same path
- [ ] All code references same path
- [ ] Research server config points to correct path
- [ ] No broken references
- [ ] Path validation in tests

## Canonical Path Decision

**Chosen Path**: `timeline/data/events/YYYY/`

**Rationale**:
- `data/` clearly indicates this is data (not generated content)
- Year subdirectories for organization
- Matches existing structure
- Clear separation from viewer code

## Implementation Steps

### Step 1: Audit All Path References

Find all files referencing timeline event paths:

```bash
cd /Users/markr/kleptocracy-timeline

# Search for event path references
grep -r "timeline.*events\|events.*timeline" \
  --include="*.md" \
  --include="*.py" \
  --include="*.js" \
  --include="*.jsx" \
  --include="*.ts" \
  --include="*.tsx" \
  --include="*.json" \
  --include="*.toml" \
  . > /tmp/event_path_references.txt

# Review findings
less /tmp/event_path_references.txt
```

### Step 2: Update CLAUDE.md

Update all path references in CLAUDE.md:

```bash
# Find current references
grep -n "timeline.*events\|TIMELINE_EVENTS_PATH" CLAUDE.md
```

**Update to**:
```markdown
# Before (various)
timeline_data/events/
timeline/events/
/events/

# After (consistent)
timeline/data/events/YYYY/
```

**Example section**:
```markdown
## Event Format

Events are stored in `timeline/data/events/YYYY/` as JSON files:

```
timeline/data/events/
├── 2024/
│   ├── 2024-01-15--event-slug.json
│   └── ...
├── 2023/
│   └── ...
```
```

### Step 3: Update Research Server Config

Update `research-server/server/config.py`:

```python
# Check current path
grep "TIMELINE_EVENTS_PATH\|events" research-server/server/config.py
```

**Update**:
```python
# Before
self.events_path = self._get_path('TIMELINE_EVENTS_PATH', '../../timeline_data/events')

# After
self.events_path = self._get_path('TIMELINE_EVENTS_PATH', '../../timeline/data/events')
```

### Step 4: Update .env.example

```bash
# Edit research-server/.env.example
```

**Update**:
```bash
# Before
TIMELINE_EVENTS_PATH=../../timeline_data/events

# After
TIMELINE_EVENTS_PATH=../../timeline/data/events
```

### Step 5: Update Documentation References

Update all README and documentation files:

**Files to Update**:
- `README.md` (root)
- `research-server/README.md`
- `timeline/README.md`
- `INSTALLATION.md`
- `ARCHITECTURE_REVIEW.md`

**Search and replace**:
```bash
# Find all .md files with old paths
grep -l "timeline_data/events\|timeline/events[^/]" *.md research-server/*.md timeline/*.md

# Update each file
# timeline_data/events → timeline/data/events/YYYY
```

### Step 6: Update Python Scripts

Update any Python scripts that reference event paths:

```bash
# Find Python files with event paths
grep -r "timeline.*events\|events.*path" \
  --include="*.py" \
  research-server/ timeline/scripts/
```

**Common files to check**:
- `timeline/scripts/validate_events.py`
- `timeline/scripts/generate_static_api.py`
- `research-server/server/app_v2.py`
- `research-server/cli/research_cli.py`

**Update pattern**:
```python
# Before
EVENT_DIR = Path("../timeline_data/events")
EVENT_DIR = Path("timeline/events")

# After
EVENT_DIR = Path("../timeline/data/events")
```

### Step 7: Update JavaScript/React References

Update viewer references:

```bash
cd timeline/viewer
grep -r "events.*path\|/events/\|data.*events" src/ --include="*.js" --include="*.jsx"
```

**Update if needed**:
```javascript
// Before
const EVENTS_PATH = '/timeline/events'

// After
const EVENTS_PATH = '/api/events'  // Use API instead of direct path
```

### Step 8: Create Path Constant

Create a single source of truth for the events path:

**In research-server/server/constants.py** (create if doesn't exist):
```python
"""
Global constants for the research server.
"""
from pathlib import Path

# Repository root (two levels up from server/)
REPO_ROOT = Path(__file__).parent.parent.parent

# Timeline events directory (canonical path)
TIMELINE_EVENTS_DIR = REPO_ROOT / "timeline" / "data" / "events"

# Validation
if not TIMELINE_EVENTS_DIR.exists():
    raise FileNotFoundError(
        f"Timeline events directory not found: {TIMELINE_EVENTS_DIR}\n"
        f"Expected structure: timeline/data/events/"
    )
```

**Use in config.py**:
```python
from constants import TIMELINE_EVENTS_DIR

class Config:
    def __init__(self):
        # Use constant instead of string path
        default_events_path = str(TIMELINE_EVENTS_DIR)
        self.events_path = self._get_path('TIMELINE_EVENTS_PATH', default_events_path)
```

### Step 9: Add Path Validation Tests

Create `research-server/tests/test_paths.py`:

```python
"""Test that all configured paths exist and are correct."""
import pytest
from pathlib import Path
from server.config import get_config
from server.constants import TIMELINE_EVENTS_DIR, REPO_ROOT

def test_timeline_events_directory_exists():
    """Ensure timeline events directory exists."""
    assert TIMELINE_EVENTS_DIR.exists(), f"Events dir not found: {TIMELINE_EVENTS_DIR}"
    assert TIMELINE_EVENTS_DIR.is_dir(), f"Events path is not a directory"

def test_timeline_events_has_year_directories():
    """Ensure events are organized by year."""
    year_dirs = list(TIMELINE_EVENTS_DIR.glob("[0-9][0-9][0-9][0-9]"))
    assert len(year_dirs) > 0, "No year directories found in events/"

def test_config_events_path_is_correct():
    """Ensure config points to correct events path."""
    config = get_config()
    events_path = Path(config.events_path)

    assert events_path.exists(), f"Config events path doesn't exist: {events_path}"
    assert events_path == TIMELINE_EVENTS_DIR or events_path.resolve() == TIMELINE_EVENTS_DIR.resolve()

def test_no_events_in_root():
    """Ensure no loose event files in events root."""
    loose_events = list(TIMELINE_EVENTS_DIR.glob("*.json"))
    assert len(loose_events) == 0, f"Found {len(loose_events)} loose events in root (should be in year dirs)"

def test_repo_structure():
    """Validate expected repository structure."""
    assert (REPO_ROOT / "timeline").exists()
    assert (REPO_ROOT / "timeline" / "data").exists()
    assert (REPO_ROOT / "timeline" / "data" / "events").exists()
    assert (REPO_ROOT / "research-server").exists()
```

### Step 10: Update Architecture Documentation

Update `ARCHITECTURE_REVIEW.md`:

```markdown
## Timeline Data Path

**Canonical Location**: `timeline/data/events/YYYY/`

All timeline events are stored as JSON files organized by year:

```
timeline/data/events/
├── 2024/
│   ├── 2024-01-15--event-slug.json
│   ├── 2024-02-20--another-event.json
│   └── ...
├── 2023/
│   └── ...
└── 1970/
    └── ...
```

**Configuration**:
- Environment variable: `TIMELINE_EVENTS_PATH`
- Default: `../../timeline/data/events`
- Constant: `server.constants.TIMELINE_EVENTS_DIR`
```

## Validation Steps

### Test 1: No Old Path References

```bash
# Should return 0 results
grep -r "timeline_data/events" --include="*.md" --include="*.py" .
grep -r "timeline/events[^/]" --include="*.md" --include="*.py" . | grep -v "data/events"
```

### Test 2: Config Points to Correct Path

```bash
cd research-server
python3 -c "from server.config import get_config; print(get_config().events_path)"
# Should print: ../../timeline/data/events
```

### Test 3: Path Validation Tests Pass

```bash
cd research-server
python3 -m pytest tests/test_paths.py -v
```

### Test 4: Server Starts Successfully

```bash
./research server-start
./research get-stats
# Should not show path errors
```

### Test 5: Documentation Consistency

```bash
# Count occurrences of canonical path
grep -r "timeline/data/events" --include="*.md" . | wc -l
# Should be > 5 (multiple docs reference it)

# Should have 0 old-style references
grep -r "timeline_data/events" --include="*.md" . | wc -l
```

## Files Modified

**Documentation**:
- `CLAUDE.md`
- `README.md`
- `INSTALLATION.md`
- `ARCHITECTURE_REVIEW.md`
- `research-server/README.md`
- `timeline/README.md`

**Configuration**:
- `research-server/server/config.py`
- `research-server/.env.example`

**Code** (if needed):
- `timeline/scripts/*.py`
- `research-server/server/constants.py` (new)
- `research-server/tests/test_paths.py` (new)

## Rollback Plan

```bash
# Revert changes
git checkout CLAUDE.md README.md INSTALLATION.md
git checkout research-server/server/config.py
git checkout research-server/.env.example
```

## Dependencies

- SPEC-003 complete (Hugo removed, paths finalized)

## Notes

- After repository split, this path will be relative to each repo
- Timeline repo: `data/events/YYYY/`
- Research server repo: will need to clone timeline repo or use API

## Future Considerations

After repository split:
- Research server may access timeline data via:
  - Git submodule
  - API endpoint
  - Local clone path (configurable)

Document this in split specification.

## Acceptance Criteria

- [x] All documentation uses `timeline/data/events/YYYY/`
- [x] Config file updated with correct default path
- [x] .env.example updated
- [x] Constants file created with canonical path
- [x] Path validation tests added and passing
- [x] No references to old paths (`timeline_data`, `timeline/events` without `/data`)
- [x] Server starts and operates correctly
