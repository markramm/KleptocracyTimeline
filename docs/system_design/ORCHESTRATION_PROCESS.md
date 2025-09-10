# Kleptocracy Timeline Orchestration Process

## Overview

The Kleptocracy Timeline project uses Claude Code as the primary orchestrator for research, validation, and timeline event creation. This document describes the actual working process.

## Core Architecture

### 1. Claude Code as Orchestrator
- **Primary Role**: Claude Code (the AI assistant) acts as the orchestrator
- **Key Capability**: Uses the Task tool with subagent types to perform research
- **Direct Control**: Claude directly manages the research → save → validate workflow

### 2. Working Components

#### Active Services
- **Timeline Search API** (`api/unified_research_server.py`)
  - Provides search functionality for timeline events
  - Runs on port 5174
  - Combines timeline events and research priorities

- **Timeline Validator** (`api/timeline_validator.py`)
  - Validates timeline events for required fields
  - Checks source credibility
  - Runs periodic spot checks

- **Event Save Scripts** (`api/save_researched_events.py`)
  - Utility for saving researched events
  - Used when batch saving is needed

#### Data Structure
- **Timeline Events**: JSON files in `timeline_data/events/`
- **Research Priorities**: JSON files in `research_priorities/`
- **PDFs**: Source documents in `ai_notes/ai-analysis/Sources/`

## Research Workflow

### 1. PDF Ingestion
```
1. Read PDF using Read tool
2. Extract key information
3. Create research priority file
4. Identify timeline events to create
```

### 2. Research Priority Creation
```json
{
  "id": "RT-XXX-descriptive-name",
  "title": "Brief title",
  "description": "Detailed description",
  "priority": 1-10,
  "status": "pending|in-progress|completed",
  "estimated_events": 5,
  "actual_events": 0
}
```

### 3. Event Research & Creation

#### Using Claude's Task Tool (Preferred Method)
```
1. Call Task tool with subagent_type="timeline-researcher"
2. Provide detailed research parameters
3. Extract JSON events from response
4. Immediately save using Write tool
```

#### Direct Creation
```
1. Research topic using WebSearch/WebFetch
2. Create event JSON with required fields
3. Save to timeline_data/events/
```

### 4. Event Validation
Events must include:
- `id`: Unique identifier
- `date`: YYYY-MM-DD format
- `title`: Clear, descriptive title
- `summary`: Detailed summary with context
- `actors`: List of key people/organizations
- `tags`: Relevant categorization tags
- `sources`: Array of credible sources with URLs
- `importance`: 1-10 scale
- `status`: "confirmed" or "alleged"

## Quality Standards

### Source Requirements
- Minimum 2 credible sources per event
- Sources must include:
  - `title`: Article/document title
  - `url`: Direct link to source
  - `outlet`: Publication name
  - `date`: Publication date

### Validation Process
1. Automated validation runs every 5 minutes
2. Checks 15 random events
3. Validates:
   - Required fields present
   - Date format correct
   - Sources have URLs
   - Summary length appropriate

## What Was Removed

The following non-functional "orchestrator" scripts were removed as they don't actually work with Claude's Task tool:
- `claude_subagent_orchestrator.py` - Simulated orchestration
- `database_integrated_orchestrator.py` - Mock database integration
- `improved_research_orchestrator.py` - Placeholder script
- `queue_based_orchestrator.py` - Non-functional queue system
- `real_claude_subagent_orchestrator.py` - Misleading name, doesn't work
- `subagent_orchestrator_with_save.py` - Simulated save functionality
- Various other mock orchestrators

**Important**: These scripts created the illusion of automated orchestration but didn't actually integrate with Claude's capabilities. The real orchestration happens through Claude Code directly using the Task tool.

## Best Practices

1. **Immediate Saving**: Save events immediately after research
2. **Batch Validation**: Run validator periodically
3. **Source Verification**: Always verify sources are accessible
4. **Clear Documentation**: Document research decisions in commit messages
5. **Priority Tracking**: Update research priorities after completing events

## Current Status

- **Timeline Events**: 1099+ events documenting institutional capture
- **Research Priorities**: 100+ tracked priorities
- **Validation**: Continuous quality checks running
- **APIs**: Timeline search available on port 5174

## Future Improvements

1. Enhanced source verification
2. Automated duplicate detection  
3. Cross-reference validation
4. Citation strength scoring
5. Research priority auto-generation from news feeds