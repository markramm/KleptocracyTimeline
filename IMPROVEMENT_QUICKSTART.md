# Improvement Plan - Quick Start Guide

**Quick reference for implementing the comprehensive improvement plan**

---

## Getting Started (5 minutes)

### 1. Install Required Tools

```bash
# Activate virtual environment
source venv/bin/activate

# Install development dependencies
pip install pytest-cov mypy pylint python-dotenv coverage radon bandit black pre-commit

# Verify installations
pytest --version
mypy --version
pylint --version
coverage --version
```

### 2. Run Baseline Assessment

```bash
# Generate test coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Open coverage report in browser
open htmlcov/index.html  # macOS
# xdg-open htmlcov/index.html  # Linux

# Run type checker (expect errors)
mypy research_cli.py research_client.py research_api.py

# Run linter (expect warnings)
pylint research_cli.py research_client.py research_api.py --score=yes
```

### 3. Document Baseline Metrics

```bash
# Create metrics tracking file
cat > METRICS.md << 'EOF'
# Code Quality Metrics Tracking

**Baseline Date**: $(date +%Y-%m-%d)

## Current Metrics

- **Tests Passing**: $(pytest --quiet --tb=no | tail -1)
- **Test Coverage**: [Run pytest --cov]
- **Type Hints**: ~30% (estimated)
- **MyPy Errors**: [Run mypy and count]
- **Pylint Score**: [Run pylint --score=yes]

## Target Metrics

- Tests Passing: 110+/117 (94%+)
- Test Coverage: ≥80%
- Type Hints: ≥80%
- MyPy Errors: 0
- Pylint Score: ≥9.0/10
EOF
```

---

## Phase 1: Foundation (Week 1-2)

### Quick Wins (Start Here)

#### Fix Test Failures (Day 1-2)

```bash
# Run tests to see current failures
pytest -v --tb=short

# Expected failures:
# - 19 tests: Event status validation issues
# - Most are due to overly strict status validation

# Fix approach:
# 1. Update research_monitor/event_validator.py
#    Add more valid status values: 'validated', 'reported', 'investigated', etc.
# 2. Run tests again to verify fixes
# 3. Commit fixes
```

**File to edit**: `research_monitor/event_validator.py`

```python
# Line ~14 - Update VALID_STATUSES
VALID_STATUSES = [
    # Core statuses
    'confirmed', 'alleged', 'developing', 'speculative',
    # Extended statuses (from actual timeline events)
    'validated', 'reported', 'investigated', 'disputed',
    'contested', 'predicted', 'verified', 'enhanced',
    'needs_work', 'unverified'
]
```

#### Set Up Configuration Files (Day 1)

**Create `mypy.ini`**:
```bash
cat > mypy.ini << 'EOF'
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False
ignore_missing_imports = True

[mypy-tests.*]
ignore_errors = True
EOF
```

**Create `.pylintrc`**:
```bash
cat > .pylintrc << 'EOF'
[MASTER]
init-hook='import sys; sys.path.append(".")'

[MESSAGES CONTROL]
disable=C0111,C0103,R0913

[FORMAT]
max-line-length=120

[DESIGN]
max-args=8
max-locals=20
EOF
```

#### Generate Coverage Report (Day 2)

```bash
# Run comprehensive coverage analysis
pytest --cov=. --cov-report=html --cov-report=term-missing \
       --cov-report=json -v

# View detailed coverage report
open htmlcov/index.html

# Identify files with <50% coverage (priority targets)
coverage report | awk '$4 < 50 {print $1, $4}'
```

---

## Phase 2: Architecture Refactoring (Week 2-4)

### Split app_v2.py Strategy

#### Step 1: Create Directory Structure (Day 1)

```bash
# Create new directory structure
mkdir -p research_monitor/routes
mkdir -p research_monitor/services
mkdir -p research_monitor/core
mkdir -p research_monitor/utils

# Create __init__.py files
touch research_monitor/routes/__init__.py
touch research_monitor/services/__init__.py
touch research_monitor/core/__init__.py
touch research_monitor/utils/__init__.py
```

#### Step 2: Extract Configuration (Day 2)

