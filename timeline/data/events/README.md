# Timeline Events Directory

This directory contains all timeline events in YAML format. Each event documents a specific occurrence related to democratic degradation, corruption, or kleptocracy.

## ⚠️ IMPORTANT: Event Creation and Validation

### Use the Timeline Event Manager Tool

**Always use the `timeline_event_manager.py` tool** instead of manually creating or editing YAML files. This prevents common errors and ensures consistency.

```bash
# From the project root:
python3 scripts/timeline_event_manager.py

# Or if you have the alias set up:
timeline-event
```

The tool provides:
- Automatic ID generation matching the filename
- Date validation
- Status validation
- Required field checks
- Proper YAML formatting
- Duplicate detection

### Manual Editing (Not Recommended)

If you must manually edit files, **always validate** your changes:

```bash
# Run validation tests
python3 tools/validation/validate_timeline_dates.py

# Or run the full test suite
python3 -m pytest tests/test_timeline_validation.py
```

## File Naming Convention

Files must follow this naming pattern:
```
YYYY-MM-DD--descriptive-slug-here.yaml
```

- `YYYY-MM-DD`: The event date
- `--`: Double dash separator
- `descriptive-slug-here`: Lowercase, hyphen-separated description

## Required Fields

Every event MUST have these fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | **Must match the filename** (without .yaml extension) |
| `date` | string | Format: YYYY-MM-DD |
| `title` | string | Brief, factual headline |
| `summary` | string | Detailed description of the event |

## Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | One of: `confirmed`, `alleged`, `reported`, `speculative`, `developing`, `disputed`, `predicted` |
| `tags` | list | Categorization tags |
| `actors` | list | Key people/organizations involved |
| `sources` | list | Source citations (see below) |
| `timeline_tags` | list | Timeline-specific categorization |
| `connections` | list | IDs of related events |

## Source Format

Each source should have:
```yaml
sources:
  - title: "Article Title"
    url: "https://example.com/article"
    date: "2024-01-15"  # Access date, not event date
    outlet: "Publication Name"  # Optional
```

## Validation Rules

1. **ID must match filename**: The `id` field must exactly match the filename (without .yaml)
2. **Date format**: Dates must be YYYY-MM-DD
3. **Future events**: Cannot be marked as `confirmed` if date is in the future
4. **Required fields**: All required fields must be present and non-empty
5. **Status values**: Must be from the allowed set

## Common Errors to Avoid

❌ **Wrong:**
```yaml
id: trump-indicted  # Doesn't match filename
date: 2024/03/30    # Wrong date format
status: proven      # Invalid status
```

✅ **Correct:**
```yaml
id: 2024-03-30--trump-indicted-manhattan
date: 2024-03-30
status: confirmed
```

## Pre-commit Validation

The repository has pre-commit hooks that validate all events before allowing commits. If your commit fails, check the error messages and fix the issues.

## Testing Your Changes

After making changes, always run:

```bash
# Quick validation
python3 -c "
import yaml
from pathlib import Path

errors = []
for f in Path('data/events').glob('*.yaml'):
    with open(f) as file:
        data = yaml.safe_load(file)
        if data.get('id') != f.stem:
            errors.append(f'{f.name}: ID mismatch')

if errors:
    print('❌ Validation failed:')
    for e in errors:
        print(f'  - {e}')
else:
    print('✅ All events valid!')
"
```

## Questions?

If you encounter issues or have questions about event formatting, please:
1. Check existing events for examples
2. Use the `timeline_event_manager.py` tool
3. Run validation tests before committing
4. Open an issue if you need clarification