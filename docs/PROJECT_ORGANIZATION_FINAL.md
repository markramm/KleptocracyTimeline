# Project Organization - Final Cleanup Plan

**Date**: 2025-10-17
**Status**: Ready for Execution
**Goal**: Complete repository organization and prepare for production deployment

## Current State Analysis

### ✅ Completed Work
1. **Repository Restructuring**: `timeline/` and `research-server/` directories created
2. **Markdown Event Format**: Complete implementation with 86% test coverage
3. **Research Infrastructure**: Research Monitor v2, CLI, MCP server all operational
4. **Documentation**: Comprehensive guides created in multiple locations

### 🔴 Remaining Issues

#### 1. Root Directory Clutter
**Problem**: 24 Python files and 21 Markdown files in root directory

**Python Files to Archive**:
```
archive/one_time_scripts/ (destination for deprecated scripts)
├── add_expansion_priorities.py           # Legacy - priorities now in research-server/
├── add_research_priorities.py            # Legacy - priorities now in research-server/
├── create_doj_weaponization_events.py    # One-time event creation script
├── create_fed_corruption_events_fixed.py # One-time event creation script
├── create_fed_corruption_events.py       # One-time event creation script
├── improved_research_agent_template.py   # Legacy - templates in agent_configs/
├── mcp_timeline_server.py                # Legacy - replaced by v2
├── orchestrator_server_manager.py        # Legacy - no longer used
├── populate_validation_run_13.py         # One-time validation run script
├── process_ttt_batch6.py                 # One-time batch processing script
├── submit_cyber_mercenary_events.py      # One-time event creation script
├── submit_truth_social_spac_events.py    # One-time event creation script
├── summarize_priorities.py               # Legacy - functionality in CLI
├── sync_priority_status.py               # Legacy - functionality in CLI
├── test_api_workflow.py                  # Legacy test script
├── test_campaign_finance_research.py     # Legacy test script
├── tiered_orchestrator.py                # Legacy orchestrator
└── validation_workflow.py                # Legacy - replaced by CLI
```

**Python Files to Keep in Root** (production tools):
```
/
├── research_cli.py                       # PRIMARY CLI TOOL
├── research_client.py                    # PRIMARY CLIENT LIBRARY
├── research_api.py                       # CORE API MODULE
└── mcp_timeline_server_v2.py             # PRODUCTION MCP SERVER
```

**Markdown Files - Consolidation Plan**:
```
docs/ (destination for documentation)
├── PROJECT_STATUS_FINAL.md               # Consolidate all PROJECT_STATUS_*.md
├── QA_WORKFLOW_COMPLETE.md               # Consolidate QA_*.md files
├── TESTING_GUIDE.md                      # Consolidate TEST_*.md files
├── DEVELOPMENT_HISTORY.md                # Archive older status files
│
archive/outdated_docs/ (deprecated docs)
├── COST_TRACKING.md                      # Outdated - GoFundMe not pursued
├── EVENTS_NEEDING_SOURCES_UPDATED.md     # Outdated list
├── GIT_SERVICE_DESIGN.md                 # Design doc - archive
├── IMPROVEMENT_PLAN.md                   # Superseded
├── IMPROVEMENT_QUICKSTART.md             # Superseded
├── METRICS.md                            # Outdated metrics
├── PR_PATCH_GENERATION_SYSTEM.md         # Unimplemented design
├── PROJECT_HYGIENE_EVALUATION.md         # Historical evaluation
├── VALIDATION_RUN_12_SUMMARY.md          # Historical report
└── WEB_UI_VALIDATION_DESIGN.md           # Unimplemented design
```

**Markdown Files to Keep in Root** (essential documentation):
```
/
├── README.md                             # PROJECT ROOT README
├── CLAUDE.md                             # AI AGENT INSTRUCTIONS
├── CONTRIBUTING.md                       # CONTRIBUTOR GUIDE
├── SECURITY.md                           # SECURITY POLICY
└── IN_MEMORIAM.md                        # DEDICATION
```

#### 2. Duplicate Directories
**Problem**: Overlapping directory structures

**Duplicates to Archive**:
```
- timeline_data/timeline_data/  → Should be timeline_data/ only
- api/ (root)                   → Content in timeline/public/api/
- research_monitor/ (root)      → Migrated to research-server/server/
- research_priorities/ (root)   → Should be in research-server/data/
- viewer/ (root)                → Migrated to timeline/viewer/
- schemas/ (root)               → Migrated to timeline/schemas/
- scripts/ (root)               → Split between timeline/ and research-server/
```

