# AI Integration Guide - Multiple AI Tools

## 🤖 Overview
This guide helps you use AI assistants (Claude Code, ChatGPT, Cursor, GitHub Copilot, etc.) to work with the Kleptocracy Timeline repository effectively.

## 🎯 Quick Start for Any AI Tool

### Initial Context Setting
Start your session with this prompt:
```
I'm working on the Kleptocracy Timeline project - a critical documentation project tracking democratic capture from 1970-2025. This is Open Source Intelligence for democratic defense.

The repository has:
- 395+ events documenting systematic corruption
- 1,900+ sources that must be verifiable
- 9 capture lanes categorizing democratic erosion
- AGENT.md files in key directories with specific instructions

Please read the AGENT.md files in the relevant directories before making changes.
```

## 📱 Tool-Specific Instructions

### Claude Code (Recommended)
**Strengths**: Deep context understanding, file operations, complex analysis

```
1. Open repository in Claude Code
2. Say: "Read all AGENT.md files to understand the project structure"
3. Use for: Pattern analysis, bulk operations, creating new investigations
```

### ChatGPT (GPT-4 with Code Interpreter)
**Strengths**: Data analysis, visualization, quick scripts

```
1. Upload key files:
   - timeline_complete.json
   - Relevant AGENT.md files
   - Event YAML files you're working on

2. Initial prompt:
   "I've uploaded timeline data from the Kleptocracy Timeline project. 
   Help me [analyze patterns/validate events/create visualizations]."

3. For ongoing work:
   - Use Custom Instructions to maintain context
   - Save analysis notebooks for continuity
```

#### ChatGPT Custom Instructions Template
```
What would you like ChatGPT to know about you?
I'm working on the Kleptocracy Timeline - documenting democratic capture 1970-2025.
Repository: github.com/markramm/KleptocracyTimeline
Focus: Data accuracy, source verification, pattern analysis

How would you like ChatGPT to respond?
- Be rigorous about source verification
- Follow YAML naming: YYYY-MM-DD--event-name-with-hyphens (NO underscores)
- Require 2+ sources for 'confirmed' status
- Focus on patterns, not partisan politics
- Cite specific event IDs when referencing timeline
```

### Cursor AI
**Strengths**: IDE integration, refactoring, code generation

```
1. Open repository in Cursor
2. Index the codebase (@codebase command)
3. Reference AGENT.md files with @file
4. Use for: React component updates, validation scripts, bulk edits
```

### GitHub Copilot
**Strengths**: In-line suggestions, boilerplate code

```
1. Install in VS Code
2. Open relevant AGENT.md alongside work
3. Use comments to guide generation:
   # Following timeline_data/AGENT.md validation rules
   # Create event following YYYY-MM-DD--hyphen-format
```

### Perplexity AI
**Strengths**: Real-time web search, source verification

```
Use for verifying timeline events:
"Verify this event from the Kleptocracy Timeline:
[paste event YAML]
Find additional sources and check facts."
```

## 🔄 Common Workflows Across AI Tools

### 1. Adding New Events
```
PROMPT: I need to add a new event to the timeline about [topic].
Date: [YYYY-MM-DD]
Sources: [URLs]

Please:
1. Check for duplicates in existing events
2. Verify sources match the event
3. Create YAML following timeline_data/AGENT.md standards
4. Generate proper ID: YYYY-MM-DD--event-name-with-hyphens
```

### 2. Pattern Analysis
```
PROMPT: Analyze timeline_complete.json to find:
- Events involving [actor/organization]
- Patterns in [capture lane]
- Acceleration in [time period]
- Network connections between actors

Output as markdown with event ID citations.
```

### 3. Source Verification
```
PROMPT: Verify these sources for timeline event [ID]:
1. Check if URLs are accessible
2. Confirm they discuss this specific event
3. Extract key quotes supporting claims
4. Create archive.org links
5. Note any discrepancies
```

### 4. Validation and QA
```
PROMPT: Run QA checks on this event:
[paste YAML]

Check:
- ID format (hyphens only, no underscores)
- Date format and logic
- Source accessibility
- Summary completeness (who/what/when/where/why)
- Status appropriateness
```

## 🎯 Best Practices for AI Collaboration

### DO:
✅ Always provide AGENT.md context first
✅ Specify which directory you're working in
✅ Request verification of sources
✅ Ask for duplicate checks
✅ Validate YAML before committing
✅ Use specific event IDs in discussions
✅ Request citations for all claims

### DON'T:
❌ Accept AI-generated events without verification
❌ Use underscores in IDs (always hyphens)
❌ Mark future events as 'confirmed'
❌ Skip source verification
❌ Add partisan language
❌ Create events without checking duplicates

