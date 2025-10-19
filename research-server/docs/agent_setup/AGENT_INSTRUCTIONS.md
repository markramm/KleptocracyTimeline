# Agent Instructions for Research Tasks

## For All Research Agents

### CRITICAL: Duplicate Detection Protocol

**BEFORE creating any event, you MUST**:

1. **Search the Research Monitor API** for duplicates:
```python
# In your agent code, always implement these checks:
def check_for_duplicates(event_date, key_terms):
    # Search by date and main terms
    search_results = []
    for term in key_terms:
        result = search_api(f"http://localhost:5558/api/events/search?q={term}")
        search_results.extend(result['events'])
    
    # Check for events on same date
    for event in search_results:
        if event['date'] == event_date:
            return True, event  # Duplicate found!
    
    return False, None  # No duplicate
```

2. **Search patterns to use**:
- Main actor: "Trump", "Biden", "Musk", "Thiel"
- Company names: "SpaceX", "Tesla", "Palantir"
- Program names: "Starlink", "DOGE", "Project 2025"
- Specific amounts: "$500 million", "7 billion"
- Key terms from title

3. **File system check**:
```python
import os
from pathlib import Path

def check_filesystem_duplicate(date, slug):
    event_id = f"{date}--{slug}"
    event_path = Path(f"timeline_data/events/{event_id}.json")
    return event_path.exists()
```

### Duplicate Decision Tree

```
Is there an event on the same date with similar content?
├── YES → Don't create new event
│   └── Consider updating existing event's summary if new info
└── NO → Does a recent event cover this topic?
    ├── YES → Is this a significant new development?
    │   ├── YES → Create new event
    │   └── NO → Don't create
    └── NO → Create new event
```

## Agent-Specific Instructions

### Web Research Agent

When tasked with researching a topic:

1. **Always start with duplicate detection**:
```python
# Before researching
existing_events = search_api(f"search?q={research_topic}")
print(f"Found {existing_events['count']} existing events on this topic")

# Document what already exists
for event in existing_events['events'][:5]:
    print(f"- {event['date']}: {event['title']}")
```

2. **Focus research on gaps**:
- If 2008 financial crisis is well-covered, look for 2007 precursors
- If major legislation is covered, look for lobbying that led to it
- If scandal is covered, look for the cover-up or aftermath

3. **Prioritize unique information**:
- New revelations from recently released documents
- Updates that significantly change understanding
- Connections between events not previously documented

### Timeline Event Creator Agent

Your primary responsibility is ensuring quality and uniqueness:

1. **Mandatory duplicate check function**:
```python
def create_event(event_data):
    # STEP 1: Check for duplicates
    duplicates = []
    
    # Check by date
    date_check = search_api(f"search?q={event_data['date']}")
    duplicates.extend(date_check['events'])
    
    # Check by key terms
    for term in extract_key_terms(event_data['title']):
        term_check = search_api(f"search?q={term}")
        duplicates.extend(term_check['events'])
    
    # Analyze duplicates
    for dup in duplicates:
        similarity = calculate_similarity(event_data, dup)
        if similarity > 0.7:
            print(f"DUPLICATE DETECTED: {dup['id']}")
            return None
    
    # STEP 2: Only create if unique
    return create_event_file(event_data)
```

2. **Event quality requirements**:
- Importance score must be justified
- Summary must be factual and specific
- Date must be the actual event date, not research date
- ID must follow format: `YYYY-MM-DD--descriptive-slug`

### Pattern Analysis Agent

When identifying patterns across events:

1. **Use search to find all related events**:
```python
def analyze_pattern(pattern_name):
    # Get all events related to pattern
    events = []
    for search_term in pattern_keywords[pattern_name]:
        results = search_api(f"search?q={search_term}")
        events.extend(results['events'])
    
    # Remove duplicates and sort
    unique_events = {e['id']: e for e in events}.values()
    sorted_events = sorted(unique_events, key=lambda x: x['date'])
    
    return analyze_timeline(sorted_events)
```

2. **Don't create duplicate pattern events**:
- If a pattern is documented, reference it
- Create new events only for new instances of the pattern
- Update pattern analysis in research priorities, not events

### Fact Checker Agent

Your role in duplicate prevention is critical:

