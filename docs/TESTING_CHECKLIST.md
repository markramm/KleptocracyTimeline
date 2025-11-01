# Comprehensive Testing Checklist

**Created**: 2025-10-17
**Purpose**: Verify all systems after repository organization

---

## 1. Core Functionality Tests

### Research Server
- [ ] Server starts without errors
- [ ] Health check endpoint responds
- [ ] Events are synced from filesystem
- [ ] Both JSON and Markdown events are indexed
- [ ] Search works for both formats
- [ ] Event creation works
- [ ] Validation queue accessible

### Research CLI
- [ ] `python3 research_cli.py --help` works
- [ ] Search events command works
- [ ] Get stats command works
- [ ] Get next priority works
- [ ] Create event works
- [ ] Validation commands work

### Timeline Viewer
- [ ] `npm install` succeeds
- [ ] `npm start` launches dev server
- [ ] `npm run build` creates production build
- [ ] Build output is valid
- [ ] No console errors

---

## 2. Multi-Format Event Tests

### JSON Events
- [ ] Existing JSON events still parse
- [ ] JSON events searchable
- [ ] JSON events validate
- [ ] Can create new JSON events

### Markdown Events
- [ ] All 10 markdown events parse correctly
- [ ] Markdown events searchable
- [ ] Markdown events validate
- [ ] Can create new markdown events
- [ ] Markdown formatting preserved

### Format Parity
- [ ] Same event in both formats produces identical results
- [ ] Both formats pass validation
- [ ] Both formats appear in search results
- [ ] Both formats work in static API

---

## 3. Parser Tests

### Unit Tests
- [ ] `pytest research-server/tests/test_markdown_parser.py` passes
- [ ] `pytest research-server/tests/test_parser_factory.py` passes
- [ ] `pytest research-server/tests/test_research_client.py` passes
- [ ] All 218 tests pass
- [ ] Test coverage ≥ 80%

### Integration Tests
- [ ] Parser factory detects file formats correctly
- [ ] Mixed directory (JSON + Markdown) parses
- [ ] README.md files are excluded
- [ ] Invalid events are rejected

---

## 4. File System Tests

### Path Configuration
- [ ] Server uses `timeline/data/events/` (not `timeline_data/`)
- [ ] Validation logs write to `timeline/data/validation_logs/`
- [ ] Research priorities read from `research_priorities/`
- [ ] Database at repository root

### File Operations
- [ ] Event creation writes to correct directory
- [ ] Event updates modify correct files
- [ ] Filesystem sync detects new files
- [ ] Filesystem sync detects modified files

---

## 5. Database Tests

### Database Integrity
- [ ] Database opens without errors
- [ ] All tables exist
- [ ] Indexes are functional
- [ ] Full-text search works

### Data Sync
- [ ] Events table matches filesystem
- [ ] Event count matches (1,590 events)
- [ ] Markdown events in database
- [ ] JSON events in database

---

## 6. API Tests

### REST API Endpoints
- [ ] `GET /api/server/health` - Returns 200
- [ ] `GET /api/events/search?q=test` - Returns results
- [ ] `GET /api/events/{id}` - Returns event
- [ ] `POST /api/events` - Creates event
- [ ] `GET /api/priorities` - Returns priorities
- [ ] `GET /api/stats` - Returns statistics (currently failing - known issue)

### Static API Files
- [ ] `timeline/public/api/timeline.json` exists
- [ ] `timeline/public/api/actors.json` exists
- [ ] `timeline/public/api/tags.json` exists
- [ ] `timeline/public/api/stats.json` exists
- [ ] Files are valid JSON
- [ ] Files contain all events (JSON + Markdown)

---

## 7. Validation Tests

### Event Validation
- [ ] `validate_events.py` runs without errors
- [ ] Validates JSON format
- [ ] Validates Markdown format
- [ ] Detects missing required fields
- [ ] Detects invalid date formats
- [ ] Detects filename/ID mismatches

### Pre-commit Hooks
- [ ] Pre-commit hook detects JSON files
- [ ] Pre-commit hook detects Markdown files
- [ ] Pre-commit hook validates both formats
- [ ] Pre-commit hook blocks invalid events
- [ ] Pre-commit hook allows valid events

---

## 8. Search Tests

### Full-Text Search
- [ ] Search by title works
- [ ] Search by summary works
- [ ] Search by actor works
- [ ] Search by tag works
- [ ] Search finds JSON events
- [ ] Search finds Markdown events
- [ ] Case-insensitive search works

### Search Quality
- [ ] Relevant results ranked highly
- [ ] No duplicate results
- [ ] Results from both formats
- [ ] Search performance acceptable (< 1 second)

---

## 9. Documentation Tests

### Documentation Availability
- [ ] `README.md` exists and is current
- [ ] `CONTRIBUTING.md` has markdown format guide
- [ ] `CLAUDE.md` has complete instructions
- [ ] `docs/PROJECT_STRUCTURE.md` exists
- [ ] `docs/DEPLOYMENT_GUIDE.md` exists
- [ ] `docs/DEVELOPMENT_SETUP.md` exists
- [ ] `timeline/docs/EVENT_FORMAT.md` exists

### Documentation Accuracy
- [ ] All file paths in docs are correct
- [ ] All commands in docs work
- [ ] Code examples run without errors
- [ ] Links to other docs work