#### 3. Configuration Files
**Current**: Multiple config files scattered in root
**Needed**: Consolidate and document

```
/
├── .gitignore                            # KEEP - root ignore rules
├── pytest.ini                            # KEEP - test configuration
├── mypy.ini                              # KEEP - type checking
├── alembic.ini                           # MOVE → research-server/
├── mcp_config.json                       # MOVE → research-server/mcp/
├── mcp_config_v2.json                    # MOVE → research-server/mcp/
├── mcp_requirements.txt                  # MOVE → research-server/mcp/
├── requirements.txt                      # KEEP - root dependencies
└── requirements-test.txt                 # KEEP - test dependencies
```

#### 4. Database Files
**Current**: Multiple database files in root
**Action**: Keep unified_research.db in root, document clearly

```
/
├── unified_research.db                   # KEEP - primary database
├── unified_research.db-shm               # KEEP - SQLite shared memory
├── unified_research.db-wal               # KEEP - SQLite write-ahead log
└── .gitignore                            # Already ignores *.db files
```

## Cleanup Execution Plan

### Phase 1: Archive Deprecated Scripts ✅ Ready
```bash
# Create archive directories if needed
mkdir -p archive/one_time_scripts
mkdir -p archive/outdated_docs

# Move deprecated Python scripts
mv add_expansion_priorities.py archive/one_time_scripts/
mv add_research_priorities.py archive/one_time_scripts/
mv create_doj_weaponization_events.py archive/one_time_scripts/
mv create_fed_corruption_events*.py archive/one_time_scripts/
mv improved_research_agent_template.py archive/one_time_scripts/
mv mcp_timeline_server.py archive/one_time_scripts/
mv orchestrator_server_manager.py archive/one_time_scripts/
mv populate_validation_run_13.py archive/one_time_scripts/
mv process_ttt_batch6.py archive/one_time_scripts/
mv submit_*_events.py archive/one_time_scripts/
mv summarize_priorities.py archive/one_time_scripts/
mv sync_priority_status.py archive/one_time_scripts/
mv test_api_workflow.py archive/one_time_scripts/
mv test_campaign_finance_research.py archive/one_time_scripts/
mv tiered_orchestrator.py archive/one_time_scripts/
mv validation_workflow.py archive/one_time_scripts/
mv timeline_event_manager.py archive/one_time_scripts/
```

### Phase 2: Consolidate Documentation
```bash
# Move outdated docs to archive
mv COST_TRACKING.md archive/outdated_docs/
mv EVENTS_NEEDING_SOURCES_UPDATED.md archive/outdated_docs/
mv GIT_SERVICE_DESIGN.md archive/outdated_docs/
mv IMPROVEMENT_PLAN.md archive/outdated_docs/
mv IMPROVEMENT_QUICKSTART.md archive/outdated_docs/
mv METRICS.md archive/outdated_docs/
mv PR_PATCH_GENERATION_SYSTEM.md archive/outdated_docs/
mv PROJECT_HYGIENE_EVALUATION.md archive/outdated_docs/
mv VALIDATION_RUN_12_SUMMARY.md archive/outdated_docs/
mv WEB_UI_VALIDATION_DESIGN.md archive/outdated_docs/

# Consolidate project status files
mv PROJECT_STATUS_2025.md archive/outdated_docs/
mv PROJECT_STATUS_2025-10-16.md archive/outdated_docs/

# Consolidate test documentation
mv TEST_PLAN_UPDATED.md archive/outdated_docs/
```

### Phase 3: Move Configuration Files
```bash
# Move MCP config to research-server
mv alembic.ini research-server/
mv mcp_config*.json research-server/mcp/
mv mcp_requirements.txt research-server/mcp/
```

### Phase 4: Clean Up Duplicate Directories
```bash
# Archive duplicate structures (after verifying migrations complete)
# NOTE: Only execute after verifying timeline/ and research-server/ have all needed files

# Verify first, then archive:
# mv research_monitor/ archive/legacy_apps_20251017/
# mv api/ archive/legacy_apps_20251017/
```

### Phase 5: Update Documentation
Create consolidated documentation in `docs/`:
- `docs/PROJECT_STRUCTURE.md` - Current repository layout
- `docs/DEPLOYMENT_GUIDE.md` - Production deployment instructions
- `docs/DEVELOPMENT_SETUP.md` - Developer onboarding guide

## Final Directory Structure

