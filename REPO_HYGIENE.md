# Repository Hygiene Issues

✅ **CLEANUP COMPLETED**: All identified files have been moved to the `archive/` folder (2024-08-26)

## Files Cleaned Up

### 1. Generated Files in Root Directory (should be gitignored)
These files were generated during processing and should be removed from the root:
- `duplicates_to_remove.txt` - Duplicate analysis output
- `duplicates.json` - Duplicate detection results
- `google_sheets_events.csv` - Downloaded CSV data
- `missing_events.yaml` - Processing intermediate file
- `new_csv_events.yaml` - Processing intermediate file
- `processing_plan.yaml` - Processing plan document
- `search_queries.txt` - Generated search queries
- `timeline_events_minimal.yaml` - Generated export
- `timeline_events.csv` - Generated export
- `timeline_events.json` - Generated export
- `timeline_events.yaml` - Generated export

**Action Taken:** ✅ Moved to `archive/generated-files/`

### 2. Temporary Python Scripts in Root
These appear to be ad-hoc processing scripts that should be moved or removed:
- `analyze_remaining_events.py`
- `batch_process_csv_events.py`
- `create_csv_events.py`
- `create_discovered_events.py`
- `create_new_events.py`
- `fix_events.py`
- `process_all_remaining_events.py`
- `process_google_sheets_events.py`
- `process_new_events.py`
- `search_for_events.py`

**Action Taken:** ✅ Moved to `archive/temp-scripts/`

### 3. OS-Specific Files
Found `.DS_Store` files (macOS metadata) that should not be in the repo:
- `./ai-analysis/.DS_Store`
- `./ai-analysis/Sources/.DS_Store`
- `./.DS_Store`
- `./viewer/node_modules/...` (in node_modules, already gitignored)

**Action Taken:** ✅ Removed all `.DS_Store` files (already gitignored)

## Recommended Actions

### ✅ Cleanup Completed

All files have been safely archived rather than deleted:

```bash
# Files were moved with these commands:
mkdir -p archive/generated-files archive/temp-scripts archive/processing-files

# Moved generated exports
mv duplicates_to_remove.txt duplicates.json timeline_events*.yaml timeline_events.csv timeline_events.json archive/generated-files/

# Moved processing files  
mv google_sheets_events.csv missing_events.yaml new_csv_events.yaml processing_plan.yaml search_queries.txt archive/processing-files/

# Moved temporary scripts
mv analyze_remaining_events.py batch_process_csv_events.py create_*.py fix_events.py process_*.py search_for_events.py archive/temp-scripts/

# Removed .DS_Store files
find . -name ".DS_Store" -not -path "./node_modules/*" -not -path "./archive/*" -delete
```

The `archive/` folder is gitignored, preserving these files locally while keeping the repo clean.

### Repository Structure Improvements

1. **Create `data/` directory for processing outputs:**
   ```bash
   mkdir -p data/exports
   mkdir -p data/temp
   mkdir -p data/reports
   ```

2. **Update scripts to use proper output directories:**
   - Exports should go to `data/exports/`
   - Temporary files to `data/temp/`
   - Reports to `data/reports/`

3. **Add pre-commit hooks to prevent accidental commits:**
   Create `.pre-commit-config.yaml`:
   ```yaml
   repos:
   - repo: local
     hooks:
     - id: check-added-large-files
       name: Check for large files
       entry: check-added-large-files
       language: system
     - id: no-commit-generated
       name: Block generated files
       entry: bash -c 'git diff --cached --name-only | grep -E "\.(csv|json|yaml)$" | grep -E "timeline_events|duplicates" && exit 1 || exit 0'
       language: system
   ```

### Documentation Updates Needed

1. **Add to README.md:**
   - Clear instructions on where generated files go
   - How to run cleanup commands
   - Development setup instructions

2. **Create CONTRIBUTING.md:**
   - File organization guidelines
   - Naming conventions
   - Where to place different types of files

### Testing Improvements

1. **Add test for repo cleanliness:**
   ```python
   def test_no_generated_files_in_root():
       """Ensure no generated files in repository root."""
       root_files = os.listdir('.')
       generated_patterns = [
           'timeline_events', 'duplicates', 'process_',
           'missing_events', 'new_csv_events'
       ]
       for file in root_files:
           for pattern in generated_patterns:
               assert pattern not in file, f"Generated file {file} found in root"
   ```

## Priority Order

1. **High Priority:**
   - Remove generated files from root
   - Move/remove temporary Python scripts
   - Update .gitignore (✓ Already done)

2. **Medium Priority:**
   - Create proper directory structure for outputs
   - Update scripts to use new directories
   - Remove .DS_Store files

3. **Low Priority:**
   - Add pre-commit hooks
   - Create CONTRIBUTING.md
   - Add repo cleanliness tests

## Verification

After cleanup, run:
```bash
# Check for remaining issues
git status --ignored
find . -name "*.pyc" -o -name "__pycache__" -o -name ".DS_Store" | grep -v node_modules
ls -la | grep -E "\.(csv|json|yaml|txt)$" | grep -vE "(README|requirements|package)"
```

The repository should have:
- No generated files in root
- No temporary scripts in root  
- No OS-specific files (.DS_Store)
- No Python cache files outside of virtual environments
- Clear directory structure for different file types