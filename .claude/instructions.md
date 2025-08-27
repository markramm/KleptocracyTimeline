# Claude Code Instructions - Kleptocracy Timeline

## CRITICAL: Schema Validation Requirements

### 🚨 ALWAYS VALIDATE TIMELINE EVENTS BEFORE AND AFTER MODIFICATIONS

When working with timeline event YAML files (`timeline_data/events/*.yaml`), you MUST:

## Before Making Changes

1. **Check Schema Compliance**
   ```bash
   # Run validation before any changes
   python timeline_data/validate_yaml.py
   ```

2. **Verify Specific Event**
   ```bash
   # Check the specific file you're about to modify
   python timeline_data/validate_yaml.py timeline_data/events/YYYY-MM-DD--event-name.yaml
   ```

## After Making Changes

1. **Validate Modified Files**
   ```bash
   # Always run after editing ANY event file
   python timeline_data/validate_yaml.py
   ```

2. **Check Date Validation**
   ```bash
   # Ensure dates are logical (no future confirmed events)
   python tools/validation/validate_timeline_dates.py
   ```

3. **Run QA Checks**
   ```bash
   # Comprehensive quality assurance
   python tools/qa/timeline_qa_system.py
   ```

## Schema Requirements

### Required Fields (MUST be present)
- `id`: Must match filename without .yaml extension
- `date`: Format 'YYYY-MM-DD' (quoted string)
- `title`: Concise, factual description
- `summary`: Detailed explanation
- `sources`: List with at least one source
- `status`: One of: confirmed, pending, predicted, disputed, reported, reported/contested

### Source Schema (each source MUST have)
```yaml
sources:
  - title: "Article Headline"     # Required
    url: "https://..."            # Required
    outlet: "Publication Name"    # Required
    date: "YYYY-MM-DD"           # Required
    archive_url: "https://..."   # Strongly recommended
```

### Critical Rules

#### 🚫 NEVER USE UNDERSCORES IN IDs
```yaml
# ✅ CORRECT
id: 2024-01-15--supreme-court-ruling
id: 2025-03-01--ice-detention-network

# ❌ WRONG - WILL FAIL
id: 2024-01-15--supreme_court_ruling
id: 2025-03-01--ice_detention_network
```

#### 📅 Future Events Cannot Be "Confirmed"
- Events with dates after today MUST use status: "predicted" or "pending"
- Only past events can have status: "confirmed"

#### 📝 All Events Need Sources
- Every event MUST have at least one source
- "Research Document" is NOT a valid URL
- Sources must be real, verifiable URLs

## Validation Commands Summary

### Quick Validation Workflow
```bash
# 1. Before any edits - check current state
python timeline_data/validate_yaml.py

# 2. Make your edits to event files

# 3. After edits - validate syntax
python timeline_data/validate_yaml.py

# 4. Check dates are logical
python tools/validation/validate_timeline_dates.py

# 5. Run comprehensive QA
python tools/qa/timeline_qa_system.py

# 6. If all pass, commit changes
git add timeline_data/events/*.yaml
git commit -m "Update events: [description] (validated)"
```

### Common Validation Errors and Fixes

| Error | Fix |
|-------|-----|
| "Missing required field: status" | Add `status: confirmed` or appropriate status |
| "Invalid date format" | Use `date: 'YYYY-MM-DD'` with quotes |
| "ID doesn't match filename" | Ensure id field matches filename without .yaml |
| "Future date with confirmed status" | Change to `status: predicted` |
| "Sources must be a list" | Format sources as YAML list with `-` prefix |
| "Invalid capture lane" | Use only approved capture lanes from schema |

## Working with Events

### 🆕 PREFERRED: Using YAML Management Tools

The project now includes unified YAML management tools (`yaml_tools.py`) for efficient event management:

