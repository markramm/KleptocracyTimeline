# Source Quality Guidelines

## Overview

This document defines the source quality classification system for timeline events. The system uses a 3-tier classification to assess source credibility and provides automated quality scoring.

## Source Quality Tiers

### Tier 1: High Credibility (Weight: 1.0)

**Major News Organizations**:
- Associated Press (AP)
- Reuters
- NPR
- PBS
- Wall Street Journal
- New York Times
- Washington Post
- Bloomberg
- The Guardian
- BBC News
- Financial Times
- The Economist

**Investigative Journalism**:
- ProPublica
- The Intercept
- ICIJ (International Consortium of Investigative Journalists)
- Center for Investigative Reporting
- The Marshall Project

**Government & Official Sources**:
- U.S. Department of Justice (DOJ)
- Federal Bureau of Investigation (FBI)
- Securities and Exchange Commission (SEC)
- Federal Trade Commission (FTC)
- White House (official statements)
- Congressional Record
- Supreme Court (SCOTUS)
- State Department
- Department of Defense
- Any .gov domain

**Academic & Research**:
- University research publications
- Academic journals
- Think tank reports (Brookings, Carnegie Endowment)
- Any .edu domain

**Specialized Legal/Policy**:
- SCOTUSblog
- Lawfare
- Just Security
- Brennan Center for Justice

**Total Tier 1 Outlets**: 79

### Tier 2: Established Credibility (Weight: 0.6)

**Political News**:
- Politico
- The Hill
- Roll Call
- National Journal
- RealClearPolitics

**Technology News**:
- TechCrunch
- Ars Technica
- The Verge
- Wired
- CNET

**Business & Finance**:
- Fortune
- Forbes
- CNBC
- MarketWatch
- Barron's
- Business Insider

**Trade Publications**:
- The Atlantic
- Slate
- Vox
- Mother Jones
- The Daily Beast

**Watchdog Organizations**:
- OpenSecrets (Center for Responsive Politics)
- ACLU
- Electronic Frontier Foundation (EFF)
- Common Cause
- Public Citizen

**International News**:
- Al Jazeera
- South China Morning Post
- The Times of India
- Deutsche Welle

**Cryptocurrency/Tech**:
- CoinDesk
- CoinTelegraph
- Protocol
- The Information

**Total Tier 2 Outlets**: 84

### Tier 3: Unknown/Questionable (Weight: 0.2)

**Should be avoided or used sparingly**:
- Unknown outlets
- Personal blogs
- Social media (Twitter, Facebook, Reddit)
- Wikipedia (use as starting point, find primary sources)
- Partisan outlets without editorial standards
- Conspiracy theory sites
- Aggregators without original reporting

**Total Tier 3 Outlets**: 25 explicitly classified

## Quality Scoring System

### Formula

```
quality_score = (tier_1_count × 1.0 + tier_2_count × 0.6 + tier_3_count × 0.2) / total_sources × 10
```

### Quality Levels

- **Excellent** (8.0-10.0): Primarily tier-1 sources, minimal tier-3
- **Good** (6.0-7.9): Mix of tier-1 and tier-2, limited tier-3
- **Fair** (4.0-5.9): Significant tier-2/tier-3 presence
- **Poor** (<4.0): Dominated by tier-3 sources

### Target Standards

For high-quality timeline events:
- **≥50% tier-1 sources** (major news, government, academic)
- **≥70% tier-1 + tier-2 sources** combined
- **<30% tier-3 sources** (unknown/questionable)

## Current System Statistics

As of Sprint 3 Task 2 completion:

- **Total Events**: 1,559
- **Total Sources**: 5,505
- **Average Sources per Event**: 3.53
- **Average Quality Score**: 6.58/10

**Quality Distribution**:
- Excellent (≥8.0): 34.2% (534 events)
- Good (6.0-7.9): 34.1% (532 events)
- Fair (4.0-5.9): 15.0% (234 events)
- Poor (<4.0): 16.7% (261 events)

**Tier Distribution**:
- Tier 1: 49.1% (2,703 sources)
- Tier 2: 16.1% (885 sources)
- Tier 3: 34.9% (1,920 sources)

## Improvement Guidelines

### Adding Sources to Events

1. **Prioritize tier-1 sources** - Always search for major news coverage first
2. **Use multiple outlets** - Aim for 3+ sources from different organizations
3. **Verify facts** - Cross-reference claims across sources
4. **Avoid single-source events** - Every event should have multiple sources
5. **Prefer original reporting** - Direct investigation over aggregation

### Identifying Issues

