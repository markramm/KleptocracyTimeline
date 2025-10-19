# SPEC-002: Consolidate Duplicate Documentation

**Status**: Ready
**Priority**: Critical
**Estimated Time**: 30 minutes
**Risk**: Low

## Problem

API documentation exists in 3 locations:
1. `research-server/server/API_DOCUMENTATION.md`
2. `research-server/server/static/API_DOCUMENTATION.md`
3. References in various README files

Additionally:
- `ARCHITECTURE.md` has outdated information (port 5555 vs 5558)
- Documentation is not version-controlled properly
- No single source of truth

## Goal

Consolidate all documentation to single canonical locations and remove duplicates.

## Success Criteria

- [ ] Single API documentation file exists
- [ ] All duplicate documentation removed
- [ ] ARCHITECTURE.md updated with current information
- [ ] All references updated to point to canonical locations
- [ ] Documentation is accurate and current

## Current State

```
research-server/
├── server/
│   ├── API_DOCUMENTATION.md        # ❌ Duplicate 1
│   ├── ARCHITECTURE.md             # ⚠️ Outdated (port 5555)
│   └── static/
│       └── API_DOCUMENTATION.md    # ❌ Duplicate 2
├── README.md                       # ⚠️ References both
└── docs/                           # ❓ Not used
```

## Target State

```
research-server/
├── docs/
│   ├── API.md                      # ✅ Single API reference
│   ├── ARCHITECTURE.md             # ✅ Moved and updated
│   ├── CLI.md                      # ✅ CLI reference (from CLAUDE.md)
│   └── MCP.md                      # ✅ MCP server docs
├── server/
│   └── (no documentation files)
├── README.md                       # ✅ References docs/
└── CHANGELOG.md                    # ✅ Version history
```

## Implementation Steps

### Step 1: Create Consolidated Docs Directory

```bash
cd research-server
mkdir -p docs
```

### Step 2: Consolidate API Documentation

Compare the two API documentation files:
```bash
diff server/API_DOCUMENTATION.md server/static/API_DOCUMENTATION.md
```

Choose the most complete version or merge them:

```bash
# Copy the most complete version
cp server/API_DOCUMENTATION.md docs/API.md

# Or merge manually if both have unique content
# Review both files and create comprehensive docs/API.md
```

**Content to Include**:
- All endpoints with request/response examples
- Authentication requirements
- Error codes and handling
- Rate limiting (if any)
- Versioning information

### Step 3: Move and Update ARCHITECTURE.md

```bash
# Copy to docs and update
cp server/ARCHITECTURE.md docs/ARCHITECTURE.md
```

Update the following in `docs/ARCHITECTURE.md`:
- Change port 5555 → 5558
- Update directory structure to match current state
- Add validation runs system documentation
- Update component descriptions
- Fix any other outdated information

**Key Updates**:
```markdown
# Before
Research Monitor (Port 5555)

# After
Research Monitor (Port 5558)
```

### Step 4: Extract CLI Documentation

Create `docs/CLI.md` by extracting relevant sections from `CLAUDE.md`:

```bash
# Create new CLI documentation
touch docs/CLI.md
```

**Content to Include**:
- CLI wrapper usage (`./research`)
- All available commands with examples
- Environment variables
- Configuration options
- Troubleshooting

### Step 5: Create MCP Documentation

If MCP server documentation exists, consolidate it:

```bash
# Check if MCP docs exist
find research-server -name "*mcp*" -name "*.md"

# Create MCP docs
touch docs/MCP.md
```

### Step 6: Remove Duplicate Files

```bash
cd research-server

# Remove duplicates
rm server/API_DOCUMENTATION.md
rm server/static/API_DOCUMENTATION.md
rm server/ARCHITECTURE.md  # Moved to docs/

# Verify removal
find server -name "*.md"  # Should not show API_DOCUMENTATION or ARCHITECTURE
```

### Step 7: Update References

Update all files that reference the old documentation locations:

```bash
# Find all references
grep -r "API_DOCUMENTATION\|ARCHITECTURE" research-server/ --include="*.md" --include="*.py"
```

Update references in:
- `research-server/README.md`
- Root `README.md`
- `INSTALLATION.md`
- Any Python files with docstring references

**Example Updates**:
```markdown
# Before
See [API Documentation](server/API_DOCUMENTATION.md)

# After
See [API Documentation](docs/API.md)
```

### Step 8: Create Documentation Index

Create `research-server/docs/README.md`:

