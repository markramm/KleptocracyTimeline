# Task Breakdown: Markdown Event Format

**Spec**: 002-markdown-event-format
**Plan**: plan.md
**Created**: 2025-10-17

## Task Status Legend
- [ ] Not started
- [🔄] In progress
- [✅] Complete
- [⏸️] Blocked/Deferred
- [❌] Cancelled

---

## Phase 1: Parser Infrastructure (Days 1-2)

### 1.1 Setup & Dependencies
- [ ] Add `python-frontmatter>=1.0.0` to `research-server/requirements.txt`
- [ ] Add `pyyaml>=6.0` to `research-server/requirements.txt`
- [ ] Add `markdown>=3.5` to requirements (optional)
- [ ] Install dependencies: `pip install -r research-server/requirements.txt`
- [ ] Verify imports work: `python3 -c "import frontmatter"`

### 1.2 Create Parser Base Class
- [ ] Create directory: `research-server/server/parsers/`
- [ ] Create `research-server/server/parsers/__init__.py`
- [ ] Create `research-server/server/parsers/base.py`
  - [ ] Define `EventParser` ABC
  - [ ] Add `can_parse()` abstract method
  - [ ] Add `parse()` abstract method
  - [ ] Add `validate_format()` abstract method
  - [ ] Add type hints
  - [ ] Add docstrings

### 1.3 Extract JSON Parser
- [ ] Create `research-server/server/parsers/json_parser.py`
- [ ] Extract JSON parsing logic from `app_v2.py`
- [ ] Implement `JsonEventParser` class
  - [ ] Implement `can_parse()` - check for `.json` suffix
  - [ ] Implement `parse()` - load JSON file
  - [ ] Implement `validate_format()` - catch JSON errors
- [ ] Add type hints
- [ ] Add docstrings

### 1.4 Create Markdown Parser
- [ ] Create `research-server/server/parsers/markdown_parser.py`
- [ ] Implement `MarkdownEventParser` class
  - [ ] Implement `can_parse()` - check for `.md` suffix
  - [ ] Implement `parse()` - parse frontmatter + content
  - [ ] Implement `validate_format()` - validate YAML
  - [ ] Handle missing frontmatter gracefully
  - [ ] Map content to `summary` field
  - [ ] Validate required fields (id, date, title)
- [ ] Add type hints
- [ ] Add docstrings

### 1.5 Create Parser Factory
- [ ] Update `research-server/server/parsers/__init__.py`
- [ ] Implement `EventParserFactory` class
  - [ ] Register parsers list
  - [ ] Implement `get_parser(file_path)` method
  - [ ] Implement `parse_event(file_path)` method
  - [ ] Handle unsupported formats gracefully
- [ ] Add type hints
- [ ] Add docstrings

---

## Phase 2: Integration (Days 3-4)

### 2.1 Update Filesystem Sync
- [ ] Update `research-server/server/app_v2.py`
- [ ] Import `EventParserFactory`
- [ ] Refactor `sync_filesystem_to_database()` function
  - [ ] Replace direct JSON parsing with parser factory
  - [ ] Add glob for `.md` files
  - [ ] Use parser factory for both `.json` and `.md`
  - [ ] Maintain existing error handling
  - [ ] Log which format was parsed
- [ ] Test sync with mixed JSON/Markdown events

### 2.2 Update Database Models
- [ ] Verify `TimelineEvent` model supports all fields
- [ ] Check if any fields need type changes
- [ ] Ensure `sources` field handles both formats
- [ ] Test database upsert with markdown events

### 2.3 Update Event Validator
- [ ] Check `research-server/server/validators/event_validator.py`
- [ ] Ensure schema validation works for both formats
- [ ] Add format-specific error messages if needed
- [ ] Test validation with markdown events

---

## Phase 3: CLI Tool Updates (Day 5)

### 3.1 Update Validation Command
- [ ] Update `research-server/cli/research_cli.py`
- [ ] Modify `validate-event` command
  - [ ] Support both `.json` and `.md` files
  - [ ] Use parser factory
  - [ ] Show format-specific errors
  - [ ] Test with both formats

### 3.2 Add Conversion Command
- [ ] Create `convert-to-markdown` command
- [ ] Implement JSON → Markdown conversion
  - [ ] Parse JSON event
  - [ ] Generate YAML frontmatter
  - [ ] Generate markdown body
  - [ ] Write to output file
- [ ] Add `--output` option
- [ ] Add `--backup` option (copy original)
- [ ] Test conversion on real events

### 3.3 Update Create Event Command
- [ ] Modify `create-event` command
- [ ] Support both `--json` and `--markdown` options
- [ ] Generate appropriate file format
- [ ] Test creating both formats

---

## Phase 4: Testing (Days 6-7)

