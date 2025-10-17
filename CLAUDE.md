# Kleptocracy Timeline - Claude Code Instructions

## System Architecture

### Research Monitor v2
The Research Monitor v2 (`research_monitor/app_v2.py`) is a Flask server that provides:
- **Filesystem-authoritative events**: Timeline events are read-only synced from JSON files
- **Database-authoritative research priorities**: Full CRUD operations on research tasks
- **Search capabilities**: Full-text search across 1,000+ timeline events
- **Commit orchestration**: Tracks when commits are needed but doesn't perform them

## Research Client (CLI Tool)

⚠️ **IMPORTANT**: Agents should use CLI commands, NOT direct API calls or Python imports.

The `research_cli.py` provides a comprehensive command-line interface powered by the unified TimelineResearchClient architecture:

### Getting Help
```bash
# Comprehensive help documentation
python3 research_cli.py help

# Topic-specific help
python3 research_cli.py help --topic validation
python3 research_cli.py help --topic search
python3 research_cli.py help --topic examples
```

### Basic Commands
```bash
# Search events
python3 research_cli.py search-events --query "Trump crypto"

# Get system statistics
python3 research_cli.py get-stats

# Get next research priority
python3 research_cli.py get-next-priority

# Update priority status
python3 research_cli.py update-priority --id "RP-123" --status "completed" --actual-events 3
```

### Research Enhancement Commands
Powered by the enhanced TimelineResearchClient with comprehensive validation and quality assurance:

```bash
# Find high-importance events needing more sources
python3 research_cli.py research-candidates --min-importance 8 --limit 10

# Get events with insufficient sources
python3 research_cli.py missing-sources --min-sources 2 --limit 20

# Get validation queue (events prioritized for review)
python3 research_cli.py validation-queue --limit 15

# Check for broken source links
python3 research_cli.py broken-links --limit 25

# Analyze actor timeline comprehensively
python3 research_cli.py actor-timeline --actor "Peter Thiel" --start-year 2000
```

### Event Management
```bash
# Create event from JSON file
python3 research_cli.py create-event --file event.json

# Validate event before creating
python3 research_cli.py validate-event --file event.json

# List available tags and actors
python3 research_cli.py list-tags
python3 research_cli.py list-actors
```

### Quality Assurance Workflow
```bash
# 1. Check system health and QA statistics
python3 research_cli.py get-stats
python3 research_cli.py qa-stats

# 2. Get validation candidates
python3 research_cli.py validation-queue --limit 10
python3 research_cli.py qa-queue --limit 10

# 3. Get next highest priority event for QA
python3 research_cli.py qa-next

# 4. Find research gaps
python3 research_cli.py missing-sources --min-sources 3

# 5. Check source quality and QA issues
python3 research_cli.py broken-links --limit 20
python3 research_cli.py qa-issues --limit 15

# 6. Validate or reject events in QA workflow
python3 research_cli.py qa-validate --event-id "2025-01-15--event-slug" --score 8.5 --notes "High quality sources verified"
python3 research_cli.py qa-reject --event-id "2025-01-15--event-slug" --reason "insufficient_sources" --notes "Needs credible sources"

# 7. Reset validation status if needed
python3 research_cli.py validation-reset
python3 research_cli.py validation-init
```

### Validation Runs System (Recommended for Parallel Processing)

**⚠️ CRITICAL**: For parallel agent processing, use the Validation Runs system to ensure unique event distribution and prevent duplicates.

#### Creating Validation Runs
```bash
# Create a validation run focused on source quality issues
python3 research_cli.py validation-runs-create --run-type source_quality --target-count 30 --focus-unvalidated --exclude-recent-validations --created-by "agent-batch-1"

# Create importance-focused validation run  
python3 research_cli.py validation-runs-create --run-type importance_focused --target-count 20 --min-importance 8 --created-by "high-priority-batch"

# Create date-range validation run
python3 research_cli.py validation-runs-create --run-type date_range --target-count 15 --start-date 2025-01-01 --end-date 2025-12-31 --created-by "2025-events"
```

