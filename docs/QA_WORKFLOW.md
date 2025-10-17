# Quality Assurance Workflow Guide

## Overview

This guide explains the systematic quality assurance workflow for timeline events, using the QA system and source quality classification to identify and improve events needing better sources or validation.

## Quick Start

```bash
# 1. Check current QA system status
python3 research_cli.py qa-stats

# 2. Get validation queue (prioritized by importance and source quality)
python3 research_cli.py validation-queue --limit 10

# 3. Get events with insufficient sources
python3 research_cli.py missing-sources --min-sources 3 --limit 10

# 4. Get low-quality events by source tier
python3 research_cli.py qa-issues --limit 15
```

## Understanding the QA System

### Current System Status (2025-10-17)

**Quality Metrics:**
- Total events: 1,561
- Average quality score: 6.77/10 (Good)
- Excellent/Good: 70.9% (1,107 events)
- Fair/Poor: 29.1% (454 events)

**Validation Status:**
- Validated: 836 events (53.6%)
- Need validation: 725 events (46.4%)
- High-priority needs QA: 561 events

**Source Quality:**
- Adequate sources (≥3): 1,491 events (95.5%)
- Two sources: 67 events (4.3%)
- One source: 2 events (0.1%)
- No sources: 1 event (0.1%)

### Quality Scoring System

**Quality Score Formula:**
```
(tier_1_count × 1.0 + tier_2_count × 0.6 + tier_3_count × 0.2) / total × 10
```

**Quality Levels:**
- **Excellent** (8.0-10.0): Primarily tier-1 sources, minimal tier-3
- **Good** (6.0-7.9): Mix of tier-1 and tier-2, limited tier-3
- **Fair** (4.0-5.9): Significant tier-2/tier-3 presence
- **Poor** (<4.0): Dominated by tier-3 sources

**Quality Targets:**
- ✅ Tier-1 sources ≥50%: **ACHIEVED** (51.7%)
- ⏳ Tier-1+Tier-2 ≥70%: Currently 67.4% (need +2.6%)
- ⏳ Tier-3 sources <30%: Currently 32.6% (need -2.6%)

### Source Tier Classification

**Tier 1 (Weight 1.0):** Major news organizations, government, academic
- Associated Press, Reuters, NPR, PBS, Bloomberg, WSJ, NYT, WaPo
- All .gov domains (DOJ, FBI, SEC, FTC, Congress, etc.)
- All .edu domains (university research, academic journals)
- Investigative: ProPublica, The Intercept, ICIJ
- **79 outlets total**

**Tier 2 (Weight 0.6):** Established outlets, trade publications
- Politico, The Hill, Axios, Fortune, Forbes
- TechCrunch, Ars Technica, Wired
- ACLU, EFF, OpenSecrets
- Regional news: LA Times, Boston Globe, Chicago Tribune
- **84 outlets total**

**Tier 3 (Weight 0.2):** Unknown, questionable sources
- Wikipedia, blogs, social media
- Partisan outlets without editorial standards
- Press releases (not independent journalism)
- **25 outlets explicitly classified**

## Systematic Improvement Workflow

### Step 1: Identify Target Events

**For High-Priority Events (Importance ≥8):**
```bash
# Get events needing validation
python3 research_cli.py validation-queue --limit 20

# Get events with low quality scores
curl -s "http://localhost:5558/api/sources/quality/low?max_score=6.0&min_importance=8&limit=20" | python3 -m json.tool
```

**For Events with Insufficient Sources:**
```bash
# Events with fewer than 3 sources
python3 research_cli.py missing-sources --min-sources 3 --limit 20
```

**For Events with Quality Issues:**
```bash
# Events with specific quality problems
python3 research_cli.py qa-issues --limit 20
```

### Step 2: Analyze Event Quality

```bash
# Get detailed quality analysis for specific event
python3 research_cli.py get-event --id "2013-06-05--snowden-mass-surveillance-revelations"

# Check source quality breakdown
curl -s "http://localhost:5558/api/sources/quality/event/2013-06-05--snowden-mass-surveillance-revelations" | python3 -m json.tool
```

**What to Look For:**
1. Current source count and tier distribution
2. Quality score and level
3. Specific quality issues flagged
4. Recommendations from the system

### Step 3: Research Better Sources

**Priority Order for Sources:**

