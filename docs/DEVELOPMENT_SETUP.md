# Development Setup Guide

**Last Updated**: 2025-10-17

This guide helps you set up a complete development environment for contributing to the Kleptocracy Timeline project.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Timeline Viewer Development](#timeline-viewer-development)
4. [Research Server Development](#research-server-development)
5. [Running Tests](#running-tests)
6. [Code Quality](#code-quality)
7. [Development Workflow](#development-workflow)
8. [Common Tasks](#common-tasks)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.9+** - Core development language
- **Node.js 16+** - For React viewer
- **npm 8+** - Node package manager
- **Git 2.x+** - Version control
- **SQLite3** - Database (usually pre-installed)

### Recommended Tools

- **VS Code** or **PyCharm** - IDEs with Python support
- **GitHub CLI** (`gh`) - For PR management
- **Docker** (optional) - For isolated testing

### System Requirements

- 4GB+ RAM
- 10GB+ free disk space
- macOS, Linux, or Windows with WSL2

---

## Initial Setup

### 1. Clone the Repository

```bash
# Clone with SSH (recommended)
git clone git@github.com:[username]/kleptocracy-timeline.git
cd kleptocracy-timeline

# Or with HTTPS
git clone https://github.com/[username]/kleptocracy-timeline.git
cd kleptocracy-timeline
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
pip install -r research-server/requirements.txt
```

### 3. Verify Python Setup

```bash
# Test CLI
python3 research_cli.py --help

# Check imports
python3 -c "from research_client import TimelineResearchClient; print('✓ Imports work')"

# Verify database access
python3 -c "import sqlite3; conn = sqlite3.connect('unified_research.db'); print('✓ Database accessible')"
```

### 4. Set Up Node.js Environment

```bash
# Navigate to viewer
cd timeline/viewer

# Install dependencies
npm install

# Verify setup
npm run build

# Clean up test build
rm -rf build
```

### 5. Configure Git Hooks

The repository includes pre-commit hooks for quality control:

```bash
# Pre-commit hook is at .git/hooks/pre-commit
# It validates:
# - Event file format (JSON and Markdown)
# - Date logic
# - API generation
# - React build (if React files changed)

# Test the hook
git add README.md
git commit -m "Test commit" --dry-run
```

---

## Timeline Viewer Development

### Running Development Server

```bash
cd timeline/viewer

# Start development server
npm start

# Browser opens automatically at http://localhost:3000
```

### Project Structure

```
timeline/viewer/
├── src/
│   ├── App.js                # Main React component
│   ├── components/           # React components
│   ├── utils/                # Utility functions
│   └── index.js              # Entry point
├── public/
│   ├── index.html            # HTML template
│   └── api/                  # Static API files
└── package.json              # Node dependencies
```

### Making Changes

1. **Edit React components** in `src/`
2. **Hot reload** works automatically
3. **Test in browser** at http://localhost:3000
4. **Lint code**: `npm run lint`
5. **Build for production**: `npm run build`

### Common Commands

```bash
# Run development server
npm start

# Build production version
npm run build

# Run linter
npm run lint

# Fix linting issues automatically
npm run lint:fix

# Run tests
npm test
```

---

## Research Server Development

### Starting the Server

```bash
# From repository root
cd research_monitor
python3 app_v2.py

# Or using CLI from root:
python3 research_cli.py server-start

# Server runs on http://localhost:5558
```

### Project Structure

```
research-server/
├── server/
│   ├── app_v2.py             # Main Flask application
│   ├── models.py             # Database models
│   ├── routes/               # API endpoints
│   ├── services/             # Business logic
│   ├── parsers/              # Event parsers (JSON + Markdown)
│   └── utils/                # Helper functions
├── tests/                    # Test suite
└── alembic/                  # Database migrations
```

### Making Changes

1. **Edit Python files** in `research-server/server/`
2. **Restart server** to see changes (no hot reload)
3. **Test API** using CLI or curl
4. **Run tests** after changes
5. **Type check** with mypy

### Testing API Changes

```bash
# Using research CLI
python3 research_cli.py server-status
python3 research_cli.py get-stats
python3 research_cli.py search-events --query "test"

# Using curl
curl http://localhost:5558/api/server/health
curl http://localhost:5558/api/events?q=test
```

### Database Migrations

When you modify `models.py`:

```bash
cd research-server

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1

# View migration history
alembic history
```

---

## Running Tests

### Full Test Suite

```bash
# From repository root
python3 -m pytest research-server/tests/ -v

# Expected output:
# ====== 218 passed in 0.4s ======
```

### Specific Test Suites

```bash
# Markdown parser tests (38 tests)
python3 -m pytest research-server/tests/test_markdown_parser.py -v
python3 -m pytest research-server/tests/test_parser_factory.py -v

# Research client tests (180 tests)
python3 -m pytest research-server/tests/test_research_client.py -v

# With coverage report
python3 -m pytest research-server/tests/ --cov=research-server/server --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Test-Driven Development

```bash
# Watch mode (requires pytest-watch)
pip install pytest-watch
ptw research-server/tests/

# Run specific test
python3 -m pytest research-server/tests/test_markdown_parser.py::TestMarkdownParserBasics::test_parse_minimal_event -v

# Run tests matching pattern
python3 -m pytest research-server/tests/ -k "markdown" -v
```

---

## Code Quality

### Type Checking

```bash
# Check types with mypy
mypy research_cli.py research_client.py research_api.py

# Check specific file
mypy research-server/server/parsers/markdown_parser.py
```

### Linting

```bash
# Python linting (if flake8 installed)
flake8 research-server/server/

# JavaScript linting
cd timeline/viewer
npm run lint
```

### Formatting

```bash
# Python formatting (if black installed)
black research_cli.py research_client.py

# JavaScript formatting (if prettier installed)
cd timeline/viewer
npm run format
```

### Pre-commit Validation

```bash
# Test what pre-commit hook will check
git add .
git commit --dry-run -m "Test validation"
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

```bash
# Edit files
# ...

# Run tests frequently
python3 -m pytest research-server/tests/ -v

# Check types
mypy your_file.py
```

### 3. Validate Events

If you created/modified timeline events:

```bash
# Validate all events
python3 timeline/scripts/validate_events.py

# Validate specific event
python3 timeline/scripts/validate_events.py timeline/data/events/2025-01-15--event-slug.json
```

### 4. Generate Static API

If timeline events changed:

```bash
cd timeline/scripts
python3 generate.py

# Verify API files updated
ls -lh ../public/api/
```

### 5. Run Full Test Suite

```bash
# Python tests
python3 -m pytest research-server/tests/ -v

# React tests (if applicable)
cd timeline/viewer
npm test

# Pre-commit validation
git add .
git commit --dry-run -m "Test"
```

### 6. Commit Changes

```bash
# Stage changes
git add .

# Commit (pre-commit hooks run automatically)
git commit -m "Add feature: description"

# If pre-commit fails, fix issues and retry
```

### 7. Push and Create PR

```bash
# Push branch
git push -u origin feature/your-feature-name

# Create PR using GitHub CLI
gh pr create --title "Add feature: description" --body "Description of changes"

# Or create PR on GitHub website
```

---

## Common Tasks

### Adding a New Timeline Event

```bash
# Option 1: JSON format
cat > timeline/data/events/2025-01-15--new-event.json <<'EOF'
{
  "id": "2025-01-15--new-event",
  "date": "2025-01-15",
  "title": "Event Title",
  "summary": "Event description...",
  "importance": 8,
  "tags": ["regulatory-capture"],
  "actors": ["Person Name"],
  "sources": [
    {
      "title": "Source Title",
      "url": "https://example.com/article",
      "publisher": "Publisher Name",
      "date": "2025-01-15",
      "tier": 1
    }
  ]
}
EOF

# Option 2: Markdown format
cat > timeline/data/events/2025-01-15--new-event.md <<'EOF'
---
id: 2025-01-15--new-event
date: 2025-01-15
title: Event Title
importance: 8
tags:
  - regulatory-capture
actors:
  - Person Name
sources:
  - title: Source Title
    url: https://example.com/article
    publisher: Publisher Name
    date: 2025-01-15
    tier: 1
---

Event description with **markdown formatting** supported.
EOF

# Validate
python3 timeline/scripts/validate_events.py timeline/data/events/2025-01-15--new-event.md

# Regenerate API
cd timeline/scripts && python3 generate.py

# Test in viewer
cd ../viewer && npm start
```

### Adding a New API Endpoint

1. **Define route** in `research-server/server/routes/`
2. **Add business logic** in `research-server/server/services/`
3. **Update models** if needed in `research-server/server/models.py`
4. **Create migration** if database changes
5. **Add tests** in `research-server/tests/`
6. **Update CLI** in `research_cli.py` if exposing to CLI
7. **Update client** in `research_client.py` if exposing to Python API

### Running QA Validation

```bash
# Start research server
python3 research_cli.py server-start

# Check QA statistics
python3 research_cli.py qa-stats

# Get validation queue
python3 research_cli.py qa-queue --limit 10

# Create validation run
python3 research_cli.py validation-runs-create --run-type source_quality --target-count 20

# Process validation run
python3 research_cli.py validation-runs-next --run-id 1 --validator-id "dev-test"
```

---

## Troubleshooting

### Import Errors

```bash
# Verify Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database Issues

```bash
# Check database integrity
sqlite3 unified_research.db "PRAGMA integrity_check;"

# Reset database (WARNING: deletes all data)
rm -f unified_research.db unified_research.db-*
cd research_monitor
python3 app_v2.py  # Rebuilds from filesystem
```

### Server Won't Start

```bash
# Check if port is in use
lsof -i :5558

# Kill process on port
kill -9 $(lsof -t -i:5558)

# Start with different port
RESEARCH_MONITOR_PORT=5559 python3 research_monitor/app_v2.py
```

### Tests Failing

```bash
# Run tests with verbose output
python3 -m pytest research-server/tests/ -vv

# Run single failing test
python3 -m pytest research-server/tests/test_file.py::test_name -vv

# Check for import issues
python3 -m pytest research-server/tests/ --collect-only
```

### React Build Fails

```bash
# Clear node_modules and reinstall
cd timeline/viewer
rm -rf node_modules package-lock.json
npm install

# Clear cache
npm cache clean --force

# Try build again
npm run build
```

---

## Development Best Practices

### 1. Always Write Tests

```python
# Example test structure
def test_new_feature():
    """Test description"""
    # Arrange
    client = TimelineResearchClient()

    # Act
    result = client.new_method()

    # Assert
    assert result['success'] is True
```

### 2. Use Type Hints

```python
def process_event(event_id: str) -> Dict[str, Any]:
    """Process event with type hints"""
    return {"id": event_id, "processed": True}
```

### 3. Document Code

```python
def complex_function(param1: str, param2: int) -> List[str]:
    """
    Short description of what function does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        List of results

    Raises:
        ValueError: When param2 is negative
    """
    if param2 < 0:
        raise ValueError("param2 must be positive")
    return [param1] * param2
```

### 4. Keep Commits Atomic

```bash
# Good: Single logical change
git commit -m "Add markdown parser for timeline events"

# Bad: Multiple unrelated changes
git commit -m "Add parser, fix bug, update docs, refactor utils"
```

### 5. Test Before Pushing

```bash
# Always run before pushing
python3 -m pytest research-server/tests/ -v
python3 research_cli.py server-status
cd timeline/viewer && npm run build
```

---

## Additional Resources

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Repository layout
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [CLAUDE.md](../CLAUDE.md) - AI agent instructions
- [timeline/docs/EVENT_FORMAT.md](../timeline/docs/EVENT_FORMAT.md) - Event format reference

### External Documentation

- Flask: https://flask.palletsprojects.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- React: https://react.dev/
- pytest: https://docs.pytest.org/
- mypy: https://mypy.readthedocs.io/

---

**Status**: Complete
**Last Updated**: 2025-10-17
**Maintained By**: Project Contributors
