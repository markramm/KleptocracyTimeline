# Agent Guidelines - Analysis Directory

## 🎯 Purpose
Pattern analysis, findings, and intelligence derived from timeline data.

## 📁 Contents

### Key Documents
- **PATTERN_ANALYSIS.md** - Comprehensive analysis of 9 capture lanes
- **CAPTURE_LANES.md** - Detailed capture mechanism definitions
- Additional analysis documents as created

## 📊 Analysis Standards

### Data-Driven Conclusions
Every claim must be:
1. **Sourced** from timeline events
2. **Quantified** where possible
3. **Reproducible** by others
4. **Transparent** about methodology

### Pattern Recognition Guidelines

#### Valid Patterns
- Same actors across multiple events
- Temporal clustering of related events
- Financial flows between entities
- Recurring tactics or strategies
- Acceleration/deceleration trends

#### Invalid Patterns
- Correlation without evidence
- Speculation beyond data
- Partisan interpretations
- Conspiracy without documentation

## 🔍 Analysis Methodologies

### Temporal Analysis
```python
# Example: Find acceleration patterns
def analyze_acceleration(events_by_year):
    for year in sorted(events_by_year.keys()):
        count = len(events_by_year[year])
        if year > min(events_by_year.keys()):
            prev_count = len(events_by_year[year-1])
            growth = (count - prev_count) / prev_count * 100
            print(f"{year}: {count} events ({growth:+.1f}% change)")
```

### Network Analysis
```python
# Example: Find connected actors
def find_actor_networks(events):
    from collections import defaultdict
    connections = defaultdict(set)
    
    for event in events:
        actors = event.get('actors', [])
        for i, actor1 in enumerate(actors):
            for actor2 in actors[i+1:]:
                connections[actor1].add(actor2)
                connections[actor2].add(actor1)
    
    return connections
```

### Financial Analysis
```python
# Example: Track money flows
def track_financial_flows(events):
    flows = []
    for event in events:
        if 'financial' in event.get('tags', []):
            amount = extract_amount(event['summary'])
            if amount:
                flows.append({
                    'date': event['date'],
                    'amount': amount,
                    'actors': event.get('actors', []),
                    'type': categorize_transaction(event)
                })
    return flows
```

## 📈 Key Metrics to Track

### Acceleration Metrics
- Events per year
- Events per month (recent)
- Growth rate
- Doubling time
- Inflection points

### Network Metrics
- Actor centrality
- Connection density
- Cluster coefficient
- Bridge actors
- Network diameter

### Financial Metrics
- Total documented flows
- Average transaction size
- Concentration ratios
- Flow directions
- Shell company usage

### Capture Lane Metrics
- Events per lane
- Lane acceleration rates
- Cross-lane coordination
- Lane effectiveness
- Resistance points

## 🔄 Analysis Workflows

### New Pattern Discovery
1. **Hypothesis Formation**
   - Based on recent events
   - Or theoretical framework

2. **Data Extraction**
   ```python
   relevant_events = [e for e in events if matches_criteria(e)]
   ```

3. **Pattern Testing**
   - Statistical significance
   - Temporal consistency
   - Cross-validation

4. **Documentation**
   - Methodology
   - Findings
   - Limitations
   - Implications

### Trend Analysis
1. **Select Timeframe**
2. **Extract Relevant Events**
3. **Calculate Metrics**
4. **Identify Inflection Points**
5. **Project Forward** (with caveats)

### Network Mapping
1. **Identify Entities**
2. **Extract Relationships**
3. **Calculate Centrality**
4. **Visualize Network**
5. **Identify Key Nodes**

## 📝 Writing Standards

### Structure
```markdown
# Analysis Title

## Executive Summary
Key findings in 3-5 bullets

## Methodology
How analysis was conducted

## Findings
### Finding 1
Evidence and explanation

### Finding 2
Evidence and explanation

## Implications
What this means

## Limitations
What we don't know

## Appendix
Supporting data
```

### Language
- **Precise**: Use exact numbers
- **Cautious**: "Suggests" not "proves"
- **Clear**: Avoid jargon
- **Honest**: State limitations