```markdown
# Research Server Documentation

## Getting Started
- [Installation Guide](../INSTALLATION.md)
- [Quick Start](../README.md)

## API Reference
- [REST API](API.md) - Complete API endpoint reference
- [CLI Tool](CLI.md) - Command-line interface guide
- [MCP Server](MCP.md) - Model Context Protocol integration

## Architecture & Development
- [System Architecture](ARCHITECTURE.md) - Design overview
- [Development Guide](DEVELOPMENT.md) - Setup for contributors

## Additional Resources
- [Root Documentation](../../README.md)
- [Release Checklist](../../RELEASE_CHECKLIST.md)
```

### Step 9: Update ARCHITECTURE.md Content

Specific updates needed in `docs/ARCHITECTURE.md`:

```bash
# Edit docs/ARCHITECTURE.md
```

**Changes**:
1. Port number: 5555 → 5558
2. Add validation runs system to architecture diagram
3. Update API endpoint list (95+ endpoints)
4. Add CLI wrapper to architecture
5. Document filesystem sync changes
6. Add database schema section
7. Update technology stack

**Example Section to Add**:
```markdown
## Validation Runs System

The validation runs system enables parallel QA processing:

- **Unique Event Distribution**: Each validator receives different events
- **Status Tracking**: pending → assigned → completed/needs_work/rejected
- **Requeue Support**: Events marked needs_work can be reprocessed
- **Progress Monitoring**: Real-time tracking of validation progress

See [API.md](API.md#validation-runs) for endpoint details.
```

### Step 10: Verify Documentation Accuracy

Review each documentation file:

```bash
# Check API.md has current endpoints
grep "POST\|GET\|PUT\|DELETE" docs/API.md

# Check ARCHITECTURE.md has current ports and structure
grep "5558\|validation_runs\|CLI wrapper" docs/ARCHITECTURE.md
```

### Step 11: Update Root Documentation Links

Edit root `README.md`:

```markdown
## Documentation

### Getting Started
- **[INSTALLATION.md](INSTALLATION.md)** - Complete setup guide
- **[CLAUDE.md](CLAUDE.md)** - CLI command reference for AI agents
- **[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)** - Maintenance & cleanup guide

### Component Documentation
- [Timeline Documentation](timeline/docs/)
- [Research Server API](research-server/docs/API.md)
- [Architecture Overview](research-server/docs/ARCHITECTURE.md)
- [CLI Reference](research-server/docs/CLI.md)
```

## Validation Steps

### Test 1: No Duplicates

```bash
find . -name "API_DOCUMENTATION.md" | wc -l  # Should be 0
find . -name "ARCHITECTURE.md" | wc -l       # Should be 1 (in docs/)
```

### Test 2: All Links Work

```bash
# Check for broken links
grep -r "\[.*\](.*.md)" --include="*.md" | grep -v "http"
# Manually verify each link exists
```

### Test 3: Documentation Accuracy

- [ ] Port numbers are 5558 (not 5555)
- [ ] All API endpoints documented
- [ ] Validation runs system documented
- [ ] CLI wrapper documented
- [ ] Current directory structure reflected

## Files Modified

**Created**:
- `research-server/docs/README.md`
- `research-server/docs/API.md`
- `research-server/docs/ARCHITECTURE.md`
- `research-server/docs/CLI.md`
- `research-server/docs/MCP.md`

**Deleted**:
- `research-server/server/API_DOCUMENTATION.md`
- `research-server/server/static/API_DOCUMENTATION.md`
- `research-server/server/ARCHITECTURE.md`

**Modified**:
- `research-server/README.md`
- `README.md` (root)
- `INSTALLATION.md` (if references exist)

## Rollback Plan

```bash
# Restore from git
git checkout research-server/server/API_DOCUMENTATION.md
git checkout research-server/server/static/API_DOCUMENTATION.md
git checkout research-server/server/ARCHITECTURE.md

# Remove new docs
rm -rf research-server/docs
```

## Dependencies

- None (standalone task)

## Notes

- Keep `CLAUDE.md` in root (AI agent reference)
- Don't move `INSTALLATION.md` or `RELEASE_CHECKLIST.md` (root-level docs)
- Consider adding badges to README (build status, coverage, etc.)

## Future Enhancements

- [ ] Generate API docs from code (OpenAPI/Swagger)
- [ ] Add API changelog
- [ ] Version documentation (docs/v1/, docs/v2/)
- [ ] Add architecture diagrams (mermaid or images)

## Acceptance Criteria

- [x] Single `docs/` directory contains all research-server documentation
- [x] No duplicate documentation files
- [x] All references updated to point to `docs/`
- [x] ARCHITECTURE.md has accurate, current information
- [x] Documentation index created in `docs/README.md`
- [x] All links tested and working
