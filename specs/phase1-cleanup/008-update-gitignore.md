# SPEC-008: Update .gitignore

**Status**: Ready
**Priority**: Low
**Estimated Time**: 10 minutes
**Risk**: Very Low
**Dependencies**: SPEC-005, SPEC-006, SPEC-007

## Problem

Current `.gitignore` may be incomplete or outdated, potentially allowing:
- Build artifacts to be committed (`__pycache__/`, `*.pyc`)
- Environment files to leak secrets (`.env`)
- IDE-specific files to pollute repo (`.vscode/`, `.idea/`)
- OS-specific files (`.DS_Store`)
- Test coverage reports
- Dependency directories (`node_modules/`, `venv/`)

This causes:
- Repository bloat
- Merge conflicts on auto-generated files
- Security risks (accidentally committed secrets)
- Noise in git status

## Goal

Create comprehensive `.gitignore` covering all common Python/JavaScript/development artifacts.

## Success Criteria

- [ ] All Python build artifacts ignored
- [ ] All JavaScript build artifacts ignored
- [ ] All IDE files ignored
- [ ] All OS files ignored
- [ ] All environment files ignored
- [ ] All test artifacts ignored
- [ ] Database files appropriately handled
- [ ] No unwanted files in `git status`

## Current .gitignore Analysis

### Step 1: Check Current .gitignore

```bash
cd /Users/markr/kleptocracy-timeline

# View current .gitignore
cat .gitignore

# Check what's currently tracked that shouldn't be
git ls-files | grep -E "__pycache__|\.pyc$|\.DS_Store|node_modules|\.env"
```

## Implementation Steps

### Step 1: Create Comprehensive .gitignore

```bash
cd /Users/markr/kleptocracy-timeline

# Backup current .gitignore
cp .gitignore .gitignore.backup

# Create new comprehensive .gitignore
cat > .gitignore << 'EOF'
# ============================================
# Python
# ============================================

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.hypothesis/
.pytest_cache/
coverage_html/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# ============================================
# JavaScript / Node.js
# ============================================

# Dependencies
node_modules/
jspm_packages/

# Build outputs
build/
dist/
*.bundle.js
*.bundle.js.map

# Testing
coverage/

# Production
/build

# Misc
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local

npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# parcel-bundler cache
.cache
.parcel-cache

# Next.js build output
.next
out

# Nuxt.js build / generate output
.nuxt
dist

# Gatsby files
.cache/
public

# Storybook
storybook-static

# ============================================
# Databases
# ============================================

# SQLite
*.db
*.sqlite
*.sqlite3

# SQLite WAL files (Write-Ahead Logging)
*.db-wal
*.db-shm
*.db-journal

# PostgreSQL
*.pgsql

# ============================================
# IDEs and Editors
# ============================================

# VSCode
.vscode/
*.code-workspace

# PyCharm
.idea/
*.iml
*.iws
.idea_modules/

# Sublime Text
*.sublime-project
*.sublime-workspace

# Vim
*.swp
*.swo
*~
.netrwhist

# Emacs
*~
\#*\#
/.emacs.desktop
/.emacs.desktop.lock
*.elc
auto-save-list
tramp
.\#*

# Eclipse
.settings/
.project
.classpath
.metadata

# NetBeans
nbproject/
nbbuild/
nbdist/
.nb-gradle/

# ============================================
# Operating Systems
# ============================================

# macOS
.DS_Store
.AppleDouble
.LSOverride
._*
.DocumentRevisions-V100
.fseventsd
.Spotlight-V100
.TemporaryItems
.Trashes
.VolumeIcon.icns
.com.apple.timemachine.donotpresent
.AppleDB
.AppleDesktop
Network Trash Folder
Temporary Items
.apdisk

# Windows
Thumbs.db
Thumbs.db:encryptable
ehthumbs.db
ehthumbs_vista.db
*.stackdump
[Dd]esktop.ini
$RECYCLE.BIN/
*.lnk

# Linux
.directory
.Trash-*
.nfs*

# ============================================
# Project Specific
# ============================================

# Temporary files
tmp/
temp/
*.tmp

# Log files
*.log
logs/

# Backup files
*.bak
*.backup
*.old
*~

# Archive files (keep in archive/ directory but ignore elsewhere)
*.tar.gz
*.zip
*.7z

# Hugo (removed but keep ignore in case)
.hugo_build.lock
/public/

# Research server
research_monitor.pid
/tmp/research_monitor.pid

# Timeline data (if using external sync)
# Uncomment if timeline data is managed separately
# timeline/data/events/

# Validation reports (if generated locally)
# Uncomment if validation reports should not be committed
# validation_reports/

# Local configuration overrides
*.local.py
local_config.py
config.local.py

# API keys and secrets
secrets.json
credentials.json
*.pem
*.key
*.cert

# Test outputs
test-results/
test_output/

# Alembic (database migrations)
# Keep alembic/ but ignore generated migration files if needed
# alembic/versions/*.pyc

# ============================================
# CI/CD
# ============================================

# GitHub Actions
# Keep .github/ but ignore logs
.github/workflows/*.log

# ============================================
# Documentation Build
# ============================================

# Sphinx
docs/_build/
docs/_static/
docs/_templates/

# MkDocs
/site/

# ============================================
# Package Managers
# ============================================

# pip
pip-log.txt
pip-delete-this-directory.txt

# Poetry
poetry.lock

# Conda
.conda/

# ============================================
# Security Scanning
# ============================================

# Bandit
.bandit

# Safety
.safety

# ============================================
# Performance Profiling
# ============================================

# cProfile
*.prof
*.pstats

# line_profiler
*.lprof

# ============================================
# Misc
# ============================================

# Compressed files in root (keep archive/ directory)
/*.tar.gz
/*.zip
/*.7z

# Editor directories
.vscode/
.idea/

# Temporary Python notebooks
*.ipynb

# Local experiments
experiments/
scratch/

EOF

echo "✓ Created comprehensive .gitignore"
```

