# SPEC-008: Fix Test Suite After Repository Reorganization

**Status**: Draft
**Created**: 2025-10-19
**Related**: SPEC-007 (Repository Reorganization)

## Overview

After completing SPEC-007 reorganization and markdown conversion, the test suite has 190/258 tests passing (73%). This spec addresses the remaining 66 test failures and 3 deprecated test files to restore full test coverage.

## Current State

### Test Results Summary
- **Total tests**: 258
- **Passing**: 190 (73%)
- **Failing**: 66 (26%)
- **Skipped**: 2 (1%)
- **Import errors**: 0 (fixed in initial cleanup)

### Categories of Failures

1. **Path-related failures** (25 tests)
   - Tests expecting `timeline_data/events` instead of `timeline/data/events`
   - Tests expecting JSON files when events are now markdown
   - Config tests checking for old directory structure

2. **Database/Fixture failures** (30 tests)
   - Integration tests missing database initialization
   - Tests using `:memory:` databases without proper setup
   - Missing FTS table creation in test fixtures

3. **Data expectations** (8 tests)
   - Tests expecting specific event counts (1857 vs 1581)
   - Tests expecting old ID formats with `enhanced_` prefix
   - Validation tests checking for JSON-specific issues

4. **Deprecated modules** (3 test files)
   - `test_research_api.py` - Testing removed ResearchAPI class
   - `test_research_cli.py` - Testing removed ResearchCLIWrapper class
   - `test_research_client.py` - Testing old TimelineResearchClient class

## Goals

1. **Fix all path-related test failures** - Update to new directory structure
2. **Fix database/fixture issues** - Proper test database initialization
3. **Update data expectations** - Match current event counts and formats
4. **Remove or update deprecated tests** - Archive old tests, create new ones if needed
5. **Achieve 95%+ test pass rate** - At least 245/258 tests passing

## Implementation Plan

### Phase 1: Fix Path-Related Issues (Priority: High)

#### 1.1 Update Config Tests
**File**: `research-server/tests/test_git_config.py`

**Changes**:
- Update `Config.TIMELINE_DIR` check from `timeline_data` to `timeline/data`
- Update `Config.EVENTS_DIR` check to `timeline/data/events`
- Update any hardcoded path references

**Expected fixes**: 3-5 tests

#### 1.2 Update Timeline Validation Tests
**File**: `research-server/tests/test_timeline_validation.py`

**Changes**:
- Update `EVENTS_DIR` constant from `timeline_data/events` to `timeline/data/events`
- Remove tests checking for JSON files specifically
- Add tests for markdown file validation
- Update event count expectations

**Expected fixes**: 5-8 tests

#### 1.3 Update Integration Test Paths
**Files**: `research-server/tests/integration/test_integration.py`

**Changes**:
- Update temporary directory structure to match new layout
- Fix fixture paths to use `timeline/data/events`
- Update any hardcoded path references in test data

**Expected fixes**: 3-5 tests

### Phase 2: Fix Database/Fixture Issues (Priority: High)

#### 2.1 Create Common Test Fixtures
**File**: `research-server/tests/conftest.py` (create new)

**Implementation**:
```python
"""
Shared pytest fixtures for all test modules.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def test_db():
    """Create in-memory test database with all tables."""
    from models import Base, init_database

    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    # Initialize FTS tables
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create FTS virtual table
    session.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS events_fts
        USING fts5(id, title, summary, content='timeline_events', content_rowid='rowid')
    """)

    session.commit()
    session.close()

    yield engine

    engine.dispose()


@pytest.fixture
def test_events_dir(tmp_path):
    """Create temporary events directory with structure."""
    events_dir = tmp_path / 'timeline' / 'data' / 'events'
    events_dir.mkdir(parents=True)

    yield events_dir

    # Cleanup handled by tmp_path


@pytest.fixture
def sample_event_markdown():
    """Sample markdown event for testing."""
    return """---
id: 2025-01-15--test-event
date: 2025-01-15
title: Test Event
importance: 8
tags:
  - test
  - sample
sources:
  - url: https://example.com/article
    title: Test Article
    publisher: Test Publisher
    date: 2025-01-15
    tier: 1
---

This is a test event summary for testing purposes.
"""


@pytest.fixture
def sample_event_json():
    """Sample JSON event for testing (legacy support)."""
    return {
        "id": "2025-01-15--test-event-json",
        "date": "2025-01-15",
        "title": "Test JSON Event",
        "summary": "Test event in JSON format",
        "importance": 7,
        "tags": ["test", "json"],
        "sources": [
            {
                "url": "https://example.com/test",
                "title": "Test Source",
                "publisher": "Test Pub",
                "date": "2025-01-15",
                "tier": 1
            }
        ]
    }
```

