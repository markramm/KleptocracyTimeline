# Kleptocracy Timeline System Design

## Updated Architecture (2025-09-09)

### Core Philosophy
**Claude Code orchestrates everything** - The AI assistant (Claude) running in Claude Code is the brain that makes all decisions and drives the workflow. All other components are passive services that Claude calls via tools.

### System Components

```
┌──────────────────────────────────────────────────────────┐
│                     USER INTERFACE                        │
│                                                           │
│  Human ←→ Claude Code (Orchestrator)                     │
│           • Makes all decisions                          │
│           • Drives workflow via tools                    │
│           • Launches subagents                           │
└───────────────────┬──────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┬────────────────┐
    ▼               ▼               ▼                ▼
┌────────┐    ┌──────────┐    ┌────────┐    ┌─────────────┐
│  Bash  │    │   Task   │    │  Read  │    │Write/Edit   │
│ (curl) │    │(subagent)│    │ (PDFs) │    │(JSON files) │
└────┬───┘    └──────────┘    └────────┘    └──────┬──────┘
     │                                              │
     │         HTTP/JSON API                       │
     ▼                                              ▼
┌──────────────────────────────────────────────────────────┐
│              Research Monitor Service                     │
│                   (Port 5555)                            │
│                                                          │
│  • Persistence layer (SQLite)                           │
│  • Priority queue management                            │
│  • Event validation & deduplication                     │
│  • Progress tracking & metrics                          │
│  • File ↔ Database synchronization                      │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                    Data Storage                          │
│                                                          │
│  • timeline_data/events/*.json  (1,065+ events)         │
│  • research_priorities/*.json   (100+ priorities)       │
│  • unified_research.db         (SQLite database)        │
└──────────────────────────────────────────────────────────┘
```

### Workflow Patterns

#### 1. PDF Document Research
```
Human: "Research this PDF document"
  ↓
Claude: 
  1. Read PDF with Read tool
  2. Extract key events and actors
  3. Check for duplicates: curl /api/events/search
  4. Create research priority: curl POST /api/priorities
  5. Launch researcher: Task(subagent="general-purpose")
  6. Validate results: curl POST /api/events/validate
  7. Save events: Write tool → JSON files
  8. Update status: curl PUT /api/priorities/{id}/status
```

#### 2. Priority-Driven Research
```
Claude (periodic check):
  1. Get next: curl /api/priorities/next
  2. Launch researcher: Task(subagent="general-purpose")
  3. Process research results
  4. Create timeline events
  5. Mark complete: curl PUT /api/priorities/{id}/status
```

#### 3. Reprioritization
```
Claude (weekly):
  1. Launch planner: Task(subagent="general-purpose", 
                         prompt="Review and reprioritize research queue")
  2. Update priorities based on recommendations
  3. Log activity: curl POST /api/activity
```

### Key Design Decisions

1. **No Background Orchestration**
   - Claude Code IS the orchestrator
   - No separate Python orchestration scripts
   - All decisions made in Claude session

2. **Simple Tool-Based Integration**
   - Bash/curl for API calls
   - Task tool for subagents
   - Read/Write for file operations
   - No complex protocols or libraries

3. **Research Monitor as Service**
   - Passive persistence layer
   - Does NOT make decisions
   - Only responds to API calls
   - Maintains data consistency

4. **File-First Data Model**
   - JSON files are source of truth
   - Database mirrors files for querying
   - Git tracks all changes
   - Simple backup (copy files)

### API Design Principles

- **RESTful** - Standard HTTP verbs (GET, POST, PUT, DELETE)
- **JSON** - Simple request/response format
- **Stateless** - Each request independent
- **Tool-Friendly** - Designed for curl/Bash
- **Minimal Auth** - Single API key for local use

### Scalability Considerations

**Current Scale (Single Researcher)**
- 2-24 writes per minute
- 100+ reads per minute
- SQLite perfectly adequate
- No concurrency issues

**Future Scale Options**
- PostgreSQL for multi-user
- Redis for queue management
- Celery for background tasks
- BUT: Not needed for current use case

### Removed Components

The following components were removed as they created false complexity:
- Mock orchestrator scripts that didn't integrate with Claude
- Complex queue systems that weren't actually used
- Database corruption from unsafe threading
- File watchers that caused segfaults

### Success Metrics

1. **Efficiency**
   - Events created per day
   - Priorities completed per week
   - Research velocity trending up

2. **Quality**
   - All events have 2+ sources
   - No duplicate events
   - Validation pass rate >95%

3. **Usability**
   - Simple Claude commands
   - Clear priority queue
   - Real-time progress visibility

### Implementation Status

- ✅ Thread-safe database layer
- ✅ Basic Research Monitor exists
- ✅ Architecture documented
- 🚧 CRUD endpoints being added
- ⏳ Validation endpoints needed
- ⏳ Progress tracking needed
- ⏳ Integration testing needed

### Next Steps

1. Complete CRUD endpoints in Research Monitor
2. Add validation and search APIs
3. Implement progress tracking
4. Test end-to-end workflow
5. Create Claude Code command shortcuts
6. Document common workflows

### Conclusion

This design prioritizes **simplicity and reliability** over complex automation. Claude Code provides the intelligence and orchestration, while the Research Monitor provides reliable persistence and validation. The system is designed to be transparent, debuggable, and maintainable by a single researcher.