# Timeline Data AI Agent Instructions

## Purpose
This document provides AI-specific guidance for performing CRUD (Create, Read, Update, Delete) and QA (Quality Assurance) operations on timeline data. For general requirements and human-readable documentation, see README.md first.

## CRITICAL: Naming Convention - NO UNDERSCORES

### ⚠️ NEVER USE UNDERSCORES IN IDs OR FILENAMES ⚠️

**All IDs and filenames must use HYPHENS (-) only. Underscores (_) will cause validation failures.**

### Correct Naming Pattern
```
YYYY-MM-DD--event-id-with-hyphens.yaml
```

### Examples
```yaml
# ✅ CORRECT - Uses hyphens
id: scotus-chevron-ruling
id: trump-cabinet-wealth
id: fec-ai-rulemaking

# ❌ WRONG - Uses underscores (WILL FAIL VALIDATION)
id: scotus_chevron_ruling
id: trump_cabinet_wealth
id: fec_ai_rulemaking
```

### Common Naming Patterns to Use
- Court cases: `scotus-case-name` NOT `scotus_case_name`
- Government agencies: `fec-ruling` NOT `fec_ruling`
- Multi-word concepts: `dark-money-disclosure` NOT `dark_money_disclosure`
- Names with initials: `trump-eo-13771` NOT `trump_eo_13771`

## CRITICAL: Mandatory Verification Protocol

### ⚠️ VERIFICATION IS MANDATORY - NOT OPTIONAL ⚠️

**Having a valid URL is NOT sufficient for any status level. You MUST actually read and verify sources.**

## CRITICAL: Schema Validation Protocol

### ⚠️ ALWAYS VALIDATE BEFORE AND AFTER MODIFICATIONS ⚠️

**You MUST run schema validation checks before and after ANY timeline event modifications.**

### Mandatory Validation Workflow
```bash
# 1. BEFORE making any changes
python timeline_data/validate_yaml.py

# 2. Make your changes to event files

# 3. AFTER making changes - MANDATORY
python timeline_data/validate_yaml.py

# 4. Check date logic
python tools/validation/validate_timeline_dates.py

# 5. Run comprehensive QA
python tools/qa/timeline_qa_system.py
```

If ANY validation fails, DO NOT commit changes. Fix issues first.

## Required Steps for ALL Timeline Operations

### Phase 1: Source Verification (MANDATORY)
For EVERY source/citation on EVERY event:

1. **FETCH THE CONTENT**
   ```python
   # DO NOT skip this step
   content = fetch_url(source_url)
   if not content:
       status = 'pending'  # Cannot verify without content
   ```

2. **READ AND VERIFY**
   - Actually read the article/document
   - Confirm it discusses THIS specific event
   - Verify key claims:
     * Names of actors mentioned?
     * Date/timeframe confirmed?
     * Main claim in title supported?
     * Summary details accurate?

3. **DOCUMENT VERIFICATION**
   ```yaml
   sources:
     - url: "https://example.com/article"
       verified: true
       verified_date: "2025-08-17"
       key_facts_confirmed:
         - "Actor name mentioned"
         - "Date confirmed as 2025-01-20"
         - "Executive order number verified"
       archive_url: "https://archive.org/..."
   ```

### Phase 2: Archive Creation (MANDATORY)
For EACH verified source:

1. **CREATE ARCHIVE LINK**
   ```python
   archive_url = create_archive(original_url)
   # Use: archive.org, archive.today, perma.cc
   ```

2. **SAVE KEY EXCERPTS**
   ```
   timeline_data/archive/[event-id]/
     ├── source1_excerpt.txt
     ├── source2_excerpt.txt
     └── metadata.json
   ```

3. **UPDATE EVENT FILE**
   ```yaml
   citations:
     - url: "original_url"
       archived: "archive_url"
       excerpt_saved: true
   ```

### Phase 3: Summary Validation (MANDATORY)

Every summary MUST answer:
- **WHO**: Specific names of actors/organizations
- **WHAT**: Precise action/decision/event
- **WHEN**: Timeframe beyond just the date
- **WHERE**: Location/jurisdiction if applicable
- **WHY**: Context/motivation/cause
- **IMPACT**: Why this matters/consequences

❌ **BAD**: "New policy announced"
✅ **GOOD**: "EPA Administrator Regan announced rollback of mercury emissions standards affecting 140 coal plants, reversing 2012 MATS rule following industry lobbying"

### Phase 4: Cross-Reference Check

1. **DUPLICATE CHECK**
   ```python
   # Search for similar events
   existing = search_events(date_range=±7_days, actors=event_actors)
   if duplicates_found:
       merge_or_reject()
   ```

2. **CONSISTENCY CHECK**
   - Does this contradict existing events?
   - Are dates/actors consistent with related events?

