# Kleptocracy Timeline - Research Server

Research infrastructure for timeline enhancement, validation, and multi-timeline support.

## Quick Start

### Start Server

```bash
cd server
RESEARCH_MONITOR_PORT=5558 python3 app_v2.py
```

### Use CLI

```bash
cd cli
python3 research_cli.py help
python3 research_cli.py search-events --query "Trump"
```

### Use Python Client

```python
from client.research_client import TimelineResearchClient

client = TimelineResearchClient()
events = client.search_events("surveillance")
```

## Directory Structure

```
research-server/
├── server/                  # Flask REST API
├── mcp/                     # MCP server for LLM integration
├── cli/                     # CLI tools
├── client/                  # Python client library
├── data/
│   └── research_priorities/ # Research priority files
├── scripts/
│   └── agents/             # Research agent scripts
├── alembic/                # Database migrations
├── tests/                  # Server tests
└── docs/                   # Research server documentation
```

## Features

- REST API for timeline event management
- MCP server for Claude Code integration
- CLI tools for research workflows
- Quality assurance system
- Multi-timeline support (planned)
- Research priority tracking

## Database

SQLite database with automatic sync from timeline event files.

## License

MIT License
