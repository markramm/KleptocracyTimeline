# Research Priority System Recommendations

Generated: 2025-09-09

## Analysis Summary

After analyzing the research priority system and running the automated updater, we found:

- **120 priorities marked as completed** (100% completion rate)
- **Average event overage**: 16.1x (actual vs estimated events)
- **False positive completions identified**: Many priorities matched on broad keywords rather than specific topics
- **Primary issue**: Overly aggressive keyword matching algorithm

## Key Problems Identified

### 1. False Positive Completions
- **Example**: RT-004 (Enron-Cheney connection) marked complete with 6 events, but only 3 actually mention Enron
- **Cause**: Broad keyword matching (e.g., "energy", "corruption") caught unrelated events
- **Impact**: Priorities marked complete when core research still needed

### 2. Lack of Specificity Validation
- Current system matches on 2+ tags or 3+ keywords without validating relevance
- No semantic understanding of whether events actually address the priority's core topic
- Generic tags like "corruption" or "institutional-capture" match too broadly

### 3. No Quality Thresholds
- Priorities marked complete based on quantity alone
- No validation of whether matched events provide the specific information requested
- Missing verification that key actors, dates, or incidents are documented

## Recommendations for Improvement

### 1. Enhanced Matching Algorithm
```python
# Proposed improvements to research_priority_updater.py

def match_events_to_priorities_v2(self, events, priorities):
    """Enhanced matching with specificity validation"""
    
    # 1. Require exact actor matches for actor-specific priorities
    if priority.get('actors_to_investigate'):
        actor_matches = 0
        for actor in priority['actors_to_investigate']:
            if any(actor.lower() in event.get('actors', []).lower() 
                   for event in matched_events):
                actor_matches += 1
        
        # Require at least 50% of key actors documented
        if actor_matches < len(priority['actors_to_investigate']) * 0.5:
            continue
    
    # 2. Validate time period alignment
    if priority.get('time_period'):
        if not event_in_time_period(event, priority['time_period']):
            continue
    
    # 3. Use required keywords vs optional keywords
    required_keywords = extract_required_keywords(priority)
    if not all(keyword in event_text for keyword in required_keywords):
        continue
```

### 2. Implement Priority Lifecycle States
- **pending**: Not yet researched
- **active**: Currently being researched
- **partial**: Some events found but core requirements not met
- **review**: Enough events found, needs human validation
- **completed**: Validated as sufficiently researched
- **archived**: No longer relevant or superseded

### 3. Create Priority Templates for Common Patterns
```json
{
  "template": "person-investigation",
  "required_fields": ["target_person", "time_period", "organizations"],
  "required_events": {
    "biography": 1,
    "key_decisions": 3,
    "connections": 5,
    "controversies": 2
  }
}
```

### 4. Automated Priority Generation from Gaps
- Scan existing events for mentioned but undocumented entities
- Generate priorities for:
  - Actors mentioned 5+ times without dedicated events
  - Organizations referenced but not investigated
  - Time periods with sparse coverage

### 5. Integration Pipeline Updates

#### A. Pre-Research Validation
```bash
# Before researching a priority
python3 api/priority_validator.py RT-XXX
# Checks:
# - Priority not already covered
# - Clear research objectives
# - Measurable completion criteria
```

#### B. Post-Research Verification
```bash
# After research completes
python3 api/priority_verifier.py RT-XXX
# Validates:
# - Core requirements met
# - Key actors documented
# - Time period covered
# - Sources quality threshold
```

#### C. Periodic Review Process
```bash
# Weekly automated review
python3 api/priority_reviewer.py --audit-completed
# Actions:
# - Flag false positives
# - Identify coverage gaps
# - Generate new priorities
# - Archive obsolete priorities
```

### 6. Priority Scoring System
```python
def calculate_priority_score(priority, matched_events):
    score = 0
    
    # Actor coverage (30 points)
    actor_coverage = count_documented_actors(priority, matched_events)
    score += min(30, actor_coverage * 10)
    
    # Time period coverage (20 points)
    period_coverage = calculate_period_coverage(priority, matched_events)
    score += period_coverage * 20
    
    # Source quality (25 points)
    source_quality = assess_source_quality(matched_events)
    score += source_quality * 25
    
    # Specific requirements (25 points)
    requirements_met = check_specific_requirements(priority, matched_events)
    score += requirements_met * 25
    
    return score  # 0-100, need 75+ for completion
```

### 7. Coverage Gap Analysis

Based on current timeline analysis, create new priorities for:

#### Underrepresented Time Periods
- 1960s-1970s: Early corporate capture foundations
- 1990s: Clinton era deregulation
- 2010-2016: Obama era institutional patterns

#### Missing Actor Networks
- Corporate board interlocks
- Think tank coordination networks
- International oligarch connections

#### Systemic Patterns
- Regulatory capture mechanisms by industry
- Crisis exploitation playbooks
- Information warfare evolution

### 8. Human-in-the-Loop Validation
- Require manual review for high-importance priorities (importance >= 8)
- Sample 10% of auto-completed priorities for quality checks
- Flag priorities with conflicting or dubious matched events

## Implementation Priority

1. **Immediate**: Fix false positive issue in research_priority_updater.py
2. **Short-term**: Implement enhanced matching algorithm
3. **Medium-term**: Add lifecycle states and scoring system
4. **Long-term**: Build automated gap analysis and priority generation

## Metrics for Success

- **Precision**: 90%+ of completed priorities have relevant matched events
- **Recall**: 80%+ of relevant events matched to appropriate priorities
- **Coverage**: No time period with <10 events per year (for covered years)
- **Quality**: 75%+ of events have 3+ credible sources
- **Efficiency**: <5% duplicate or redundant priorities

## Next Steps

1. Reset falsely completed priorities to "pending" or "partial"
2. Implement enhanced matching algorithm
3. Run validation on existing "completed" priorities
4. Generate new priorities for identified gaps
5. Integrate updater into research pipeline with quality gates