**Expected fixes**: Provides foundation for 20+ tests

#### 2.2 Update Integration Tests to Use Fixtures
**Files**:
- `research-server/tests/integration/test_integration.py`
- `research-server/tests/integration/test_app_v2.py`

**Changes**:
- Replace manual database setup with `test_db` fixture
- Replace manual directory creation with `test_events_dir` fixture
- Add proper FTS table initialization
- Ensure all tests clean up properly

**Expected fixes**: 15-20 tests

#### 2.3 Fix FilesystemSync Tests
**File**: `research-server/tests/test_filesystem_sync.py`

**Changes**:
- Use `test_db` fixture for database
- Use `test_events_dir` fixture for filesystem
- Add proper teardown to prevent test pollution
- Update to handle both JSON and markdown formats

**Expected fixes**: 3-5 tests

### Phase 3: Update Data Expectations (Priority: Medium)

#### 3.1 Fix Event Count Tests
**Files**: `research-server/tests/test_data_quality_validation.py`

**Changes**:
- Update expected event count from 1857 to 1581 (after deduplication)
- Remove checks for `enhanced_` prefix events (these are database artifacts)
- Update ID validation to accept current format
- Add test to verify no enhanced_ prefix events in filesystem

**Code changes**:
```python
def test_api_stats_structure(self):
    """Test API stats endpoint structure"""
    response = requests.get(f"{self.base_url}/api/stats")
    self.assertEqual(response.status_code, 200)
    data = response.json()['data']

    # Updated count after deduplication
    self.assertEqual(data['events']['total'], 1581)  # Changed from 1857
```

**Expected fixes**: 2-3 tests

#### 3.2 Fix ID Format Validation
**Files**: `research-server/tests/test_data_quality_validation.py`

**Changes**:
- Update ID validation regex to match `YYYY-MM-DD--slug` format
- Exclude database-only events with `enhanced_` prefix from validation
- Add separate test for database sync issues

**Expected fixes**: 1-2 tests

#### 3.3 Fix Markdown Parser Tests
**File**: `research-server/tests/test_markdown_parser.py`

**Changes**:
- Update test expecting ValueError for missing ID
- Parser now handles missing IDs gracefully (returns error in result)
- Change assertion from expecting exception to checking error in result

**Code changes**:
```python
def test_missing_id_raises_error(self):
    """Test that missing ID is caught during parsing"""
    content = """---
date: 2025-01-15
title: Test Event
---
Summary without ID
"""
    parser = MarkdownEventParser()
    result = parser.parse(content, Path("test.md"))

    # Parser returns error dict instead of raising
    assert not result['valid']
    assert 'Missing required field: id' in result.get('errors', [])
```

**Expected fixes**: 1 test

### Phase 4: Handle Deprecated Modules (Priority: Low)

#### 4.1 Archive Deprecated Test Files
**Action**: Move to `research-server/tests/deprecated/`

**Files to archive**:
- `test_research_api.py` - ResearchAPI class no longer exists
- `test_research_cli.py` - ResearchCLIWrapper no longer exists
- `test_research_client.py` - TimelineResearchClient moved to server/research_client.py with different name

**Implementation**:
```bash
mkdir -p research-server/tests/deprecated
mv research-server/tests/test_research_api.py research-server/tests/deprecated/
mv research-server/tests/test_research_cli.py research-server/tests/deprecated/
mv research-server/tests/test_research_client.py research-server/tests/deprecated/
```

Add `research-server/tests/deprecated/README.md`:
```markdown
# Deprecated Tests

Tests in this directory are for modules that have been refactored or removed.
They are kept for reference but not executed in the test suite.

## Files

- `test_research_api.py` - Old ResearchAPI interface (replaced by research_cli.py)
- `test_research_cli.py` - Old CLI wrapper (replaced by unified CLI in cli/research_cli.py)
- `test_research_client.py` - Old TimelineResearchClient (now ResearchMonitorClient)

## Migration Path

If these modules are needed again:
1. Update class names to match current implementation
2. Update import paths to new structure
3. Move back to tests/ directory
```

**Expected fixes**: Removes 3 import errors from test suite

#### 4.2 Create New CLI Tests (Optional)
**File**: `research-server/tests/test_cli_integration.py` (new)

