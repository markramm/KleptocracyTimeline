# Research Workflow for Kleptocracy Timeline

## Overview
This document describes the complete workflow for researching and adding events to the kleptocracy timeline using the Research Monitor v2 system.

## Prerequisites

1. **Start the Research Monitor server**:
```bash
cd research_monitor
RESEARCH_MONITOR_PORT=5558 python3 app_v2.py &
```

2. **Verify server is running**:
```bash
curl http://localhost:5558/api/stats | jq
```

## Complete Research Workflow

### Phase 1: Priority Selection

1. **Get the next research priority**:
```bash
curl http://localhost:5558/api/priorities/next | jq
```

2. **Note the priority details**:
- ID (e.g., `RT-050-clinton-era-financial-deregulation-capture`)
- Title and description
- Estimated events to find
- Time period to focus on
- Key actors to investigate

3. **Update priority status to in_progress**:
```bash
curl -X PUT "http://localhost:5558/api/priorities/{PRIORITY_ID}/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### Phase 2: Duplicate Detection (CRITICAL)

Before researching, check what already exists:

1. **Search for topic-related events**:
```bash
# Search for the main topic
curl "http://localhost:5558/api/events/search?q=clinton+deregulation"
curl "http://localhost:5558/api/events/search?q=glass+steagall"
curl "http://localhost:5558/api/events/search?q=derivatives"
```

2. **Search for key actors mentioned**:
```bash
curl "http://localhost:5558/api/events/search?q=Robert+Rubin"
curl "http://localhost:5558/api/events/search?q=Larry+Summers"
curl "http://localhost:5558/api/events/search?q=Phil+Gramm"
```

3. **Check the relevant time period**:
```bash
# For Clinton era (1993-2001)
ls -la timeline_data/events/199*.json | wc -l
ls -la timeline_data/events/2000*.json | wc -l
ls -la timeline_data/events/2001*.json | head -20
```

4. **Document what you found**:
- Make notes of existing events
- Identify gaps in coverage
- Note which aspects are already well-documented

### Phase 3: Research

1. **Conduct web searches** for:
- Specific dates of key events
- Legislative actions (bills passed, hearings)
- Executive actions (appointments, orders)
- Corporate actions (mergers, lobbying)
- Scandals or investigations

2. **Focus on verifiable facts**:
- Exact dates
- Specific people involved
- Concrete actions taken
- Measurable outcomes
- Named organizations

3. **Prioritize high-impact events**:
- Major legislation (importance: 8-10)
- Significant appointments (importance: 6-8)
- Large financial transactions (importance: 7-9)
- Regulatory changes (importance: 6-9)
- Scandals/investigations (importance: 5-8)

### Phase 4: Event Creation

For each potential event:

1. **Final duplicate check**:
```bash
# Search for the specific date and key terms
curl "http://localhost:5558/api/events/search?q=1999+11+12+gramm"
ls -la timeline_data/events/1999-11-12*.json
```

2. **If not a duplicate, create the event**:
```bash
curl -X POST "http://localhost:5558/api/events/staged" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{
    "id": "1999-11-12--gramm-leach-bliley-act-repeals-glass-steagall",
    "date": "1999-11-12",
    "title": "Gramm-Leach-Bliley Act Repeals Glass-Steagall Banking Separation",
    "summary": "President Clinton signs the Gramm-Leach-Bliley Act, repealing the Glass-Steagall Act of 1933 that separated commercial and investment banking. The legislation, pushed by Sen. Phil Gramm (R-TX) and supported by Treasury Secretary Robert Rubin (former Goldman Sachs co-chairman), allows commercial banks, investment banks, and insurance companies to consolidate. The repeal enables the creation of 'too big to fail' financial institutions and is later identified as a key factor in the 2008 financial crisis. Citigroup, which had already merged with Travelers Group in violation of Glass-Steagall, heavily lobbied for the repeal with CEO Sandy Weill personally calling President Clinton.",
    "importance": 9,
    "tags": ["glass-steagall-repeal", "financial-deregulation", "clinton-administration", "wall-street-capture", "2008-crisis-precursor"],
    "priority_id": "RT-050-clinton-era-financial-deregulation-capture"
  }'
```

3. **Verify the event was created**:
```bash
ls -la timeline_data/events/1999-11-12*.json
```

### Phase 5: Progress Tracking

1. **Check commit status regularly**:
```bash
curl http://localhost:5558/api/commit/status | jq
```

2. **When you've created several events**, update the priority:
```bash
curl -X PUT "http://localhost:5558/api/priorities/{PRIORITY_ID}/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "actual_events": 5,
    "notes": "Found 5 major deregulation events: Glass-Steagall repeal, CFMA 2000, etc."
  }'
