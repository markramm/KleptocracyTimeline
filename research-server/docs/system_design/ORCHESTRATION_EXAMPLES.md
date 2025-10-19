# Claude Code Orchestration Examples

## Overview
This document provides practical examples of how to use the Claude Code Task tool with subagents to achieve high-quality, low-cost timeline research and event creation.

## Example 1: Single Event Research to Creation

### Scenario
User wants to add an event about a specific scandal.

### Orchestration Flow
```python
# Step 1: Check for duplicates (Haiku - $0.0003)
duplicate_check = Task(
    subagent_type="general-purpose",
    description="Check for duplicate event",
    prompt="""
    Using the duplicate-checker agent instructions:
    Check if "Halliburton $7B Iraq contract 2003" exists.
    Search the Research Monitor API at http://localhost:5558
    Return JSON with is_duplicate, confidence, and similar_events.
    """
)

# Step 2: If not duplicate, research details (Haiku - $0.002)
if not duplicate_check.is_duplicate:
    research = Task(
        subagent_type="general-purpose",
        description="Research Halliburton contract",
        prompt="""
        Using the timeline-researcher agent instructions:
        Research "Halliburton no-bid Iraq contract 2003 Dick Cheney"
        Focus on: contract value, date awarded, Cheney connection
        Return structured JSON with sources.
        """
    )

# Step 3: Validate sources (Haiku - $0.0003)
source_validation = Task(
    subagent_type="general-purpose",
    description="Validate research sources",
    prompt=f"""
    Using the source-validator agent instructions:
    Validate these sources: {research.sources}
    Check credibility and accessibility.
    Return validation results with recommendations.
    """
)

# Step 4: Main Claude creates and saves event
# Total cost: ~$0.003 (vs $0.075 with Opus only)
```

## Example 2: PDF Document Processing

### Scenario
Process a 500-page Senate report to extract all timeline events.

### Orchestration Flow
```python
# Step 1: Analyze PDF with Sonnet ($0.05)
pdf_analysis = Task(
    subagent_type="general-purpose",
    description="Analyze Senate report",
    prompt="""
    Using the pdf-analyzer agent instructions:
    Process the Senate Torture Report PDF.
    Extract all timeline events with dates, actors, and sources.
    Identify patterns and generate research priorities.
    Return structured JSON with extracted_events array.
    """
)

# Step 2: Parallel duplicate checking for all events (Haiku - $0.003 total)
duplicate_checks = []
for event in pdf_analysis.extracted_events[:10]:  # First 10 events
    check = Task(
        subagent_type="general-purpose",
        description=f"Check duplicate for {event.date}",
        prompt=f"""
        Using duplicate-checker instructions:
        Check if this event exists: {event.title} on {event.date}
        Return is_duplicate and similar_events.
        """
    )
    duplicate_checks.append(check)

# Run all checks in parallel
results = await gather(*duplicate_checks)

# Step 3: Create unique events
new_events = [e for e, r in zip(events, results) if not r.is_duplicate]

# Total cost: ~$0.053 for 10 events (vs $0.50 with Opus)
```

## Example 3: Batch Research Priority Processing

### Scenario
Process the top 5 research priorities from the queue.

### Orchestration Flow
```python
# Step 1: Get priorities from Research Monitor
priorities = curl("http://localhost:5558/api/priorities/next?limit=5")

# Step 2: Launch parallel research tasks (Haiku - $0.01 total)
research_tasks = []
for priority in priorities:
    task = Task(
        subagent_type="general-purpose",
        description=f"Research {priority.title}",
        prompt=f"""
        Using timeline-researcher instructions:
        Research: {priority.description}
        Focus on: {priority.specific_questions}
        Date range: {priority.date_range}
        Return structured events with sources.
        """
    )
    research_tasks.append(task)

# Step 3: Parallel source validation (Haiku - $0.0015 total)
research_results = await gather(*research_tasks)
validation_tasks = []
for result in research_results:
    task = Task(
        subagent_type="general-purpose",
        description="Validate sources",
        prompt=f"Validate sources: {result.sources}"
    )
    validation_tasks.append(task)

# Step 4: Main Claude synthesizes and saves
# Total cost: ~$0.015 for 5 priorities (vs $0.375 with Opus)
```

## Example 4: Pattern Detection Across Timeline

### Scenario
Identify patterns of regulatory capture across multiple agencies.

### Orchestration Flow
```python
# Step 1: Search for relevant events
events = curl("http://localhost:5558/api/events/search?q=regulatory+capture")

# Step 2: Analyze patterns with Sonnet ($0.03)
pattern_analysis = Task(
    subagent_type="general-purpose",
    description="Analyze regulatory capture patterns",
    prompt=f"""
    Analyze these {len(events)} events for patterns:
    {events}
    
    Identify:
    - Common tactics used
    - Key actors across agencies  
    - Timeline of escalation
    - Financial beneficiaries
    
    Return structured pattern analysis.
    """
)

# Step 3: Generate research priorities for gaps (Haiku - $0.002)
gap_research = Task(
    subagent_type="general-purpose",
    description="Identify research gaps",
    prompt=f"""
    Based on patterns: {pattern_analysis.patterns}
    Identify missing events or time periods.
    Generate 5 research priorities.
    """
)

# Total cost: ~$0.032 (vs $0.15 with Opus)
```

