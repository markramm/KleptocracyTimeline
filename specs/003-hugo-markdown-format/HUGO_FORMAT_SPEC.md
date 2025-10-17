# Hugo-Compatible Markdown Format Specification

**Version**: 1.0
**Created**: 2025-10-17
**Status**: Draft

## Overview

This specification defines the Hugo-compatible markdown format for timeline events. This format is designed for the timeline static site (future standalone repository) while maintaining compatibility with the research server's event creation workflows.

## File Organization

### Directory Structure
```
timeline/
├── content/
│   └── events/
│       ├── 1953/
│       │   └── 1953-04-13-cia-mkultra-project-inception.md
│       ├── 1971/
│       │   └── 1971-08-23-powell-memo-institutional-capture.md
│       └── 2025/
│           └── 2025-01-15-event-slug.md
```

### File Naming Convention
- **Pattern**: `YYYY-MM-DD-event-slug.md`
- **Directory**: Organized by year (`content/events/YYYY/`)
- **Slug**: Descriptive, lowercase, hyphen-separated
- **No underscores**: Use hyphens only for Hugo compatibility

### Examples
```
✅ Good: content/events/2025/2025-01-15-trump-crypto-conflicts.md
✅ Good: content/events/1971/1971-08-23-powell-memo-institutional-capture.md
❌ Bad:  content/events/2025-01-15--event-slug.md (double hyphen)
❌ Bad:  content/events/2025_01_15_event_slug.md (underscores)
```

## Hugo Front Matter Format

### Required Fields
```yaml
---
title: "Event Title"
date: 2025-01-15
importance: 8
draft: false
---
```

### Complete Front Matter Example
```yaml
---
title: "Trump Crypto Conflicts Escalate"
date: 2025-01-15
importance: 8
draft: false

# Taxonomies
tags:
  - cryptocurrency
  - conflicts-of-interest
  - trump-administration
  - financial-corruption

actors:
  - Donald Trump
  - Eric Trump
  - Trump Organization

# Additional Metadata
location: "Washington, DC"
impact_score: 9
verification_status: "verified"
last_updated: 2025-01-15T10:30:00Z
---
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Event title |
| `date` | date | Yes | Event date (YYYY-MM-DD) |
| `importance` | integer | Yes | 1-10 scale |
| `draft` | boolean | Yes | false for published events |
| `tags` | array | No | Event categories/topics |
| `actors` | array | No | People/organizations involved |
| `location` | string | No | Geographic location |
| `impact_score` | integer | No | 1-10 impact rating |
| `verification_status` | string | No | verified/pending/disputed |
| `last_updated` | datetime | No | ISO 8601 timestamp |

## Content Body Format

### Basic Structure
```markdown
---
[Front Matter]
---

Brief summary paragraph introducing the event context and significance.

## Details

Detailed explanation of the event, its background, and implications.

### Key Facts
- Fact 1
- Fact 2
- Fact 3

## Sources

