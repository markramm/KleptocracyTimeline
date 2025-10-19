# SPEC-005: Create Timeline Data Repository

**Status**: Ready
**Priority**: Critical
**Estimated Time**: 1-2 hours
**Risk**: Medium
**Dependencies**: All Phase 1 specs complete

## Problem

Current monorepo mixing two concerns:
- Timeline data + viewer (public, CC0 licensed)
- Research server (development tool, MIT licensed)

This makes it harder to:
- Manage permissions (data is public, server may be private)
- Deploy independently
- Version separately
- Onboard contributors (unclear what repo contains)

## Goal

Extract timeline data and viewer into separate repository with full git history.

## Success Criteria

- [ ] New repository created: `kleptocracy-timeline`
- [ ] Contains only timeline-related files
- [ ] Git history preserved for timeline files
- [ ] Working React viewer
- [ ] GitHub Pages deployment configured
- [ ] README and documentation updated
- [ ] License files correct (CC0 for data, MIT for code)

## Repository Structure

**New Repository**: `kleptocracy-timeline`

```
kleptocracy-timeline/
├── events/                      # Timeline event data
│   └── YYYY/
│       └── *.json
├── viewer/                      # React viewer app
│   ├── src/
│   ├── public/
│   └── package.json
├── schemas/                     # Event validation schemas
│   └── event_schema.json
├── scripts/                     # Validation & conversion tools
│   ├── validate_events.py
│   ├── generate_static_api.py
│   └── convert_to_markdown.py
├── docs/                        # Documentation
│   ├── EVENT_FORMAT.md
│   ├── CONTRIBUTING.md
│   └── VALIDATION.md
├── .github/
│   └── workflows/
│       ├── validate-events.yml  # CI for event validation
│       └── deploy-viewer.yml    # GitHub Pages deployment
├── README.md                    # Project overview
├── LICENSE-DATA                 # CC0 for event data
├── LICENSE-CODE                 # MIT for viewer & scripts
└── CHANGELOG.md                 # Version history
```

## Implementation Steps

### Step 1: Create Local Branch with Timeline Only

Use git subtree to extract timeline directory with history:

```bash
cd /Users/markr/kleptocracy-timeline

# Create branch with only timeline/ directory and its history
git subtree split -P timeline -b timeline-data-only

# Verify branch
git checkout timeline-data-only
ls -la
# Should only show contents of timeline/
```

**Validation**:
```bash
# Check history preserved
git log --oneline | head -20
# Should show commits related to timeline

# Check file count
find . -type f | wc -l
# Should be much smaller than full repo
```

### Step 2: Create GitHub Repository

```bash
# Create new public repository
gh repo create kleptocracy-timeline \
  --public \
  --description "Comprehensive timeline documenting institutional capture and kleptocracy (1970-2025)" \
  --homepage "https://kleptocracy-timeline.github.io"

# Verify creation
gh repo view kleptocracy-timeline
```

### Step 3: Restructure for New Repository

```bash
# Still on timeline-data-only branch

# Rename data/events to just events (cleaner for standalone repo)
mv data/events events
rmdir data

# Move docs if not at root
mv docs/* ./ 2>/dev/null || true

# Verify structure
ls -la
# Should see: events/, viewer/, schemas/, scripts/, docs/, README.md
```

### Step 4: Create Dual License Files

**Create LICENSE-DATA** (CC0 for event data):
```markdown
# Creative Commons Zero v1.0 Universal

The timeline event data in the `events/` directory is dedicated to the public domain under CC0 1.0 Universal.

See: https://creativecommons.org/publicdomain/zero/1.0/

## Statement

The person who associated a work with this deed has dedicated the work to the public domain by waiving all of his or her rights to the work worldwide under copyright law, including all related and neighboring rights, to the extent allowed by law.

You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.
```

**Create LICENSE-CODE** (MIT for viewer & scripts):
```markdown
# MIT License

Copyright (c) 2025 Kleptocracy Timeline Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction...

[Full MIT license text]
```

### Step 5: Update README for Standalone Repository

Create new `README.md`:

```markdown
# Kleptocracy Timeline

A comprehensive timeline documenting patterns of institutional capture, regulatory capture, and kleptocracy across 50+ years with 1,600+ verified events.

🔗 **View Timeline**: https://kleptocracy-timeline.github.io

## Quick Start

### View Timeline Locally

```bash
git clone https://github.com/yourusername/kleptocracy-timeline.git
cd kleptocracy-timeline/viewer
npm install
npm start
```

Open http://localhost:3000

### Add or Validate Events

```bash
# Validate all events
cd scripts
python3 validate_events.py