```

### Phase 6: Commit Orchestration

1. **When threshold is reached** (10 events):
```bash
curl http://localhost:5558/api/commit/status | jq
# Should show: "commit_needed": true
```

2. **Perform the git commit**:
```bash
cd /Users/markr/kleptocracy-timeline
git add timeline_data/events research_priorities
git commit -m "Add researched events on Clinton-era financial deregulation

- Glass-Steagall repeal (1999)
- Commodity Futures Modernization Act (2000)
- Treasury-Wall Street revolving door appointments
- Derivatives deregulation
"
```

3. **Reset the counter**:
```bash
curl -X POST http://localhost:5558/api/commit/reset -H "X-API-Key: test-key"
```

## Quality Guidelines

### Event Importance Scores

| Score | Description | Examples |
|-------|-------------|----------|
| 10 | Constitutional crisis, systemic transformation | Coup attempt, constitutional amendment |
| 9 | Major legislation, massive corruption | Glass-Steagall repeal, trillion-dollar fraud |
| 8 | Significant policy change, large scandal | Major deregulation, billion-dollar scheme |
| 7 | Important appointment, substantial conflict | Cabinet appointment, major no-bid contract |
| 6 | Notable investigation, significant merger | Congressional investigation, major acquisition |
| 5 | Relevant development, moderate impact | Policy announcement, million-dollar deal |
| 4 | Minor scandal, small policy change | Ethics violation, regulatory adjustment |
| 3 | Contextual information | Meeting, statement, minor appointment |
| 2 | Background detail | Routine action, minor development |
| 1 | Tangential connection | Peripheral event, minor relevance |

### Event ID Best Practices

Format: `YYYY-MM-DD--descriptive-slug`

Good examples:
- `1999-11-12--gramm-leach-bliley-act-repeals-glass-steagall`
- `2001-01-20--robert-rubin-joins-citigroup-after-treasury`
- `2000-12-21--commodity-futures-modernization-act-deregulates-derivatives`

Bad examples:
- `1999-11-12--act-passed` (too vague)
- `1999-11-12--clinton-signs-important-banking-legislation-that-changes-everything` (too long)
- `1999-11--glass-steagall` (missing day)

### Summary Writing Guidelines

1. **First sentence**: State the key fact with date and actors
2. **Context**: Explain why this matters
3. **Details**: Include specific names, amounts, organizations
4. **Connections**: Link to related events or patterns
5. **Consequences**: Mention known outcomes if applicable

Example:
> "President Clinton signs the Gramm-Leach-Bliley Act, repealing the Glass-Steagall Act of 1933 that separated commercial and investment banking. The legislation, pushed by Sen. Phil Gramm (R-TX) and supported by Treasury Secretary Robert Rubin (former Goldman Sachs co-chairman), allows commercial banks, investment banks, and insurance companies to consolidate. The repeal enables the creation of 'too big to fail' financial institutions and is later identified as a key factor in the 2008 financial crisis."

## Common Duplicate Patterns to Avoid

### Same Event, Different Angles
- Don't create separate events for announcement and implementation
- Don't create separate events for House and Senate passage
- Combine related developments on the same day

### Updates vs New Events
- Minor updates go in existing event summaries
- Only create new events for significant new developments
- Personnel changes at same organization can be combined

### Check These Formats
Before creating, search for:
- Different date formats (check day before/after)
- Alternate spellings of names
- Acronyms vs full names
- Company name variations

## Automation Tips

### Batch Duplicate Checking
```bash
# Check multiple terms at once
for term in "glass-steagall" "gramm-leach" "banking-deregulation"; do
  echo "=== Searching for: $term ==="
  curl -s "http://localhost:5558/api/events/search?q=$term" | jq '.count'
done
```

### Quick Event Count
```bash
# Count events in a time period
ls -la timeline_data/events/1999-*.json | wc -l
```

### View Recent Additions
```bash
# See most recently modified events
ls -lt timeline_data/events/*.json | head -20
```

## Troubleshooting

### Event Not Appearing in Search
- Wait 30 seconds for filesystem sync
- Check the JSON is valid: `jq . < timeline_data/events/YOUR-EVENT.json`
- Verify the server is running: `curl http://localhost:5558/api/stats`

### Duplicate Event Created
- Delete the duplicate: `rm timeline_data/events/DUPLICATE-EVENT.json`
- Wait for sync, then search again
- Update the original event if needed

### Server Errors
- Check logs: Look at the terminal where server is running
- Restart if needed: Kill the process and restart
- Check database: Stats endpoint shows database status

## Final Checklist

Before committing a batch of events:
- [ ] All events have been searched for duplicates
- [ ] Event IDs follow the correct format
- [ ] Importance scores are consistent and justified
- [ ] Summaries include specific facts and dates
- [ ] Tags are consistent with existing taxonomy
- [ ] Priority status has been updated
- [ ] Commit message summarizes the additions