# SPEC-006: Create Research Server Repository

**Status**: Ready
**Priority**: Critical
**Estimated Time**: 1 hour
**Risk**: Medium
**Dependencies**: SPEC-005 (timeline repo created)

## Problem

Research server currently mixed with timeline data in monorepo.

## Goal

Extract research server into separate repository with git history.

## Success Criteria

- [ ] New repository: `timeline-research-server`
- [ ] Contains only research-server files
- [ ] Git history preserved
- [ ] Tests pass
- [ ] CLI wrapper works
- [ ] Documentation updated

## Repository Structure

```
timeline-research-server/
├── src/
│   ├── api/              # Flask REST API
│   ├── cli/              # CLI interface
│   ├── mcp/              # MCP server
│   ├── services/         # Business logic (to be created in Phase 3)
│   └── repositories/     # Data access (to be created in Phase 3)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── CLI.md
│   └── DEVELOPMENT.md
├── scripts/
│   └── cleanup_for_release.sh
├── .github/workflows/
│   ├── tests.yml
│   └── lint.yml
├── README.md
├── LICENSE (MIT)
├── requirements.txt
└── .env.example
```

## Implementation Steps

### Step 1: Create Branch with Research Server Only

```bash
cd /Users/markr/kleptocracy-timeline
git subtree split -P research-server -b research-server-only
git checkout research-server-only
```

### Step 2: Create GitHub Repository

```bash
gh repo create timeline-research-server \
  --public \
  --description "Research infrastructure for Kleptocracy Timeline - API, CLI, and MCP server" \
  --license mit
```

### Step 3: Restructure Directories

```bash
# Rename server/ to src/api/ (clearer structure)
mkdir -p src
mv server src/api
mv client src/client
mv cli src/cli
mv mcp src/mcp

# Move tests to root level
# (already correct location if Phase 1 complete)

# Create src/__init__.py
touch src/__init__.py
```

### Step 4: Update Imports

Update all imports to use new structure:

```bash
# Find imports that need updating
grep -r "from server\." src/ tests/

# Update pattern:
# from server.models import → from src.api.models import
# from server.config import → from src.api.config import
```

### Step 5: Update README

```markdown
# Timeline Research Server

Research infrastructure for the Kleptocracy Timeline project.

## Features

- **REST API**: Full CRUD operations on timeline events
- **CLI Tool**: Command-line interface for research workflows
- **MCP Server**: AI agent integration via Model Context Protocol
- **Validation Runs**: Parallel QA processing system

## Quick Start

```bash
./research server-start
./research get-stats
```

See [Installation Guide](docs/INSTALLATION.md)

## Timeline Data

This server works with timeline data from:
👉 [kleptocracy-timeline](https://github.com/yourusername/kleptocracy-timeline)

Clone both repositories:
```bash
git clone https://github.com/yourusername/timeline-research-server.git
git clone https://github.com/yourusername/kleptocracy-timeline.git
```

## Documentation

- [API Reference](docs/API.md)
- [CLI Reference](docs/CLI.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development Setup](docs/DEVELOPMENT.md)
```

### Step 6: Update Configuration for Separate Repos

Update `src/api/config.py`:

```python
# Default path now looks for sibling directory
self.events_path = self._get_path(
    'TIMELINE_EVENTS_PATH',
    '../kleptocracy-timeline/events'  # Sibling repo
)
```

Update `.env.example`:

```bash
# Path to timeline events (clone sibling repo)
TIMELINE_EVENTS_PATH=../kleptocracy-timeline/events

# Or use absolute path
# TIMELINE_EVENTS_PATH=/path/to/kleptocracy-timeline/events
```

### Step 7: Create GitHub Actions

**`.github/workflows/tests.yml`**:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov=src
```

### Step 8: Push to GitHub

```bash
git remote add origin git@github.com:yourusername/timeline-research-server.git
git push -u origin research-server-only:main
```

### Step 9: Add Development Setup Docs

Create `docs/DEVELOPMENT.md`:

```markdown
# Development Setup

## Prerequisites

- Python 3.9+
- Timeline data repository cloned

## Setup

```bash
# Clone both repos
git clone https://github.com/yourusername/timeline-research-server.git
git clone https://github.com/yourusername/kleptocracy-timeline.git

# Install dependencies
cd timeline-research-server
pip install -r requirements.txt

# Run tests
pytest tests/

# Start server
./research server-start
```

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=src tests/
```
```

## Validation Steps

- [ ] Repository cloned and installs successfully
- [ ] Tests pass: `pytest tests/`
- [ ] CLI works: `./research get-stats`
- [ ] Server starts: `./research server-start`
- [ ] Cross-repo reference works (can access timeline events)

## Acceptance Criteria

- [x] New repository created
- [x] Only research-server files included
- [x] Git history preserved
- [x] Restructured to src/ directory
- [x] Documentation updated
- [x] CI configured
- [x] Cross-links to timeline repo added