**Purpose**: Test the current `research_cli.py` implementation

**Scope**:
- Test CLI argument parsing
- Test basic commands (get-stats, search-events, list-tags)
- Test error handling
- Integration tests with mock server

**Priority**: Low (existing CLI works well, comprehensive tests can wait)

### Phase 5: Remaining Edge Cases (Priority: Medium)

#### 5.1 Fix Git Service Tests
**File**: `research-server/tests/test_git_service.py`

**Issue**: Still importing from `research_monitor.services`

**Changes**:
- Verify all imports are from `services.git_service`
- May need to stub out some GitConfig dependencies
- Update any references to old paths

**Expected fixes**: 1-3 tests

#### 5.2 Fix PR Builder Tests
**File**: `research-server/tests/test_pr_builder.py`

**Issue**: Trying to access `research_monitor.services` module attribute

**Changes**:
- Verify imports are correct
- Check for dynamic imports that might be cached
- May need to add `services` package to sys.path differently

**Expected fixes**: 2-3 tests

#### 5.3 Fix Timeline Sync Tests
**File**: `research-server/tests/test_timeline_sync.py`

**Changes**:
- Update test expectations for new event format (markdown)
- Fix import test expecting file changes
- Update sync test to create markdown files instead of JSON

**Expected fixes**: 1-2 tests

## Testing Strategy

### Test Execution Order

1. **Phase 1** (Paths) - Run first, these are easiest to fix
   ```bash
   pytest research-server/tests/test_git_config.py -v
   pytest research-server/tests/test_timeline_validation.py -v
   ```

2. **Phase 2** (Fixtures) - Core infrastructure
   ```bash
   pytest research-server/tests/conftest.py -v
   pytest research-server/tests/integration/ -v
   ```

3. **Phase 3** (Data) - After fixtures are working
   ```bash
   pytest research-server/tests/test_data_quality_validation.py -v
   pytest research-server/tests/test_markdown_parser.py -v
   ```

4. **Phase 4** (Deprecation) - Quick cleanup
   ```bash
   # Just move files, no testing needed
   ```

5. **Phase 5** (Edge cases) - Final cleanup
   ```bash
   pytest research-server/tests/ -v --ignore=research-server/tests/deprecated/
   ```

### Success Criteria

After all phases:
- ✅ At least 245/255 tests passing (95%+) - 3 deprecated tests excluded
- ✅ All integration tests passing
- ✅ All parser tests passing
- ✅ No import errors
- ✅ Test suite runs in under 30 seconds
- ✅ Clear documentation for any remaining skipped tests

## Rollback Plan

If issues arise:
1. All changes are isolated to `research-server/tests/` directory
2. No production code changes required
3. Can revert individual test files independently
4. Original broken state documented in this spec

## Documentation Updates

After completion, update:

1. **`research-server/tests/README.md`** - Add test running instructions
2. **`CONTRIBUTING.md`** - Update testing section with new structure
3. **`CLAUDE.md`** - Add note about test fixture usage
4. **`.github/workflows/tests.yml`** (if exists) - Update CI configuration

## Estimated Effort

- **Phase 1** (Paths): 1-2 hours
- **Phase 2** (Fixtures): 2-3 hours
- **Phase 3** (Data): 1 hour
- **Phase 4** (Deprecation): 15 minutes
- **Phase 5** (Edge cases): 1-2 hours

**Total**: 5-8 hours of focused work

## Dependencies

- Python 3.13+
- pytest 8.4+
- SQLAlchemy (current version)
- All dependencies from `requirements.txt`

## Breaking Changes

None - all changes are in test code only.

## Future Improvements

After completing this spec:

1. **Add test coverage reporting** - Use pytest-cov to track coverage
2. **Add performance benchmarks** - Test database query performance
3. **Add integration with pre-commit** - Run critical tests before commit
4. **Create test data fixtures** - Reusable event data for all tests
5. **Add stress tests** - Test with 10,000+ events

## Related Issues

- Tests broken after SPEC-007 reorganization
- Event count discrepancy (1857 → 1581 after deduplication)
- Database sync lag showing `enhanced_` prefix events
- Markdown conversion completed but tests still expect JSON

## Approval

- [ ] Reviewed by: _______
- [ ] Approved by: _______
- [ ] Implementation started: _______
- [ ] Implementation completed: _______

---

**Next Steps**: Begin with Phase 1 (path fixes) as they are straightforward and will provide immediate improvement in pass rate.
