# Repository Split Manifest

This document defines the exact file distribution for splitting this repository into two separate repositories:
1. **kleptocracy-timeline-core** - Forkable timeline + viewer
2. **kleptocracy-timeline-research-server** - Shared research infrastructure

## Repository 1: kleptocracy-timeline-core

### Purpose
Forkable timeline repository for domain-specific timeline projects. Contains event data, viewer, validation schemas, and basic tooling.

### Directory Structure
```
kleptocracy-timeline-core/
├── timeline_data/
│   └── events/              # All 1,581 event JSON files
├── viewer/                  # React-based timeline viewer
├── schemas/                 # Event validation schemas
├── api/                     # Generated static API files
├── scripts/
│   ├── generate.py          # Static API generation
│   ├── generate_csv.py      # CSV export
│   ├── generate_yaml_export.py
│   ├── validate_existing_events.py
│   ├── fix_id_mismatches.py
│   └── utils/
│       ├── events.py
│       ├── io.py
│       └── logging.py
├── .github/
│   └── workflows/           # CI/CD for viewer deployment
├── docs/
│   ├── README.md            # Getting started guide
│   ├── FORKING_GUIDE.md     # How to fork for your own timeline
│   ├── EVENT_FORMAT.md      # Event JSON schema documentation
│   └── CONTRIBUTING.md      # Contribution guidelines
├── LICENSE                  # MIT License
├── README.md                # Main project README
├── .gitignore
└── package.json             # For viewer dependencies (if needed)
```

### Files to Include

#### Root Level Files
- `LICENSE`
- `.gitignore` (filtered for core only)
- `README.md` (new, core-focused version)

#### From timeline_data/
- `timeline_data/events/*.json` (all 1,581 event files)
- **EXCLUDE**: `timeline_data/timeline_data/` (appears to be duplicate/mistake)

#### From viewer/
- `viewer/*` (entire React application)

#### From schemas/
- `schemas/*` (all validation schemas)

#### From api/
- `api/*` (generated static API files)

#### From scripts/
Include these core timeline scripts:
- `scripts/generate.py`
- `scripts/generate_csv.py`
- `scripts/generate_yaml_export.py`
- `scripts/validate_existing_events.py`
- `scripts/fix_id_mismatches.py`
- `scripts/utils/events.py`
- `scripts/utils/io.py`
- `scripts/utils/logging.py`

**EXCLUDE** these research-related scripts:
- `scripts/validation_fix_agent.py`
- `scripts/agents/*`
- `scripts/utils/update_rag_index.py`

#### From .github/
- `.github/workflows/` (GitHub Actions for CI/CD)
  - Filter to keep only viewer deployment workflows
  - Remove research server related workflows

#### From docs/
Create new documentation:
- `docs/README.md` - Getting started
- `docs/FORKING_GUIDE.md` - Step-by-step forking instructions
- `docs/EVENT_FORMAT.md` - Event schema documentation
- `docs/CONTRIBUTING.md` - How to contribute events
- `docs/VIEWER_SETUP.md` - How to run the viewer locally