## 📊 Optimizing Different AI Tools

### For Analysis Tasks
**Best tools**: Claude Code, ChatGPT with Code Interpreter
```python
# Example prompt for analysis
"Load timeline_complete.json and:
1. Count events by year
2. Find top 10 most connected actors
3. Identify acceleration patterns
4. Create network visualization
5. Export findings as markdown"
```

### For Code Development
**Best tools**: Cursor, Claude Code, GitHub Copilot
```javascript
// Example prompt for React component
"Update EnhancedTimelineView.js to:
1. Add filter for capture lanes
2. Implement date range selector
3. Follow existing component patterns
4. Maintain URL state sync"
```

### For Content Creation
**Best tools**: Claude, ChatGPT
```markdown
# Example prompt for Substack post
"Using events from 2025-01 to 2025-02:
1. Identify key patterns
2. Write analysis in AI Discovery series style
3. Cite specific event IDs
4. Focus on pattern recognition
5. Avoid partisan language"
```

## 🔧 Handling AI Limitations

### Context Window Management
For large operations with limited context:
1. Break into smaller tasks
2. Process in batches
3. Save intermediate results
4. Maintain session notes

### Consistency Across Sessions
Create a session file:
```markdown
# Session: [Date] - [Task]
## Context
Working on: [specific task]
Directory: [path]
Relevant AGENT.md: [list]

## Progress
- [x] Task 1
- [ ] Task 2

## Key Information
- Event ID format: YYYY-MM-DD--hyphenated-name
- Status rules: [pending/confirmed/disputed]
- Source requirements: 2+ for confirmed
```

### Verification Protocol
Always verify AI output:
```bash
# After AI generates events
python timeline_data/validate_yaml.py

# Check for duplicates
grep -r "similar-title" timeline_data/events/

# Verify sources
python tools/validation/check_all_links.py
```

## 🚀 Advanced Integration

### Chaining AI Tools
1. **Perplexity**: Find and verify sources
2. **ChatGPT**: Analyze and create event YAML
3. **Claude Code**: Validate and integrate into timeline
4. **Cursor**: Update React components

### Custom GPTs for Timeline Work
Create a custom GPT with:
- Knowledge: Upload AGENT.md files
- Instructions: Timeline standards and rules
- Actions: GitHub API for direct commits

### API Integration
```python
# Example: Automated validation with AI
import openai

def validate_event_with_ai(event_yaml):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": open('timeline_data/AGENT.md').read()},
            {"role": "user", "content": f"Validate this event:\n{event_yaml}"}
        ]
    )
    return response.choices[0].message.content
```

## 📋 Prompt Templates

### Event Creation
```
Create a timeline event:
Topic: [describe]
Date: [YYYY-MM-DD]
Sources: [list URLs]
Capture lanes: [select from 9 lanes]
Importance: [1-10]

Follow timeline_data/AGENT.md standards exactly.
```

### Pattern Investigation
```
Investigate pattern in timeline:
Pattern: [describe]
Time range: [start] to [end]
Output:
1. Supporting events (with IDs)
2. Key actors involved
3. Financial flows if any
4. Acceleration metrics
5. Visualization suggestions
```

### Quality Assurance
```
QA check for timeline_data/events/:
1. Find events with single sources
2. Identify missing archive links
3. Check for duplicate events
4. Validate date consistency
5. Ensure summary completeness
```

## 🔗 Resources

### Documentation
- Main README: `/README.md`
- Timeline Data: `/timeline_data/AGENT.md`
- Viewer App: `/viewer/AGENT.md`
- Analysis: `/analysis/AGENT.md`
- Tools: `/tools/AGENT.md`

### Key Files
- Complete timeline: `timeline_complete.json`
- Validation: `timeline_data/validate_yaml.py`
- Static API: `timeline_data/generate_static_api.py`

### GitHub Integration
- Repository: https://github.com/markramm/KleptocracyTimeline
- Issues: Report problems or submit events
- Wiki: Extended documentation

## 🚨 Critical Reminders

1. **NEVER use underscores in IDs** - Always use hyphens
2. **ALWAYS verify sources** - Don't trust URLs alone
3. **REQUIRE 2+ sources** for confirmed status
4. **CHECK for duplicates** before adding events
5. **FOLLOW AGENT.md** instructions in each directory
6. **VALIDATE YAML** before committing
7. **ARCHIVE sources** immediately

---

*"AI amplifies human capability. Use it wisely, verify everything, and maintain rigorous standards. The timeline's integrity depends on it."*