#### Processing Events from Validation Runs
```bash
# 1. Get next unique event with validator reservation
python3 research_cli.py validation-runs-next --run-id 1 --validator-id "agent-1"

# 2. Enhance event with proper sources and save to filesystem
cp enhanced_event.json "/Users/markr/kleptocracy-timeline/timeline_data/events/[EVENT_ID].json"

# 3. Log validation with quality score
python3 research_cli.py qa-validate --event-id [EVENT_ID] --quality-score 9.0 --validation-notes "Enhanced with authoritative sources"

# 4. Complete validation run event
python3 research_cli.py validation-runs-complete --run-id 1 --run-event-id [RUN_EVENT_ID] --status validated --notes "Successfully enhanced"
```

#### Validation Status Options

The validation system supports multiple completion statuses:

- **`validated`** - Event successfully validated and enhanced (default)
- **`needs_work`** - Event requires additional work or sources (can be requeued)
- **`rejected`** - Event should be removed (automatically archived)
- **`skipped`** - Event skipped for this validation round

**Rejected Event Archive System:**
When an event is marked as `rejected`, it is automatically:
1. Moved from `timeline_data/events/` to `archive/rejected_events/`
2. Logged in `archive/rejected_events/rejection_log.txt` with timestamp and reason
3. Removed from the active timeline (no longer searchable)

**Requeuing Events That Need Work:**
```bash
# Requeue all events marked as 'needs_work' back to pending status
python3 research_cli.py validation-runs-requeue --run-id 1
```

**Examples of Different Status Completions:**
```bash
# Event successfully validated and enhanced
python3 research_cli.py validation-runs-complete --run-id 1 --run-event-id 15 --status validated --notes "Enhanced with credible sources and improved accuracy"

# Event needs more work (can be requeued later)
python3 research_cli.py validation-runs-complete --run-id 1 --run-event-id 16 --status needs_work --notes "Sources need verification, importance score questionable"

# Event should be rejected and archived
python3 research_cli.py validation-runs-complete --run-id 1 --run-event-id 17 --status rejected --notes "Duplicate of existing event 2023-01-15--similar-event"

# Event skipped for this validation round
python3 research_cli.py validation-runs-complete --run-id 1 --run-event-id 18 --status skipped --notes "Requires specialized domain expertise"
```

#### Key Requirements for Parallel Processing

**🔴 CRITICAL**: Each agent MUST use a unique `--validator-id` parameter:
- ✅ **Correct**: `--validator-id "agent-1"`, `--validator-id "agent-2"`, etc.
- ❌ **Wrong**: No validator-id (causes duplicate event assignment)

**Example for 5 parallel agents:**
```bash
# Agent 1
python3 research_cli.py validation-runs-next --run-id 1 --validator-id "qa-agent-1"

# Agent 2  
python3 research_cli.py validation-runs-next --run-id 1 --validator-id "qa-agent-2"

# Agent 3
python3 research_cli.py validation-runs-next --run-id 1 --validator-id "qa-agent-3"

# Agent 4
python3 research_cli.py validation-runs-next --run-id 1 --validator-id "qa-agent-4"

# Agent 5
python3 research_cli.py validation-runs-next --run-id 1 --validator-id "qa-agent-5"
```

#### Monitoring Validation Runs

**Automated Monitoring Script (Recommended for Parallel Batches):**

The `monitor_validation_progress.sh` script provides real-time monitoring of validation runs with automatic stuck agent detection:

```bash
# Start monitoring (checks every 30s, stuck threshold 3 minutes)
./scripts/monitor_validation_progress.sh <run_id> [expected_agents] [check_interval] [stuck_threshold]

# Example: Monitor run 1 with 5 agents
./scripts/monitor_validation_progress.sh 1 5 30 180

# Example: Monitor run 2 with 10 agents, checking every 20s
./scripts/monitor_validation_progress.sh 2 10 20 180
```