1. **Verify events aren't duplicated across different dates**:
```python
def verify_event_uniqueness(event):
    # Check if same event reported on different dates
    title_words = event['title'].split()
    key_words = [w for w in title_words if len(w) > 4]
    
    # Search for each key word
    potential_dups = []
    for word in key_words[:5]:  # Check first 5 key words
        results = search_api(f"search?q={word}")
        potential_dups.extend(results['events'])
    
    # Look for suspiciously similar events
    for dup in potential_dups:
        if dup['id'] != event['id']:
            if similar_content(event, dup):
                return False, f"Possible duplicate of {dup['id']}"
    
    return True, "Event appears unique"
```

## Integration with Research Monitor

### All agents should:

1. **Initialize connection**:
```python
MONITOR_URL = "http://localhost:5558"

def init_monitor():
    # Check server is running
    response = requests.get(f"{MONITOR_URL}/api/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"Connected to Research Monitor: {stats['events']['total']} events")
        return True
    return False
```

2. **Use search before create**:
```python
def safe_create_event(event_data):
    # Search for duplicates
    search_queries = [
        event_data['date'],
        event_data['title'].split()[0],  # First word of title
        event_data.get('main_actor', ''),
    ]
    
    for query in search_queries:
        if query:
            results = search_api(f"search?q={query}")
            if results['count'] > 0:
                print(f"Found {results['count']} potential duplicates")
                # Review each one
                for existing in results['events']:
                    if is_duplicate(event_data, existing):
                        print(f"DUPLICATE: Not creating {event_data['id']}")
                        return False
    
    # Safe to create
    return create_event_api(event_data)
```

3. **Track creation for commit orchestration**:
```python
def check_commit_needed():
    response = requests.get(f"{MONITOR_URL}/api/commit/status")
    status = response.json()
    
    if status['commit_needed']:
        print(f"COMMIT NEEDED: {status['events_since_commit']} events staged")
        # Notify orchestrator
        return True
    return False
```

## Examples of Duplicate Scenarios

### Scenario 1: Same event, different dates
```
Search: "Trump crypto announcement"
Found: "2025-01-17--trump-launches-crypto-memecoin"
New: "2025-01-18--trump-announces-cryptocurrency"
Decision: DUPLICATE - Same event, don't create
```

### Scenario 2: Update to existing story
```
Search: "Musk Starlink government"
Found: "2025-02-01--starlink-pentagon-contract"
New: "2025-02-15--starlink-contract-expanded"
Decision: CREATE - Significant new development
```

### Scenario 3: Different aspects of same event
```
Search: "Glass-Steagall repeal"
Found: "1999-11-12--gramm-leach-bliley-act-signed"
New: "1999-11-12--clinton-signs-banking-deregulation"
Decision: DUPLICATE - Same event, same date
```

## Verification Checklist

Before any agent creates an event:

- [ ] Searched API for date matches
- [ ] Searched API for key actor names
- [ ] Searched API for organization names
- [ ] Searched API for key terms from title
- [ ] Checked filesystem for exact ID match
- [ ] Verified this is new information
- [ ] Confirmed event date is correct
- [ ] Validated importance score
- [ ] Ensured summary has specific facts

## Error Prevention

### Common mistakes to avoid:

1. **Creating "update" events**: If it's just an update, modify the original
2. **Different dates for same event**: Use the most significant date
3. **Splitting single events**: One bill signing = one event, not multiple
4. **Vague duplicates**: "Trump announcement" could be many things
5. **Date confusion**: Use event date, not article publication date

### Required search patterns:

```python
REQUIRED_SEARCHES = [
    event_date,
    main_actor_name,
    organization_name,
    dollar_amount if mentioned,
    bill_number if legislation,
    case_name if legal,
]
```

## Reporting

Agents should report their duplicate detection:

```python
def report_duplicate_check(event_id, searches_performed, duplicates_found):
    report = {
        "event_id": event_id,
        "timestamp": datetime.now().isoformat(),
        "searches": searches_performed,
        "duplicates_found": len(duplicates_found),
        "decision": "created" if len(duplicates_found) == 0 else "skipped"
    }
    
    print(f"Duplicate Check Report: {json.dumps(report, indent=2)}")
    return report
```

This ensures transparency and helps improve the duplicate detection system over time.