Events need improvement when they have:
- **Low quality score** (<6.0)
- **High importance + low quality** (importance ≥8, quality <6.0)
- **Too few sources** (<3 sources total)
- **Too many tier-3 sources** (>50% tier-3)
- **No tier-1 sources** (all tier-2 or tier-3)

### Upgrading Low-Quality Events

**Step 1: Search for better coverage**
- Major news organization coverage
- Government records or statements
- Academic research or analysis
- Investigative journalism reports

**Step 2: Verify existing sources**
- Check if tier-3 sources are actually reputable (may need reclassification)
- Look for original reporting vs. aggregation
- Verify links are working and content matches

**Step 3: Add new sources**
- Minimum 3 sources total
- At least 1 tier-1 source if possible
- Multiple outlets for verification
- Include government/official sources when available

**Step 4: Document improvements**
- Note quality score increase
- Record source tier distribution
- Update event metadata

## API Endpoints

### Get Overall Statistics
```bash
curl http://localhost:5558/api/sources/quality/stats
```

Returns:
- Average quality score
- Quality level distribution
- Tier distribution
- Issue counts

### Get Low-Quality Events
```bash
curl "http://localhost:5558/api/sources/quality/low?max_score=6.0&min_importance=8&limit=50"
```

Query parameters:
- `max_score`: Maximum quality score (default: 6.0)
- `min_importance`: Minimum importance (default: 7)
- `limit`: Maximum results (default: 100)

### Analyze Specific Event
```bash
curl http://localhost:5558/api/sources/quality/event/2025-01-15--event-slug
```

Returns:
- Quality score and level
- Tier distribution
- Source-by-source classification
- Improvement recommendations

### Get Tier Outlet Lists
```bash
curl http://localhost:5558/api/sources/quality/tier/1  # Tier 1 outlets
curl http://localhost:5558/api/sources/quality/tier/2  # Tier 2 outlets
curl http://localhost:5558/api/sources/quality/tier/3  # Tier 3 outlets
```

## CLI Analysis Tool

### Basic Analysis
```bash
python3 scripts/analyze_source_quality.py
```

### High-Priority Issues
```bash
python3 scripts/analyze_source_quality.py --priority high
```

Filters to events with:
- Importance ≥ 8
- Quality score < 6.0

### JSON Output
```bash
python3 scripts/analyze_source_quality.py --json > quality_report.json
```

## High-Priority Improvement Targets

337 events with importance ≥8 and quality <6.0 need improvement. Examples:

**Event**: "Musk-Putin contact raises security concerns"
- Current: 10 sources (0 tier-1, 0 tier-2, 10 tier-3)
- Quality: 2.0/10 (Poor)
- **Action Needed**: Find tier-1 news coverage or government statements

**Event**: "Trump crypto holdings revealed"
- Current: 2 sources (0 tier-1, 1 tier-2, 1 tier-3)
- Quality: 3.0/10 (Poor)
- **Action Needed**: Add financial news coverage, SEC filings

**Event**: "Regulatory capture of FCC documented"
- Current: 4 sources (1 tier-1, 0 tier-2, 3 tier-3)
- Quality: 4.0/10 (Fair)
- **Action Needed**: Add investigative journalism, academic research

## Quality Assurance Workflow

1. **Identify targets**: Use `/api/sources/quality/low` endpoint
2. **Research improvements**: Search for tier-1/tier-2 coverage
3. **Update events**: Add better sources, remove questionable ones
4. **Verify improvements**: Re-run quality analysis
5. **Document changes**: Note quality score improvements in commits

## Best Practices

### DO:
✅ Use multiple independent sources
✅ Prioritize tier-1 outlets (major news, government, academic)
✅ Cross-reference facts across sources
✅ Include original reporting when possible
✅ Cite government records and official statements
✅ Use investigative journalism for complex events

### DON'T:
❌ Rely on single sources
❌ Use only tier-3 sources for important events
❌ Accept claims without verification
❌ Use social media as primary sources
❌ Trust partisan outlets without fact-checking
❌ Skip source verification

## Maintaining Quality Standards

### For New Events:
- Aim for quality score ≥6.0 (Good or better)
- Use at least 3 sources
- Include at least 1 tier-1 source if possible
- Verify facts across multiple outlets

### For Existing Events:
- Review low-quality events systematically
- Prioritize high-importance events first
- Research and add better sources
- Remove questionable sources when better alternatives exist

### Regular Audits:
- Run quality analysis monthly
- Track improvement progress
- Update outlet classifications as needed
- Document systematic issues and patterns

## Future Enhancements

Potential improvements to the quality system:
- Source freshness tracking (last verified date)
- Automated link checking integration
- Source diversity metrics (geographic, political, medium)
- Citation network analysis (who cites whom)
- Fact-checking integration
- Archive.org backup for source preservation