1. [Source Title](https://example.com/article) - Publisher Name, Date
2. [Another Source](https://example.org/report) - Organization, Date
3. [Government Document](https://gov.example/doc.pdf) - Agency, Date

## Related Events

- [Related Event Title](link-to-event)
- [Another Related Event](link-to-event)

## Analysis

Deeper analysis, context, and connections to broader patterns.
```

### Markdown Features

**Supported:**
- Standard markdown (headers, bold, italic, lists)
- Links and images
- HTML (if needed, via `unsafe = true` in hugo.toml)
- Code blocks (for quotes, data, etc.)
- Tables

**Example:**
```markdown
## Key Figures

| Name | Role | Organization |
|------|------|--------------|
| Donald Trump | President | United States |
| Eric Trump | Executive | Trump Organization |
```

## Comparison: JSON vs. Hugo Format

### JSON Format (Current)
```json
{
  "id": "2025-01-15--event-slug",
  "date": "2025-01-15",
  "title": "Event Title",
  "summary": "Event summary here...",
  "importance": 8,
  "tags": ["tag1", "tag2"],
  "actors": ["Actor 1"],
  "sources": [
    {
      "url": "https://example.com",
      "title": "Source Title",
      "type": "article"
    }
  ]
}
```

### Hugo Markdown Format (New)
```markdown
---
title: "Event Title"
date: 2025-01-15
importance: 8
draft: false
tags: ["tag1", "tag2"]
actors: ["Actor 1"]
---

Event summary here...

## Sources

1. [Source Title](https://example.com) - Publication, Date
```

## Conversion Rules

### ID Field
- **JSON**: `id: "2025-01-15--event-slug"`
- **Hugo**: Derived from filename and path
- **Rule**: Remove `id` field, encode in filename

### Date Field
- **JSON**: `date: "2025-01-15"` (string)
- **Hugo**: `date: 2025-01-15` (YAML date without quotes)
- **Rule**: Keep format but remove quotes in YAML

### Summary Field
- **JSON**: `summary: "Text here..."`
- **Hugo**: Content body (after front matter)
- **Rule**: Move summary to markdown body

### Sources Array
- **JSON**: Array of objects with url/title/type
- **Hugo**: Markdown numbered list with links
- **Rule**: Convert to `## Sources` section with links

### Tags and Actors
- **JSON**: `tags: ["tag1", "tag2"]`
- **Hugo**: Same YAML array format
- **Rule**: Keep as-is in front matter

## Validation Rules

### File Validation
1. ✅ Filename matches pattern: `YYYY-MM-DD-slug.md`
2. ✅ File located in correct year directory: `content/events/YYYY/`
3. ✅ Date in filename matches date in front matter
4. ✅ Front matter has all required fields
5. ✅ Importance is integer between 1-10
6. ✅ Tags and actors are valid YAML arrays
7. ✅ Content body is not empty

### Front Matter Validation
```python
required_fields = ["title", "date", "importance", "draft"]
importance_range = (1, 10)
draft_values = [True, False]
```

### Content Validation
- At least 50 characters of content
- At least one source link (recommended)
- Valid markdown syntax
- No broken internal links

## Hugo Integration

### Page Templates
Hugo will use these templates to render events:

**List Template**: `layouts/events/list.html`
- Timeline view
- Filterable by tag, actor, year
- Sortable by date, importance

**Single Template**: `layouts/events/single.html`
- Individual event page
- Full details and sources
- Related events sidebar
- Tag and actor links

### URL Structure
```
https://kleptocracy-timeline.github.io/events/2025/01/event-slug/
https://kleptocracy-timeline.github.io/events/1971/08/powell-memo-institutional-capture/
```

### Taxonomies
- **Tags**: `/tags/cryptocurrency/`, `/tags/corruption/`
- **Actors**: `/actors/donald-trump/`, `/actors/peter-thiel/`
- **Years**: `/events/2025/`, `/events/1971/`

## Research Server Integration

### Event Creation Workflow
1. Research server receives event data (JSON or dict)
2. Convert to Hugo markdown format
3. Write to `content/events/YYYY/YYYY-MM-DD-slug.md`
4. Validate markdown file
5. Commit to timeline repo
6. GitHub Actions triggers Hugo rebuild
7. Static site deployed to GitHub Pages

### Conversion Script Location
- **Script**: `timeline/scripts/json_to_hugo.py`
- **Usage**: `python json_to_hugo.py --input event.json --output content/events/`
- **Batch**: `python json_to_hugo.py --batch timeline_data/events/*.json`

### Update Workflow
- Research server can update existing events
- Preserves Hugo front matter structure
- Updates last_updated timestamp
- Creates git commit with changes

## Migration Strategy

### Phase 1: Proof of Concept (Current)
- ✅ 10 example events in Hugo format
- ✅ Hugo site initialized
- ✅ Configuration complete

### Phase 2: Conversion Script (Next)
- Build JSON → Hugo markdown converter
- Test on 20-50 events
- Validate output

### Phase 3: Batch Conversion
- Convert high-importance events (≥8)
- Convert by date range (oldest first or newest first)
- Validate all conversions

### Phase 4: Full Migration
- Convert remaining 1,500+ events
- Deprecate JSON format in timeline repo
- Keep JSON support in research server

### Phase 5: Repository Split
- Extract timeline/ to standalone repo
- Configure research server to push to timeline repo
- Set up GitHub Actions for auto-rebuild

## Example Event: Complete

```markdown
---
title: "CIA MKULTRA Project Officially Begins"
date: 1953-04-13
importance: 9
draft: false

tags:
  - cia
  - intelligence-operations
  - human-experimentation
  - cold-war
  - mind-control

actors:
  - CIA
  - Allen Dulles
  - Sidney Gottlieb

location: "Langley, Virginia"
impact_score: 10
verification_status: "verified"
last_updated: 2025-10-17T12:00:00Z
---

The CIA formally establishes MKULTRA, a covert program for mind control experimentation, under Director Allen Dulles. The project involved illegal human experimentation with LSD, hypnosis, sensory deprivation, and other psychological techniques, often on unwitting subjects.

## Background

MKULTRA was established in response to alleged Soviet, Chinese, and North Korean use of mind control techniques during the Korean War. CIA Director Allen Dulles authorized the program under the authority of the National Security Act of 1947, allowing covert operations without congressional oversight.

## Key Facts

- **Budget**: Approximately $25 million (1953-1973)
- **Scope**: 149 subprojects at 80+ institutions
- **Subjects**: Thousands of unwitting American and Canadian citizens
- **Techniques**: LSD, hypnosis, sensory deprivation, isolation, verbal and sexual abuse
- **Duration**: 1953-1973 (20 years)

## Significance

MKULTRA represents one of the most egregious violations of medical ethics and human rights by a U.S. government agency. The program:

- Violated the Nuremberg Code on human experimentation
- Operated without informed consent
- Continued for two decades with minimal oversight
- Was only exposed through investigative journalism and FOIA requests
- Led to at least one documented death (Frank Olson, 1953)

## Church Committee Findings

In 1975, the U.S. Senate Church Committee investigated MKULTRA and found:
- Widespread violations of ethical standards
- Destruction of most records in 1973
- Lack of accountability and oversight
- Continuation of similar programs under different names

## Sources

1. [Church Committee Report](https://www.intelligence.senate.gov/sites/default/files/94465.pdf) - U.S. Senate Select Committee, 1975
2. [CIA MKULTRA Documents](https://www.cia.gov/readingroom/collection/foia-collection-cia-mkultra-documents) - CIA Reading Room
3. [The Search for the Manchurian Candidate](https://www.amazon.com/dp/0393307948) - John Marks, 1979
4. [Project MKULTRA: The CIA's Program of Research in Behavioral Modification](https://www.intelligence.senate.gov/sites/default/files/hearings/95mkultra.pdf) - Senate Hearing, 1977

## Related Events

- [1975-04-22: Church Committee Democratic Resistance Framework](../1975/1975-04-22-church-committee-democratic-resistance-framework/)
- [1973-01-01: Destruction of MKULTRA Records](../1973/1973-01-01-mkultra-records-destroyed/)

## Analysis

MKULTRA exemplifies the dangers of unchecked intelligence agency power. Operating with minimal congressional oversight and shrouded in secrecy, the program continued for 20 years before exposure. The destruction of records in 1973 prevented full accountability.

The program's legacy includes:
- Strengthened oversight of intelligence operations
- Formation of congressional intelligence committees
- Reforms to human subject research protections
- Ongoing debate about intelligence agency accountability

The exposure of MKULTRA during the Church Committee investigations became a cornerstone of the post-Watergate reforms, demonstrating the importance of institutional oversight and transparency in preventing government abuse.

---

**Last Updated**: October 17, 2025
**Verification Status**: Verified with primary sources
**Documentation Quality**: Excellent (congressional records, declassified CIA documents)
```

## Implementation Checklist

- [x] Hugo installed and initialized
- [x] Hugo configuration complete
- [x] Content directory structure created
- [x] Format specification documented
- [ ] Conversion script created
- [ ] Test conversion (10-20 events)
- [ ] Hugo templates created
- [ ] Theme configured
- [ ] Test Hugo site build
- [ ] Research server integration
- [ ] Full migration plan

## References

- [Hugo Documentation](https://gohugo.io/documentation/)
- [Hugo Front Matter](https://gohugo.io/content-management/front-matter/)
- [Hugo Content Organization](https://gohugo.io/content-management/organization/)
- [Hugo Taxonomies](https://gohugo.io/content-management/taxonomies/)
- [Timeline Event Format](../002-markdown-event-format/IMPLEMENTATION_REPORT.md)