**Features:**
- ⚡ Real-time progress tracking with completion estimates
- 🚨 Automatic detection of stuck agents (>3 min by default)
- 📊 Active agent status and working time monitoring
- 🔧 SQL commands provided for quick stuck agent reset
- ⏹️ Auto-stops when validation run completes
- 🎯 Warns when approaching stuck threshold (70% of limit)

**Example Output:**
```
╔════════════════════════════════════════════════════════════╗
║     Validation Run Monitor - Stuck Agent Detection        ║
╚════════════════════════════════════════════════════════════╝

Run Status: active
Progress: 8 / 20 events (40%)
  ✅ Validated: 7
  ❌ Rejected: 0
  ⚠️  Needs Work: 1

Active Agents: 5 / 5
  qa-agent-1: 1 event assigned (working 2 min)
  qa-agent-2: 1 event assigned (working 3 min)
  ...

⚠️  STUCK AGENTS DETECTED: 1
  Validator: qa-agent-3
  Event: 2025-01-15--event-slug
  Stuck for: 5 minutes

Recovery Option: [SQL command provided]
```

**Manual Monitoring Commands:**

```bash
# Check validation run progress
python3 research_cli.py validation-runs-get --run-id 1

# List all validation runs
python3 research_cli.py validation-runs-list

# View validation logs
python3 research_cli.py validation-logs-list --limit 20
```

#### Validation Runs vs. Traditional QA Queue

**Use Validation Runs when:**
- Processing events with multiple parallel agents
- Need guaranteed unique event distribution  
- Want systematic progress tracking
- Processing large batches (10+ events)

**Use Traditional QA Queue when:**
- Single agent processing
- Ad-hoc validation tasks
- Quick individual event checks

### Architecture Notes
- **Unified Implementation**: CLI now uses TimelineResearchClient for all operations
- **Enhanced Error Handling**: Superior error detection and structured JSON responses
- **Comprehensive Help**: Built-in documentation system accessible via `help` command
- **Better Validation**: Improved event validation and quality assurance tools

⚠️ **For Agents**: Use only these CLI commands for all research operations. The CLI returns structured JSON for easy parsing and includes comprehensive help for troubleshooting failures.

### Starting the Server
⚠️ **IMPORTANT**: Use the CLI server management commands instead of manual server operations:

```bash
# Start server (preferred method)
python3 research_cli.py server-start

# Alternative manual start (if needed)
cd research_monitor
RESEARCH_MONITOR_PORT=5558 python3 app_v2.py &
```

To verify the server is running:
```bash
python3 research_cli.py server-status
```

### Server Management

The CLI provides comprehensive server management commands:

#### Server Status and Control
```bash
# Check server status with detailed process information
python3 research_cli.py server-status

# Start the server (if not running)
python3 research_cli.py server-start

# Stop the server gracefully
python3 research_cli.py server-stop

# Restart the server (stop + start)
python3 research_cli.py server-restart

# View server logs
python3 research_cli.py server-logs
```

#### Legacy Server Commands (if CLI commands fail)

**Graceful Shutdown:**
```bash
curl -X POST "http://localhost:5558/api/server/shutdown" \
  -H "X-API-Key: test-key"
```

**Health Check:**
```bash
curl "http://localhost:5558/api/server/health"
```

**Emergency Shutdown (last resort):**
```bash
# Use SIGTERM first (allows cleanup)
kill -TERM $(lsof -t -i:5558)

# Last resort only (can corrupt database)
kill -9 $(lsof -t -i:5558)
```

## Research CLI Tool - RECOMMENDED FOR AGENTS

**⚠️ IMPORTANT: Agents should use CLI commands, NOT direct API calls or Python imports.**

### Agentic Research API CLI
The `research_cli.py` tool is the **primary interface for AI agents**. It provides JSON output and is completely self-contained:

```bash
# All commands return structured JSON for easy parsing
python3 research_cli.py <command> [options]
```

### Search Events
```bash
# Search for events by keyword
python3 research_cli.py search-events --query "Trump"
python3 research_cli.py search-events --query "surveillance FISA" --limit 20
```

### Research Priorities
```bash
# Get next priority to research
python3 research_cli.py get-next-priority

# Update priority status
python3 research_cli.py update-priority --id "RP-123" --status "in_progress" --notes "Research notes here"
python3 research_cli.py update-priority --id "RP-123" --status "completed" --actual-events 3
```

### Event Creation
```bash
# Create event from JSON string
python3 research_cli.py create-event --json '{
  "id": "YYYY-MM-DD--event-slug",
  "date": "YYYY-MM-DD", 
  "title": "Event Title",
  "summary": "Detailed summary",
  "importance": 8,
  "tags": ["tag1", "tag2"]
}'

# Create event from JSON file
python3 research_cli.py create-event --file event.json

# Validate event without creating
python3 research_cli.py validate-event --json '{"date": "2025-01-15", ...}'
```

### System Information
```bash
# Get system statistics
python3 research_cli.py get-stats

# List available tags and actors
python3 research_cli.py list-tags
python3 research_cli.py list-actors

# Check commit status
python3 research_cli.py commit-status
python3 research_cli.py reset-commit
```

### Research Enhancement Commands
The CLI provides specialized research workflow commands for quality assurance and research prioritization:

```bash
# Find events with insufficient sources for research
python3 research_cli.py missing-sources --min-sources 3 --limit 10

# Get high-importance events needing more sources
python3 research_cli.py research-candidates --min-importance 8 --limit 5

# Find events prioritized for fact-checking and validation
python3 research_cli.py validation-queue --limit 15

# Check for events with potentially broken source links
python3 research_cli.py broken-links --limit 10

# Get comprehensive timeline analysis for specific actors
python3 research_cli.py actor-timeline --actor "Peter Thiel" --start-year 2000 --end-year 2025
python3 research_cli.py actor-timeline --actor "Trump"
```

### Advanced QA System Commands
The CLI includes a comprehensive quality assurance system for systematic event validation:

```bash
# QA System Statistics and Overview
python3 research_cli.py qa-stats                    # Get comprehensive QA statistics
python3 research_cli.py qa-queue --limit 20         # Get prioritized queue of events needing QA
python3 research_cli.py qa-next                     # Get next highest priority event for QA

# QA Issue Analysis
python3 research_cli.py qa-issues --limit 15        # Get events with specific QA issues
python3 research_cli.py qa-score --json '{"date": "2025-01-15", "importance": 8}'  # Calculate QA priority score

# QA Validation Actions
python3 research_cli.py qa-validate --event-id "2025-01-15--event-slug" --score 8.5 --notes "Sources verified"
python3 research_cli.py qa-reject --event-id "2025-01-15--event-slug" --reason "insufficient_sources" --notes "Needs more credible sources"

# QA System Management
python3 research_cli.py validation-init             # Initialize validation audit trail for all events
python3 research_cli.py validation-reset            # Reset all validation records to pending status

# Event Update Failure Monitoring
python3 research_cli.py update-failures-stats       # Get statistics on event save failures
python3 research_cli.py update-failures-list --limit 20  # List recent event update failures
```

#### QA Agent Requirements

**🔴 CRITICAL: Web Fetch Timeout Handling**

The WebFetch tool does not have built-in timeout limits. Agents MUST implement defensive strategies:

**🚫 BLACKLISTED SOURCES (NEVER FETCH - Will Cause Timeout):**

The following sources have confirmed timeout issues and MUST be avoided:

**Confirmed Timeouts (Production Testing):**
- ❌ **washingtonpost.com** - Confirmed timeout 2025-10-17 (agent hung for minutes)
- ❌ **nytimes.com** - Paywall + slow response
- ❌ **wsj.com** - Strict paywall