### 4.1 Unit Tests - Parsers
- [ ] Create `research-server/tests/test_markdown_parser.py`
- [ ] Test `can_parse()` method
- [ ] Test `parse()` with valid markdown
- [ ] Test `parse()` with invalid YAML
- [ ] Test `parse()` with missing fields
- [ ] Test content → summary mapping
- [ ] Test sources array parsing
- [ ] Test tags array parsing
- [ ] Aim for 90%+ coverage on parser code

### 4.2 Unit Tests - Factory
- [ ] Create `research-server/tests/test_parser_factory.py`
- [ ] Test `get_parser()` for `.json` files
- [ ] Test `get_parser()` for `.md` files
- [ ] Test `get_parser()` for unsupported formats
- [ ] Test `parse_event()` with both formats
- [ ] Test error handling

### 4.3 Integration Tests
- [ ] Create `research-server/tests/test_markdown_integration.py`
- [ ] Test markdown event filesystem sync
- [ ] Test database storage of markdown events
- [ ] Test mixed JSON/Markdown in same directory
- [ ] Test search with markdown events
- [ ] Test API responses include markdown events

### 4.4 Validation Tests
- [ ] Create `research-server/tests/test_markdown_validation.py`
- [ ] Test schema validation for markdown
- [ ] Test required fields enforcement
- [ ] Test source structure validation
- [ ] Test error messages are helpful

### 4.5 Performance Tests
- [ ] Benchmark JSON parsing (baseline)
- [ ] Benchmark markdown parsing
- [ ] Calculate performance difference
- [ ] Ensure <5% slowdown
- [ ] Test with 100+ events

### 4.6 Run Full Test Suite
- [ ] Run all existing tests
- [ ] Ensure no regressions
- [ ] Fix any broken tests
- [ ] Achieve 80%+ coverage overall

---

## Phase 5: Documentation (Days 8-9)

### 5.1 Event Format Documentation
- [ ] Create `timeline/docs/EVENT_FORMAT.md`
- [ ] Document JSON format (existing)
- [ ] Document Markdown format (new)
- [ ] Add examples for both formats
- [ ] Document field requirements
- [ ] Document source structure
- [ ] Add troubleshooting section

### 5.2 Update CONTRIBUTING.md
- [ ] Add section "Adding Events (Markdown)"
- [ ] Link to EVENT_FORMAT.md
- [ ] Provide step-by-step guide
- [ ] Add example markdown event
- [ ] Document pull request process

### 5.3 Update CLAUDE.md
- [ ] Add section on markdown events
- [ ] Update CLI command examples
- [ ] Document both formats
- [ ] Update agent instructions

### 5.4 Create Example Events
- [ ] Convert 10 high-visibility events to markdown
  - [ ] 1971-08-23--powell-memo-institutional-capture.md
  - [ ] 2010-01-21--citizens-united-unleashes-unlimited-corporate-spending.md
  - [ ] 2002-08-01--whig-formation.md
  - [ ] 2006-02-22--dubai-ports-world-crisis.md
  - [ ] 2008-09-15--lehman-brothers-collapse.md
  - [ ] 2013-06-05--snowden-revelations.md
  - [ ] 2016-11-08--trump-election.md
  - [ ] 2020-01-06--capitol-attack.md
  - [ ] Recent Trump crypto events (2025)
  - [ ] Recent AI regulation events (2025)
- [ ] Place in `timeline/examples/` directory
- [ ] Link from documentation

### 5.5 GitHub Issue Templates
- [ ] Create `.github/ISSUE_TEMPLATE/add-event-markdown.md`
- [ ] Provide markdown template
- [ ] Add instructions
- [ ] Link to documentation

---

## Phase 6: Pre-commit Hooks (Day 10)

### 6.1 Local Pre-commit Hook
- [ ] Create `.git/hooks/pre-commit` script
- [ ] Add validation for JSON events
- [ ] Add validation for Markdown events
- [ ] Make executable: `chmod +x .git/hooks/pre-commit`
- [ ] Test hook with valid events
- [ ] Test hook with invalid events

### 6.2 GitHub Actions Workflow
- [ ] Update `.github/workflows/validate-events.yml`
- [ ] Add markdown validation step
- [ ] Test workflow with PR
- [ ] Ensure fails on invalid events
- [ ] Ensure passes on valid events

### 6.3 Validation Script
- [ ] Create `scripts/validate_events.py`
- [ ] Support `--format` option (json, markdown, all)
- [ ] Validate all events in directory
- [ ] Print clear error messages
- [ ] Exit with appropriate code

---

## Phase 7: Deployment & Rollout (Days 11-12)

### 7.1 Code Review
- [ ] Self-review all changes
- [ ] Run MyPy: `mypy research-server/server/parsers/`
- [ ] Run tests: `python3 -m pytest research-server/tests/`
- [ ] Check test coverage: `coverage report`
- [ ] Review constitution compliance