```bash
# Create core/config.py
cat > research_monitor/core/config.py << 'EOF'
"""Application configuration"""
import os
from pathlib import Path

class Config:
    """Configuration settings"""
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    TIMELINE_DIR = BASE_DIR / 'timeline_data' / 'events'
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///unified_research.db')

    # Server
    API_KEY = os.environ.get('RESEARCH_MONITOR_API_KEY', None)
    PORT = int(os.environ.get('RESEARCH_MONITOR_PORT', 5558))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Sync settings
    SYNC_INTERVAL = 30  # seconds
    COMMIT_THRESHOLD = 10  # events
EOF
```

#### Step 3: Extract First Route Blueprint (Day 3-4)

```bash
# Create routes/events.py
# Move all event-related routes from app_v2.py
# Start with GET /api/events endpoint

# Test after each extraction:
pytest tests/test_api_integration.py::TestEventEndpoints -v
```

#### Step 4: Continue Incrementally (Day 5-10)

- Extract priorities routes
- Extract validation routes
- Extract QA routes
- Extract services
- Update main app.py
- Run full test suite after each extraction

**Critical**: Run tests after each change!

```bash
# After each file extraction
pytest -v
# If tests fail, fix immediately before proceeding
```

---

## Phase 3: Type Safety (Week 3-5)

### Adding Type Hints - File Priority Order

#### High Priority Files (Start Here)

**1. research_client.py** (Most used, highest impact)
```bash
# Add type hints to all methods
# Start with public API methods
# Then private helper methods

# Example pattern:
def search(self, query: str = '', **filters: Any) -> Dict[str, Any]:
    """Search timeline events"""
    ...

# Run mypy after each function
mypy research_client.py --no-error-summary | head -20
```

**2. research_api.py**
```bash
# Similar approach - public methods first
# Check after each addition:
mypy research_api.py
```

**3. research_monitor/models.py**
```bash
# SQLAlchemy models - easier to type
# Focus on method signatures and return types
```

### MyPy Incremental Approach

```bash
# Start with one file
mypy research_client.py

# Fix errors one by one
# Common patterns:

# Pattern 1: Missing return type
# Before: def get_stats(self):
# After:  def get_stats(self) -> Dict[str, Any]:

# Pattern 2: Missing argument types
# Before: def update(self, id, data):
# After:  def update(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:

# Pattern 3: Use Any for complex types initially
from typing import Any, Dict, List, Optional

# Gradually replace Any with specific types
```

---

## Phase 4: Testing & Production (Week 4-6)

### Increase Test Coverage

#### Find Uncovered Code

```bash
# Generate coverage with missing lines
coverage run -m pytest
coverage report --show-missing

# Focus on files with <80% coverage
coverage report | awk '$4 < 80 && $1 !~ /test/ {print}'
```

#### Write Tests for Uncovered Functions

```python
# Pattern: tests/test_<module_name>.py

# Example for services/event_sync.py
# tests/test_event_sync_service.py

import pytest
from research_monitor.services.event_sync import EventSyncService

@pytest.fixture
def event_sync_service(mock_db, mock_filesystem):
    return EventSyncService(mock_db, mock_filesystem)

def test_sync_creates_new_events(event_sync_service):
    # Given: New event file on filesystem
    # When: Sync runs
    # Then: Event created in database
    ...

def test_sync_updates_existing_events(event_sync_service):
    # Given: Modified event file
    # When: Sync runs
    # Then: Event updated in database
    ...
```

### Remove Hardcoded Credentials

```bash
# 1. Create .env.example
cat > .env.example << 'EOF'
RESEARCH_MONITOR_API_KEY=your-api-key-here
RESEARCH_MONITOR_PORT=5558
DATABASE_URL=sqlite:///unified_research.db
DEBUG=false
EOF

# 2. Update code to require env vars
# research_monitor/core/config.py
API_KEY = os.environ.get('RESEARCH_MONITOR_API_KEY')
if not API_KEY and not DEBUG:
    raise ValueError("RESEARCH_MONITOR_API_KEY required in production")

# 3. Update documentation
echo "## Environment Setup\n\nCopy .env.example to .env and configure:\n\`\`\`bash\ncp .env.example .env\n\`\`\`" >> README.md
```