```python
from yaml_tools import YamlEventManager
manager = YamlEventManager("timeline_data/events")

# Search for events needing work
weak_events = manager.yaml_search(return_full=True)
weak_events = [e for e in weak_events if len(e.get('sources', [])) < 2]

# Edit events with automatic validation and backup
result = manager.yaml_edit(
    file_path="timeline_data/events/example.yaml",
    updates={"status": "confirmed", "importance": 8},
    validate_before_save=True,  # Automatic validation
    create_backup=True,          # Automatic backup
    dry_run=False               # Set True to preview
)

# Manage sources efficiently
result = manager.manage_sources(
    file_path="timeline_data/events/example.yaml",
    action="add",
    sources=[{"title": "...", "outlet": "...", "url": "...", "date": "..."}],
    check_duplicates=True,
    check_urls=True
)

# Bulk operations with safety
result = manager.yaml_bulk_edit(
    search_criteria={"status": ["reported"], "date_range": ("2025-01-01", "2025-12-31")},
    updates={"status": "developing"},
    interactive=True,  # Shows preview and confirms
    max_files=50       # Safety limit
)
```

### CLI Usage
```bash
# Search events
python yaml_tools.py search "Trump" --date-from 2024-01-01 --status confirmed

# Validate with suggestions
python yaml_tools.py validate timeline_data/events/example.yaml

# Check and manage sources
python yaml_tools.py sources timeline_data/events/example.yaml --action check-urls

# Edit with automatic backup
python yaml_tools.py edit timeline_data/events/example.yaml --field importance --value 8 --dry-run
```

### Legacy Method: Manual Event Management
```bash
# 1. Create file with proper naming
touch timeline_data/events/2024-11-20--event-description.yaml

# 2. Add required fields (use template)
# 3. Validate immediately
python timeline_data/validate_yaml.py

# 4. Fix any issues before committing
```

### Updating Existing Events (Legacy)
```bash
# 1. Validate current state
python timeline_data/validate_yaml.py

# 2. Make edits

# 3. Validate changes
python timeline_data/validate_yaml.py

# 4. Check for broken links
python tools/validation/check_all_links.py

# 5. Archive new sources if added
python tools/archiving/archive_with_progress.py
```

### Bulk Operations (Legacy)
```bash
# ALWAYS validate before and after bulk changes
python timeline_data/validate_yaml.py > before.txt
# ... make bulk changes ...
python timeline_data/validate_yaml.py > after.txt
diff before.txt after.txt  # Review what changed
```

## Event Status Definitions

- **confirmed**: Past event with multiple verified sources
- **pending**: Recent event awaiting verification
- **predicted**: Future event based on announcements
- **disputed**: Conflicting reports exist
- **reported**: Single source, unverified
- **reported/contested**: Reported but actively disputed

## Archive Requirements

For confirmed events, create archive URLs:
```bash
# Archive sources for preservation
python tools/archiving/archive_with_progress.py

# Check archive coverage
python tools/archiving/gen_archive_qa.py
```

## Git Commit Standards

Always mention validation in commits:
```bash
git commit -m "Add: 2024-11-20 event (validated, 3 sources)"
git commit -m "Update: Fix date formats in 5 events (validated)"
git commit -m "Fix: Correct validation errors in timeline events"
```

## Emergency Fixes

If validation fails after changes:
```bash
# Auto-fix common issues
python tools/validation/auto_fix_simple_cases.py

# Re-validate
python timeline_data/validate_yaml.py

# If still failing, check specific file
python tools/validation/smart_qa.py --file timeline_data/events/problem-file.yaml
```

## Remember

⚠️ **NEVER commit timeline changes without validating first**
⚠️ **ALWAYS run validate_yaml.py after ANY event modification**
⚠️ **NEVER use underscores in event IDs or filenames**
⚠️ **ALWAYS check that future events are not marked "confirmed"**

---

*These instructions ensure timeline data integrity. Schema validation is not optional—it's mandatory for maintaining data quality.*