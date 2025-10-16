# QA Agent Instructions V2 - Search-Only Strategy
## Critical Rules to Prevent Hangs

### ⛔ NEVER DO THESE (They cause hangs):
1. ❌ DO NOT use WebFetch on existing sources in the event
2. ❌ DO NOT try to verify existing sources
3. ❌ DO NOT fetch from: New York Times, Washington Post, Wall Street Journal
4. ❌ DO NOT fetch any URL that's already in the event's sources list

### ✅ ALWAYS DO THESE:
1. ✅ Use WebSearch ONLY to find NEW sources
2. ✅ Add NEW sources from search results
3. ✅ Trust existing sources are valid (don't verify them)
4. ✅ Skip fetching if unsure - just use search results

---

## Step-by-Step Workflow

### Step 1: Get Event
```bash
python3 research_cli.py validation-runs-next --run-id 13 --validator-id "qa-search-[YOUR_ID]"
```

### Step 2: Read Event File & Count Sources
```bash
# Read the event file directly
cat "/Users/markr/kleptocracy-timeline/timeline_data/events/[EVENT_ID].json"
```

**What to note:**
- Current source count (e.g., 2 sources)
- Existing outlets (e.g., "NYT", "Reuters")
- Event title, date, key actors
- **DO NOT FETCH THESE SOURCES**

### Step 3: WebSearch for NEW Sources
Use WebSearch (safe, never hangs) to find additional coverage:

```bash
# Search using event details
# Example queries:
# - "Trump Taj Mahal 1990 bankruptcy"
# - "Cambridge Analytica Facebook 2016 data"
# - "Powell memo 1971 corporate"
```

**What to look for in search results:**
- News articles from different outlets
- Government documents (.gov)
- Academic sources (.edu)
- Investigative journalism (ProPublica, ICIJ)
- Court records
- Congressional reports

### Step 4: Select NEW Source Candidates

From search results, pick 2-3 sources that:
1. ✅ Are NOT already in the event
2. ✅ Are from credible outlets (tier-1/tier-2)
3. ✅ Cover the same event/date
4. ✅ Are NOT paywalled (avoid NYT, WaPo, WSJ)

**Good tier-1 sources:**
- Reuters, AP, Bloomberg
- NPR, PBS, BBC
- Government sites (.gov)
- Academic sites (.edu)
- ProPublica, ICIJ
- Congressional records
- Court documents

### Step 5: Add NEW Sources (NO FETCHING REQUIRED)

You can add sources directly from search results WITHOUT fetching:
- Use the title from search result snippet
- Use the URL from search result
- Use the outlet name
- Use the date from search result or event date

**Example new source object:**
```json
{
  "title": "Title from search result",
  "url": "https://reuters.com/article/...",
  "outlet": "Reuters",
  "date": "2016-01-15"
}
```

### Step 6: Update Event JSON

```bash
# Create updated event with existing + new sources
# Keep ALL existing sources
# Add 1-2 NEW sources
# Update summary if new info found (from search snippets)
```

### Step 7: Save & Complete

```bash
# Save updated event
cp enhanced_event.json "/Users/markr/kleptocracy-timeline/timeline_data/events/[EVENT_ID].json"

# Log validation
python3 research_cli.py qa-validate --event-id [EVENT_ID] --quality-score 8 --validation-notes "Added 2 new sources via search: Reuters, NPR"

# Complete validation run
python3 research_cli.py validation-runs-complete --run-id 13 --run-event-id [RUN_EVENT_ID] --status validated --notes "Added 2 credible sources"
```

---

## Success Criteria

✅ Event has 3+ total sources (existing + new)
✅ At least 1 NEW credible source added
✅ NO hanging on WebFetch
✅ Completed in <2 minutes

---

## If You Must Fetch (Advanced Only)

**Only fetch if:**
- Source looks highly credible from search
- It's a government/academic site
- You have time budget remaining

**Immediate skip list:**
- New York Times (nytimes.com)
- Washington Post (washingtonpost.com)
- Wall Street Journal (wsj.com)
- Any site requiring login
- Any site with paywall indicators

**If fetching:**
- Set mental timer: 10 seconds max
- If page hasn't loaded in 10 seconds, abandon immediately
- Use search result info instead

---

## Example Successful Run

1. Get event: "2016-01-01--cambridge-analytica-deploys-facebook-data"
2. Read event: Has 2 sources (Rolling Stone, CNBC)
3. WebSearch: "Cambridge Analytica Facebook 2016 data scandal"
4. Search results show:
   - NPR article
   - ProPublica investigation
   - Congressional testimony
5. Add 2 new sources from search results (no fetching needed):
   - NPR (from search snippet + URL)
   - ProPublica (from search snippet + URL)
6. Save event with 4 total sources
7. Complete: Quality score 9/10

**Time: 1 minute, 30 seconds**

---

## Return Summary Format

```
Event: [EVENT_ID]
Title: [Event Title]
Original sources: [count] from [outlets]
NEW sources added: [count] from [outlets]
Total sources: [final count]
Strategy: Search-only (no fetching)
Quality score: [8-10]
Time: [duration]
Issues: None
```
