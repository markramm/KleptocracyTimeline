# Claude Code Custom Agents Setup Guide

## Overview

This guide provides instructions for setting up custom subagents in Claude Code to optimize the timeline research and entry creation workflow using smaller, faster models for specific tasks.

## Architecture

The system uses two specialized agents:

1. **timeline-researcher**: Handles web research and source verification (Haiku model)
2. **timeline-entry-creator**: Creates properly formatted YAML entries (Haiku model)

The main Claude (Opus/Sonnet) orchestrates these agents, synthesizes results, and handles complex analysis.

## Setup Instructions

### 1. Directory Structure

The agent configuration files have been created in:
```
kleptocracy-timeline/
├── .claude/
│   └── agents/
│       ├── timeline-researcher.md
│       └── timeline-entry-creator.md
```

### 2. Agent Configuration

Each agent file contains:
- **YAML frontmatter**: Defines name, description, model, and available tools
- **System prompt**: Provides detailed instructions for the agent's role

### 3. Using the Agents in Claude Code

#### Research Workflow

```markdown
# Research a specific event
@timeline-researcher Please research the Halliburton no-bid contracts during the Iraq War, focusing on:
- Contract values and timeline
- Dick Cheney's connections
- Congressional investigations
- GAO reports
```

#### Entry Creation Workflow

```markdown
# Create entry from research
@timeline-entry-creator Using this research data, create a timeline entry:
[paste research results]

Importance: 8 (major war profiteering scandal)
Tags: iraq-war, no-bid-contracts, cheney, halliburton
```

### 4. Workflow Examples

#### Example 1: Single Event Research to Entry

```python
# Step 1: Research with subagent
research_prompt = """
Research the Jack Abramoff lobbying scandal:
- Total fraud amount
- Number of convictions
- Key political figures involved
- Indian casino connections
"""

# Step 2: Create entry with subagent
entry_prompt = """
Create timeline entry from research:
[research results]
Date: 2006-01-03 (Abramoff plea)
Importance: 8
"""

# Step 3: Main Claude validates and saves
# The main model reviews, adjusts importance if needed, and saves
```

#### Example 2: Batch Processing

```python
# Create a batch research list
events_to_research = [
    "Halliburton Iraq contracts",
    "Jack Abramoff scandal", 
    "US attorneys firing scandal",
    "Blackwater Nisour Square"
]

# Research each with subagent
for event in events_to_research:
    # @timeline-researcher researches
    # @timeline-entry-creator creates entry
    # Main Claude validates and saves
```

### 5. Model Selection Rationale

**Claude 3 Haiku** is used for both agents because it:
- Processes routine tasks 3-5x faster than Opus
- Costs significantly less per token
- Handles structured data extraction well
- Follows detailed instructions reliably

**Main Claude (Opus/Sonnet)** handles:
- Complex historical analysis
- Pattern recognition across events
- Importance scoring validation
- Quality control and synthesis

### 6. Task Delegation Patterns

#### Pattern 1: Simple Research
```
User: "Add event about Cheney energy task force"
Main Claude → timeline-researcher → timeline-entry-creator → Main Claude (validate) → Save
```

#### Pattern 2: Complex Analysis
```
User: "Analyze patterns of regulatory capture 2001-2009"
Main Claude: Analyzes patterns, identifies gaps
Main Claude → timeline-researcher (multiple events) → Main Claude: Synthesizes findings
Main Claude → timeline-entry-creator (batch) → Main Claude: Validates and saves
```

#### Pattern 3: Source Verification
```
User: "Verify and improve sources for 2019 events"
Main Claude: Identifies weak sources
Main Claude → timeline-researcher (find better sources) → Main Claude: Updates entries
```

### 7. Performance Optimization Tips

1. **Batch Similar Tasks**: Group research queries to minimize context switching
2. **Use Specific Prompts**: Provide clear, detailed instructions to subagents
3. **Validate in Batches**: Have main Claude validate multiple entries together
4. **Cache Common Data**: Reuse actor names and tag lists across entries

### 8. Quality Control Checklist

Before saving any entry created by subagents:
- [ ] Verify date accuracy
- [ ] Check for duplicate events
- [ ] Validate importance score (adjust if needed)
- [ ] Ensure sources are credible
- [ ] Confirm actor names are consistent
- [ ] Review summary for neutrality and accuracy

### 9. Monitoring and Debugging

#### Check Agent Performance
```bash
# View agent activity logs (if available in Claude Code)
claude code agents --list
claude code agents --stats timeline-researcher
```

#### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Agent returns incomplete data | Make prompt more specific |
| Sources not credible | Add source requirements to prompt |
| Duplicate events created | Always check existing events first |
| Importance scores inconsistent | Main Claude should validate scores |

### 10. Future Enhancements

Potential improvements to implement:
1. **timeline-validator**: Dedicated validation agent
2. **timeline-pattern-analyzer**: Identifies historical patterns
3. **timeline-source-enhancer**: Improves existing entries
4. **timeline-fact-checker**: Verifies claims across entries

## Testing the Setup

### Test Case 1: Bush Administration Event

```markdown
@timeline-researcher Research the Bush administration's use of signing statements to nullify congressional oversight, particularly:
- Number of signing statements issued
- Comparison to previous presidents
- Constitutional implications
- ABA task force findings
```

### Test Case 2: Create Entry

```markdown
@timeline-entry-creator Create an entry for:
Date: 2006-07-24
Event: ABA condemns Bush signing statements
Research: [paste research results]
Importance: 7
```

## Conclusion

This setup enables efficient timeline development by:
- Delegating routine research to faster models
- Maintaining quality through main model oversight
- Reducing token costs by 60-70%
- Accelerating event creation by 3-5x

The system is designed to scale as the timeline grows, with clear separation of concerns between research, creation, and validation tasks.