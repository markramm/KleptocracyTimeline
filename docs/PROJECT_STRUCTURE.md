# Project Structure

**Last Updated**: 2025-10-17

## Overview

The Kleptocracy Timeline repository is organized into two main components:

1. **timeline/** - Timeline data and viewer (for public access and forking)
2. **research-server/** - Research infrastructure (for contributors and AI agents)

This document describes the complete repository structure and the purpose of each component.

## Root Directory

```
kleptocracy-timeline/
├── README.md                     # Project overview and quick start
├── CLAUDE.md                     # AI agent instructions (comprehensive)
├── CONTRIBUTING.md               # Contributor guide
├── SECURITY.md                   # Security policy
├── IN_MEMORIAM.md                # Dedication
│
├── research_cli.py               # PRIMARY CLI TOOL for research workflows
├── research_client.py            # PRIMARY CLIENT LIBRARY (Python API)
├── research_api.py               # CORE API MODULE
├── mcp_timeline_server_v2.py     # PRODUCTION MCP SERVER (for n8n/AI integration)
│
├── unified_research.db           # Primary SQLite database
├── unified_research.db-shm       # SQLite shared memory file
├── unified_research.db-wal       # SQLite write-ahead log
│
├── pytest.ini                    # Test configuration
├── mypy.ini                      # Type checking configuration
├── requirements.txt              # Root dependencies
├── requirements-test.txt         # Test dependencies
├── .gitignore                    # Git ignore rules
│
├── timeline/                     # Timeline data + viewer
├── research-server/              # Research infrastructure
├── docs/                         # Shared documentation
├── archive/                      # Deprecated code and docs
├── specs/                        # Technical specifications
└── tests/                        # Integration tests
```

### Root-Level Production Tools

**research_cli.py** - Command-line interface for all research operations
- Event search, creation, validation
- Research priority management
- QA workflow commands
- Server management
- Validation runs system
- Returns structured JSON for scripting

**research_client.py** - Python client library
- 40+ methods for programmatic access
- Used by CLI and scripts
- Full API coverage
- Built-in help system

**research_api.py** - Core API module
- Helper functions for API interactions
- Used by research_client.py

**mcp_timeline_server_v2.py** - Model Context Protocol server
- Enables AI integration (Claude, n8n)
- Provides tool-based event access
- Production-ready MCP implementation

## Timeline Directory

```
timeline/
├── data/
│   ├── events/                   # 1,590 timeline event files (.json and .md)
│   └── timeline_data/            # Legacy symlink (to be removed)
│
├── viewer/                       # React-based interactive timeline viewer
│   ├── src/                      # React components
│   ├── public/                   # Static assets
│   ├── package.json              # Node dependencies
│   └── build/                    # Built static site (generated)
│
├── public/
│   └── api/                      # Generated static API files
│       ├── timeline.json         # All events (4.3 MB)
│       ├── actors.json           # Actor index
│       ├── tags.json             # Tag index
│       └── stats.json            # Statistics
│
├── scripts/                      # Timeline utilities
│   ├── generate.py               # Generate static API files
│   ├── generate_csv.py           # Export to CSV
│   ├── validate_events.py        # Multi-format event validation
│   ├── convert_to_markdown.py    # JSON → Markdown converter
│   └── utils/                    # Shared utilities
│
├── schemas/                      # JSON Schema validation
│   └── event_schema.json
│
├── docs/                         # Timeline documentation
│   ├── EVENT_FORMAT.md           # Complete format reference (JSON + Markdown)
│   └── ...
│
├── package.json                  # Timeline-specific Node config
└── README.md                     # Timeline-specific README
```

### Event Formats

**JSON Format** (`.json`):
```json
{
  "id": "2025-01-15--event-slug",
  "date": "2025-01-15",
  "title": "Event Title",
  "summary": "Event description...",
  "importance": 8,
  "tags": ["regulatory-capture"],
  "actors": ["Person Name"],
  "sources": [...]
}
```

**Markdown Format** (`.md`):
```markdown
---
id: 2025-01-15--event-slug
date: 2025-01-15
title: Event Title
importance: 8
tags:
  - regulatory-capture
actors:
  - Person Name
sources:
  - title: Source Title
    url: https://...
---

Event description with **markdown formatting** supported.
```

Both formats are fully equivalent and parsed by the same infrastructure.

## Research Server Directory

```
research-server/
├── server/                       # Flask REST API
│   ├── app_v2.py                 # Main Flask application
│   ├── models.py                 # SQLAlchemy models
│   ├── routes/                   # API route handlers
│   ├── services/                 # Business logic
│   ├── parsers/                  # Multi-format event parsers
│   │   ├── json_parser.py
│   │   ├── markdown_parser.py
│   │   └── factory.py
│   └── utils/                    # Utilities
│
├── mcp/                          # Model Context Protocol server
│   ├── mcp_server.py             # MCP server implementation
│   ├── mcp_config.json           # MCP configuration
│   ├── mcp_config_v2.json        # Updated config
│   └── mcp_requirements.txt      # MCP dependencies
│
├── cli/                          # CLI tools (future dedicated directory)
├── client/                       # Python client (future dedicated directory)
│
├── data/                         # Research data
│   └── research_priorities/      # Research priority JSON files
│
├── scripts/                      # Research utilities
│   └── agents/                   # AI agent scripts
│
├── tests/                        # Comprehensive test suite
│   ├── test_markdown_parser.py   # Markdown parser tests (21 tests)
│   ├── test_parser_factory.py    # Parser factory tests (17 tests)
│   ├── test_research_client.py   # Client tests (142 tests)
│   └── ...                       # 218 total tests, 86%+ coverage
│
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration scripts
│   └── env.py
│
├── docs/                         # Server documentation
│
├── alembic.ini                   # Database migration config
├── requirements.txt              # Server dependencies
└── README.md                     # Server-specific README
```

## Documentation Directory

```
docs/
├── PROJECT_STRUCTURE.md          # This file - repository layout
├── PROJECT_ORGANIZATION_FINAL.md # Cleanup plan and execution record
├── DEPLOYMENT_GUIDE.md           # Production deployment instructions
├── DEVELOPMENT_SETUP.md          # Developer onboarding
│
├── system_design/                # System architecture docs
│   ├── DATABASE_MIGRATIONS.md
│   ├── EXCEPTION_HANDLING_GUIDE.md
│   └── ...
│
├── agent_setup/                  # AI agent setup guides
│
├── QA_WORKFLOW.md                # Quality assurance processes
├── SOURCE_QUALITY.md             # Source evaluation criteria
├── TAG_TAXONOMY.md               # Tag categorization system
│
└── (various analysis reports)
```

## Archive Directory

```
archive/
├── one_time_scripts/             # Historical scripts (18 files)
│   ├── add_expansion_priorities.py
│   ├── create_*_events.py        # One-time event creation
│   ├── mcp_timeline_server.py    # Legacy MCP (replaced by v2)
│   └── ...
│
├── outdated_docs/                # Deprecated documentation (14 files)
│   ├── PROJECT_STATUS_2025*.md   # Historical status reports
│   ├── TEST_*.md                 # Old test plans
│   ├── COST_TRACKING.md          # Abandoned GoFundMe plan
│   └── ...
│
├── legacy_apps_20251016/         # Migrated applications
├── old_databases_20251015/       # Database backups
├── rejected_events/              # Archived timeline events
├── reports/                      # Historical reports
└── tests/                        # Old test infrastructure
```

## Specs Directory

```
specs/
├── 001-extract-routes/           # Route extraction specification
└── 002-markdown-event-format/    # Markdown format implementation
    ├── IMPLEMENTATION_REPORT.md  # Complete implementation documentation
    └── ...
```

## Tests Directory

```
tests/
├── fixtures/                     # Test data
├── scripts/                      # Test utilities
└── __pycache__/                  # Python bytecode cache
```

## Key Design Principles

### 1. Separation of Concerns
- **timeline/** contains all public-facing data and viewer
- **research-server/** contains all contributor/research tools
- Both can be deployed independently

### 2. Multi-Format Support
- Events can be JSON or Markdown
- Single parser infrastructure handles both
- Zero breaking changes to existing JSON events

### 3. Filesystem-Authoritative Events
- Timeline events stored as files in `timeline/data/events/`
- Database is read-only sync for search performance
- Files are source of truth, database is cache

### 4. Database-Authoritative Research
- Research priorities stored in database
- Can export to JSON for backup
- Supports full CRUD operations

### 5. CLI-First Tooling
- All operations available via `research_cli.py`
- Returns structured JSON for scripting
- Human-readable help system

### 6. Progressive Enhancement
- New features don't break existing workflows
- Backward compatibility maintained
- Markdown format added without disrupting JSON

## File Counts

- **Timeline Events**: 1,590 files (1,580 JSON + 10 Markdown)
- **Python Scripts**: 4 production tools in root
- **Documentation**: 5 essential docs in root
- **Tests**: 218 automated tests (86%+ coverage)
- **Research Priorities**: 100+ JSON files
- **Archived Scripts**: 18 files (one-time use)
- **Archived Docs**: 14 files (outdated)

## Common Operations

### Running the Timeline Viewer
```bash
cd timeline/viewer
npm install
npm start
```

### Starting the Research Server
```bash
cd research-monitor
python3 app_v2.py
# Or use CLI: python3 research_cli.py server-start
```

### Using the CLI
```bash
# Search events
python3 research_cli.py search-events --query "Trump crypto"

# Create event
python3 research_cli.py create-event --file event.json

# Get QA queue
python3 research_cli.py qa-queue --limit 10
```

### Running Tests
```bash
# All tests from root
python3 -m pytest research-server/tests/ -v

# Specific test suite
python3 -m pytest research-server/tests/test_markdown_parser.py -v

# With coverage
python3 -m pytest research-server/tests/ --cov=research-server/server/parsers
```

### Generating Static API
```bash
cd timeline/scripts
python3 generate.py
```

## Dependencies

### Timeline Dependencies
- Node.js + npm (for React viewer)
- Python 3.9+ (for scripts)
- Basic Python packages (json, csv, pathlib)

### Research Server Dependencies
- Python 3.9+
- Flask (web server)
- SQLAlchemy (database ORM)
- pytest (testing)
- python-frontmatter (markdown parsing)
- PyYAML (YAML parsing)
- See `research-server/requirements.txt` for complete list

### Development Dependencies
- pytest + pytest-cov (testing)
- mypy (type checking)
- See `requirements-test.txt` for complete list

## Environment Variables

### Research Server
- `RESEARCH_MONITOR_PORT` - Port for Flask server (default: 5558)
- `DATABASE_URL` - SQLite database path (default: unified_research.db)

### Timeline Viewer
- `PUBLIC_URL` - Base URL for GitHub Pages deployment
- `REACT_APP_API_URL` - API endpoint URL

## Related Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment
- [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) - Developer onboarding
- [timeline/docs/EVENT_FORMAT.md](../timeline/docs/EVENT_FORMAT.md) - Event format reference
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [CLAUDE.md](../CLAUDE.md) - AI agent instructions

---

**Status**: ✅ Production Ready
**Last Cleanup**: 2025-10-17
**Version**: 2.0 (Post-restructuring)