### Step 2: Remove Tracked Files That Should Be Ignored

After updating .gitignore, remove files from git that should no longer be tracked:

```bash
# Find files that are tracked but should be ignored
git ls-files -i --exclude-standard

# Remove them from git (but keep local copies)
git ls-files -i --exclude-standard | xargs git rm --cached

# Common files to remove from tracking:
git rm --cached -r __pycache__/ 2>/dev/null || true
git rm --cached -r .pytest_cache/ 2>/dev/null || true
git rm --cached -r .mypy_cache/ 2>/dev/null || true
git rm --cached -r htmlcov/ 2>/dev/null || true
git rm --cached -r coverage_html/ 2>/dev/null || true
git rm --cached **/*.pyc 2>/dev/null || true
git rm --cached .DS_Store 2>/dev/null || true
git rm --cached -r venv/ 2>/dev/null || true
git rm --cached -r node_modules/ 2>/dev/null || true
git rm --cached *.db-wal 2>/dev/null || true
git rm --cached *.db-shm 2>/dev/null || true

echo "✓ Removed ignored files from git tracking"
```

### Step 3: Verify Git Status is Clean

```bash
# Check what's still tracked
git status

# Should show:
# - Changes to .gitignore
# - Deletions of cache/build files (staged)

# Should NOT show:
# - __pycache__/
# - *.pyc
# - node_modules/
# - .DS_Store
# - venv/
```

## Validation Steps

### Test 1: Verify .gitignore Works

```bash
# Create test files that should be ignored
touch test.pyc
mkdir -p test_cache/__pycache__
touch test_cache/__pycache__/foo.pyc
touch .DS_Store

# Check git status
git status

# Should NOT show these test files

# Clean up
rm test.pyc
rm -rf test_cache/
rm .DS_Store
```

### Test 2: Check No Ignored Files Are Tracked

```bash
# List tracked files that match ignore patterns
git ls-files | grep -E "__pycache__|\.pyc$|\.DS_Store|node_modules"

# Should return nothing
```

### Test 3: Verify Important Files Still Tracked

```bash
# Ensure actual source files are still tracked
git ls-files | grep -E "\.py$|\.js$|\.md$" | head -10

# Should show Python, JavaScript, and Markdown files
```

### Test 4: Check Timeline Events Still Tracked

```bash
# Make sure event data is still tracked
git ls-files | grep "timeline.*\.json" | head -5

# Should show event JSON files (unless explicitly ignored)
```

