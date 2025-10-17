# Technical Implementation Plan: Markdown Event Format

**Spec**: 002-markdown-event-format
**Created**: 2025-10-17
**Status**: Draft

## Architecture Overview

### High-Level Design

```
timeline/data/events/
├── event.json              # Existing JSON format
├── another-event.md        # New markdown format
└── third-event.md          # Both coexist

         ↓ Filesystem Sync

EventParser (Factory Pattern)
├── JsonEventParser
└── MarkdownEventParser
         ↓
    Validation
         ↓
SQLite Database (Unified Storage)
```

### Component Architecture

```
research-server/server/
├── parsers/
│   ├── __init__.py
│   ├── base.py              # EventParser interface
│   ├── json_parser.py       # Existing JSON parser (extract)
│   └── markdown_parser.py   # New markdown parser
├── validators/
│   └── event_validator.py   # Schema validation (existing)
└── app_v2.py                # Updated to use parser factory
```

## Technology Stack

### Core Libraries
| Library | Version | Purpose |
|---------|---------|---------|
| `python-frontmatter` | 1.0.0+ | Parse YAML frontmatter |
| `pyyaml` | 6.0+ | YAML validation |
| `jsonschema` | 4.19+ | Schema validation (existing) |
| `markdown` | 3.5+ | Optional: markdown rendering |

### Installation
```bash
# Add to research-server/requirements.txt
python-frontmatter>=1.0.0
pyyaml>=6.0
markdown>=3.5  # optional
```

## Implementation Strategy

### Phase 1: Parser Infrastructure

#### 1.1 Create Base Parser Interface
**File**: `research-server/server/parsers/base.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path

class EventParser(ABC):
    """Base interface for event file parsers"""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if parser can handle this file"""
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse event file into dictionary"""
        pass

    @abstractmethod
    def validate_format(self, file_path: Path) -> List[str]:
        """Validate file format, return errors"""
        pass
```

#### 1.2 Extract Existing JSON Parser
**File**: `research-server/server/parsers/json_parser.py`

Extract JSON parsing logic from `app_v2.py` into dedicated class:

```python
from pathlib import Path
from typing import Dict, Any, List
import json
from .base import EventParser

class JsonEventParser(EventParser):
    """Parser for JSON event files"""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix == '.json'

    def parse(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def validate_format(self, file_path: Path) -> List[str]:
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
        return errors
```

#### 1.3 Create Markdown Parser
**File**: `research-server/server/parsers/markdown_parser.py`

```python
from pathlib import Path
from typing import Dict, Any, List
import frontmatter
import yaml
from .base import EventParser

class MarkdownEventParser(EventParser):
    """Parser for markdown event files with YAML frontmatter"""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix == '.md'

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse markdown file into event dictionary"""
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # Frontmatter becomes event data
        event_data = dict(post.metadata)

        # Content becomes summary
        if post.content.strip():
            event_data['summary'] = post.content.strip()

        return event_data

    def validate_format(self, file_path: Path) -> List[str]:
        """Validate YAML frontmatter and required fields"""
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            # Check required frontmatter fields
            required = ['id', 'date', 'title']
            for field in required:
                if field not in post.metadata:
                    errors.append(f"Missing required field: {field}")

            # Validate YAML is safe
            yaml.safe_load(frontmatter.dumps(post))

        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML frontmatter: {e}")
        except Exception as e:
            errors.append(f"Parse error: {e}")

        return errors
```

#### 1.4 Create Parser Factory
**File**: `research-server/server/parsers/__init__.py`

```python
from pathlib import Path
from typing import Optional
from .base import EventParser
from .json_parser import JsonEventParser
from .markdown_parser import MarkdownEventParser

class EventParserFactory:
    """Factory to get appropriate parser for event file"""

    def __init__(self):
        self.parsers = [
            JsonEventParser(),
            MarkdownEventParser()
        ]

    def get_parser(self, file_path: Path) -> Optional[EventParser]:
        """Get parser for file, or None if unsupported"""
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        return None

    def parse_event(self, file_path: Path) -> Dict[str, Any]:
        """Parse event file using appropriate parser"""
        parser = self.get_parser(file_path)
        if not parser:
            raise ValueError(f"No parser for {file_path.suffix} files")

        return parser.parse(file_path)
```

