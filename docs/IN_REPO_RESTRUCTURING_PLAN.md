# In-Repo Restructuring Plan

**Goal**: Reorganize current repository into two clean directory structures before book launch (~1 month)

## Target Structure

```
kleptocracy-timeline/
├── timeline/                    # Timeline data + static viewer (for book URLs)
│   ├── data/
│   │   └── events/             # All 1,581 event JSON files
│   ├── viewer/                 # React viewer app
│   ├── schemas/                # Event validation schemas
│   ├── scripts/                # Timeline utilities
│   │   ├── generate_static_api.py
│   │   ├── generate_csv.py
│   │   └── validate_events.py
│   ├── docs/                   # Timeline documentation
│   ├── public/                 # Static site output (GitHub Pages)
│   │   └── api/                # Generated JSON API
│   ├── README.md
│   └── package.json
│
├── research-server/             # Research infrastructure
│   ├── server/                 # Flask API (from research_monitor/)
│   ├── mcp/                    # MCP server
│   ├── cli/                    # CLI tools
│   ├── client/                 # Python client library
│   ├── data/
│   │   └── research_priorities/  # Research priority files
│   ├── scripts/                # Research agent scripts
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Server tests
│   ├── docs/                   # Research server docs
│   ├── requirements.txt
│   └── README.md
│
├── docs/                        # Shared/root documentation
├── .github/                     # GitHub Actions (both)
├── README.md                    # Root README explaining structure
├── LICENSE
└── .gitignore
```

## Book Launch URLs

After restructuring, the static viewer will be at:
- **Production**: `https://username.github.io/kleptocracy-timeline/` (from `timeline/public/`)
- **Development**: Run locally from `timeline/viewer/`

Events will be at clean paths:
- `timeline/data/events/YYYY-MM-DD--event-slug.json`

## Migration Strategy

### Phase 1: Create New Structure (Now)
1. Create `timeline/` directory with subdirectories
2. Create `research-server/` directory with subdirectories
3. Keep originals in place (don't move yet)

### Phase 2: Copy Timeline Files
1. Copy `timeline_data/events/` → `timeline/data/events/`
2. Copy `viewer/` → `timeline/viewer/`
3. Copy `schemas/` → `timeline/schemas/`
4. Copy relevant scripts → `timeline/scripts/`
5. Create `timeline/README.md`
6. Update `timeline/viewer/` to reference new paths

### Phase 3: Copy Research Server Files
1. Copy `research_monitor/` → `research-server/server/`
2. Copy `mcp_timeline_server_v2.py` → `research-server/mcp/`
3. Copy `research_cli.py` → `research-server/cli/`
4. Copy `research_client.py` → `research-server/client/`
5. Copy `research_api.py` → `research-server/client/`
6. Copy `research_priorities/` → `research-server/data/research_priorities/`
7. Copy `alembic/` → `research-server/alembic/`
8. Create `research-server/README.md`
9. Update all import paths

### Phase 4: Update References
1. Update GitHub Actions to use new paths
2. Update documentation
3. Update .gitignore for new structure
4. Test both timeline viewer and research server

### Phase 5: Cleanup (After Testing)
1. Remove old directory structure
2. Clean up root directory
3. Update all documentation
4. Final testing

### Phase 6: Deploy for Book
1. Configure GitHub Pages from `timeline/public/`
2. Test all book URLs
3. Document URLs for book inclusion
4. Final validation

## Implementation Script

We'll create a script that:
1. Creates new directory structure
2. Copies files with path updates
3. Validates both sides work
4. Provides rollback capability

## Timeline

- **Week 1**: Create structure, copy files, update paths
- **Week 2**: Test both sides, fix issues
- **Week 3**: Cleanup old structure, documentation
- **Week 4**: Deploy static site, finalize book URLs

## Rollback Plan

Keep original structure until:
- Both timeline and research-server work independently
- All tests pass
- GitHub Pages deployment works

Then commit and remove old structure.
