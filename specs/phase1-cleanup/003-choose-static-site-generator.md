# SPEC-003: Choose One Static Site Generator

**Status**: Ready
**Priority**: Critical
**Estimated Time**: 1 hour
**Risk**: Medium (data loss if not careful)

## Problem

Timeline component has TWO competing static site generators:

1. **Hugo** - Static site in `timeline/content/events/` (1,552+ Markdown files)
2. **React** - Viewer application in `timeline/viewer/` (interactive)

This creates:
- 759MB timeline directory (should be ~50MB)
- Confusion about which is authoritative
- Duplicate data in JSON and Markdown
- Maintenance burden (two systems)

## Goal

Choose ONE static site generator and remove the other, establishing clear data flow.

## Decision Matrix

| Criteria | Hugo | React Viewer |
|----------|------|--------------|
| **Interactivity** | ❌ Static only | ✅ Filtering, search, sorting |
| **Build Speed** | ✅ Very fast | ⚠️ Slower (npm build) |
| **Maintenance** | ⚠️ Learning curve | ✅ Team knows React |
| **Deployment** | ✅ Simple (static files) | ✅ Simple (npm build) |
| **Event Format** | Needs Markdown conversion | ✅ Uses JSON directly |
| **Search** | ❌ Limited | ✅ Full client-side search |
| **Mobile** | ✅ Responsive themes | ✅ Custom responsive |
| **Current State** | ⚠️ 1,552 files generated | ✅ Working, deployed |

## Recommendation: **React Viewer**

**Rationale**:
- More interactive (filtering, search, sorting)
- Uses JSON directly (no conversion needed)
- Team already familiar with React
- Already working and deployed
- Better for timeline visualization

## Success Criteria

- [ ] Single source of truth for event data (JSON)
- [ ] Single viewer application (React)
- [ ] Hugo files removed or archived
- [ ] Timeline directory size reduced significantly (<100MB)
- [ ] Documentation updated
- [ ] Deployment process updated

## Current State

```
timeline/
├── data/events/              # 1,607 JSON files (source of truth)
├── content/events/           # 1,552+ Markdown files (HUGO - duplicate)
├── viewer/                   # React app (working)
├── public/                   # Hugo output (static HTML)
├── hugo.toml                 # Hugo config
├── layouts/                  # Hugo templates
├── archetypes/               # Hugo archetypes
└── .hugo_build.lock         # Hugo lock file
```

**Size**: 759MB (way too large)

## Target State

```
timeline/
├── events/                   # 1,607 JSON files (SINGLE source)
│   └── YYYY/                # Organized by year
│       └── *.json
├── viewer/                   # React app (ONLY viewer)
│   ├── src/
│   ├── public/
│   └── package.json
├── schemas/                  # Event validation
│   └── event_schema.json
├── scripts/                  # Validation tools
│   └── validate_events.py
└── docs/
    └── EVENT_FORMAT.md
```

**Expected Size**: ~20-50MB

## Implementation Steps

### Step 1: Backup Current State

```bash
cd /Users/markr/kleptocracy-timeline

# Create backup
git checkout -b backup-before-hugo-removal
git push origin backup-before-hugo-removal

# Create archive
tar -czf timeline-backup-$(date +%Y%m%d).tar.gz timeline/
```

**Validation**: Backup exists
```bash
ls -lh timeline-backup-*.tar.gz
```

### Step 2: Verify React Viewer Works

```bash
cd timeline/viewer
npm install
npm start
```

**Manual Test**:
- [ ] Viewer loads at http://localhost:3000
- [ ] Events display correctly
- [ ] Search/filter works
- [ ] No console errors

### Step 3: Document Hugo Removal Decision

Create `timeline/docs/HUGO_REMOVAL.md`:

```markdown
# Hugo Removal Decision

**Date**: 2025-10-19
**Decision**: Remove Hugo static site generator in favor of React viewer

## Rationale
- React provides better interactivity
- Hugo created duplicate Markdown files from JSON
- React uses JSON directly (simpler pipeline)
- Team more familiar with React

## What Was Removed
- `content/events/` - 1,552+ Markdown files
- `public/` - Hugo static output
- `layouts/` - Hugo templates
- `archetypes/` - Hugo archetypes
- `hugo.toml` - Hugo configuration
- `.hugo_build.lock` - Hugo lock file

## Backup
See git branch: `backup-before-hugo-removal`
Archive: `timeline-backup-YYYYMMDD.tar.gz`

## Migration Path
If Hugo needed again:
1. Use `scripts/convert_to_markdown.py` to regenerate Markdown from JSON
2. Restore Hugo configuration from backup branch
```

### Step 4: Remove Hugo Files

```bash
cd timeline

# Remove Hugo content (CAREFUL - verify backup first!)
rm -rf content/events/
rm -rf public/
rm -rf layouts/
rm -rf archetypes/
rm -f hugo.toml
rm -f .hugo_build.lock

# Keep these (not Hugo-specific)
# - data/events/ (JSON source)
# - viewer/ (React)
# - schemas/
# - scripts/
# - docs/
```

**Validation**: Check what remains
```bash
ls -la timeline/
```

Should see:
- ✅ `data/events/`
- ✅ `viewer/`
- ✅ `schemas/`
- ✅ `scripts/`
- ✅ `docs/`
- ❌ No `content/`, `public/`, `layouts/`, `archetypes/`

### Step 5: Reorganize Events by Year

Make events easier to navigate:

```bash
cd timeline/data/events

# Create year directories
for year in {1970..2025}; do
  mkdir -p $year
done

# Move events to year directories
for file in *.json; do
  if [[ $file =~ ^([0-9]{4})-.*\.json$ ]]; then
    year="${BASH_REMATCH[1]}"
    mv "$file" "$year/"
  fi
done

# Verify
ls -la 2024/ | head -10
```