### Phase 2: Integration with Filesystem Sync

#### 2.1 Update app_v2.py Sync Logic

**File**: `research-server/server/app_v2.py`

Replace direct JSON parsing with parser factory:

```python
from parsers import EventParserFactory

# In sync_filesystem_to_database()
parser_factory = EventParserFactory()

for event_file in events_path.glob('*.json'):
    # Existing JSON logic
    ...

# Add markdown support
for event_file in events_path.glob('*.md'):
    try:
        event_data = parser_factory.parse_event(event_file)

        # Validate against schema
        validator.validate_event(event_data)

        # Upsert to database (same as JSON)
        event = db.query(TimelineEvent).filter_by(id=event_data['id']).first()
        if not event:
            event = TimelineEvent()
            db.add(event)

        # Update fields
        event.id = event_data['id']
        event.date = datetime.strptime(event_data['date'], '%Y-%m-%d')
        event.title = event_data['title']
        # ... etc

        db.commit()
        synced_count += 1

    except Exception as e:
        logger.error(f"Failed to sync markdown event {event_file}: {e}")
        continue
```

### Phase 3: Validation Enhancement

#### 3.1 Schema Validation
**File**: `research-server/server/validators/event_validator.py`

Existing schema validation works for both formats (validates dictionary):

```python
# No changes needed - validates dict regardless of source
def validate_event(self, event_data: Dict[str, Any]) -> List[str]:
    """Validate event against JSON schema"""
    errors = []
    try:
        jsonschema.validate(event_data, self.schema)
    except jsonschema.ValidationError as e:
        errors.append(str(e))
    return errors
```

#### 3.2 Helpful Error Messages

Add format-specific error messages:

```python
def validate_event_file(self, file_path: Path) -> List[str]:
    """Validate event file with format-specific errors"""
    errors = []

    # Format validation
    parser = parser_factory.get_parser(file_path)
    if not parser:
        return [f"Unsupported format: {file_path.suffix}"]

    format_errors = parser.validate_format(file_path)
    errors.extend(format_errors)

    # Schema validation
    try:
        event_data = parser.parse(file_path)
        schema_errors = self.validate_event(event_data)
        errors.extend(schema_errors)
    except Exception as e:
        errors.append(f"Parse error: {e}")

    return errors
```

### Phase 4: CLI Tool Updates

#### 4.1 Update research_cli.py

**File**: `research-server/cli/research_cli.py`

Add support for markdown in existing commands:

```python
@click.command()
@click.option('--file', type=click.Path(exists=True), required=True)
def validate_event(file):
    """Validate event file (JSON or Markdown)"""
    file_path = Path(file)

    # Detect format
    parser = parser_factory.get_parser(file_path)
    if not parser:
        click.echo(f"Error: Unsupported format {file_path.suffix}")
        return

    # Validate
    errors = validator.validate_event_file(file_path)
    if errors:
        click.echo("Validation failed:")
        for error in errors:
            click.echo(f"  - {error}")
    else:
        click.echo("✓ Valid event file")
```

#### 4.2 Add Conversion Command

```python
@click.command()
@click.argument('json_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path())
def convert_to_markdown(json_file, output):
    """Convert JSON event to Markdown format"""
    json_path = Path(json_file)

    # Parse JSON
    json_parser = JsonEventParser()
    event_data = json_parser.parse(json_path)

    # Generate markdown
    md_content = generate_markdown_from_dict(event_data)

    # Write output
    output_path = Path(output) if output else json_path.with_suffix('.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    click.echo(f"✓ Converted to {output_path}")
```

### Phase 5: Documentation & Examples

#### 5.1 Create Event Format Guide
**File**: `timeline/docs/EVENT_FORMAT.md`

Document both JSON and Markdown formats with examples.

#### 5.2 Update CONTRIBUTING.md

Add section on markdown events:

```markdown
## Adding Events (Markdown Format)

Create a new file in `timeline/data/events/`:

1. Filename: `YYYY-MM-DD--event-slug.md`
2. Format:
   - YAML frontmatter with metadata
   - Markdown body with summary
3. Submit pull request

[See examples](./examples/)
```