---

## 10. Import and Dependency Tests

### Python Imports
- [ ] `from research_client import TimelineResearchClient` works
- [ ] `from research_api import *` works
- [ ] All research-server modules import
- [ ] No circular dependencies

### Dependencies
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `pip install -r requirements-test.txt` succeeds
- [ ] `pip install -r research-server/requirements.txt` succeeds
- [ ] All required packages installed
- [ ] No conflicting package versions

---

## 11. Workflow Tests

### Event Creation Workflow
1. [ ] Search for duplicates
2. [ ] Create event (JSON or Markdown)
3. [ ] Validate event
4. [ ] Event appears in search
5. [ ] Event in database
6. [ ] Event in filesystem

### QA Workflow
1. [ ] Get QA queue
2. [ ] Get next event for QA
3. [ ] Enhance event
4. [ ] Validate event
5. [ ] Mark as validated
6. [ ] Verify in database

### Research Workflow
1. [ ] Get next priority
2. [ ] Search for related events
3. [ ] Create new events
4. [ ] Update priority status
5. [ ] Complete priority

---

## 12. Performance Tests

### Response Times
- [ ] Server startup < 5 seconds
- [ ] Search query < 1 second
- [ ] Event creation < 500ms
- [ ] Static API generation < 30 seconds

### Load Tests
- [ ] 100 concurrent searches
- [ ] 1000 events parsed
- [ ] Database with 10,000 events
- [ ] Filesystem sync with 5,000 files

---

## 13. Edge Case Tests

### Invalid Input
- [ ] Malformed JSON rejected
- [ ] Malformed Markdown rejected
- [ ] Missing required fields rejected
- [ ] Invalid date format rejected
- [ ] Invalid ID format rejected

### Special Characters
- [ ] Unicode in event titles
- [ ] Special characters in summaries
- [ ] URLs with query parameters
- [ ] Markdown formatting preserved

### Boundary Conditions
- [ ] Empty search query
- [ ] Very long event summaries
- [ ] Events with 100+ sources
- [ ] Events with no tags

---

## 14. Security Tests

### Input Validation
- [ ] SQL injection prevention
- [ ] XSS prevention in event data
- [ ] Path traversal prevention
- [ ] Command injection prevention

### Access Control
- [ ] Unauthorized requests blocked (if auth enabled)
- [ ] API key validation (if configured)
- [ ] Rate limiting (if configured)

---

## 15. Regression Tests

### After Cleanup
- [ ] All previously working features still work
- [ ] No broken imports
- [ ] No missing files
- [ ] All paths updated correctly
- [ ] Markdown events still accessible

### Backward Compatibility
- [ ] Existing JSON events unchanged
- [ ] Old CLI commands still work
- [ ] API responses unchanged
- [ ] Database schema compatible

---

## Quick Test Commands

### Run All Tests
```bash
# Python tests
python3 -m pytest research-server/tests/ -v

# Event validation
python3 timeline/scripts/validate_events.py

# Server health
curl http://localhost:5558/api/server/health | python3 -m json.tool

# Search test
python3 research_cli.py search-events --query "MKUltra"
```

### Test Markdown Events
```bash
# Search for all 10 markdown events
python3 research_cli.py search-events --query "MKUltra"
python3 research_cli.py search-events --query "Powell Memo"
python3 research_cli.py search-events --query "Heritage Foundation"
python3 research_cli.py search-events --query "ALEC"
python3 research_cli.py search-events --query "Church Committee"
python3 research_cli.py search-events --query "Buckley v Valeo"
python3 research_cli.py search-events --query "Gramm-Leach-Bliley"
python3 research_cli.py search-events --query "Katherine Harris"
python3 research_cli.py search-events --query "WHIG"
python3 research_cli.py search-events --query "Citizens United"
```

### Test Static API
```bash
cd timeline/scripts
python3 generate.py
ls -lh ../public/api/
python3 -m json.tool ../public/api/timeline.json | head -50
```

### Test Timeline Viewer
```bash
cd timeline/viewer
npm install
npm run build
ls -lh build/
```

---

## Test Results Log

Date: ___________
Tested by: ___________

| Test Suite | Status | Notes |
|------------|--------|-------|
| Core Functionality | ☐ Pass ☐ Fail | |
| Multi-Format Events | ☐ Pass ☐ Fail | |
| Parser Tests | ☐ Pass ☐ Fail | |
| File System | ☐ Pass ☐ Fail | |
| Database | ☐ Pass ☐ Fail | |
| API Tests | ☐ Pass ☐ Fail | |
| Validation | ☐ Pass ☐ Fail | |
| Search | ☐ Pass ☐ Fail | |
| Documentation | ☐ Pass ☐ Fail | |
| Imports/Dependencies | ☐ Pass ☐ Fail | |
| Workflows | ☐ Pass ☐ Fail | |
| Performance | ☐ Pass ☐ Fail | |
| Edge Cases | ☐ Pass ☐ Fail | |
| Security | ☐ Pass ☐ Fail | |
| Regression | ☐ Pass ☐ Fail | |

**Overall Result**: ☐ PASS ☐ FAIL

**Issues Found**:
1.
2.
3.

**Follow-up Actions**:
1.
2.
3.

---

**Status**: Ready for testing
**Last Updated**: 2025-10-17