**Validation**: Events organized by year
```bash
# Count events per year
for year in {2020..2025}; do
  count=$(ls -1 $year/*.json 2>/dev/null | wc -l)
  echo "$year: $count events"
done
```

### Step 6: Update Viewer to Use New Paths

Update `timeline/viewer/src/` files to reference new event paths:

**Find files that reference event paths**:
```bash
cd timeline/viewer
grep -r "data/events" src/ --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx"
```

**Update paths**:
```javascript
// Before
const eventsPath = '../data/events/2024-01-15--event.json'

// After
const eventsPath = '../data/events/2024/2024-01-15--event.json'
```

Or update to use API endpoint:
```javascript
// Use static API instead
const eventsPath = '/api/events/2024-01-15--event.json'
```

### Step 7: Update Static API Generator

Update `timeline/scripts/generate_static_api.py` to work with new structure:

```python
# Update EVENT_DIR path
EVENT_DIR = Path("../data/events")

# Update to scan year subdirectories
def load_all_events():
    events = []
    for year_dir in sorted(EVENT_DIR.glob("[0-9][0-9][0-9][0-9]")):
        for event_file in year_dir.glob("*.json"):
            events.append(load_event(event_file))
    return events
```

### Step 8: Test Static API Generation

```bash
cd timeline/scripts
python3 generate_static_api.py
```

**Validation**: API files generated
```bash
ls -la timeline/viewer/public/api/
# Should see events.json, actors.json, tags.json, etc.
```

### Step 9: Update Documentation

Update `timeline/README.md`:

```markdown
# Timeline Data & Viewer

## Event Data

Events are stored as JSON files in `data/events/YYYY/`:

```
data/events/
├── 2024/
│   ├── 2024-01-15--event-slug.json
│   └── ...
├── 2023/
│   └── ...
└── ...
```

## Viewer

React-based interactive viewer in `viewer/`:

```bash
cd viewer
npm install
npm start
```

## Removed Components

**Hugo Static Site** - Removed 2025-10-19
- Created duplicate Markdown files
- React viewer provides better interactivity
- See `docs/HUGO_REMOVAL.md` for details
```

Update `timeline/docs/EVENT_FORMAT.md`:
- Remove references to Markdown format
- Emphasize JSON as single format
- Update example paths to include year directory

### Step 10: Update .gitignore

```bash
# Add to .gitignore if not present
cat >> .gitignore << 'EOF'

# Hugo (removed but keep in gitignore)
/timeline/content/events/
/timeline/public/
/timeline/layouts/
/timeline/archetypes/
/timeline/hugo.toml
/timeline/.hugo_build.lock
EOF
```

### Step 11: Verify Directory Size Reduction

```bash
du -sh timeline/
```

**Expected**: Should be <100MB (down from 759MB)

**Breakdown**:
```bash
du -sh timeline/data/events/    # Should be ~10-20MB (JSON)
du -sh timeline/viewer/         # Should be ~30-50MB (with node_modules)
```

### Step 12: Update Deployment Process

Update deployment documentation (if exists) to only use React:

**GitHub Pages / Static Deployment**:
```bash
# Build React app
cd timeline/viewer
npm run build

# Deploy build/ directory
# (process depends on deployment target)
```

Remove any Hugo build steps from CI/CD.

## Validation Steps

### Test 1: React Viewer Works

```bash
cd timeline/viewer
npm install
npm start
```

- [ ] Opens at http://localhost:3000
- [ ] All events display
- [ ] Search works
- [ ] Filter works
- [ ] No 404 errors for event files

### Test 2: Directory Size

```bash
du -sh timeline/
```

- [ ] Size is <100MB (down from 759MB)

### Test 3: No Hugo Files

```bash
find timeline -name "*.md" -path "*/content/events/*" | wc -l
```

- [ ] Returns 0 (no Markdown event files)

### Test 4: Events Organized by Year

```bash
ls timeline/data/events/
```

- [ ] Shows year directories (2020, 2021, 2022, etc.)
- [ ] No loose JSON files in events root

### Test 5: Static API Generation

```bash
cd timeline/scripts
python3 generate_static_api.py
ls -la timeline/viewer/public/api/
```

- [ ] API files generated successfully

## Rollback Plan

If issues found:

```bash
# Restore from backup branch
git checkout backup-before-hugo-removal

# Or restore from archive
tar -xzf timeline-backup-YYYYMMDD.tar.gz
```

## Dependencies

- SPEC-002 complete (documentation consolidated)
- React viewer tested and working
- Backup created and verified

## Risks & Mitigations

**Risk**: Data loss if backup fails
**Mitigation**:
- Create git backup branch
- Create tar archive
- Verify backups before deletion

**Risk**: Viewer breaks with new paths
**Mitigation**:
- Test viewer before removing Hugo
- Update paths incrementally
- Keep static API generator working

**Risk**: Team wants Hugo back
**Mitigation**:
- Document decision clearly
- Keep conversion script
- Backup branch available

## Notes

- Keep `scripts/convert_to_markdown.py` for future Markdown export if needed
- Consider adding year-based navigation to React viewer
- Event IDs already include year (YYYY-MM-DD--slug) so no collision risk

## Future Enhancements

- [ ] Add year-based navigation to viewer
- [ ] Implement lazy loading by year (performance)
- [ ] Generate year-based API endpoints (/api/2024/events.json)
- [ ] Add event count badges per year

## Acceptance Criteria

- [x] Hugo files removed from timeline/
- [x] React viewer works with new event structure
- [x] Events organized by year directory
- [x] Static API generator updated and working
- [x] Documentation updated (removed Hugo references)
- [x] Directory size reduced significantly
- [x] Backup created and verified
- [x] .gitignore updated