---

## Progress Tracking

### Daily Checklist

**Before starting work**:
- [ ] Review improvement plan
- [ ] Pick next task from current phase
- [ ] Run tests to ensure baseline

**After completing task**:
- [ ] Run full test suite
- [ ] Update metrics tracking
- [ ] Commit changes with descriptive message
- [ ] Update IMPROVEMENT_PLAN.md progress

### Weekly Review

```bash
# Generate progress report
cat > weekly_progress.md << EOF
# Week [N] Progress Report

## Completed Tasks
- [List completed tasks]

## Metrics Update
- Tests passing: [X/117]
- Coverage: [X%]
- Type hints: [X%]
- MyPy errors: [X]
- Pylint score: [X/10]

## Blockers
- [Any issues encountered]

## Next Week Plan
- [Top 3 priorities]
EOF
```

---

## Useful Commands Reference

### Testing
```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_research_client.py -v

# Run specific test function
pytest tests/test_research_client.py::test_search -v

# Run failed tests only
pytest --lf

# Stop on first failure
pytest -x
```

### Type Checking
```bash
# Check single file
mypy research_client.py

# Check all tracked files
mypy .

# Ignore missing imports
mypy --ignore-missing-imports research_client.py

# Show error codes
mypy --show-error-codes research_client.py
```

### Linting
```bash
# Check file
pylint research_client.py

# Check with score
pylint research_client.py --score=yes

# Check only errors (ignore warnings)
pylint research_client.py --errors-only

# Disable specific check
pylint research_client.py --disable=C0111
```

### Coverage
```bash
# Run coverage
coverage run -m pytest

# Generate HTML report
coverage html

# Show report in terminal
coverage report

# Show missing lines
coverage report --show-missing

# Focus on specific files
coverage report --include="research_monitor/*"
```

---

## Emergency Rollback

If something breaks:

```bash
# Check what changed
git status
git diff

# Rollback uncommitted changes
git restore <file>

# Rollback last commit (keep changes)
git reset HEAD~1

# Rollback last commit (discard changes)
git reset --hard HEAD~1

# Return to specific commit
git log --oneline  # find commit hash
git reset --hard <commit-hash>
```

---

## Success Validation

### Phase 1 Complete When:
```bash
# All tests pass
pytest --quiet && echo "✅ Phase 1 Complete"

# Coverage report generated
[ -f htmlcov/index.html ] && echo "✅ Coverage report exists"

# Configs in place
[ -f mypy.ini ] && [ -f .pylintrc ] && echo "✅ Configs ready"
```

### Phase 2 Complete When:
```bash
# app_v2.py is small
lines=$(wc -l research_monitor/app_v2.py | awk '{print $1}')
[ $lines -lt 1000 ] && echo "✅ app_v2.py split complete" || echo "⚠️ Still $lines lines"

# All tests still pass
pytest --quiet && echo "✅ No regression"
```

### Phase 3 Complete When:
```bash
# MyPy passes
mypy . && echo "✅ Type checking clean"

# Pylint score high
score=$(pylint research_*.py 2>&1 | grep "rated at" | awk '{print $7}')
echo "Pylint score: $score"
```

### Phase 4 Complete When:
```bash
# High coverage
coverage run -m pytest --quiet
coverage report | tail -1 | awk '{print "Coverage: " $4}'

# No hardcoded keys
! grep -r "test-key" *.py && echo "✅ No hardcoded credentials"

# .env.example exists
[ -f .env.example ] && echo "✅ Environment template ready"
```

---

## Getting Help

**Resources**:
- Full plan: `IMPROVEMENT_PLAN.md`
- Project docs: `CLAUDE.md`
- Testing docs: `TEST_DOCUMENTATION.md`

**Common Issues**:
1. **Tests failing after refactor** → Run `pytest -vv -s` for details
2. **MyPy type errors** → Start with `--ignore-missing-imports`
3. **Import errors** → Check `__init__.py` files exist
4. **Coverage too low** → Use `coverage report --show-missing`

---

Ready to start? Begin with **Phase 1: Foundation** → Fix test failures first!