**Likely Timeouts (Use with Caution):**
- ⚠️ **ft.com** (Financial Times) - Paywall
- ⚠️ **economist.com** - Paywall
- ⚠️ Any site requiring login/authentication

**Alternative Sources to Use Instead:**

When you encounter a blacklisted source, use these alternatives:

**For Political/Government News (WaPo/NYT replacement):**
- ✅ **Associated Press** (ap.org) - Fast, tier-1, no paywall
- ✅ **Reuters** (reuters.com) - Fast, tier-1, no paywall
- ✅ **NPR** (npr.org) - Fast, tier-1, public media
- ✅ **PBS** (pbs.org) - Fast, tier-1, public media
- ✅ **C-SPAN** (c-span.org) - Fast, tier-1, government coverage

**For Financial News (WSJ replacement):**
- ✅ **Bloomberg** (bloomberg.com) - Tier-1, usually accessible
- ✅ **Reuters** (reuters.com) - Excellent financial coverage
- ✅ **CNBC** (cnbc.com) - Tier-2, fast access

**For Investigative Journalism:**
- ✅ **ProPublica** (propublica.org) - Tier-1, open access
- ✅ **The Intercept** (theintercept.com) - Tier-1, open access
- ✅ **ICIJ** (icij.org) - Tier-1, investigative

**For Government/Official Sources:**
- ✅ **.gov domains** - Always tier-1, fast, authoritative
- ✅ **Congressional records** (congress.gov) - Official documents
- ✅ **Agency press releases** - Direct from source

**Timeout Recovery Protocol:**

1. **If you encounter a blacklisted URL:**
   - ❌ DO NOT attempt to fetch it
   - ✅ Search for alternative coverage using the sources above
   - ✅ Document in validation_notes: "Used [alternative source] instead of [blacklisted source] due to known timeout"

2. **If an unknown URL appears slow (>30 seconds):**
   - ❌ DO NOT wait indefinitely
   - ✅ Move to next source immediately
   - ✅ Document in validation_notes: "URL [url] appeared slow, used alternative source"
   - ✅ Report the slow URL for blacklist consideration

3. **If agent appears completely stuck:**
   - Agent has likely hung on a WebFetch call
   - This is a known limitation - agents cannot self-recover
   - User must interrupt and restart with different validator-id
   - Document problematic URLs in validation notes for future avoidance

**Quality Standards:**
- **Minimum**: 2 credible sources (tier-1 or tier-2)
- **Target**: 3 sources from different outlets
- **Never sacrifice progress** for a single slow source
- **Document all timeout issues** in validation notes for pattern tracking

#### QA Workflow Integration
The QA system provides structured event validation with:
- **Priority scoring**: Events ranked by importance and source quality
- **Issue tracking**: Specific validation problems identified
- **Audit trail**: Complete validation history for each event
- **Quality metrics**: Comprehensive statistics on validation status
- **Failure monitoring**: Automatic detection and logging of event update failures
- **Concurrent processing**: Support for 10+ concurrent QA agents with proper queue management

## Client Architecture

**FOR AGENTS: Use `python3 research_cli.py` commands only. DO NOT import Python modules.**

### Two Interface Options

1. **research_cli.py** - **RECOMMENDED FOR AGENTS** 
   - Self-contained CLI tool with JSON output
   - Usage: `python3 research_cli.py <command> <options>`
   - No Python imports needed - just run commands
   - Perfect for AI agents and automation

2. **research_client.py** - For Python Scripts Only
   - Python library: `from research_client import TimelineResearchClient`
   - 40+ methods with built-in help system
   - Use only when building Python applications

**Agents should use the CLI commands, not Python imports.** The CLI provides the same functionality with structured JSON responses.

## CRITICAL: Duplicate Detection Workflow

### Before Creating Any Event

1. **Search for exact duplicates by date and key terms**:
```bash
# Search by main actor/entity
python3 research_cli.py search-events --query "Trump crypto"
python3 research_cli.py search-events --query "Musk Starlink"

# Search by specific terms from the event
python3 research_cli.py search-events --query "specific company name"
```