3. **LINK RELATED**
   ```yaml
   related_events:
     - "2025-01-15--related-event-id"
     - "2025-01-20--followup-event-id"
   ```

### Phase 5: Status Assignment Rules

```python
def determine_status(event):
    if not all_sources_verified:
        return 'pending'
    
    if event.date > today:
        return 'predicted'  # NEVER 'confirmed' for future
    
    if contradicting_sources:
        return 'disputed'
    
    if verified_source_count >= 2:
        return 'confirmed'
    
    return 'pending'  # When in doubt
```

## Automated Validation Tests

### Test Suite Requirements
Every event MUST pass these tests:

```python
def test_event_verification(event):
    # 1. Sources are accessible
    assert all(source.is_accessible for source in event.sources)
    
    # 2. Archives exist
    assert all(source.has_archive for source in event.sources)
    
    # 3. Summary is complete
    assert len(event.summary) >= 50
    assert has_who_what_when_where_why(event.summary)
    
    # 4. Status is appropriate
    if event.date > today:
        assert event.status != 'confirmed'
    
    # 5. No duplicates
    assert not find_duplicates(event)
    
    # 6. Sources support claims
    assert verify_sources_support_event(event)
```

### Continuous Validation
```bash
# Run these checks on every commit
python tools/qa/verify_sources.py
python tools/qa/check_archives.py
python tools/qa/validate_summaries.py
python tools/qa/find_duplicates.py
```

## Quick Reference

### Adding New Event Checklist
- [ ] Search for duplicates
- [ ] Fetch all source URLs
- [ ] Read and verify each source
- [ ] Create archive links
- [ ] Save source excerpts
- [ ] Write complete summary (who/what/when/where/why/impact)
- [ ] Set appropriate status
- [ ] Link related events
- [ ] Run validation tests
- [ ] Commit with verification notes

### Status Transition Rules
```
pending → confirmed:     2+ sources verified
pending → disputed:      Conflicting sources found
confirmed → disputed:    New contradicting evidence
predicted → confirmed:   After date + verification
predicted → failed:      Event didn't occur
any → pending:          Verification incomplete
```

## AI Agent Workflow Example

```python
async def add_timeline_event(title, date, sources):
    # 1. ALWAYS start with pending
    event = {
        'id': generate_id(date, title),
        'status': 'pending',
        'date': date,
        'title': title
    }
    
    # 2. Verify EACH source
    verified_sources = []
    for source_url in sources:
        # MANDATORY: Actually fetch and read
        content = await fetch_url(source_url)
        if not content:
            log_error(f"Cannot access {source_url}")
            continue
        
        # MANDATORY: Verify relevance
        if verify_content_matches_event(content, event):
            # MANDATORY: Create archive
            archive_url = await create_archive(source_url)
            
            # MANDATORY: Save excerpt
            save_excerpt(event['id'], source_url, content)
            
            verified_sources.append({
                'url': source_url,
                'archived': archive_url,
                'verified': True,
                'verified_date': today()
            })
    
    # 3. Only proceed if sources verified
    if len(verified_sources) < 1:
        raise Error("No sources could be verified")
    
    event['sources'] = verified_sources
    
    # 4. Generate complete summary
    event['summary'] = generate_complete_summary(
        who=extract_actors(verified_sources),
        what=extract_action(verified_sources),
        when=extract_timeframe(verified_sources),
        where=extract_location(verified_sources),
        why=extract_context(verified_sources),
        impact=extract_significance(verified_sources)
    )
    
    # 5. Set final status
    if len(verified_sources) >= 2:
        event['status'] = 'confirmed'
    
    # 6. Save and validate
    save_event(event)
    run_validation_tests(event)
    
    return event
```

## Common Failures and Solutions

### ❌ FAILURE: "Forgot to run schema validation"
✅ SOLUTION: ALWAYS run `python timeline_data/validate_yaml.py` before AND after changes

### ❌ FAILURE: "Source URL returns 200 so marking as confirmed"
✅ SOLUTION: Actually fetch, read, and verify content matches event

### ❌ FAILURE: "Added event without checking for duplicates"
✅ SOLUTION: Always search existing events first

### ❌ FAILURE: "Future event marked as confirmed"
✅ SOLUTION: Use 'predicted' status for future dates

### ❌ FAILURE: "Summary is just headline repetition"
✅ SOLUTION: Include who, what, when, where, why, impact

### ❌ FAILURE: "No archives created"
✅ SOLUTION: Create archive.org link for every source

### ❌ FAILURE: "Schema validation errors after edits"
✅ SOLUTION: Run validation BEFORE committing, fix all issues first

## Performance Metrics