1. **Government/Official Sources** (Tier 1)
   - Congressional testimony/records (congress.gov)
   - Court documents (supremecourt.gov, pacer.gov)
   - Agency reports (SEC, FTC, DOJ, FBI)
   - Official statements (whitehouse.gov)

2. **Major News Organizations** (Tier 1)
   - Wire services: Associated Press, Reuters
   - National news: NPR, PBS, Bloomberg, WSJ, NYT, WaPo
   - Major international: BBC, The Guardian, Financial Times

3. **Investigative Journalism** (Tier 1)
   - ProPublica, The Intercept, ICIJ
   - In-depth reporting with original research

4. **Established Outlets** (Tier 2)
   - Political: Politico, The Hill, Axios
   - Business: Fortune, Forbes, Business Insider
   - Regional: LA Times, Boston Globe, Chicago Tribune

**Research Tips:**
- Use Google News with date filters for the event date
- Search government sites: `site:.gov [event keywords]`
- Check congressional records for testimony
- Look for investigative reports on the topic
- Cross-reference multiple sources

### Step 4: Add/Update Sources

**Source Format Requirements:**
```json
{
  "outlet": "Reuters",
  "url": "https://www.reuters.com/article/...",
  "title": "Article Title Here",
  "date": "YYYY-MM-DD"
}
```

**Alternate Format (Legacy):**
```json
{
  "publication": "NPR",
  "url": "https://www.npr.org/...",
  "title": "Article Title Here",
  "date": "YYYY-MM-DD"
}
```

**Minimal Format (URL-based classification):**
```json
{
  "url": "https://www.washingtonpost.com/...",
  "title": "Article Title Here"
}
```

**Quality Guidelines:**
- Minimum 2 sources (3+ recommended)
- At least 1 tier-1 source if possible
- Multiple outlets for verification
- Original reporting preferred over aggregation

### Step 5: Validate Changes

```bash
# Validate event file before committing
python3 research_cli.py validate-event --file timeline_data/events/2013-06-05--snowden-mass-surveillance-revelations.json

# Check updated quality score
curl -s "http://localhost:5558/api/sources/quality/event/2013-06-05--snowden-mass-surveillance-revelations" | python3 -m json.tool
```

**Expected Improvements:**
- Quality score should increase
- Tier-1 percentage should increase
- Tier-3 percentage should decrease
- System issues should be resolved

## Parallel Processing with Validation Runs

For processing large batches of events with multiple agents, use the Validation Runs system to ensure unique event distribution.

### Creating a Validation Run

```bash
# Create source quality focused validation run
python3 research_cli.py validation-runs-create \
  --run-type source_quality \
  --target-count 30 \
  --focus-unvalidated \
  --exclude-recent-validations \
  --created-by "qa-sprint-1"

# Create importance-focused run
python3 research_cli.py validation-runs-create \
  --run-type importance_focused \
  --target-count 20 \
  --min-importance 8 \
  --created-by "high-priority-batch"
```

### Processing Events (Parallel Agents)

**Critical: Each agent MUST use unique validator ID**

```bash
# Agent 1
python3 research_cli.py validation-runs-next --run-id 1 --validator-id "qa-agent-1"

# Agent 2
python3 research_cli.py validation-runs-next --run-id 1 --validator-id "qa-agent-2"

# Agent 3
python3 research_cli.py validation-runs-next --run-id 1 --validator-id "qa-agent-3"
```

### Completing Validation

```bash
# After improving event, mark as validated
python3 research_cli.py validation-runs-complete \
  --run-id 1 \
  --run-event-id 15 \
  --status validated \
  --notes "Enhanced with tier-1 sources, quality improved to 8.5"

# If event needs more work
python3 research_cli.py validation-runs-complete \
  --run-id 1 \
  --run-event-id 16 \
  --status needs_work \
  --notes "Sources need verification"

# If event should be rejected/archived
python3 research_cli.py validation-runs-complete \
  --run-id 1 \
  --run-event-id 17 \
  --status rejected \
  --notes "Duplicate of existing event"
```

### Monitoring Progress

```bash
# Check validation run status
python3 research_cli.py validation-runs-get --run-id 1

# List all validation runs
python3 research_cli.py validation-runs-list

# View validation logs
python3 research_cli.py validation-logs-list --limit 20
```

## Best Practices