# Generate static API
python3 generate_static_api.py
```

## Repository Structure

- **events/** - 1,600+ timeline events (1970-2025) in JSON format
- **viewer/** - Interactive React viewer application
- **schemas/** - JSON Schema for event validation
- **scripts/** - Validation and conversion tools
- **docs/** - Documentation and contributing guidelines

## Event Format

Events are stored as JSON in `events/YYYY/`:

```json
{
  "id": "2024-01-15--event-slug",
  "date": "2024-01-15",
  "title": "Event Title",
  "summary": "Detailed description...",
  "importance": 8,
  "tags": ["tag1", "tag2"],
  "sources": [...]
}
```

See [docs/EVENT_FORMAT.md](docs/EVENT_FORMAT.md) for complete specification.

## Contributing

We welcome contributions! See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for:
- How to add new events
- Event quality standards
- Validation requirements
- Pull request process

## Research Tools

Looking to use this data for research? Check out:
- [Timeline Research Server](https://github.com/yourusername/timeline-research-server) - API, CLI, and AI agent integration

## License

- **Event Data** (`events/`): [CC0 1.0 Universal](LICENSE-DATA) - Public Domain
- **Code** (viewer, scripts): [MIT License](LICENSE-CODE)

## About

This timeline serves as empirical documentation for patterns of institutional capture spanning 50+ years. It is designed to support both academic research and public awareness.

For questions: [Open an issue](https://github.com/yourusername/kleptocracy-timeline/issues)
```

### Step 6: Create GitHub Actions Workflows

**Create `.github/workflows/validate-events.yml`**:
```yaml
name: Validate Events

on:
  push:
    paths:
      - 'events/**/*.json'
  pull_request:
    paths:
      - 'events/**/*.json'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd scripts
          pip install -r requirements.txt

      - name: Validate events
        run: |
          cd scripts
          python3 validate_events.py

      - name: Check event IDs are unique
        run: |
          cd events
          duplicates=$(find . -name "*.json" -exec basename {} \; | sort | uniq -d)
          if [ -n "$duplicates" ]; then
            echo "Duplicate event IDs found:"
            echo "$duplicates"
            exit 1
          fi
```

**Create `.github/workflows/deploy-viewer.yml`**:
```yaml
name: Deploy Viewer to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd viewer
          npm install

      - name: Build viewer
        run: |
          cd viewer
          npm run build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2
        with:
          path: viewer/build

      - name: Deploy to GitHub Pages
        uses: actions/deploy-pages@v2
```

### Step 7: Create CONTRIBUTING.md

```markdown
# Contributing to Kleptocracy Timeline

Thank you for your interest in contributing!

## How to Add Events

### 1. Choose the Right Format

Events are stored as JSON files in `events/YYYY/`:

```json
{
  "id": "YYYY-MM-DD--descriptive-slug",
  "date": "YYYY-MM-DD",
  "title": "Event Title",
  "summary": "Detailed description...",
  "importance": 7,
  "tags": ["tag1", "tag2"],
  "sources": [
    {
      "url": "https://example.com/article",
      "title": "Article Title",
      "publisher": "Publisher Name",
      "date": "YYYY-MM-DD"
    }
  ]
}
```

### 2. Validate Your Event

```bash
cd scripts
python3 validate_events.py ../events/2024/your-event.json
```

### 3. Submit Pull Request

1. Fork this repository
2. Create feature branch: `git checkout -b add-event-description`
3. Add your event file to `events/YYYY/`
4. Run validation: `python3 scripts/validate_events.py`
5. Commit: `git commit -m "Add: [Event Title]"`
6. Push: `git push origin add-event-description`
7. Open Pull Request

### Event Quality Standards

- **Sources Required**: Minimum 2 credible sources
- **Verifiable Facts**: Events must be publicly documented
- **Neutral Language**: Avoid editorializing
- **Accurate Dates**: Use best available date information
- **Proper Tagging**: Use existing tags when possible

### Importance Scale

- **1-3**: Minor events, limited impact
- **4-6**: Significant events, notable impact
- **7-8**: Major events, widespread impact
- **9-10**: Critical events, systemic impact

## Code Contributions

### Viewer Improvements

```bash
cd viewer
npm install
npm start
```

Make changes, test locally, then submit PR.

### Script Improvements

Scripts use Python 3.9+. Add tests for new functionality.

## Questions?

Open an issue for:
- Event addition questions
- Technical issues
- Feature requests
```

