# Timeline Researcher Agent

## Purpose
The timeline-researcher agent specializes in researching, verifying, and maintaining timeline events for the kleptocracy timeline project. This includes fact-checking, source verification, updating event details, ensuring schema compliance, and running QA scripts.

## Current Status (2025-08-18)
- **Total timeline events**: 303
- **Events verified**: 28 (9.2%)
- **Events with broken links fixed**: 32 (12.4% of 259)
- **Optimization tools created**: 6 new Python scripts for automated QA

## Core Responsibilities

### 1. Event Verification
- Verify sources are real and accessible
- Check dates match actual event occurrence
- Ensure summaries are accurate and complete
- Validate status field (confirmed/pending/predicted/disputed)
- Add archive.org links for source preservation

### 2. Source Management
- Find reliable replacement sources for broken links
- Add multiple sources for better verification
- Prioritize authoritative sources (government, major news, academic)
- Create archive links for all sources

### 3. Schema Compliance
- Ensure all required fields are present
- Fix date format issues
- Correct filename-date mismatches
- Validate YAML structure

### 4. QA Process
- Run validation scripts
- Fix identified issues immediately
- Update verification_status.json
- Track progress systematically

## Optimization Tools Available

### Automated Scripts
1. **check_all_links.py** - Identifies all broken URLs
2. **extract_pdf_citations.py** - Extracts known good sources from research PDFs
3. **auto_fix_simple_cases.py** - Fixes common URL issues automatically
4. **batch_verify_and_fix.py** - Matches broken URLs with known sources
5. **smart_qa.py** - Prioritizes events needing fixes
6. **batch_archive.py** - Archives working URLs

### Manual Tools
- **validate_timeline_dates.py** - Checks for date issues
- **build_footnotes.py** - Generates citations
- **build_timeline_index.py** - Creates searchable index

## Workflow for New Sessions

### Initial Setup
```bash
# 1. Check current status
python3 tools/validation/check_all_links.py

# 2. Extract known sources (if not done)
python3 tools/validation/extract_pdf_citations.py

# 3. Auto-fix simple cases
python3 tools/validation/auto_fix_simple_cases.py

# 4. Batch verify with known sources
python3 tools/validation/batch_verify_and_fix.py
```

### Manual Verification Process
1. Read `timeline_data/qa_reports/batch_verify_report.json`
2. Focus on "needs_manual_review" events
3. For each event:
   - Search for reliable sources
   - Update with working URLs
   - Add archive links
   - Fix any factual errors
   - Save and commit in batches

## Key Guidelines

### Source Priorities
1. Government websites (.gov)
2. Major news outlets (NYT, WaPo, CNN, NPR, BBC)
3. Legal databases (Justia, SCOTUS, court records)
4. Academic sources (.edu, peer-reviewed)
5. Archived versions when originals unavailable

### Verification Standards
- **NEVER** mark future events as "confirmed" (use "predicted")
- **ALWAYS** verify source content, not just URL validity
- **MUST** include archive.org links when possible
- **SHOULD** have 2+ sources for major events

### Commit Strategy
- Commit every 10-20 events fixed
- Use descriptive commit messages
- Include count of events fixed
- Note major corrections made

## File Locations

### Event Files
- `timeline_data/events/*.yaml`

### Reports
- `timeline_data/qa_reports/broken_links.json` - Current broken links
- `timeline_data/qa_reports/verification_status.json` - QA progress
- `timeline_data/qa_reports/batch_verify_report.json` - Auto-fix results
- `timeline_data/qa_reports/extracted_sources.json` - Known good sources

### Tools
- `tools/validation/` - QA and validation scripts
- `tools/archiving/` - Archive management scripts
- `tools/generation/` - Index and report generation

## Progress Tracking

Update `verification_status.json` after each session:
```json
{
  "total_events": 303,
  "verified_events": ["list", "of", "verified", "files"],
  "verification_rate": 9.2,
  "broken_links_fixed": 32,
  "broken_links_remaining": 207,
  "last_session": "2025-08-18",
  "next_priority": "2024-2025 events with broken links"
}
```

## Common Fixes

### URL Issues
- `http://` → `https://`
- `twitter.com` → `x.com`
- Add archive.org wildcards: `/web/*/URL`

### Date Issues
- Filename date must match event date
- Future events must be "predicted"
- Use ISO format: YYYY-MM-DD

### Source Replacements
- Broken government URLs → archive.org versions
- Dead news links → alternative coverage
- Social media → news articles about the posts

## Performance Metrics
- **Manual fix rate**: 10-15 events/hour
- **Auto-fix success**: ~40% of broken URLs
- **Batch verify success**: ~30% of remaining
- **Total estimated time**: 8-10 hours for full QA

## Next Session Priorities
1. Run automated tools on remaining events
2. Fix high-priority 2024-2025 events
3. Archive all working sources
4. Complete verification of unverified events
5. Update documentation with final stats