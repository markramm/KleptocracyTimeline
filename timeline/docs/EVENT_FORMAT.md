# Timeline Event Format Guide

This document describes the event format for timeline events in the Kleptocracy Timeline project.

## Event Format

The timeline uses **Markdown** (`.md`) files with YAML frontmatter as the canonical event format.

This format provides:
- **Human-friendly editing** - Easy to read and edit in any text editor
- **GitHub-native UX** - Edit events directly on GitHub with full markdown preview
- **Structured metadata** - YAML frontmatter for machine-readable fields
- **Rich formatting** - Full markdown support for summaries and descriptions
- **Version control friendly** - Clean, readable diffs in git history

## Why Markdown?

Markdown with YAML frontmatter provides the best balance of human readability and machine parseability. It enables:
- Quick edits via GitHub's web interface
- Better collaboration with markdown preview
- Rich text formatting for complex summaries
- Clean, readable event files

## Event Schema

All events must include these **required fields**:
- `id` - Unique identifier in format `YYYY-MM-DD--descriptive-slug`
- `date` - Event date in ISO format `YYYY-MM-DD`
- `title` - Brief, descriptive title
- `summary` - Detailed description of the event

Optional fields include:
- `importance` - Numeric score 1-10 (1=minor, 10=critical)
- `tags` - Array of topic/category tags
- `actors` - Array of people/organizations involved
- `sources` - Array of source citations
- `status` - Verification status (confirmed, validated, disputed, etc.)
- `related_events` - Array of related event IDs

## Markdown Format Examples

### Minimal Example

```markdown
---
id: 2025-01-15--event-slug
date: 2025-01-15
title: Event Title
---

Detailed description of what happened and why it matters.
```

### Complete Example

```markdown
---
id: 2025-01-15--federal-contract-investigation
date: 2025-01-15
title: Federal Investigation into No-Bid Contract Announced
importance: 8
status: confirmed
tags:
  - corruption
  - government-contracts
  - doj-investigation
actors:
  - Department of Justice
  - Company X
  - Official Name
sources:
  - url: https://www.reuters.com/article/investigation-2025
    title: DOJ Announces Investigation into No-Bid Contract
    publisher: Reuters
    date: 2025-01-15
    tier: 1
  - url: https://www.npr.org/investigation-details
    title: Details of Federal Contract Investigation
    publisher: NPR
    date: 2025-01-15
    tier: 1
related_events:
  - 2025-01-01--contract-award
---

The Department of Justice announced an investigation into a $500 million no-bid contract awarded to Company X. The investigation will examine potential violations of federal procurement law and conflicts of interest involving senior officials.

## Background

The contract was awarded in January 2025 without competitive bidding...

## Significance

This investigation represents the first major corruption probe...
```

### Markdown Format Notes

1. **YAML Frontmatter** - Metadata goes between `---` markers at the top
2. **Summary Content** - Everything after the frontmatter becomes the `summary` field
3. **Markdown Formatting** - You can use standard Markdown (headers, lists, links, bold, etc.)
4. **Date Handling** - Dates in YAML can be written as `2025-01-15` or `"2025-01-15"` (both work)
5. **Arrays** - Use YAML array syntax with hyphens for lists

## Source Citation Format

Sources follow this structure:

```yaml
sources:
  - url: https://example.com/article
    title: Article Title
    publisher: Publisher Name
    date: 2025-01-15
    tier: 1
    access_date: 2025-01-16  # optional
    archive_url: https://archive.org/...  # optional
```

**Source Tiers:**
- **Tier 1**: Major news outlets (Reuters, AP, Bloomberg, NPR, PBS, WSJ, NYT, WaPo)
- **Tier 2**: Secondary news sources, investigative journalism, government documents
- **Tier 3**: Analysis, opinion pieces, social media (use sparingly)

## Importance Scores

Guide for assigning importance scores:

- **1-3**: Minor events with limited impact
- **4-6**: Significant events affecting specific areas
- **7-8**: Major events with broad institutional impact
- **9-10**: Critical events marking major systemic changes or crises

## Event ID Format

Event IDs must follow this format: `YYYY-MM-DD--descriptive-slug`

**Examples:**
- ✅ `2025-01-15--doj-announces-investigation`
- ✅ `2002-08-01--whig-formation`
- ❌ `2025-01-15-event` (single dash)
- ❌ `my-event-2025` (date not at start)
- ❌ `2025-01-15--Event-Title` (no capitals in slug)

**Slug Guidelines:**
- Use lowercase letters, numbers, and hyphens only
- Be descriptive but concise (3-5 words ideal)
- Include key actors/organizations when relevant
- Make it searchable (think: what would someone search for?)

