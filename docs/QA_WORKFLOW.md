# Timeline QA Workflow

## Overview

This document describes the optimized workflow for verifying and fixing timeline events, particularly focusing on handling broken links efficiently.

## Current Status (as of 2025-08-18)

- **Total Events**: 303
- **Events with URLs**: 303
- **Total URLs**: 525
- **Working URLs**: 236 (45.0%)
- **Broken URLs**: 289 (55.0%)
- **Events with broken links**: 239
- **Manual fixes completed**: 32 events (12.4% of broken)
- **Verified events**: 28 (9.2% of total)

## Optimization Tools

The following tools have been created to streamline the QA process:

### 1. Link Checking (`check_all_links.py`)
Scans all timeline events and identifies broken URLs.
```bash
python3 tools/validation/check_all_links.py
```
Output: `timeline_data/qa_reports/link_check_*.json`

### 2. Citation Extraction (`extract_pdf_citations.py`)
Extracts URLs and citations from research PDFs to build a known good sources database.
```bash
python3 tools/validation/extract_pdf_citations.py
```
Output: `timeline_data/qa_reports/extracted_sources.json`

### 3. Auto-Fix Simple Cases (`auto_fix_simple_cases.py`)
Automatically fixes common URL issues:
- HTTP → HTTPS conversion
- Domain migrations (twitter.com → x.com)
- Archive.org URL formatting
- URL normalization
```bash
python3 tools/validation/auto_fix_simple_cases.py
```
Output: `timeline_data/qa_reports/auto_fixes_report.json`

### 4. Batch Verify and Fix (`batch_verify_and_fix.py`)
Matches broken URLs with known good sources from the extracted database.
```bash
python3 tools/validation/batch_verify_and_fix.py
```
Output: `timeline_data/qa_reports/batch_verify_report.json`

### 5. Smart QA Analysis (`smart_qa.py`)
Analyzes events and prioritizes fixes based on broken links and missing data.
```bash
python3 tools/validation/smart_qa.py
```
Output: `timeline_data/qa_reports/fix_report_*.json`

### 6. Batch Archive (`batch_archive.py`)
Archives working URLs to archive.org and updates events with archive links.
```bash
python3 tools/archiving/batch_archive.py
```
Output: `timeline_data/qa_reports/archive_map_*.json`

## Recommended Workflow

### Phase 1: Automated Fixes
1. **Extract known sources** from research documents:
   ```bash
   python3 tools/validation/extract_pdf_citations.py
   ```

2. **Auto-fix simple cases**:
   ```bash
   python3 tools/validation/auto_fix_simple_cases.py
   ```

3. **Batch verify with known sources**:
   ```bash
   python3 tools/validation/batch_verify_and_fix.py
   ```

4. **Check link status**:
   ```bash
   python3 tools/validation/check_all_links.py
   ```

### Phase 2: Archive Working Links
5. **Archive all working URLs**:
   ```bash
   python3 tools/archiving/batch_archive.py
   ```

### Phase 3: Manual Review
6. **Run smart QA analysis**:
   ```bash
   python3 tools/validation/smart_qa.py
   ```

7. **Use timeline-researcher agent** for remaining fixes:
   - Focus on events in `fix_report_*.json` priority list
   - Process in batches of 10-20 events
   - Commit after each batch

## Whitelisted Domains for Automation

The following domains are pre-approved for automated checking and archiving:

### News Sources
- nytimes.com, washingtonpost.com, cnn.com, npr.org
- bbc.com, reuters.com, apnews.com, bloomberg.com
- wsj.com, theguardian.com, nbcnews.com, foxnews.com
- politico.com, axios.com, thehill.com, newsweek.com

### Government
- All *.gov domains
- supremecourt.gov, congress.gov, whitehouse.gov
- senate.gov, house.gov, fec.gov, justice.gov

### Legal/Academic
- justia.com, scotusblog.com, courtlistener.com
- All *.edu domains
- scholar.google.com, jstor.org, arxiv.org

### Archives
- archive.org, archive.today, archive.is

## Progress Tracking

Track progress in `timeline_data/qa_reports/verification_status.json`:
```json
{
  "total_events": 303,
  "verified_events": ["event1.yaml", "event2.yaml"],
  "verification_rate": 9.2,
  "last_updated": "2025-08-18",
  "broken_links_fixed": 32,
  "broken_links_remaining": 207
}
```

## Next Steps for New Session

1. Run the automated tools in sequence (Phase 1)
2. Archive working links (Phase 2)
3. Review `batch_verify_report.json` for events needing manual fixes
4. Use timeline-researcher agent to fix remaining broken links
5. Continue verification of unverified events

## Key Files

- **Broken links list**: `timeline_data/qa_reports/broken_links.json`
- **Verification status**: `timeline_data/qa_reports/verification_status.json`
- **Extracted sources**: `timeline_data/qa_reports/extracted_sources.json`
- **Auto-fix report**: `timeline_data/qa_reports/auto_fixes_report.json`
- **Batch verify report**: `timeline_data/qa_reports/batch_verify_report.json`

## Performance Metrics

- Manual fixing rate: ~10-15 events per hour
- Auto-fix potential: ~30-40% of broken URLs
- Batch verify potential: ~20-30% of remaining
- Total time estimate: ~8-10 hours for full QA with tools

## Notes

- Always verify future events are marked as "predicted" not "confirmed"
- Add archive.org links for all sources when possible
- Correct dates must match between filename and event data
- Focus on 2024-2025 events first as they have better source availability