# Release Preparation Checklist

## 🧹 Cleanup Tasks

### Critical (Must Do Before Release)

- [ ] **Remove Legacy Directories**
  - [ ] Delete `research_monitor/` (superseded by `research-server/`)
  - [ ] Delete `api/` (superseded by `research-server/`)
  - [ ] Delete duplicate `unified_research.db*` files in root (keep only in `research-server/`)

- [ ] **Remove Temporary/Backup Files**
  - [ ] Delete `research-server/server/app_v2.py.backup`
  - [ ] Delete `research-server/server/enhanced_event_validator.py.bak`
  - [ ] Delete `research_api.py` from root (functionality moved to research-server)

- [ ] **Clean Up Log Files**
  - [ ] Delete stale `.log` files from `research_monitor/`, `api/`, `research-server/server/`
  - [ ] Keep only active server logs
  - [ ] Add log rotation configuration

- [ ] **Remove Python Cache**
  - [ ] Delete all `__pycache__/` directories
  - [ ] Delete `.pytest_cache/`, `.mypy_cache/` directories
  - [ ] Add to `.gitignore` if not already present

- [ ] **Verify .gitignore Coverage**
  - [x] Hugo build artifacts (`timeline/public/`, `.hugo_build.lock`)
  - [x] Database WAL files (`*.db-wal`, `*.db-shm`)
  - [ ] Legacy directories (`research_monitor/`, `api/`)
  - [ ] Backup files (`*.backup`, `*.bak`)
  - [ ] Python cache (`__pycache__/`, `*.pyc`)

### Important (Recommended)

- [ ] **Documentation Updates**
  - [ ] Update main README.md with accurate event count
  - [ ] Update research-server/README.md with new CLI wrapper
  - [ ] Consolidate duplicate API_DOCUMENTATION.md files
  - [ ] Add INSTALLATION.md with setup instructions
  - [ ] Add DEVELOPMENT.md with contribution guidelines

- [ ] **Code Quality**
  - [ ] Run linters (pylint, flake8) on research-server
  - [ ] Fix import inconsistencies
  - [ ] Review error handling in all API endpoints
  - [ ] Add type hints to critical functions

- [ ] **Testing**
  - [ ] Run existing test suites
  - [ ] Add tests for validation runs system
  - [ ] Test CLI wrapper on clean environment
  - [ ] Verify MCP server functionality

- [ ] **Security**
  - [ ] Remove any hardcoded credentials (check complete)
  - [ ] Add .env.example file
  - [ ] Document API key configuration
  - [ ] Review file permissions

### Nice to Have

- [ ] **Performance Optimization**
  - [ ] Review database indexes
  - [ ] Optimize slow queries
  - [ ] Add query result caching where appropriate
  - [ ] Database vacuum/optimize

- [ ] **Git Cleanup**
  - [ ] Delete stale branches (feature/ux-improvements, json-migration, etc.)
  - [ ] Create release tag
  - [ ] Update branch protection rules

- [ ] **CI/CD Setup**
  - [ ] Add GitHub Actions for tests
  - [ ] Add pre-commit hooks
  - [ ] Set up automated linting

## 📝 Documentation Tasks

### Required Documentation

- [ ] **README.md Updates**
  - [ ] Current event count (1,581+)
  - [ ] Architecture diagram
  - [ ] Quick start instructions
  - [ ] Link to detailed docs

- [ ] **INSTALLATION.md**
  - [ ] System requirements
  - [ ] Python dependencies
  - [ ] Database setup
  - [ ] Environment variables
  - [ ] Running the server

- [ ] **API_DOCUMENTATION.md**
  - [ ] Consolidate duplicate files
  - [ ] Add validation runs endpoints
  - [ ] Add CLI wrapper examples
  - [ ] Update endpoint descriptions

- [ ] **CONTRIBUTING.md**
  - [ ] Code style guidelines
  - [ ] PR process
  - [ ] Testing requirements
  - [ ] Development setup

### Architecture Documentation

- [ ] **Update ARCHITECTURE.md**
  - [ ] Two-component structure (timeline + research-server)
  - [ ] Data flow diagrams
  - [ ] Database schema
  - [ ] API design principles

## 🔒 Security Checklist

- [x] No hardcoded credentials found
- [ ] API key authentication documented
- [ ] Environment variable usage documented
- [ ] .env.example provided
- [ ] Sensitive files in .gitignore

## 🧪 Testing Checklist

- [x] Validation runs system tested
- [x] CLI wrapper tested
- [ ] Full test suite passes
- [ ] Integration tests pass
- [ ] Server startup/shutdown tested
- [ ] Database migration tested

## 📦 Release Preparation

- [ ] Version number updated
- [ ] CHANGELOG.md created/updated
- [ ] Release notes drafted
- [ ] Migration guide (if needed)
- [ ] Backup procedures documented

## 🚀 Deployment Checklist

- [ ] Database backup procedure documented
- [ ] Server restart procedure documented
- [ ] Monitoring setup documented
- [ ] Log rotation configured
- [ ] Error alerting configured

## Priority Order

### Phase 1: Critical Cleanup (30 minutes)
1. Remove legacy directories
2. Delete backup files
3. Update .gitignore
4. Clean Python cache

### Phase 2: Documentation (1-2 hours)
1. Update README.md
2. Create INSTALLATION.md
3. Consolidate API docs
4. Add CONTRIBUTING.md

### Phase 3: Testing & Quality (1 hour)
1. Run test suites
2. Fix any failing tests
3. Run linters
4. Fix critical issues

### Phase 4: Polish (optional, 2+ hours)
1. Performance optimization
2. Git branch cleanup
3. CI/CD setup
4. Enhanced documentation

## Command Reference

### Cleanup Commands

```bash
# Remove legacy directories (VERIFY FIRST!)
rm -rf research_monitor/
rm -rf api/

# Remove duplicate databases
rm unified_research.db*

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Remove backup files
find . -name "*.backup" -delete
find . -name "*.bak" -delete

# Clean logs
rm research-server/server/*.log
rm timeline_data/*.log
```

### Testing Commands

```bash
# Run tests
cd research-server
python3 -m pytest tests/

# Run linter
python3 -m pylint server/ client/ cli/

# Check test coverage
python3 -m pytest --cov=server --cov=client tests/
```

### Git Cleanup

```bash
# Delete merged branches
git branch --merged | grep -v "main\|master" | xargs git branch -d

# Delete remote branches
git push origin --delete feature/ux-improvements
git push origin --delete json-migration
```

## Notes

- Always backup database before major changes
- Test on clean environment before release
- Document any breaking changes
- Update version numbers consistently