#### 5.3 Create Example Events

Convert 10 high-visibility events:
- Powell Memo
- Citizens United
- WHIG formation
- Financial crisis events
- Recent Trump events

#### 5.4 GitHub Issue Template

**File**: `.github/ISSUE_TEMPLATE/markdown-event.md`

```markdown
---
name: Add Event (Markdown)
about: Contribute a timeline event using markdown format
---

## Event Information

**Date**: YYYY-MM-DD
**Title**: Brief event title

## Event File

Please create a markdown file following this template:

\`\`\`markdown
---
id: YYYY-MM-DD--event-slug
date: YYYY-MM-DD
title: Event Title
importance: 5
tags:
  - tag1
  - tag2
sources:
  - url: https://example.com
    title: Source Title
    publisher: Publisher Name
    tier: 1
---

Event summary here...
\`\`\`

[Full format documentation](link)
```

### Phase 6: Testing Strategy

#### 6.1 Unit Tests

**File**: `research-server/tests/test_markdown_parser.py`

```python
import unittest
from pathlib import Path
from parsers.markdown_parser import MarkdownEventParser

class TestMarkdownParser(unittest.TestCase):
    def setUp(self):
        self.parser = MarkdownEventParser()

    def test_can_parse_md_files(self):
        self.assertTrue(self.parser.can_parse(Path('event.md')))
        self.assertFalse(self.parser.can_parse(Path('event.json')))

    def test_parse_valid_markdown(self):
        # Create temporary markdown file
        test_file = Path('/tmp/test_event.md')
        test_file.write_text("""---
id: 2025-01-01--test
date: 2025-01-01
title: Test Event
importance: 5
tags: [test]
---
Test summary""")

        event_data = self.parser.parse(test_file)

        self.assertEqual(event_data['id'], '2025-01-01--test')
        self.assertEqual(event_data['title'], 'Test Event')
        self.assertEqual(event_data['summary'], 'Test summary')

    def test_validate_missing_required_fields(self):
        test_file = Path('/tmp/invalid.md')
        test_file.write_text("""---
title: Missing ID and Date
---
Summary""")

        errors = self.parser.validate_format(test_file)

        self.assertIn('Missing required field: id', errors)
        self.assertIn('Missing required field: date', errors)

    # More tests...
```

#### 6.2 Integration Tests

Test markdown events through full sync cycle:

```python
def test_markdown_event_filesystem_sync(self):
    """Test markdown event syncs to database"""
    # Create markdown event file
    md_path = events_path / '2025-01-01--test.md'
    md_path.write_text(markdown_content)

    # Trigger sync
    sync_filesystem_to_database()

    # Verify in database
    event = db.query(TimelineEvent).filter_by(id='2025-01-01--test').first()
    self.assertIsNotNone(event)
    self.assertEqual(event.title, 'Test Event')
```

#### 6.3 Validation Tests

Test schema validation works for both formats:

```python
def test_schema_validation_for_markdown(self):
    """Schema validation works same for markdown and JSON"""
    json_event = json_parser.parse('event.json')
    md_event = markdown_parser.parse('event.md')

    json_errors = validator.validate_event(json_event)
    md_errors = validator.validate_event(md_event)

    # Both should pass or fail consistently
    self.assertEqual(len(json_errors), len(md_errors))
```

#### 6.4 Performance Tests

Benchmark markdown vs JSON parsing:

```python
def test_parsing_performance(self):
    """Markdown parsing should be <5% slower than JSON"""
    json_time = timeit.timeit(lambda: json_parser.parse('event.json'), number=1000)
    md_time = timeit.timeit(lambda: md_parser.parse('event.md'), number=1000)

    slowdown_pct = ((md_time - json_time) / json_time) * 100
    self.assertLess(slowdown_pct, 5.0)
```

### Phase 7: Pre-commit Hooks

#### 7.1 Add Markdown Validation Hook

**File**: `.github/workflows/validate-events.yml`

```yaml
name: Validate Events

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install python-frontmatter pyyaml jsonschema

      - name: Validate JSON events
        run: |
          python scripts/validate_events.py --format json

      - name: Validate Markdown events
        run: |
          python scripts/validate_events.py --format markdown
```