### Step 8: Push to GitHub

```bash
# Still on timeline-data-only branch

# Set upstream
git remote add origin git@github.com:yourusername/kleptocracy-timeline.git

# Push
git push -u origin timeline-data-only:main

# Verify
gh repo view kleptocracy-timeline
```

### Step 9: Configure GitHub Pages

```bash
# Enable GitHub Pages via CLI
gh api repos/yourusername/kleptocracy-timeline/pages \
  -X POST \
  -f source[branch]=main \
  -f source[path]=/viewer/build

# Or use web interface:
# Settings → Pages → Source: GitHub Actions
```

### Step 10: Verify Deployment

```bash
# Check GitHub Actions
gh run list --repo yourusername/kleptocracy-timeline

# Wait for deployment
gh run watch --repo yourusername/kleptocracy-timeline

# Visit site
open https://yourusername.github.io/kleptocracy-timeline
```

## Validation Steps

### Test 1: Repository Contains Only Timeline Files

```bash
git clone https://github.com/yourusername/kleptocracy-timeline.git /tmp/timeline-test
cd /tmp/timeline-test

# Should NOT contain research-server
ls | grep research-server
# Should return nothing

# Should contain timeline files
ls -la
# Should see: events/, viewer/, schemas/, scripts/, docs/
```

### Test 2: Git History Preserved

```bash
git log --oneline | wc -l
# Should have many commits (history preserved)

git log --grep="event" --oneline | head
# Should show event-related commits
```

### Test 3: Viewer Works

```bash
cd viewer
npm install
npm start
# Should open at localhost:3000 without errors
```

### Test 4: Validation Works

```bash
cd scripts
python3 validate_events.py
# Should validate all events successfully
```

### Test 5: GitHub Actions Pass

```bash
gh run list --repo yourusername/kleptocracy-timeline --limit 5
# Should show green checkmarks
```

### Test 6: GitHub Pages Deployed

```bash
curl -I https://yourusername.github.io/kleptocracy-timeline
# Should return 200 OK
```

## Files Created

**In New Repository**:
- `LICENSE-DATA` (CC0)
- `LICENSE-CODE` (MIT)
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `.github/workflows/validate-events.yml`
- `.github/workflows/deploy-viewer.yml`
- Updated `README.md`

## Post-Split Actions

### Update Original Repository

After split, update original repo README:

```markdown
# Kleptocracy Research Infrastructure

**Note**: This repository has been split. Timeline data moved to:
👉 https://github.com/yourusername/kleptocracy-timeline

This repository contains:
- Research Server (API, CLI, MCP)
- Quality Assurance Tools
- Research Priority Tracking
```

### Cross-Link Repositories

In timeline repo README, add:
```markdown
## Research Tools

For API access and research workflows:
👉 [Timeline Research Server](https://github.com/yourusername/timeline-research-server)
```

## Rollback Plan

If split fails:

```bash
# Delete remote repository
gh repo delete yourusername/kleptocracy-timeline --yes

# Delete local branch
git branch -D timeline-data-only

# Continue using monorepo
git checkout main
```

## Dependencies

- All Phase 1 specs completed
- Git installed and configured
- GitHub CLI installed (`gh`)
- Node.js installed (for viewer testing)
- Python 3.9+ installed (for validation)

## Risks & Mitigations

**Risk**: History loss
**Mitigation**: Use `git subtree split` to preserve history

**Risk**: Broken viewer after split
**Mitigation**: Test locally before pushing

**Risk**: GitHub Actions fail
**Mitigation**: Test workflows with `act` before pushing

## Notes

- Keep original repo as backup until split confirmed working
- Coordinate with team before making repositories public
- Consider adding branch protection rules
- Set up issue/PR templates

## Acceptance Criteria

- [x] New repository created and accessible
- [x] Contains only timeline-related files
- [x] Git history preserved (100+ commits)
- [x] React viewer deploys to GitHub Pages
- [x] CI validates events on PR
- [x] Documentation complete and accurate
- [x] Dual licenses properly configured
- [x] CONTRIBUTING.md exists
- [x] Cross-links added between repositories
