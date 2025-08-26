# Timeline Data Documentation

## Overview

This directory contains 318+ chronological timeline events documenting kleptocratic capture patterns and democratic system failures from 1972 to present. Each event is stored as a YAML file with structured metadata, source citations, and verification status.

## 🗺️ Critical Project Resources Map

### Primary Working Directories
- **`/timeline_data/events/`** - 318+ YAML event files (main data)
- **`/timeline_data/`** - Validation scripts and documentation
- **`/DemocracyResearchDocs/queue/`** - PDFs to process (2 remaining)
- **`/DemocracyResearchDocs/completed/`** - Processed PDFs (4 completed)

### Key Scripts & Tools
- **`validate_yaml.py`** - ⚠️ RUN FREQUENTLY - Validates all YAML syntax
- **`archive_links_slow.py`** - Archives to archive.org (5/min rate limit)
- **`find_broken_links.py`** - Identifies broken source URLs
- **`fix_archive_urls.py`** - Repairs malformed archive URLs

### Documentation
- **`README.md`** - This file - Human documentation
- **`AGENT.md`** - AI agent instructions & YAML escaping guide
- **`CLAUDE.md`** - Claude-specific context and patterns

## Table of Contents

1. [File Structure](#file-structure)
2. [Naming Convention](#naming-convention)
3. [Event Schema](#event-schema)
4. [Citation Requirements](#citation-requirements)
5. [Inclusion Criteria](#inclusion-criteria)
6. [Search Methodology](#search-methodology)
7. [Quality Assurance](#quality-assurance)
8. [Working with Data](#working-with-data)
9. [Current Statistics](#current-statistics)

## File Structure

```
timeline_data/
├── YYYY-MM-DD--event-name.yaml   # 303+ individual event files
├── scripts/                       # Management and validation tools
│   ├── validation/               # Data quality checks
│   ├── archiving/               # Wayback Machine tools
│   ├── sources/                 # Source management
│   ├── fixes/                   # Data cleanup utilities
│   └── testing/                 # Test scripts
├── reports/                      # Generated validation reports
├── README.md                     # This documentation
└── AGENT.md                      # AI agent guidance
```

## Naming Convention

### CRITICAL: No Underscores Allowed

**File names and IDs must use HYPHENS ONLY - NO UNDERSCORES**

### File Names
Event files must follow this strict naming pattern:
```
YYYY-MM-DD--event-id-with-hyphens.yaml
```

**Rules:**
- Date format: `YYYY-MM-DD` (ISO 8601)
- Separator: `--` (double hyphen between date and ID)
- ID: lowercase letters, numbers, and **hyphens only**
- **NO UNDERSCORES (_)** anywhere in filenames or IDs
- Extension: `.yaml`

**Examples:**
- ✅ `2024-01-15--trump-cabinet-wealth-report.yaml`
- ✅ `2025-03-01--scotus-ruling-chevron.yaml`  
- ✅ `2024-06-27--scotus-sec-v-jarkesy.yaml`
- ❌ `2024_01_15--event.yaml` (underscores in date)
- ❌ `2024-01-15--event_name.yaml` (underscores in ID)
- ❌ `2024-01-15--scotus_ruling.yaml` (underscores not allowed)

### Event IDs
The `id` field in the YAML must match the ID portion of the filename:
```yaml
id: trump-cabinet-wealth  # ✅ Correct - uses hyphens
id: trump_cabinet_wealth  # ❌ Wrong - uses underscores
```

**ID Requirements:**
- Use hyphens (-) not underscores (_)
- Keep descriptive but concise
- Must be unique across all events
- Must exactly match the filename ID portion

All timeline files follow strict naming format: `YYYY-MM-DD--event-description.yaml`

### Format Rules
- **Date prefix**: ISO 8601 format (YYYY-MM-DD)
- **Separator**: Double dash (`--`) separates date from description
- **Description**: Lowercase, hyphens between words, no underscores
- **Extension**: Always `.yaml`

### Examples
✅ Correct: `2024-11-05--election-results-announced.yaml`
❌ Wrong: `2024-11-05_election_results.yaml` (uses underscore)
❌ Wrong: `2024-11-5--election.yaml` (date not zero-padded)

## Event Schema

### Required Fields

```yaml
id: YYYY-MM-DD--event-description  # Must match filename without .yaml
date: 'YYYY-MM-DD'                  # ISO 8601 date format, quoted
title: Event Title                  # Concise, factual, neutral tone
summary: |                          # Comprehensive description
  Detailed explanation of what happened,
  why it matters, and its implications
  for democratic systems
status: confirmed                   # One of: confirmed|pending|predicted|disputed
```

### Optional but Recommended Fields

```yaml
location: City, State/Country       # Geographic location
actors:                             # Key people/organizations involved
  - Person Name
  - Organization Name
tags:                               # Categorization (see Tag Categories)
  - democratic-erosion
  - regulatory-capture
sources:                            # Citations (REQUIRED for confirmed status)
  - title: Article Headline
    url: https://original-source.com/article
    outlet: Publication Name
    date: '2024-01-15'
    archived_url: https://web.archive.org/...
    author: Reporter Name           # Optional
notes: |                           # Internal research notes
  Additional context not in summary
related_events:                     # Links to connected events
  - 2023-01-15--previous-event
  - 2024-03-20--consequence-event
consequences:                       # Direct outcomes
  - Specific outcome or impact
patterns:                          # Recurring patterns observed
  - kleptocratic-capture
  - institutional-decay
```

## Citation Requirements

### Verification Status Levels

#### 1. **Confirmed** (Highest Standard)
- ✅ Event date is in the past
- ✅ Multiple credible sources (2+ preferred)
- ✅ Sources have been accessed and content verified
- ✅ All claims in summary are supported by sources
- ✅ Archive URLs provided for key sources
- ✅ No contradicting credible reports

#### 2. **Pending**
- Single source or breaking news
- Recent events awaiting additional verification
- Sources not yet fully reviewed
- Archive URLs being created

#### 3. **Predicted**
- Future events based on official announcements
- Scheduled proceedings (trials, hearings, elections)
- Policy implementations with set dates
- Must update to confirmed/disputed after date passes

#### 4. **Disputed**
- Conflicting credible reports exist
- Key facts are contested
- Different sources report different versions
- Requires note explaining the dispute

### Source Format Requirements

```yaml
sources:
  - title: Full Article Headline      # REQUIRED: Exact headline
    url: https://original.url         # REQUIRED: Original URL
    outlet: Washington Post           # REQUIRED: Publication name
    date: '2024-01-15'                # REQUIRED: Publication date
    archived_url: https://web.archive.org/... # STRONGLY RECOMMENDED
    author: Jane Doe                  # Optional: Byline
    verified_claims:                  # Optional: For tracking
      - "Attorney General resignation"
      - "DOJ independence concerns"
```

### Archive Requirements

**Priority Archives** (Must archive within 48 hours):
- Government statements/documents
- Corporate press releases
- Controversial or disputed events
- Sources from outlets prone to paywall/deletion
- Social media posts

**Archive Services** (in order of preference):
1. Internet Archive (archive.org)
2. Archive.today (archive.is)
3. Perma.cc (for legal documents)
4. Screenshots with metadata (last resort)

## Inclusion Criteria

### Required Criteria (Must Meet ALL)

1. **Democratic Relevance**
   - Impacts democratic institutions or norms
   - Demonstrates capture or corruption patterns
   - Affects electoral integrity
   - Involves disinformation/information warfare
   - Shows regulatory or judicial capture

2. **Systemic Significance**
   - Not an isolated incident
   - Part of documented pattern
   - Sets precedent or policy
   - Has measurable institutional impact
   - Affects multiple stakeholders

3. **Factual Verifiability**
   - Based on documented facts, not speculation
   - Has specific date and details
   - Named actors (not anonymous sources only)
   - Corroborated by credible sources

4. **Neutral Documentation**
   - Uses objective, factual language
   - Avoids editorial commentary in title/summary
   - Includes relevant perspectives
   - Separates facts from analysis

### Exclusion Criteria (Do NOT Include)

❌ Opinion pieces without factual events
❌ Unverified rumors or speculation
❌ Personal scandals without systemic relevance
❌ Minor policy disagreements
❌ Events without reliable sources
❌ Duplicate events (merge instead)
❌ Pure predictions without official basis

### Edge Cases

For borderline events, ask:
1. Will this matter in 5 years?
2. Does it reveal systemic issues?
3. Is it part of a larger pattern?
4. Can it be objectively documented?

If 3+ are "yes", consider inclusion with `pending` status.

## Search Methodology

### Primary Source Hierarchy

1. **Official Documents** (Highest credibility)
   - Government reports/releases
   - Court filings and decisions
   - Legislative records
   - Regulatory filings
   - FOIA documents

2. **Institutional Sources**
   - Academic research
   - Think tank reports (note bias)
   - NGO investigations
   - International observer reports

3. **Journalistic Sources**
   - Investigative reporting
   - Major newspaper reporting
   - Wire services (AP, Reuters)
   - Fact-checking organizations
   - Local news (for local events)

4. **Corporate/Organizational**
   - Press releases
   - SEC filings
   - Shareholder reports
   - Official statements

### Search Process

1. **Initial Discovery**
   ```
   - Monitor key sources daily
   - Set up Google Alerts for key terms
   - Check court dockets (PACER, Courtlistener)
   - Review government releases
   ```

2. **Verification Steps**
   ```
   - Find original source/document
   - Cross-reference 2+ sources
   - Check for corrections/retractions
   - Verify dates and actors
   - Look for opposing viewpoints
   ```

3. **Documentation**
   ```
   - Create timeline entry with pending status
   - Add all sources with dates
   - Create archive URLs
   - Note any disputes or uncertainties
   - Update status after full verification
   ```

### Testing Methodology

Before marking as `confirmed`, verify:

- [ ] Date accuracy (check multiple sources)
- [ ] Actor identification (full names, roles)
- [ ] Claim verification (each claim has source)
- [ ] Source quality (credible, accessible)
- [ ] Archive creation (especially priority sources)
- [ ] Pattern identification (link related events)
- [ ] Neutral language (remove editorial tone)

## Quality Assurance

### Validation Scripts

```bash
# Daily validation routine
python scripts/validate_timeline_dates.py      # Check dates and status
python scripts/validation/final_quality_check.py # Comprehensive validation
python scripts/build_timeline_index.py         # Generate searchable index
python scripts/link_check.py timeline_data/    # Verify source URLs

# Archive management
python scripts/archiving/quick_archive.py      # Archive new sources
python scripts/archiving/final_archive_report.py # Archive coverage report

# Fix common issues
python scripts/fixes/fix_critical_issues.py    # Auto-fix formatting
python scripts/rename_timeline_separator.py    # Fix naming convention
```

### Review Checklist

#### For New Events
1. Create file with correct naming format
2. Add all required fields
3. Set status to `pending`
4. Include initial sources
5. Run validation scripts
6. Create archive URLs
7. Cross-reference additional sources
8. Update to `confirmed` when verified

#### For Updates
1. Preserve original sources
2. Add new sources with dates
3. Update summary if significant new info
4. Document changes in notes field
5. Re-run validation
6. Update status if needed

### Common Validation Errors

| Error | Solution |
|-------|----------|
| "Future date with confirmed status" | Change to `predicted` or fix date |
| "ID doesn't match filename" | Ensure id field matches filename without .yaml |
| "Missing required field" | Add missing field (usually status or summary) |
| "Invalid date format" | Use YYYY-MM-DD format with quotes |
| "No sources for confirmed event" | Add sources or change to pending |

## Working with Data

### Adding New Events

```bash
# 1. Create new file
touch timeline_data/2024-11-20--event-description.yaml

# 2. Add required fields (see template below)
# 3. Validate
python scripts/validate_timeline_dates.py

# 4. Archive sources
python scripts/archiving/quick_archive.py

# 5. Commit with clear message
git add timeline_data/2024-11-20--event-description.yaml
git commit -m "Add: 2024-11-20 event description (confirmed with 3 sources)"
```

### Event Template

```yaml
id: 2024-11-20--event-description
date: '2024-11-20'
title: Concise Factual Title
summary: |
  Comprehensive description of what happened.
  Include key actors, actions, and implications.
  Explain significance to democratic systems.
status: pending
location: Washington, DC
actors:
  - Key Person
  - Organization
tags:
  - appropriate-category
  - another-tag
sources:
  - title: Article Headline
    url: https://source.com/article
    outlet: Publication
    date: '2024-11-20'
notes: |
  Internal notes for researchers
```

### Linking Related Events

Use `related_events` to connect:

```yaml
related_events:
  - 2024-01-15--preceding-cause
  - 2024-11-21--immediate-consequence
  - 2023-11-20--similar-pattern-previous-year
```

### Tag Categories

#### System/Pattern Tags
- `democratic-erosion` - Weakening of democratic norms
- `kleptocratic-capture` - Corruption for private gain
- `regulatory-capture` - Agencies serving special interests
- `judicial-capture` - Court system compromise
- `electoral-manipulation` - Voting/election interference
- `disinformation` - Coordinated false information
- `institutional-decay` - Breakdown of governing norms
- `authoritarian-tactics` - Anti-democratic methods

#### Actor Category Tags
- `executive-branch` - Presidential/administrative
- `legislative-branch` - Congressional
- `judicial-branch` - Courts/judges
- `state-government` - State-level actors
- `local-government` - Municipal/county
- `political-parties` - Party organizations
- `tech-platforms` - Social media/tech companies
- `media-manipulation` - Press/propaganda
- `foreign-influence` - International actors
- `corporate-influence` - Business interests

#### Subject Tags
- `surveillance` - Privacy/monitoring
- `censorship` - Speech restrictions
- `protest-suppression` - Assembly rights
- `voting-rights` - Electoral access
- `rule-of-law` - Legal system integrity
- `transparency` - Government openness
- `accountability` - Oversight/consequences
- `norms-violation` - Breaking precedents

## Current Statistics

As of August 2025:
- **Total Events**: 318
- **Date Range**: 1972-01-01 to 2025-10-01
- **Confirmed Events**: ~260
- **Pending Verification**: ~55
- **Archive Coverage**: 60.8%
- **Source Coverage**: 100%
- **Unique Tags**: 548
- **Active Patterns**: 15+
- **Research Docs Processed**: 4 of 6
- **New Events Added Today**: 18

### Coverage by Era
- 1972-1990: Foundation/historical context
- 1990-2000: Early digital age transitions
- 2000-2010: Post-9/11 institutional changes
- 2010-2016: Social media emergence
- 2016-2020: Acceleration period
- 2020-2025: Democratic crisis/recovery

## Data Integrity

### Git Commit Standards

```bash
# Adding events
git commit -m "Add: 2024-11-20 Attorney General resignation (confirmed)"

# Updating events  
git commit -m "Update: 2024-11-20 event - add court filing source"

# Fixing issues
git commit -m "Fix: 2024-11-20 event - correct date format"

# Bulk changes
git commit -m "Validate: Fix 15 events with missing status field"
```

### Backup Strategy
- Git repository (primary)
- Generated JSON indexes (timeline_data/reports/)
- Archive.org backups of sources
- Periodic full exports

## Related Documentation

- `/timeline_data/AGENT.md` - AI agent CRUD guidance
- `/scripts/README.md` - Script documentation
- `/posts/_footnotes/` - Generated citations
- `/timeline-app/` - React visualization app
- `/TIMELINE_README.md` - System overview

## Contributing

Before contributing:
1. Read this README thoroughly
2. Review existing events for patterns
3. Run validation scripts
4. Ensure sources meet requirements
5. Follow naming conventions exactly
6. Create descriptive commit messages

For questions, check existing similar events first, then consult AGENT.md for AI-specific guidance.