### DO:
✅ Search for tier-1 sources first (government, major news, academic)
✅ Use multiple independent sources from different outlets
✅ Cross-reference facts across sources
✅ Include original reporting when possible
✅ Cite government records and official statements
✅ Check URLs work and match the event date
✅ Verify source credibility before adding

### DON'T:
❌ Rely on single sources
❌ Use only tier-3 sources for important events
❌ Accept claims without verification
❌ Use social media as primary sources
❌ Trust partisan outlets without fact-checking
❌ Add sources without reading them
❌ Use Wikipedia as a primary source (find the original)

### Common Quality Issues and Fixes

**Issue: "No tier-1 sources"**
- Fix: Search for government records, congressional testimony, major news coverage
- Example sources: congress.gov, sec.gov, npr.org, reuters.com

**Issue: "More tier-3 sources than tier-1/tier-2 combined"**
- Fix: Replace tier-3 sources with tier-1/tier-2 alternatives
- Keep tier-3 only if no better sources exist

**Issue: "Only 1-2 sources"**
- Fix: Add at least one more source for verification
- Target: 3+ sources for credibility

**Issue: "Only Wikipedia/blogs"**
- Fix: Find the original sources cited in Wikipedia
- Use Wikipedia as a research starting point, not final source

## Quality Improvement Examples

### Example 1: Snowden NSA Revelations

**Before:**
```json
{
  "sources": [
    {"title": "washingtonpost.com", "url": "https://washingtonpost.com/..."},
    {"title": "theguardian.com", "url": "https://theguardian.com/..."},
    {"title": "aclu.org", "url": "https://aclu.org/..."}
  ]
}
```
- Quality Score: 2.0 (Poor)
- Issue: Outlet names missing, URLs not properly classified

**After (Automatic Fix):**
- Quality Score: 8.67 (Excellent)
- Tier 1: Washington Post, The Guardian
- Tier 2: ACLU
- **Improvement: +6.67 points (334%)**

### Example 2: Typical Improvement Process

**Original Event:**
- 2 sources (1 Wikipedia, 1 blog)
- Quality: 2.0 (Poor)
- Tier 3: 100%

**Research Phase:**
- Search: `site:.gov "Event Topic"`
- Find: Congressional testimony
- Search: `site:npr.org OR site:reuters.com "Event Topic" date:YYYY`
- Find: NPR and Reuters coverage
- Search: `site:propublica.org "Event Topic"`
- Find: Investigative report

**Improved Event:**
- 4 sources (Congressional Record, NPR, Reuters, ProPublica)
- Quality: 10.0 (Excellent)
- Tier 1: 100%
- **Improvement: +8.0 points (400%)**

## Troubleshooting

### Server Not Responding
```bash
# Check server status
python3 research_cli.py server-status

# View logs
python3 research_cli.py server-logs

# Restart if needed
python3 research_cli.py server-restart
```

### Quality Scores Seem Wrong
```bash
# Check classifier statistics
curl -s "http://localhost:5558/api/sources/quality/stats" | python3 -m json.tool

# Verify specific outlet classification
curl -s "http://localhost:5558/api/sources/quality/tier/1" | python3 -m json.tool
```

### Events Not Showing Improvements
```bash
# Wait for filesystem sync (30 seconds)
sleep 30

# Force database sync by restarting server
python3 research_cli.py server-restart
```

## Metrics and Progress Tracking

### Daily Quality Check
```bash
# Overall quality statistics
curl -s "http://localhost:5558/api/sources/quality/stats" | python3 -m json.tool

# QA system progress
python3 research_cli.py qa-stats

# Events needing attention
python3 research_cli.py validation-queue --limit 10
```

### Progress Indicators

**Target: All Events "Good" or Better (≥6.0)**
- Current: 70.9% (1,107/1,561)
- Remaining: 454 events need improvement

**Target: All High-Priority Events "Excellent" (≥8.0)**
- Current: Varies by importance level
- Focus: 561 high-priority events unvalidated

**Target: Tier Distribution Goals**
- ✅ Tier-1 ≥50%: **ACHIEVED** (51.7%)
- ⏳ Tier-1+Tier-2 ≥70%: 67.4% (need +2.6%)
- ⏳ Tier-3 <30%: 32.6% (need -2.6%)

## Related Documentation

- `docs/SOURCE_QUALITY.md` - Source tier definitions and scoring
- `CLAUDE.md` - Research CLI complete reference
- `docs/SPRINT_3_PROGRESS.md` - Sprint 3 quality improvements