2. **Check events around the same date**:
```bash
# List events by browsing the filesystem
ls -la timeline_data/events/YYYY-MM-*.json

# Check specific date range
ls -la timeline_data/events/2025-01-*.json | grep -i keyword
```

3. **Search for related events**:
```bash
# Search for broader patterns
python3 research_cli.py search-events --query "FISA court"
python3 research_cli.py search-events --query "no-bid contract"
```

### Duplicate Detection Rules

**DO NOT CREATE** if:
- An event with the same date and similar title exists
- The core facts are already covered in an existing event
- It's a minor update to an existing story (add to the existing event instead)

**DO CREATE** if:
- It's a genuinely new development
- It reveals new information not in existing events
- It represents a significant escalation or change

### Event ID Format
Always use: `YYYY-MM-DD--descriptive-slug-here`
- Use the actual event date, not today's date
- Make slugs descriptive and searchable
- Keep slugs concise but meaningful

## Research Workflow

**⚠️ For Parallel Agent Processing**: Use the [Validation Runs System](#validation-runs-system-recommended-for-parallel-processing) instead of this sequential workflow to ensure unique event distribution.

### 1. Get Next Priority
```bash
python3 research_cli.py get-next-priority
```

### 2. Search for Existing Related Events
**ALWAYS DO THIS FIRST**
```bash
# Search broadly for the topic
python3 research_cli.py search-events --query "topic keywords"

# Search for specific actors
python3 research_cli.py search-events --query "actor name"

# Check the time period
ls -la timeline_data/events/YYYY-*.json
```

### 3. Research the Topic
- Use web search for current information
- Focus on credible sources
- Look for specific dates and verifiable facts

### 4. Create New Events (If Not Duplicates)
For each potential event:
1. Search for duplicates (see above)
2. If unique, validate and create with proper format
3. Include importance score (1-10)
4. Add relevant tags

```bash
# Validate before creating
python3 research_cli.py validate-event --json '{"date": "2025-01-15", "title": "Event Title", "summary": "Summary...", "importance": 8, "tags": ["tag1"]}'

# Create the event
python3 research_cli.py create-event --json '{"id": "2025-01-15--event-slug", "date": "2025-01-15", "title": "Event Title", "summary": "Summary...", "importance": 8, "tags": ["tag1"]}'
```

### 5. Update Priority Status
```bash
python3 research_cli.py update-priority --id "RP-123" --status "completed" --actual-events 3 --notes "Research completed successfully"
```

### 6. Commit When Threshold Reached
The server tracks events and will signal when 10 events are staged:
```bash
# Check status
python3 research_cli.py commit-status

# If commit_needed is true, perform git operations:
cd /Users/markr/kleptocracy-timeline
git add timeline_data/events research_priorities
git commit -m "Add X researched events and update priorities"

# Reset the counter
python3 research_cli.py reset-commit
```

## Best Practices

### Event Quality
- **Importance scores**: 1-3 minor, 4-6 significant, 7-9 major, 10 critical
- **Summaries**: Provide context and explain significance
- **Sources**: Mention credible sources in summary when possible
- **Tags**: Use consistent tagging for better searchability

### Avoiding Duplicates
1. **Always search first** - Multiple searches are better than creating duplicates
2. **Check date ranges** - Events might be off by a day or two
3. **Search key actors** - "Trump", "Musk", "Thiel", etc.
4. **Search key terms** - Company names, program names, specific amounts

### Performance
- The database indexes over 1,500 events efficiently after duplicate cleanup
- Full-text search is available via SQLite FTS5 with fallback LIKE search for special characters
- The server handles 10+ concurrent QA agents simultaneously
- Filesystem sync runs every 30 seconds
- Comprehensive event update failure monitoring and logging
- Auto-correction system applies validated improvements directly to event files

## Common Tasks

### Find Events by Actor
```bash
# Search returns structured JSON with events array
python3 research_cli.py search-events --query "Cheney" | jq '.data.events[] | {date, title}'
```

### Find Events by Pattern
```bash
# Get count of matching events
python3 research_cli.py search-events --query "no-bid contract" | jq '.data.count'
```

### Check System Stats
```bash
# Get comprehensive system statistics
python3 research_cli.py get-stats | jq '.data'
```

### List Metadata
```bash
# Get all available tags and actors
python3 research_cli.py list-tags | jq '.data.tags[]'
python3 research_cli.py list-actors | jq '.data.actors[]'
```

### Get Specific Event
```bash
# Get event by ID
python3 research_cli.py get-event --id "2025-01-15--event-slug"
```

## Troubleshooting

### Server Management Issues
```bash
# Check current server status
python3 research_cli.py server-status

# View server logs for errors
python3 research_cli.py server-logs

# Restart server if having issues
python3 research_cli.py server-restart

# Stop problematic server
python3 research_cli.py server-stop
```

### Server Won't Start
```bash
# Check if port is in use
lsof -i :5558

# Use CLI to start server
python3 research_cli.py server-start

# If CLI fails, manual start with different port
RESEARCH_MONITOR_PORT=5559 python3 research_monitor/app_v2.py &
```

### Database Corruption
```bash
# Stop server gracefully first
python3 research_cli.py server-stop

# Remove corrupted database files
cd /Users/markr/kleptocracy-timeline
rm -f unified_research.db unified_research.db-wal unified_research.db-shm

# Restart server - it will rebuild from filesystem
python3 research_cli.py server-start
```

### QA System Issues
```bash
# Check QA system status
python3 research_cli.py qa-stats

# Reset validation if needed
python3 research_cli.py validation-reset
python3 research_cli.py validation-init

# Check for QA issues
python3 research_cli.py qa-issues --limit 20
```

### Stuck QA Agents (WebFetch Timeout)

**Symptoms:**
- Agent stops responding mid-processing
- No output after "researching event" or "fetching source"
- Task appears to run indefinitely

**Root Cause:**
- WebFetch tool has no built-in timeout
- Agent hung trying to fetch from slow/paywalled site
- Cannot self-recover once stuck

**Recovery Steps:**

1. **Identify stuck agents:**
   ```bash
   # Check validation run for "assigned" events that never complete
   python3 research_cli.py validation-runs-get --run-id 11
   # Look for: "assigned": N where N > 0 for extended time
   ```

2. **Reset stuck events back to pending:**
   ```bash
   # Direct database fix
   sqlite3 unified_research.db "UPDATE validation_run_events SET validation_status = 'pending', assigned_validator = NULL, assigned_date = NULL WHERE validation_status = 'assigned' AND validation_run_id = 11;"
   ```

3. **Prevention for future batches:**
   - Launch agents with explicit instructions to avoid slow sites
   - Use unique validator IDs for each agent
   - Monitor progress - if agents don't complete within 3-5 minutes, likely stuck
   - Document problematic URLs when restarting

4. **Best practices:**
   - Process in batches of 10 agents
   - Check progress every 2-3 minutes
   - Reset and restart stuck agents promptly
   - Build list of problematic URLs to avoid

### Search Not Working
- Wait 30 seconds for filesystem sync
- Check server status: `python3 research_cli.py server-status`
- Check server logs: `python3 research_cli.py server-logs`
- Verify events are valid JSON

## Architecture Notes

The system uses a **hybrid architecture**:
- **Events**: Filesystem is authoritative (one-way sync to database)
- **Priorities**: Database is authoritative (can export to filesystem)
- **Search**: SQLite FTS5 for full-text search
- **Commits**: Server signals, orchestrator (you) performs

This design ensures:
- No data loss (filesystem is source of truth for events)
- Fast searching (database indexes)
- Clean separation of concerns (server manages data, orchestrator manages git)