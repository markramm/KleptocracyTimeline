# Repository Cleanup Plan

## Current Issues

### 1. Root Directory Clutter
- **30+ markdown files** in root directory
- **Multiple test scripts** (test_yaml_tools.py, pre_launch_check.sh, etc.) in root
- **Duplicate/outdated documentation** with hardcoded statistics

### 2. Script Organization Issues
- Python scripts scattered across multiple directories
- Duplicate functionality (e.g., generate_csv.py vs generate_csv_v2.py)
- Test files mixed with source files
- Archive folder containing old but potentially useful scripts

### 3. Documentation Problems
- Multiple README variants (README.md, README_PUBLIC.md, etc.)
- Hardcoded statistics that become outdated immediately
- Overlapping content across multiple docs
- AI/development guides mixed with user documentation

## Proposed Structure

```
kleptocracy-timeline/
├── README.md                    # Main user-facing README (keep updated)
├── CONTRIBUTING.md              # How to contribute (keep)
├── LICENSE                      # License file (keep)
├── .gitignore                  
├── package.json                 # For root-level npm scripts
│
├── docs/                        # All documentation
│   ├── user/                   # User-facing docs
│   │   ├── FAQ.md
│   │   ├── DEPLOYMENT.md
│   │   └── GITHUB_PAGES_SETUP.md
│   ├── development/            # Developer docs
│   │   ├── DEVELOPMENT_SETUP.md
│   │   ├── TESTING.md
│   │   ├── AI_COLLABORATION_GUIDE.md
│   │   └── PROJECT_STRUCTURE.md
│   └── maintenance/            # Maintenance & operations
│       ├── REPO_HYGIENE.md
│       ├── LAUNCH_CHECKLIST.md
│       └── RESPONSE_TEMPLATES.md
│
├── scripts/                     # All operational scripts
│   ├── generation/             # Data generation scripts
│   │   ├── generate_static_api.py
│   │   ├── generate_csv.py
│   │   └── generate_yaml_export.py
│   ├── validation/             # Validation scripts
│   │   ├── validate_yaml.py
│   │   ├── validate_timeline_dates.py
│   │   └── check_links.py
│   ├── maintenance/            # Maintenance scripts
│   │   ├── find_duplicates.py
│   │   ├── analyze_sources.py
│   │   └── standardize_actors.py
│   └── utils/                  # Shared utilities
│
├── tests/                       # All test files
│   ├── unit/
│   ├── integration/
│   └── scripts/
│       └── test_before_commit.sh
│
├── timeline_data/              # Timeline data (keep as is)
│   ├── events/
│   └── validation_app_enhanced.py  # Move to tools/
│
├── viewer/                     # React app (keep as is)
│
├── api/                        # API server (keep as is)
│
├── tools/                      # Interactive tools & utilities
│   ├── validation_app.py       # Web-based validation tool
│   ├── test_before_commit.sh   # Pre-commit test script
│   └── archiving/             # Archive tools
│
└── .github/                    # GitHub specific files
    └── workflows/
```

## Cleanup Tasks

### Phase 1: Documentation Consolidation
1. **Merge duplicate content** from multiple README files into main README.md
2. **Move active docs to organized folders** under docs/
3. **Replace hardcoded statistics** with dynamic badges or links to live data
4. **Delete outdated docs** (preserved in git history)

### Phase 2: Script Organization
1. **Consolidate duplicate scripts** (keep v2 versions, archive originals)
2. **Move all test scripts** to tests/ directory
3. **Move operational scripts** to appropriate scripts/ subdirectories
4. **Clean up root directory** - no loose .py or .sh files

### Phase 3: Remove Redundancy
1. **Delete truly duplicate files** after confirming functionality
2. **Consolidate yaml_tools.py** with other validation scripts
3. **Remove test_yaml_tools.py** from root (move to tests/)

### Phase 4: Update References
1. **Update all script imports** to reflect new locations
2. **Update GitHub Actions** to use new script paths
3. **Update documentation** to reference new structure
4. **Update .gitignore** if needed

## Implementation Order

1. **Create new directory structure** (non-destructive)
2. **Copy/move files** to new locations (keep originals temporarily)
3. **Test everything works** with new structure
4. **Update all references** in code and docs
5. **Remove old files** after confirming everything works
6. **Update README** with new structure

## Files to Definitely Keep

- README.md (update with current info)
- CONTRIBUTING.md
- LICENSE
- .gitignore
- package.json / package-lock.json

## Files to Remove (Preserved in Git History)

- README_PUBLIC.md (content merged into README.md)
- PROJECT_STATUS.md, PROJECT_HEALTH.md, PROJECT_STATS.md (outdated stats)
- PROJECT_EVALUATION.md, LAUNCH_READY.md (outdated launch docs)
- INITIAL_COMMIT.md, GITHUB_INTEGRATION.md (no longer needed)
- Test scripts in root (moved to tests/)
- Original versions of _v2 scripts (keeping v2 only)

## Success Criteria

- [ ] Root directory has <10 files (only essential ones)
- [ ] All scripts organized by function
- [ ] No duplicate functionality
- [ ] All tests in tests/ directory
- [ ] Documentation organized and up-to-date
- [ ] GitHub Actions still work
- [ ] Pre-commit hooks still work
- [ ] No broken imports or references

## Notes

- Git history preserves all deleted files (use `git log --follow` to track)
- The existing archive/ folder is .gitignored for temporary/working files only
- Create a MIGRATION.md to document what moved where
- Run full test suite after each phase
- Use `git rm` to properly remove files and preserve history