**EXCLUDE** from current docs:
- Any research server documentation
- API documentation (that's for research server)

---

## Repository 2: kleptocracy-timeline-research-server

### Purpose
Shared research infrastructure providing API, MCP server, CLI tools, and database services for timeline research and enhancement. Designed to serve multiple timeline forks.

### Directory Structure
```
kleptocracy-timeline-research-server/
├── server/
│   ├── app.py                    # Main Flask application (from research_monitor/app_v2.py)
│   ├── models.py                 # Database models
│   ├── routes/                   # API routes
│   ├── services/                 # Business logic
│   ├── core/                     # Core functionality
│   └── utils/                    # Utilities
├── mcp/
│   └── mcp_server.py            # MCP (Model Context Protocol) server
├── cli/
│   └── research_cli.py          # Command-line interface
├── client/
│   └── research_client.py       # Python client library
├── api/
│   └── research_api.py          # API interface
├── n8n/
│   ├── workflows/               # Example n8n workflow templates
│   └── README.md                # n8n integration guide
├── scripts/
│   ├── agents/                  # Research agent templates
│   │   ├── research_agent_c.py
│   │   └── research_agent_d.py
│   └── utils/
│       └── update_rag_index.py
├── alembic/                      # Database migrations
├── tests/                        # Server tests
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── README.md                 # Docker deployment guide
├── docs/
│   ├── README.md                 # Getting started
│   ├── API_REFERENCE.md          # API documentation
│   ├── MCP_GUIDE.md              # MCP server usage
│   ├── TIMELINE_REGISTRATION.md  # How to register your timeline
│   ├── DEPLOYMENT.md             # Production deployment
│   └── N8N_INTEGRATION.md        # n8n workflow guide
├── .github/
│   └── workflows/                # CI/CD for server
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment configuration
├── LICENSE                       # MIT License
├── README.md
└── .gitignore
```

### Files to Include

#### Root Level Files
- `research_cli.py`
- `research_client.py`
- `research_api.py`
- `requirements.txt` (new, server-only dependencies)
- `.env.example`
- `LICENSE`
- `.gitignore` (filtered for server)
- `README.md` (new, server-focused)

#### From research_monitor/
- `research_monitor/*` (entire Flask application)
  - Rename root directory to `server/` in new repo
  - `research_monitor/app_v2.py` → `server/app.py`
  - `research_monitor/models.py` → `server/models.py`
  - `research_monitor/routes/*` → `server/routes/*`
  - `research_monitor/services/*` → `server/services/*`
  - `research_monitor/core/*` → `server/core/*`
  - `research_monitor/utils/*` → `server/utils/*`

#### From research_priorities/
- `research_priorities/*.json` (all research priority files)
  - Move to `data/research_priorities/` in new repo
  - These are server-side data, not timeline events

#### MCP Server
- `mcp_timeline_server_v2.py` → `mcp/mcp_server.py`
- **EXCLUDE**: `mcp_timeline_server.py` (older version)

#### From scripts/
Include research-related scripts:
- `scripts/agents/*` → `scripts/agents/*`
- `scripts/validation_fix_agent.py` → `scripts/validation_fix_agent.py`
- `scripts/utils/update_rag_index.py` → `scripts/utils/update_rag_index.py`

**EXCLUDE** timeline-only scripts (those go to core repo)

#### From alembic/
- `alembic/*` (all database migration files)
- `alembic.ini`

#### From tests/
- `tests/` (filter to include only server tests)
  - Include tests for research_monitor, API, MCP server
  - **EXCLUDE** viewer tests (those go to core repo)

#### Docker Configuration (NEW)
Create Docker setup:
- `docker/Dockerfile` - Multi-stage build for production
- `docker/docker-compose.yml` - Complete stack (server + PostgreSQL + Redis)
- `docker/README.md` - Docker deployment instructions

#### Documentation (NEW)
Create comprehensive server documentation:
- `docs/README.md` - Getting started with research server
- `docs/API_REFERENCE.md` - Complete API documentation
- `docs/MCP_GUIDE.md` - MCP server setup and usage
- `docs/TIMELINE_REGISTRATION.md` - How to register your timeline fork
- `docs/DEPLOYMENT.md` - Production deployment guide
- `docs/N8N_INTEGRATION.md` - n8n workflow examples
- `docs/ARCHITECTURE.md` - System architecture overview

#### n8n Workflows (NEW)
Create example n8n workflows:
- `n8n/workflows/example_research_workflow.json` - Basic research automation
- `n8n/workflows/example_qa_workflow.json` - Quality assurance automation
- `n8n/workflows/README.md` - How to import and use workflows

---

## Files That Need Decisions

### Files in Root Directory (Current Repo)
These files need review to determine which repo they belong to:

**Likely CORE timeline:**
- `build_static_site.sh` - Builds static viewer

**Likely RESEARCH SERVER:**
- `add_expansion_priorities.py` - Research priorities
- `add_research_priorities.py` - Research priorities
- `create_doj_weaponization_events.py` - Research agent
- `create_fed_corruption_events_fixed.py` - Research agent
- `create_fed_corruption_events.py` - Research agent
- `improved_research_agent_template.py` - Research agent template
- `orchestrator_server_manager.py` - Server management
- `populate_validation_run_13.py` - QA system
- `process_ttt_batch6.py` - Research processing
- `submit_cyber_mercenary_events.py` - Research agent
- `submit_truth_social_spac_events.py` - Research agent
- `summarize_priorities.py` - Research priorities
- `sync_priority_status.py` - Research priorities
- `test_api_workflow.py` - API testing
- `test_campaign_finance_research.py` - Research testing
- `tiered_orchestrator.py` - Orchestration
- `timeline_event_manager.py` - Event management
- `validate_event.py` - Event validation
- `validation_workflow.py` - Validation system

**ARCHIVE or EXCLUDE:**
- `all_python_files.txt` - Development artifact
- Files in `archive/` - Historical, keep in current repo only

### Directories That Need Decisions

**utils/** - Need to split:
- Timeline utilities → CORE
- Research utilities → RESEARCH SERVER

**tests/** - Need to split:
- Viewer tests → CORE
- Server tests → RESEARCH SERVER
- Integration tests → Both? Or RESEARCH SERVER?

**validation_reports/** - Likely RESEARCH SERVER or ARCHIVE

**htmlcov/**, **coverage_html/** - Development artifacts, exclude from both

---

## Migration Strategy

### Phase 1: Preparation (Current Branch)
1. Create this manifest
2. Review and finalize file assignments
3. Create migration scripts to automate the split

### Phase 2: Create Core Repository
1. Create new empty repo: `kleptocracy-timeline-core`
2. Copy files according to manifest
3. Update README.md for core focus
4. Update .gitignore for core files only
5. Create new documentation (FORKING_GUIDE.md, etc.)
6. Test viewer deployment
7. Commit and push

### Phase 3: Create Research Server Repository
1. Create new empty repo: `kleptocracy-timeline-research-server`
2. Copy files according to manifest
3. Rename `research_monitor/` → `server/`
4. Update all import paths
5. Create Docker configuration
6. Create n8n workflow examples
7. Create comprehensive documentation
8. Test server deployment
9. Commit and push

### Phase 4: Update Original Repository
1. Add README redirect explaining the split
2. Archive old structure
3. Update CLAUDE.md to point to new repositories
4. Add deprecation notice

### Phase 5: Integration Testing
1. Test core timeline viewer standalone
2. Test research server with multiple timeline forks
3. Test MCP server integration
4. Test n8n workflow examples
5. Document any issues

---

## Success Criteria

### For Core Repository:
- [ ] Viewer runs with `npm start` or `npm run dev`
- [ ] Event validation works: `python3 scripts/validate_existing_events.py`
- [ ] Static API generation works: `python3 scripts/generate.py`
- [ ] CSV export works: `python3 scripts/generate_csv.py`
- [ ] Can be forked and customized easily
- [ ] Documentation is clear for new users
- [ ] GitHub Actions deploy viewer to GitHub Pages

### For Research Server Repository:
- [ ] Server starts with `python3 server/app.py`
- [ ] CLI tool works: `python3 cli/research_cli.py help`
- [ ] MCP server starts: `python3 mcp/mcp_server.py`
- [ ] API endpoints respond correctly
- [ ] Docker deployment works: `docker-compose up`
- [ ] Timeline registration API functional
- [ ] n8n workflows can be imported
- [ ] Documentation is comprehensive
- [ ] Can serve multiple timeline forks simultaneously

---

## Notes

### Git History
- Both new repositories will start with clean history (no git history from original repo)
- Original repository will remain intact as archive
- This allows clean separation and smaller repository sizes

### Dependencies
- Core repo: Minimal dependencies (React, validation libraries)
- Research server: Full dependencies (Flask, SQLAlchemy, etc.)
- This separation keeps core timeline lightweight

### Timeline Data Location
- Core repo: `timeline_data/events/` (authoritative source)
- Research server: Syncs from registered timeline repos via git webhooks
- Research server does NOT store timeline events, only metadata

### Future Extensibility
- Core timeline can be forked unlimited times
- Research server remains centralized (but can be self-hosted)
- MCP protocol allows other tools to integrate
- n8n workflows allow custom automation

---

## Open Questions

1. **Should research_priorities stay in core or move to server?**
   - Current thinking: Move to server (they're research metadata, not timeline events)

2. **Should we preserve any git history?**
   - Current thinking: No, start fresh for cleaner repos

3. **What about the nested timeline_data/timeline_data/?**
   - Current thinking: Remove it, appears to be error

4. **Should tests be included in both repos?**
   - Current thinking: Split tests between repos based on what they test

5. **What license for both repos?**
   - Current thinking: MIT for both (current license)

6. **Should Docker be included in core for viewer?**
   - Current thinking: Optional, GitHub Pages is primary deployment

7. **Where should CLAUDE.md live?**
   - Current thinking: Update in both repos, customized for each
