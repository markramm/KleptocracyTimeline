# SPEC-001: Move Test Files to Correct Location

**Status**: Ready
**Priority**: Critical
**Estimated Time**: 15 minutes
**Risk**: Low

## Problem

Test files are located in `research-server/server/` alongside production code:
- `test_app_v2.py`
- `test_e2e.py`
- `test_integration.py`
- `test_final_validation.py`

This violates Python project structure best practices and makes it unclear which files are production code vs tests.

## Goal

Move all test files to the proper `research-server/tests/` directory, organized by test type.

## Success Criteria

- [ ] All `test_*.py` files removed from `research-server/server/`
- [ ] All tests moved to appropriate subdirectories in `research-server/tests/`
- [ ] All tests still pass after move
- [ ] Import statements updated if needed
- [ ] No duplicate test files

## Current State

```
research-server/
├── server/
│   ├── app_v2.py                 # Production code
│   ├── test_app_v2.py            # ❌ Wrong location
│   ├── test_e2e.py               # ❌ Wrong location
│   ├── test_integration.py       # ❌ Wrong location
│   └── test_final_validation.py  # ❌ Wrong location
└── tests/
    ├── test_filesystem_sync.py   # ✅ Correct location
    ├── test_markdown_parser.py   # ✅ Correct location
    └── ...
```

## Target State

```
research-server/
├── server/
│   ├── app_v2.py                 # Production code only
│   ├── routes/
│   ├── services/
│   └── ...
└── tests/
    ├── unit/
    │   └── ...
    ├── integration/
    │   ├── test_app_v2.py        # ✅ Moved here
    │   ├── test_integration.py   # ✅ Moved here
    │   └── test_final_validation.py  # ✅ Moved here
    ├── e2e/
    │   └── test_e2e.py           # ✅ Moved here
    └── ...
```

## Implementation Steps

### Step 1: Create Test Subdirectories

```bash
cd research-server/tests
mkdir -p integration
mkdir -p e2e
```

**Validation**: Directories exist
```bash
ls -la research-server/tests/integration
ls -la research-server/tests/e2e
```

### Step 2: Move Integration Tests

```bash
mv research-server/server/test_app_v2.py research-server/tests/integration/
mv research-server/server/test_integration.py research-server/tests/integration/
mv research-server/server/test_final_validation.py research-server/tests/integration/
```

**Validation**: Files moved
```bash
ls research-server/server/test_*.py  # Should return "No such file"
ls research-server/tests/integration/test_*.py  # Should show 3 files
```

### Step 3: Move E2E Tests

```bash
mv research-server/server/test_e2e.py research-server/tests/e2e/
```

**Validation**: File moved
```bash
ls research-server/tests/e2e/test_e2e.py
```

### Step 4: Update Import Paths (if needed)

Check if tests have relative imports that need updating:

```bash
grep -r "from \.\." research-server/tests/integration/ research-server/tests/e2e/
```

If imports use relative paths like `from ..app_v2 import`, update them to:
```python
# Before
from ..app_v2 import create_app

# After
from server.app_v2 import create_app
```

Or add `sys.path` manipulation:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'server'))
```

### Step 5: Run Tests

```bash
cd research-server
python3 -m pytest tests/ -v
```

**Expected Result**: All tests should pass

### Step 6: Verify No Test Files Remain

```bash
find research-server/server -name "test_*.py" -o -name "*_test.py"
```

**Expected Result**: No output (no test files found)

## Rollback Plan

If tests fail after moving:

```bash
# Restore from git
git checkout research-server/server/test_*.py
git clean -fd research-server/tests/integration/
git clean -fd research-server/tests/e2e/
```

## Testing

1. **Test Discovery**: `pytest --collect-only` should find all tests
2. **Test Execution**: `pytest tests/` should run all tests successfully
3. **Coverage**: `pytest --cov=server tests/` should show coverage

## Dependencies

- None (standalone task)

## Notes

- Keep `conftest.py` in `tests/` root for shared fixtures
- Consider adding `__init__.py` to test directories for better imports
- Update CI/CD configuration if it references specific test paths

## Acceptance Criteria

- [x] All test files moved from `server/` to `tests/`
- [x] Tests organized by type (integration, e2e)
- [x] All tests pass
- [x] No test files remain in production code directories
- [x] pytest discovery works correctly