#### 7.2 Local Pre-commit Hook

**File**: `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Validate changed event files before commit

for file in $(git diff --cached --name-only | grep 'timeline/data/events/.*\.\(json\|md\)$'); do
    echo "Validating $file..."
    python3 research-server/cli/research_cli.py validate-event --file "$file"
    if [ $? -ne 0 ]; then
        echo "Validation failed for $file"
        exit 1
    fi
done
```

## Migration Strategy

### Converting Existing Events

**Priority Order**:
1. High-visibility events (Powell Memo, Citizens United, etc.)
2. Events with many sources (easier to format)
3. Events needing updates anyway
4. Recent events (likely to be edited)

**Conversion Process**:
```bash
# Convert single event
python3 research-server/cli/research_cli.py convert-to-markdown \
    timeline/data/events/1971-08-23--powell-memo.json

# Batch convert (if desired)
for file in timeline/data/events/2020-*.json; do
    python3 research-server/cli/research_cli.py convert-to-markdown "$file"
done
```

**Timeline**:
- Week 1: Convert 10 example events
- Month 1: Convert 50-100 high-priority events
- Month 3: Convert 200-300 events (as edited)
- Year 1: Gradual conversion of remaining events

## Deployment Plan

### Development
1. Implement parsers on feature branch
2. Add comprehensive tests
3. Test with 10 converted events
4. Review and iterate

### Staging
1. Deploy to development server
2. Convert 50 events
3. Monitor for issues
4. Load testing

### Production
1. Merge to main branch
2. Update documentation
3. Announce markdown support
4. Monitor contributions

## Rollback Plan

If critical issues discovered:

1. **Disable markdown parsing**: Comment out `.md` glob in sync
2. **Revert parser changes**: Git revert to before parser refactor
3. **Remove markdown events**: Move to separate branch
4. **Document issues**: Create spec for fixes

Rollback should take <30 minutes.

## Performance Considerations

### Parsing Performance
- **Target**: <5% slower than JSON
- **Optimization**: Cache parsed frontmatter
- **Monitoring**: Log parse times

### Memory Usage
- **Estimate**: Markdown events ~10-20% larger
- **Total impact**: 1,580 events * 20% = ~2-3 MB increase
- **Acceptable**: Well within limits

### Startup Time
- **Current**: ~2 seconds to sync 1,580 events
- **Target**: <2.5 seconds with mixed formats
- **Monitoring**: Log sync time

## Security Considerations

### YAML Safety
```python
# ALWAYS use safe_load, never load()
yaml.safe_load(content)  # ✓ Safe
yaml.load(content)       # ✗ Unsafe - code execution
```

### Markdown Injection
- No HTML rendering in research server
- Content stored as plain text
- Hugo handles rendering (trusted environment)

### File Permissions
- Same as JSON events: 644 (rw-r--r--)
- No executable permissions
- Normal git file handling

## Monitoring & Metrics

### Success Metrics
- Contribution rate increase
- JSON syntax errors decrease
- Markdown adoption rate
- User feedback sentiment

### Technical Metrics
- Parse error rate (target: <1%)
- Validation pass rate (target: >99%)
- Performance impact (target: <5%)
- Test coverage (target: >80%)

## Open Questions

1. **Markdown rendering**: Should we render markdown in viewer?
   - **Decision needed**: Week 1

2. **Format preference**: Guide users to one format?
   - **Decision needed**: Month 3 (after usage data)

3. **Hugo priority**: When to implement static site?
   - **Decision needed**: Week 2 (based on capacity)

4. **Linting**: Enforce style in markdown?
   - **Decision needed**: Week 4 (after initial adoption)

## Dependencies & Prerequisites

- [x] Repository restructured
- [x] Research server working
- [ ] Install python-frontmatter library
- [ ] Create parser infrastructure
- [ ] Write tests
- [ ] Update documentation

## Next Steps

1. Create detailed task breakdown (`tasks.md`)
2. Review plan with maintainer
3. Begin implementation
4. Iterate based on feedback

---

**Ready for task breakdown**: Yes
**Estimated timeline**: 2-3 weeks to production-ready
**Risk level**: Low (backward compatible, well-scoped)