### Citations
- Reference specific events by ID
- Link to timeline entries
- Quote sources directly
- Provide reproducible queries

## 🚨 Quality Checks

### Before Publishing Analysis
1. **Data Accuracy**: All numbers verified
2. **Methodology Clear**: Others can reproduce
3. **Limitations Stated**: What we don't know
4. **Sources Cited**: Every claim backed
5. **Peer Review**: Second opinion if possible

### Red Flags to Avoid
- Claiming causation without evidence
- Extrapolating beyond data
- Ignoring contradictory events
- Overstating confidence
- Political bias in interpretation

## 🎯 High-Priority Analyses

### Needed Now
1. **2025 Acceleration Analysis** - Why 162x increase?
2. **Network Centrality Study** - Who are key nodes?
3. **Financial Flow Mapping** - Where's money going?
4. **Capture Lane Interactions** - How do lanes reinforce?
5. **Prediction Modeling** - What's next?

### Ongoing Monitoring
- Weekly acceleration rates
- New actor appearances
- Emerging patterns
- Tactical innovations
- Resistance effectiveness

## 🔧 Analysis Tools

### Python Scripts
```python
# Load timeline data
import json
import pandas as pd
from datetime import datetime

with open('timeline_complete.json') as f:
    data = json.load(f)
    events = pd.DataFrame(data['events'])
    events['date'] = pd.to_datetime(events['date'])
```

### SQL Queries
```sql
-- Find most connected actors
SELECT actor, COUNT(*) as appearances
FROM events, json_each(events.actors) as actor
GROUP BY actor
ORDER BY appearances DESC
LIMIT 20;
```

### Visualization
```python
import matplotlib.pyplot as plt
import networkx as nx

# Create network graph
G = nx.Graph()
# Add nodes and edges from events
# Visualize with spring layout
```

## 📊 Standard Visualizations

### Required Charts
1. **Acceleration Curve** - Events over time
2. **Network Graph** - Actor connections
3. **Heat Map** - Capture lane activity
4. **Sankey Diagram** - Financial flows
5. **Timeline** - Key events marked

### Chart Standards
- Clear titles and labels
- Source attribution
- Date of analysis
- Methodology note
- Interactive if possible

## 🎯 Analysis Templates

### Pattern Analysis Template
```markdown
## Pattern: [Name]

### Description
What the pattern is

### Evidence
- Event 1 (ID: xxx)
- Event 2 (ID: xxx)
- Event 3 (ID: xxx)

### Frequency
How often it occurs

### Implications
What it means

### Counter-examples
Events that don't fit

### Confidence Level
High/Medium/Low with reasoning
```

### Acceleration Analysis Template
```markdown
## Period: [Start] to [End]

### Metrics
- Starting rate: X events/month
- Ending rate: Y events/month
- Acceleration: Z% increase

### Contributing Factors
- Factor 1: Evidence
- Factor 2: Evidence

### Projection
If trend continues: [calculation]

### Uncertainties
What could change this
```

## 🚀 Quick Analysis Commands

```bash
# Count events by year
jq '.events | group_by(.date[0:4]) | map({year: .[0].date[0:4], count: length})' timeline_complete.json

# Find most common actors
jq '.events | map(.actors[]?) | group_by(.) | map({actor: .[0], count: length}) | sort_by(.count) | reverse | .[0:10]' timeline_complete.json

# Extract financial events
jq '.events | map(select(.tags[]? | contains("financial")))' timeline_complete.json

# Calculate monthly rate for 2025
jq '.events | map(select(.date | startswith("2025"))) | length' timeline_complete.json
```

## 📋 Analysis Checklist

- [ ] Clear hypothesis or question
- [ ] Appropriate methodology
- [ ] Sufficient data sample
- [ ] Statistical significance tested
- [ ] Alternative explanations considered
- [ ] Limitations documented
- [ ] Findings clearly stated
- [ ] Implications discussed
- [ ] Reproducible process
- [ ] Peer review if possible
- [ ] Visualizations included
- [ ] Sources cited
- [ ] Ready for publication

---

*"In patterns we find predictions. In networks we find power. In acceleration we find urgency. Analyze with rigor, conclude with caution."*