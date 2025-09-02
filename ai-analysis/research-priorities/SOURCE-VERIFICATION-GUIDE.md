# Source Verification Guide

## Critical Lesson Learned

**DO NOT ADD FAKE SOURCES.** Adding hypothetical or unverified sources is worse than having single-source events. It destroys credibility.

## Current Status (September 2, 2025)

### Source Quality Breakdown
- **1 future event** (Nov 4, 2025) - Should be marked 'developing'
- **30 high-importance events** with only 1 real source
- **56 events** with mix of real + placeholder sources  
- **276 events** are well-sourced (2+ real sources)

### What We've Fixed
- ✅ Qatar jet event: Added 8 real sources from web search
- ✅ Removed 133 placeholder sources from events
- ✅ Properly marked status fields based on source quality

## Process for Adding Sources

### Step 1: Identify Target Event
Use the audit script to find events needing sources:
```bash
python3 scripts/audit_event_sources.py
```

### Step 2: Search for Real Coverage
Use web search to find actual coverage:
```python
# Example search queries:
"[Event headline] [Date] [Key actor]"
"[Organization] investigation [Topic] 2025"
"Senate hearing [Topic] [Date]"
```

### Step 3: Verify Sources Exist
Before adding ANY source:
1. Check the URL actually loads
2. Verify the article date matches the event timeframe
3. Confirm the content relates to the event

```bash
# Quick verification
curl -I "[URL]" 2>/dev/null | head -3
```

### Step 4: Add Diverse Perspectives
For each event, try to include:
- **Official sources** (government statements, court documents)
- **Mainstream media** (major news outlets)
- **Fact-checkers** (FactCheck.org, Snopes, PolitiFact)
- **Congressional responses** (Senator statements, committee reports)
- **Watchdog organizations** (Common Cause, CREW, etc.)

### Step 5: Use the Event Manager
Add sources using the timeline_event_manager:
```python
from timeline_event_manager import TimelineEventManager
manager = TimelineEventManager()

# Load event
event = manager.load_event(event_id)

# Add verified sources
event['sources'].append({
    "title": "Actual article title",
    "url": "https://verified-url.com/article",
    "outlet": "News Organization",
    "date": "2025-05-15"
})

# Update status
if len(event['sources']) >= 3:
    event['status'] = 'confirmed'
elif len(event['sources']) >= 2:
    event['status'] = 'reported'

# Save
manager.save_event(event, overwrite=True)
```

## Priority Events Needing Sources

### Top 10 Single-Source Events (as of Sept 2, 2025)

1. **Paramount/60 Minutes settlement** (2025-04-29)
   - Current: New York Times
   - Search: "Paramount CBS 60 Minutes Trump settlement 2025"

2. **Donor pay-for-access list** (2025-08-02)
   - Current: New York Times  
   - Search: "MAGA Inc donor list Trump access 2025"

3. **Capital One CFPB case dropped** (2025-02-15)
   - Current: House Oversight Democrats
   - Search: "Capital One CFPB case dropped inauguration donation"

4. **DHS sensitive locations policy** (2025-07-01)
   - Current: NBC News
   - Search: "DHS ICE arrests churches schools policy 2025"

5. **Large investors Trump Media stake** (2025-05-09)
   - Current: The Guardian
   - Search: "Trump Media institutional investors SEC filing 2025"

6. **Miller/Noem 3000 daily arrests** (2025-06-01)
   - Current: Axios
   - Search: "Stephen Miller Kristi Noem ICE arrests quota 2025"

7. **DOJ/FBI corruption teams gutted** (2025-02-01)
   - Current: NBC News
   - Search: "DOJ FBI public corruption unit disbanded 2025"

8. **Trump megadonor access claims** (2025-04-11)
   - Current: Rolling Stone
   - Search: "Trump donor White House access video 2025"

9. **ICE whistleblower retaliation** (2022-12-27)
   - Current: The Intercept
   - Search: "Carlo Jimenez ICE whistleblower weapons detention"

10. **Vietnam resort groundbreaking** (2025-05-21)
    - Current: New Republic
    - Search: "Eric Trump Vietnam golf resort $1.5 billion 2025"

## Scripts Available

### For Analysis
- `scripts/audit_event_sources.py` - Identifies events needing sources
- `scripts/check_source_status.py` - Current source quality report
- `scripts/analyze_single_source_events.py` - Detailed single-source analysis

### For Adding Sources
- `scripts/add_real_sources.py` - Template for adding verified sources
- `timeline_event_manager.py` - Core tool for event updates

### For Cleanup
- `scripts/smart_source_cleanup.py` - Marks status without removing sources
- `tools/validation/check_all_links.py` - Verifies all URLs work

## Guidelines for Future Events

### Events After September 2, 2025
- Mark as `status: developing` or `status: predicted`
- Note in summary that this is planned/announced
- Still require sources for the announcement itself

### Events Without Additional Sources
If thorough search finds no additional coverage:
1. Keep the single source
2. Mark `status: needs-review`
3. Add note: "Single source - additional verification needed"
4. Consider reaching out to journalists for confirmation

## Quality Standards

### Minimum Requirements
- **Importance ≥ 8**: Need at least 2 real sources
- **Importance ≥ 9**: Need at least 3 real sources, including fact-check if controversial
- **Importance 10**: Need comprehensive sourcing (5+ sources) from diverse perspectives

### Source Types to Prioritize
1. **Primary documents** (court filings, government releases)
2. **Major news outlets** (AP, Reuters, mainstream papers)
3. **Fact-checkers** (for controversial claims)
4. **Congressional records** (hearings, statements)
5. **Watchdog reports** (CREW, Common Cause, etc.)

### Sources to Avoid
- Placeholder URLs (example.com)
- Generic outlets ("Major News Outlet")
- Future-dated articles we can't verify
- Opinion pieces as sole sources
- Social media posts without corroboration

## Next Steps

1. **Run audit**: `python3 scripts/audit_event_sources.py`
2. **Pick top event** from single-source list
3. **Web search** for real coverage
4. **Verify URLs** actually exist
5. **Add sources** using event manager
6. **Update status** appropriately
7. **Commit changes** with clear message
8. **Repeat** for next event

## Progress Tracking

Create a simple tracking file:
```markdown
# Source Addition Progress

## Completed
- [x] Qatar jet - Added 8 sources (Sept 2)

## In Progress
- [ ] Paramount settlement - Searching...

## To Do
- [ ] Donor pay-for-access
- [ ] Capital One CFPB
[etc...]
```

## Remember

**Quality over quantity.** One real, verified source is better than ten fake ones. The timeline's credibility depends on every source being real and verifiable.