## Validation

All events are automatically validated for:
- Required fields present
- Proper date format (YYYY-MM-DD)
- Valid event ID format
- Source URL format (if provided)
- Reasonable importance scores (1-10)

Use the research CLI to validate events before committing:

```bash
# Validate JSON event
python3 research_cli.py validate-event --file event.md

# Validate Markdown event
python3 research_cli.py validate-event --file event.md
```

## Converting Between Formats

### JSON to Markdown

Use the conversion script:

```bash
# No longer needed - all events are now in markdown format
```

Or programmatically:
```bash
# All events are stored in markdown format with .md extension
```

This will create `2025-01-15--event.md` with the same data.

### Markdown to JSON

No conversion tool needed - both formats are parsed identically by the system. If you need JSON output for a Markdown event, just parse it with the research CLI:

```bash
python3 research_cli.py get-event --id "2025-01-15--event-slug"
```

## Best Practices

### Writing Good Summaries

1. **Start with the core fact** - What happened?
2. **Provide context** - Why does it matter?
3. **Include key details** - Who, what, when, where, how much?
4. **Cite sources** - At minimum 2 credible sources
5. **Use clear language** - Avoid jargon when possible
6. **Be objective** - Present facts, not opinions

### Example of a Good Summary

```markdown
The Department of Justice announced charges against three executives
of Company X for defrauding the government of $50 million through
false billing on federal contracts. The indictment alleges the
executives created shell companies to inflate costs and secure
no-bid contracts between 2020-2024. This represents one of the
largest procurement fraud cases in the agency's history.
```

### Example of a Poor Summary

```markdown
Some people got in trouble for doing bad things with government money.
```

### Choosing Tags

- Use **existing tags** when possible (check existing events or the tag index)
- Create **new tags** only for genuinely new topics
- Prefer **specific tags** over generic ones
- Use **3-5 tags** per event (not too many)
- Use **lowercase-with-hyphens** format

**Good tag examples:**
- `regulatory-capture`
- `doj-investigation`
- `no-bid-contract`
- `conflict-of-interest`

**Poor tag examples:**
- `important` (too vague)
- `corruption-and-fraud-and-abuse` (too long)
- `Corruption` (should be lowercase)

### Source Selection

1. **Prioritize primary sources** - Government documents, court filings, official statements
2. **Use tier-1 news outlets** - Reuters, AP, Bloomberg for factual reporting
3. **Include investigative journalism** - ProPublica, ICIJ, The Intercept for in-depth analysis
4. **Archive sources** - Use archive.org or archive.is for important articles
5. **Verify dates** - Ensure source dates match or are close to event date

## File Organization

Events are stored in `data/events/`:

```
data/events/
├── 1971-08-23--powell-memo-institutional-capture.md
├── 1973-01-01--heritage-foundation-establishment.json
├── 2002-08-01--whig-formation.md
├── 2025-01-15--federal-investigation.json
└── README.md
```

**Naming conventions:**
- File name **must match** the event ID (plus file extension)
- Use `.md` extension for markdown files
- One event per file

## Troubleshooting

### "Missing required field" error

Make sure all required fields are present:
- `id`
- `date`
- `title`
- `summary` (or markdown content after frontmatter)

### "Invalid date format" error

Dates must be in `YYYY-MM-DD` format:
- ✅ `2025-01-15`
- ✅ `2025-01-01`
- ❌ `01-15-2025`
- ❌ `2025/01/15`
- ❌ `January 15, 2025`

### "Event not syncing to database" error

Check:
1. File name matches event ID
2. File is in `data/events/` directory
3. File is not hidden (doesn't start with `.`)
4. File is not `README.md`
5. JSON is valid (use `jq` or `python -m json.tool`)
6. YAML frontmatter is valid (no syntax errors)

### "YAML parsing error"

Common YAML issues:
- Unmatched quotes: `title: "Event` → `title: "Event"`
- Wrong indentation: Use 2 spaces, not tabs
- Missing colons: `title Event` → `title: Event`
- List format: Use `- item` with hyphen and space

## Getting Help

- Check existing events in `data/events/` for examples
- Run validation: `python3 research_cli.py validate-event --file event.md`
- View the schema: Check `timeline/docs/SCHEMA.md`
- Ask in issues: Create an issue on GitHub for format questions

## Related Documentation

- [Contributing Guide](../../CONTRIBUTING.md) - How to contribute events
- [Research CLI Guide](../../CLAUDE.md) - Using the research CLI
- [Timeline Schema](SCHEMA.md) - Complete field definitions