```
kleptocracy-timeline/
├── README.md                     # Root README explaining project
├── CLAUDE.md                     # AI agent instructions
├── CONTRIBUTING.md               # Contributor guide
├── SECURITY.md                   # Security policy
├── IN_MEMORIAM.md                # Dedication
├── LICENSE-MIT                   # Code license
├── LICENSE-DATA                  # Data license
│
├── .gitignore                    # Git ignore rules
├── pytest.ini                    # Test configuration
├── mypy.ini                      # Type checking
├── requirements.txt              # Root dependencies
├── requirements-test.txt         # Test dependencies
│
├── research_cli.py               # PRIMARY CLI TOOL
├── research_client.py            # PRIMARY CLIENT LIBRARY
├── research_api.py               # CORE API MODULE
├── mcp_timeline_server_v2.py     # PRODUCTION MCP SERVER
│
├── unified_research.db           # Primary database
│
├── timeline/                     # Timeline data + viewer
│   ├── data/events/              # 1,590 event files
│   ├── viewer/                   # React viewer
│   ├── schemas/                  # Validation schemas
│   ├── scripts/                  # Timeline utilities
│   ├── docs/                     # Timeline documentation
│   ├── public/api/               # Static API
│   └── README.md
│
├── research-server/              # Research infrastructure
│   ├── server/                   # Flask API
│   ├── mcp/                      # MCP server
│   ├── cli/                      # CLI tools
│   ├── client/                   # Python client
│   ├── data/                     # Research priorities
│   ├── scripts/                  # Research utilities
│   ├── tests/                    # Server tests
│   ├── alembic/                  # Database migrations
│   ├── docs/                     # Server documentation
│   ├── alembic.ini               # DB migration config
│   └── README.md
│
├── docs/                         # Shared documentation
│   ├── PROJECT_STRUCTURE.md      # Repository layout
│   ├── DEPLOYMENT_GUIDE.md       # Production deployment
│   ├── DEVELOPMENT_SETUP.md      # Developer setup
│   └── (consolidated docs)
│
├── archive/                      # Deprecated code
│   ├── one_time_scripts/         # Historical scripts
│   ├── outdated_docs/            # Old documentation
│   ├── legacy_apps_20251017/     # Migrated applications
│   └── rejected_events/          # Archived events
│
├── specs/                        # Technical specifications
│   ├── 001-extract-routes/
│   └── 002-markdown-event-format/
│
└── tests/                        # Integration tests
```

## Production Readiness Checklist

### Code Organization ✅
- [x] timeline/ directory structure complete
- [x] research-server/ directory structure complete
- [ ] Root directory cleaned up
- [ ] Deprecated scripts archived
- [ ] Configuration files organized
- [ ] Documentation consolidated

### Testing ✅
- [x] 86% test coverage for markdown parser
- [x] 45/45 tests passing
- [x] Integration tests passing
- [x] Research server operational
- [x] CLI tools functional

### Documentation 📝
- [x] README.md comprehensive
- [x] CONTRIBUTING.md with markdown guide
- [x] CLAUDE.md for AI agents
- [ ] PROJECT_STRUCTURE.md (new)
- [ ] DEPLOYMENT_GUIDE.md (new)
- [ ] DEVELOPMENT_SETUP.md (new)

### Deployment 🚀
- [ ] GitHub Pages configuration
- [ ] CI/CD pipeline setup
- [ ] Production database backup strategy
- [ ] Monitoring and logging setup
- [ ] SSL certificates configured

### Security 🔒
- [x] SECURITY.md present
- [ ] Secret management documented
- [ ] API authentication configured
- [ ] Rate limiting implemented
- [ ] Backup procedures documented

## Estimated Timeline

- **Phase 1-3 (Cleanup)**: 1-2 hours
- **Phase 4 (Verification)**: 1 hour
- **Phase 5 (Documentation)**: 2-3 hours
- **Total**: 4-6 hours

## Success Criteria

✅ Root directory contains only:
- Essential documentation (5 files)
- Core tools (4 Python files)
- Configuration files (5 files)
- Database files (3 files)
- Subdirectories (timeline/, research-server/, docs/, archive/, specs/, tests/)

✅ All deprecated code archived and documented

✅ Documentation consolidated and comprehensive

✅ All tests passing

✅ Research server operational

✅ Ready for production deployment

## Next Steps

1. **Execute Phase 1-3** - Clean up root directory
2. **Create consolidated documentation** - Write PROJECT_STRUCTURE.md, DEPLOYMENT_GUIDE.md
3. **Test everything** - Verify no broken imports or paths
4. **Commit cleanup** - Create clean commit with organized structure
5. **Deploy** - Configure GitHub Pages and production environment

---

**Implementation Date**: 2025-10-17
**Status**: Ready for Execution
**Estimated Completion**: Same day (4-6 hours)
