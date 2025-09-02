# Cross-Cutting Cleanups

Systematic improvements needed across multiple timeline events.

## 1. Remove All Placeholders

**Search for and replace**:
- [ ] "Timeline Documentation / example.com" placeholders
- [ ] "/source" empty references
- [ ] Placeholder URLs

**Known clusters**:
- 2025-03-12/13
- 2025-04-02/11
- 2025-02-12
- 2025-05-28

**Action**: Replace with actual sources or remove entries if unverifiable

---

## 2. Archive All External URLs

**Process**:
- [ ] Use Wayback Machine to archive all external links
- [ ] Add `archive_url` field for every external link
- [ ] Use "first seen" date near article publication date
- [ ] Prioritize sources that may be paywalled or removed

**Tools**:
- Internet Archive Save Page: https://web.archive.org/save
- Bulk archiving scripts if needed

---

## 3. Tone and Attribution Adjustments

**Replace categorical phrases with precise, attributed language**:

### Terms to review:
- "monopoly" → "dominant market position" or cite regulator using term
- "police-state tactics" → describe specific actions with citations
- "total control" → specify exact access/permissions granted
- "digital coup" → attribute to source or use neutral description
- "political prisoner" → attribute claim to specific filing/statement

**Exception**: Keep strong language if:
- Used by regulator/court in official capacity
- Direct quote from named official
- Part of legal filing language

---

## 4. Balance Official vs Independent Sources

**For all controversial items, ensure both perspectives**:

### Key areas needing balance:
- **Turnberry/Doonbeg lodging**: Include Air Mobility Command review + investigative reporting
- **Tesla procurement**: State Dept denials + watchdog concerns
- **DOGE access**: Treasury "read-only" statements + court filings showing write access
- **Section 232 exclusions**: GAO methodology reviews + investigative reporting

### Template format:
```yaml
sources:
  # Official position
  - title: [Official statement/review]
    outlet: [Government agency]
    
  # Independent investigation
  - title: [Investigative report]
    outlet: [News organization]
    
  # Watchdog/oversight
  - title: [Analysis/complaint]
    outlet: [Watchdog group]
```

---

## 5. Court and Agency Documentation

**Ensure all legal items include**:
- [ ] Court name and jurisdiction
- [ ] Judge name (if available)
- [ ] Case number/caption
- [ ] Docket links
- [ ] Filing dates

**For Executive Orders/Memos**:
- [ ] EO/Memo number
- [ ] Federal Register citation
- [ ] Effective date
- [ ] Key provisions

---

## 6. Date and Timeline Accuracy

**Verify**:
- [ ] Event dates match source documentation
- [ ] Multi-day events show date range
- [ ] Future events marked as "developing" not "confirmed"
- [ ] Retroactive discoveries dated to occurrence, not discovery

**Date format standard**: YYYY-MM-DD

---

## 7. Status Field Consistency

**Apply consistently**:
- `confirmed`: Multiple reliable sources + official documentation
- `reported`: Credible reporting but awaiting confirmation
- `disputed`: Conflicting accounts or official challenges
- `developing`: Ongoing situations or future events
- `retracted`: If sources have issued corrections

---

## 8. Actor and Tag Standardization

**Ensure consistency**:
- [ ] Actor names spelled consistently
- [ ] Organizations use official names
- [ ] Tags are lowercase with hyphens
- [ ] No duplicate tags with different spellings

**Common issues**:
- "DOD" vs "DoD" vs "Department of Defense"
- "FBI" vs "Federal Bureau of Investigation"
- Inconsistent hyphenation in tags

---

## 9. Source Quality Tiers

**Establish hierarchy**:

**Tier 1 (Primary)**:
- Government documents
- Court filings
- Corporate SEC filings
- Official statements

**Tier 2 (Reliable Secondary)**:
- Major news outlets
- Established trade publications
- Academic sources
- Think tank research

**Tier 3 (Supporting)**:
- Advocacy organizations
- Opinion pieces
- Social media (only if from official accounts)

**Rule**: Every event should have at least one Tier 1 or 2 source

---

## 10. Systematic Review Checklist

For each event:
- [ ] No placeholders
- [ ] Minimum 2 sources (exception: breaking news)
- [ ] Official + independent balance for controversial items
- [ ] Archive URLs present
- [ ] Neutral tone with attribution
- [ ] Accurate dates and status
- [ ] Standardized actors and tags
- [ ] Court/agency details complete

---

## Priority Implementation

1. **First Pass**: Remove all placeholders (blocks timeline credibility)
2. **Second Pass**: Add archive URLs (preserves sources)
3. **Third Pass**: Balance controversial items (ensures fairness)
4. **Fourth Pass**: Standardize format/fields (improves usability)

---

## Tracking Progress

- [ ] Placeholder removal complete
- [ ] Archive URLs added to all entries
- [ ] Controversial items balanced
- [ ] Legal documentation complete
- [ ] Tone/attribution reviewed
- [ ] Actors/tags standardized
- [ ] Status fields verified