## Example 5: Real-time Event Validation

### Scenario
User manually creates an event that needs validation.

### Orchestration Flow
```python
# Parallel validation tasks (all Haiku - $0.001 total)
validation_tasks = [
    # Check duplicates
    Task(
        subagent_type="general-purpose",
        description="Check duplicates",
        prompt=f"Check if {event.title} on {event.date} exists"
    ),
    
    # Validate sources
    Task(
        subagent_type="general-purpose",
        description="Validate sources",
        prompt=f"Validate sources: {event.sources}"
    ),
    
    # Extract and normalize dates
    Task(
        subagent_type="general-purpose",
        description="Verify dates",
        prompt=f"Verify date format and logic: {event.date}"
    ),
    
    # Generate tags
    Task(
        subagent_type="general-purpose",
        description="Generate tags",
        prompt=f"Generate tags for: {event.summary}"
    )
]

results = await gather(*validation_tasks)

# Main Claude makes final decision
if all_valid(results):
    save_event(event)
else:
    return_issues(results)

# Total cost: ~$0.001 (vs $0.06 with Opus)
```

## Cost Comparison Table

| Workflow | Opus Only | Optimized (Haiku/Sonnet) | Savings |
|----------|-----------|---------------------------|---------|
| Single Event | $0.075 | $0.003 | 96% |
| PDF Processing (10 events) | $0.50 | $0.053 | 89% |
| 5 Research Priorities | $0.375 | $0.015 | 96% |
| Pattern Analysis | $0.15 | $0.032 | 79% |
| Event Validation | $0.06 | $0.001 | 98% |
| **Daily Total (100 operations)** | **$7.50** | **$0.50** | **93%** |

## Orchestration Best Practices

### 1. Always Start with Cheap Checks
```python
# Good: Check duplicate first (cheap)
if not duplicate_exists:
    do_expensive_research()

# Bad: Research first (expensive)
research_everything()
then_check_if_needed()
```

### 2. Use Parallel Execution
```python
# Good: Parallel tasks (faster)
tasks = [check1, check2, check3]
results = await gather(*tasks)

# Bad: Sequential tasks (slower)
result1 = await check1
result2 = await check2
result3 = await check3
```

### 3. Batch Similar Operations
```python
# Good: Batch validation
validate_all_sources(sources_list)

# Bad: Individual validation
for source in sources:
    validate_source(source)
```

### 4. Cache Common Queries
```python
# Good: Cache duplicate checks
cache_key = f"{date}_{actor}"
if cache_key in checked_cache:
    return cached_result

# Bad: Repeat same search
search_again_for_same_thing()
```

### 5. Fail Fast
```python
# Good: Stop on first failure
if duplicate_found:
    return "Skip event"
# Don't do more expensive checks

# Bad: Do all checks regardless
do_all_expensive_checks()
then_check_if_duplicate()
```

## Monitoring Usage

### Track Agent Costs
```python
agent_usage = {
    "duplicate-checker": {"calls": 45, "cost": 0.014},
    "timeline-researcher": {"calls": 12, "cost": 0.024},
    "source-validator": {"calls": 23, "cost": 0.007},
    "pdf-analyzer": {"calls": 2, "cost": 0.10}
}

daily_total = sum(a["cost"] for a in agent_usage.values())
print(f"Daily cost: ${daily_total:.3f}")
```

### Performance Metrics
```python
metrics = {
    "events_created": 25,
    "duplicates_prevented": 8,
    "sources_validated": 75,
    "patterns_identified": 3,
    "cost_per_event": 0.02,
    "time_saved": "4 hours"
}
```

## Troubleshooting

### If Haiku Can't Handle Task
```python
try:
    result = haiku_task()
    if result.confidence < 0.7:
        # Escalate to Sonnet
        result = sonnet_task()
except ComplexityError:
    # Skip Haiku, go straight to Sonnet
    result = sonnet_task()
```

### If API is Down
```python
try:
    api_search()
except ConnectionError:
    # Fallback to filesystem
    grep_search()
```

### If Costs Exceed Budget
```python
if daily_cost > budget_limit:
    # Switch to essential operations only
    disable_pattern_analysis()
    reduce_source_validation()
    increase_caching()
```

## Summary

By using this orchestration pattern:
- **93% cost reduction** for routine operations
- **3-5x faster** event creation
- **No quality loss** for standard tasks
- **Better quality** through systematic validation
- **Scalable** to hundreds of events per day

The key is using the right tool for each job:
- Haiku for structured, simple tasks
- Sonnet for complex analysis
- Opus for orchestration and synthesis