### 7.2 Create Pull Request
- [ ] Create feature branch from repository-restructure-prototype
- [ ] Commit all parser changes
- [ ] Commit CLI updates
- [ ] Commit tests
- [ ] Commit documentation
- [ ] Push to GitHub
- [ ] Create PR with description

### 7.3 Testing in Development
- [ ] Deploy to development environment
- [ ] Test with 10 example markdown events
- [ ] Verify research server loads both formats
- [ ] Test CLI commands
- [ ] Check performance metrics

### 7.4 Merge & Deploy
- [ ] Address PR feedback
- [ ] Merge to main branch
- [ ] Deploy to production
- [ ] Monitor for errors
- [ ] Verify markdown events appear in search

### 7.5 Announcement
- [ ] Update README with markdown support
- [ ] Announce in project communications
- [ ] Share example markdown events
- [ ] Invite contributions

---

## Phase 8: Hugo Integration (Days 13-15, Optional)

### 8.1 Hugo Setup
- [ ] Install Hugo: `brew install hugo`
- [ ] Initialize Hugo site: `hugo new site timeline-hugo`
- [ ] Choose Hugo theme
- [ ] Configure `config.toml`

### 8.2 Hugo Content Integration
- [ ] Configure Hugo to read from `timeline/data/events/`
- [ ] Create event template: `layouts/events/single.html`
- [ ] Create list template: `layouts/events/list.html`
- [ ] Add pagination
- [ ] Add search functionality

### 8.3 Hugo Deployment
- [ ] Configure GitHub Pages for Hugo
- [ ] Add build workflow: `.github/workflows/hugo.yml`
- [ ] Deploy to separate URL: `timeline.project.com`
- [ ] Test Hugo site
- [ ] Add link from main README

### 8.4 SEO Optimization
- [ ] Add meta tags to templates
- [ ] Generate sitemap
- [ ] Add structured data (JSON-LD)
- [ ] Test with Google Search Console

---

## Phase 9: Monitoring & Iteration (Days 16+)

### 9.1 Monitor Usage
- [ ] Track markdown event creation rate
- [ ] Track JSON → Markdown conversions
- [ ] Monitor validation error rates
- [ ] Track contribution patterns

### 9.2 Gather Feedback
- [ ] Review GitHub issues
- [ ] Monitor pull requests
- [ ] Collect user feedback
- [ ] Identify pain points

### 9.3 Iterate
- [ ] Address common errors
- [ ] Improve documentation
- [ ] Add helpful error messages
- [ ] Consider additional tooling

### 9.4 Performance Tuning
- [ ] Profile parsing performance
- [ ] Optimize if needed
- [ ] Cache parsed events
- [ ] Monitor memory usage

---

## Dependencies & Blockers

### Critical Dependencies
- [✅] Repository restructuring complete
- [✅] Research server working
- [ ] python-frontmatter library installed
- [ ] Tests passing

### Potential Blockers
- [ ] Performance issues with markdown parsing
  - **Mitigation**: Benchmark early, optimize if needed
- [ ] Schema validation incompatibilities
  - **Mitigation**: Test thoroughly with real events
- [ ] User confusion about formats
  - **Mitigation**: Clear documentation, good examples

---

## Success Criteria Checklist

### Functional
- [ ] Research server parses both .json and .md files
- [ ] All 1,580 existing JSON events continue working
- [ ] Markdown events pass same validation as JSON
- [ ] CLI tools work with both formats
- [ ] At least 10 example events converted

### Quality
- [ ] 80%+ test coverage for new code
- [ ] 100% MyPy compliance
- [ ] All existing tests still pass
- [ ] Performance <5% slower
- [ ] Documentation complete

### User Experience
- [ ] Contributor can add markdown event via GitHub
- [ ] Reviewer can understand changes from diff
- [ ] Error messages help fix issues
- [ ] Format documented in CONTRIBUTING.md
- [ ] Examples available

---

## Estimated Timeline

- **Phase 1 (Parser Infrastructure)**: 2 days
- **Phase 2 (Integration)**: 2 days
- **Phase 3 (CLI Updates)**: 1 day
- **Phase 4 (Testing)**: 2 days
- **Phase 5 (Documentation)**: 2 days
- **Phase 6 (Pre-commit Hooks)**: 1 day
- **Phase 7 (Deployment)**: 2 days
- **Phase 8 (Hugo, Optional)**: 3 days
- **Phase 9 (Monitoring)**: Ongoing

**Total**: ~12 days (or ~15 days with Hugo)

---

## Notes

- Tasks can be parallelized where noted
- Hugo integration (Phase 8) is optional and can be deferred
- Monitor Phase 9 is ongoing after deployment
- Add new tasks as issues are discovered

**Ready for implementation**: Yes
**Next step**: Begin Phase 1 - Parser Infrastructure