Track these for quality assurance:
- Source verification rate: Must be 100%
- Archive creation rate: Target >95%
- Summary completeness: Target >80% have all elements
- Duplicate detection: Must be 100%
- Status accuracy: 0 future events as 'confirmed'

## YAML Character Escaping Guidelines

### Common YAML Validation Errors and Solutions

The most frequent cause of YAML validation errors is improper escaping of apostrophes and quotes in titles and text fields.

#### ❌ COMMON ERROR: Apostrophes in single-quoted strings
```yaml
# WRONG - Will cause validation error
- title: 'Trump's Business Profits'
- title: 'Trump raised $250 million to fight election fraud claims. Here's where that money went'
```

#### ✅ SOLUTION: Use double quotes for strings with apostrophes
```yaml
# CORRECT
- title: "Trump's Business Profits"
- title: "Trump raised $250 million to fight election fraud claims. Here's where that money went"
```

#### Alternative Solutions:
```yaml
# Option 1: Escape the apostrophe in single quotes
- title: 'Trump\'s Business Profits'

# Option 2: Use plain style (no quotes) when safe
- title: Trump announces new policy

# Option 3: Use literal block style for multi-line
summary: |
  Trump's administration announced new policies
  that affect multiple sectors including finance
```

### Best Practices:
1. **Default to double quotes** for all titles containing apostrophes
2. **Use single quotes** only for strings without apostrophes
3. **Always validate** after creating/editing YAML files
4. **Watch for**: Contractions (don't, won't), possessives (Trump's, Congress's), and quotes within quotes

## Critical Project Resources

### Core Project Structure
```
/Users/markr/kleptocracy-timeline/
├── timeline_data/
│   ├── events/              # All timeline event YAML files (300+ files)
│   ├── validate_yaml.py     # Main validation script - RUN THIS FREQUENTLY
│   ├── AGENT.md            # This file - AI agent instructions
│   └── README.md           # Human documentation
├── DemocracyResearchDocs/   # Research document processing
│   ├── queue/              # Documents to process
│   └── completed/          # Processed documents
└── tools/                  # QA and archiving tools
```

### Key Scripts and Tools
1. **validate_yaml.py** - Critical validation script, run after every change
2. **archive_links_slow.py** - Archives sources to archive.org (5 req/min limit)
3. **find_broken_links.py** - Identifies broken source links
4. **fix_archive_urls.py** - Fixes malformed archive.org URLs

### Document Processing Workflow
1. Read PDF from `DemocracyResearchDocs/queue/`
2. Extract kleptocracy-related events
3. Check timeline for duplicates
4. Create new event YAML files
5. Validate with `validate_yaml.py`
6. Commit changes
7. Move PDF to `completed/` folder

## AI Tool Integration

### Using Multiple AI Tools
For comprehensive instructions on using ChatGPT, Claude, Cursor, and other AI tools with this timeline, see `/AI_INTEGRATION.md`.

### Quick Setup for Any AI Tool
1. Provide this context: "Working on Kleptocracy Timeline, following timeline_data/AGENT.md standards"
2. Share the naming convention: `YYYY-MM-DD--event-name-with-hyphens` (NO underscores)
3. Emphasize: 2+ sources required for 'confirmed' status
4. Request: Source verification and archive creation

## Schema Validation Quick Reference

### Essential Commands
```bash
# Run these EVERY time you modify events:
python timeline_data/validate_yaml.py          # Schema validation
python tools/validation/validate_timeline_dates.py  # Date logic check
python tools/qa/timeline_qa_system.py          # Comprehensive QA
```

### Common Schema Errors
| Error | Fix |
|-------|-----|
| Missing required field | Add: `status`, `sources`, `summary`, etc. |
| Invalid date format | Use: `date: 'YYYY-MM-DD'` |
| ID mismatch | Match filename: `id: 2024-01-01--event-name` |
| Future confirmed | Change to: `status: predicted` |
| No sources | Add at least one source with title, url, outlet, date |
| Underscores in ID | Replace with hyphens: `supreme_court` → `supreme-court` |

### Validation Workflow
1. **BEFORE edits**: `python timeline_data/validate_yaml.py`
2. **Make changes**
3. **AFTER edits**: `python timeline_data/validate_yaml.py`
4. **Date check**: `python tools/validation/validate_timeline_dates.py`
5. **Full QA**: `python tools/qa/timeline_qa_system.py`
6. **Only then commit**

## Notes

- **When in doubt**: Use `status: pending`
- **Never assume**: Always verify
- **Document everything**: Use notes field
- **Fail gracefully**: Better pending than wrong
- **Archive immediately**: Sources disappear
- **Escape apostrophes**: Use double quotes for titles with apostrophes
- **Multiple AI tools**: See `/AI_INTEGRATION.md` for tool-specific guides
- **ALWAYS VALIDATE**: Run schema checks before AND after ANY changes