## Special Considerations

### Database Files

**Decision needed**: Should `*.db` be ignored?

**Option 1**: Ignore all database files (recommended)
```bash
# In .gitignore:
*.db
*.db-wal
*.db-shm
```

**Option 2**: Track specific database file, ignore others
```bash
# In .gitignore:
*.db
!unified_research.db
*.db-wal
*.db-shm
```

**Option 3**: Track database in git LFS
```bash
# Install git-lfs
git lfs install

# Track database files in LFS
git lfs track "*.db"

# Add to .gitattributes
*.db filter=lfs diff=lfs merge=lfs -text
```

### Node Modules

`node_modules/` should NEVER be committed. If currently tracked:

```bash
# Check if node_modules is tracked
git ls-files | grep node_modules

# If found, remove it
git rm -r --cached timeline/viewer/node_modules/
git rm -r --cached viewer/node_modules/ 2>/dev/null || true
```

### Environment Files

Never commit `.env` files with secrets:

```bash
# Ensure .env is ignored
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore

# Remove if currently tracked
git rm --cached .env 2>/dev/null || true
git rm --cached **/.env 2>/dev/null || true

# Create .env.example template instead
cp research-server/.env.example .env.example 2>/dev/null || true
```

## Post-Update Actions

### Commit Changes

```bash
# Stage .gitignore changes
git add .gitignore

# Stage removal of ignored files
git add -A

# Commit
git commit -m "SPEC-008: Update .gitignore with comprehensive patterns

- Add Python build artifacts (__pycache__/, *.pyc)
- Add JavaScript build artifacts (node_modules/, build/)
- Add IDE files (.vscode/, .idea/, etc.)
- Add OS files (.DS_Store, Thumbs.db)
- Add environment files (.env)
- Add test artifacts (.pytest_cache/, coverage/)
- Add database files (*.db-wal, *.db-shm)
- Remove previously tracked files that should be ignored

This prevents build artifacts and sensitive files from being committed."

# Verify clean state
git status
# Should show "working tree clean"
```

### Update Documentation

Update CONTRIBUTING.md or README.md if needed:

```markdown
## Development Setup

After cloning:

1. Install Python dependencies:
   ```bash
   cd research-server
   pip install -r requirements.txt
   ```

2. Install Node dependencies:
   ```bash
   cd timeline/viewer
   npm install
   ```

3. Create environment file:
   ```bash
   cp research-server/.env.example research-server/.env
   # Edit .env with your configuration
   ```

**Note**: Do not commit `node_modules/`, `venv/`, `.env`, or build artifacts.
```

## Rollback Plan

If .gitignore causes issues:

```bash
# Restore old .gitignore
git checkout .gitignore.backup
mv .gitignore.backup .gitignore

# Or restore from git
git checkout HEAD~1 -- .gitignore

# Re-track files if needed
git add <files>
```

## Dependencies

- None (can be done independently)
- Recommended: Complete SPEC-005, SPEC-006, SPEC-007 first for cleaner diff

## Risks & Mitigations

**Risk**: Accidentally ignoring important files
**Mitigation**: Test with sample files, verify source files still tracked

**Risk**: Breaking existing workflows that depend on tracked files
**Mitigation**: Review git ls-files before and after, keep backup

## Notes

- This is a one-time cleanup; .gitignore prevents future issues
- Some files may need to be removed from git history for full cleanup
- Use `git filter-branch` or `BFG Repo-Cleaner` for deep history cleanup (optional)

## Acceptance Criteria

- [x] Comprehensive .gitignore created
- [x] All Python artifacts ignored
- [x] All JavaScript artifacts ignored
- [x] All IDE files ignored
- [x] All OS files ignored
- [x] Environment files ignored
- [x] Previously tracked ignored files removed
- [x] Source files still tracked correctly
- [x] Git status clean
- [x] Documentation updated

## Size Impact

Initial commit may be large (removing tracked files), but prevents future bloat.

## Reference

Based on:
- [GitHub's Python .gitignore](https://github.com/github/gitignore/blob/main/Python.gitignore)
- [GitHub's Node .gitignore](https://github.com/github/gitignore/blob/main/Node.gitignore)
- Common development best practices
