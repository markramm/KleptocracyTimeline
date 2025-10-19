#!/bin/bash
# monitor_validation_progress.sh - Monitor QA validation run progress and detect stuck agents
#
# Usage:
#   ./monitor_validation_progress.sh <run_id> [expected_agents] [check_interval] [stuck_threshold]
#
# Arguments:
#   run_id           - Validation run ID to monitor
#   expected_agents  - Expected number of concurrent agents (default: 5)
#   check_interval   - Seconds between checks (default: 30)
#   stuck_threshold  - Seconds before considering agent stuck (default: 180)
#
# Example:
#   ./monitor_validation_progress.sh 1 5 30 180
#
# Features:
#   - Detects agents stuck on same event for >3 minutes (default)
#   - Shows real-time progress statistics
#   - Provides SQL commands to reset stuck agents
#   - Warns about slow completion rates
#   - Auto-stops when validation run completes

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RUN_ID="${1:-}"
EXPECTED_AGENTS="${2:-5}"
CHECK_INTERVAL="${3:-30}"
STUCK_THRESHOLD="${4:-180}"
DB_PATH="unified_research.db"

# Validate arguments
if [ -z "$RUN_ID" ]; then
    echo "Usage: $0 <run_id> [expected_agents] [check_interval] [stuck_threshold]"
    echo ""
    echo "Example: $0 1 5 30 180"
    echo "  Monitors run 1 with 5 agents, checking every 30s, stuck threshold 180s"
    exit 1
fi

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}Error: Database not found at $DB_PATH${NC}"
    echo "Make sure you're running this from the kleptocracy-timeline root directory"
    exit 1
fi

# Check if run exists
RUN_EXISTS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM validation_runs WHERE id = $RUN_ID;")
if [ "$RUN_EXISTS" -eq 0 ]; then
    echo -e "${RED}Error: Validation run $RUN_ID not found${NC}"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Validation Run Monitor - Stuck Agent Detection        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Run ID: $RUN_ID"
echo "Expected Agents: $EXPECTED_AGENTS"
echo "Check Interval: ${CHECK_INTERVAL}s"
echo "Stuck Threshold: ${STUCK_THRESHOLD}s ($(($STUCK_THRESHOLD / 60)) minutes)"
echo "Database: $DB_PATH"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Initialize counters
CHECK_COUNT=0
STUCK_WARNINGS=0

# Monitoring loop
while true; do
    CHECK_COUNT=$((CHECK_COUNT + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Check #$CHECK_COUNT - $TIMESTAMP${NC}"
    echo ""

    # Get validation run overview
    RUN_OVERVIEW=$(sqlite3 "$DB_PATH" "
        SELECT
            status,
            target_count,
            COALESCE(events_validated, 0) as events_validated,
            COALESCE(events_remaining, 0) as events_remaining,
            COALESCE(progress_percentage, 0) as progress_percentage
        FROM validation_runs
        WHERE id = $RUN_ID;
    ")

    if [ -z "$RUN_OVERVIEW" ]; then
        echo -e "${RED}Error: Run $RUN_ID not found${NC}"
        exit 1
    fi

    IFS='|' read -r STATUS TARGET_COUNT EVENTS_VALIDATED EVENTS_REMAINING PROGRESS_PCT <<< "$RUN_OVERVIEW"

    # Calculate completed count from database counters
    COMPLETED_COUNT=$(sqlite3 "$DB_PATH" "
        SELECT COUNT(*)
        FROM validation_run_events
        WHERE validation_run_id = $RUN_ID
        AND validation_status IN ('validated', 'rejected', 'needs_work', 'skipped');
    ")

    # Get breakdown by status
    VALIDATED_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM validation_run_events WHERE validation_run_id = $RUN_ID AND validation_status = 'validated';")
    REJECTED_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM validation_run_events WHERE validation_run_id = $RUN_ID AND validation_status = 'rejected';")
    NEEDS_WORK_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM validation_run_events WHERE validation_run_id = $RUN_ID AND validation_status = 'needs_work';")
    SKIPPED_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM validation_run_events WHERE validation_run_id = $RUN_ID AND validation_status = 'skipped';")

    # Display overview
    echo -e "${GREEN}Run Status: $STATUS${NC}"
    echo "Progress: $COMPLETED_COUNT / $TARGET_COUNT events (${PROGRESS_PCT}%)"
    echo "  ✅ Validated: $VALIDATED_COUNT"
    echo "  ❌ Rejected: $REJECTED_COUNT"
    echo "  ⚠️  Needs Work: $NEEDS_WORK_COUNT"
    if [ "$SKIPPED_COUNT" -gt 0 ]; then
        echo "  ⏭️  Skipped: $SKIPPED_COUNT"
    fi
    echo ""

    # Check if run is completed
    if [ "$STATUS" = "completed" ]; then
        echo -e "${GREEN}✅ Validation run completed!${NC}"
        echo ""
        echo "Final Results:"
        echo "  Total Completed: $COMPLETED_COUNT events"
        echo "  ✅ Validated: $VALIDATED_COUNT"
        echo "  ❌ Rejected: $REJECTED_COUNT"
        echo "  ⚠️  Needs Work: $NEEDS_WORK_COUNT"
        if [ "$SKIPPED_COUNT" -gt 0 ]; then
            echo "  ⏭️  Skipped: $SKIPPED_COUNT"
        fi
        exit 0
    fi

    # Get status breakdown
    STATUS_BREAKDOWN=$(sqlite3 "$DB_PATH" "
        SELECT
            validation_status,
            COUNT(*) as count
        FROM validation_run_events
        WHERE validation_run_id = $RUN_ID
        GROUP BY validation_status;
    ")

    echo "Event Status Breakdown:"
    while IFS='|' read -r STATUS_NAME COUNT; do
        case "$STATUS_NAME" in
            "pending")
                echo "  ⏳ Pending: $COUNT"
                ;;
            "assigned")
                echo "  🔄 Assigned (in progress): $COUNT"
                ;;
            "validated")
                echo "  ✅ Validated: $COUNT"
                ;;
            "rejected")
                echo "  ❌ Rejected: $COUNT"
                ;;
            "needs_work")
                echo "  ⚠️  Needs Work: $COUNT"
                ;;
            "skipped")
                echo "  ⏭️  Skipped: $COUNT"
                ;;
        esac
    done <<< "$STATUS_BREAKDOWN"
    echo ""

    # Check for stuck agents (events assigned for > stuck_threshold)
    STUCK_AGENTS=$(sqlite3 "$DB_PATH" "
        SELECT
            assigned_validator,
            event_id,
            assigned_date,
            CAST((julianday('now') - julianday(assigned_date)) * 86400 AS INTEGER) as seconds_stuck
        FROM validation_run_events
        WHERE validation_run_id = $RUN_ID
        AND validation_status = 'assigned'
        AND (julianday('now') - julianday(assigned_date)) * 86400 > $STUCK_THRESHOLD
        ORDER BY seconds_stuck DESC;
    ")

    if [ -n "$STUCK_AGENTS" ]; then
        STUCK_COUNT=$(echo "$STUCK_AGENTS" | wc -l)
        STUCK_WARNINGS=$((STUCK_WARNINGS + 1))

        echo -e "${RED}⚠️  STUCK AGENTS DETECTED: $STUCK_COUNT${NC}"
        echo ""

        while IFS='|' read -r VALIDATOR EVENT_ID ASSIGNED_DATE SECONDS_STUCK; do
            MINUTES_STUCK=$((SECONDS_STUCK / 60))
            echo -e "${YELLOW}  Validator: $VALIDATOR${NC}"
            echo "    Event: $EVENT_ID"
            echo "    Assigned: $ASSIGNED_DATE"
            echo -e "    ${RED}Stuck for: ${MINUTES_STUCK} minutes ($SECONDS_STUCK seconds)${NC}"
            echo ""
        done <<< "$STUCK_AGENTS"

        echo -e "${YELLOW}Possible Causes:${NC}"
        echo "  1. Agent hung on WebFetch timeout (Washington Post, NYT, WSJ)"
        echo "  2. Agent crashed or disconnected"
        echo "  3. Event requires complex research taking longer than threshold"
        echo ""

        echo -e "${YELLOW}Recovery Options:${NC}"
        echo ""
        echo "Option 1: Reset ALL stuck agents to pending (recommended):"
        echo -e "${GREEN}sqlite3 $DB_PATH \"UPDATE validation_run_events SET validation_status = 'pending', assigned_validator = NULL, assigned_date = NULL WHERE validation_run_id = $RUN_ID AND validation_status = 'assigned' AND (julianday('now') - julianday(assigned_date)) * 86400 > $STUCK_THRESHOLD;\"${NC}"
        echo ""
        echo "Option 2: Reset specific validator (replace VALIDATOR_ID):"
        echo -e "${GREEN}sqlite3 $DB_PATH \"UPDATE validation_run_events SET validation_status = 'pending', assigned_validator = NULL, assigned_date = NULL WHERE validation_run_id = $RUN_ID AND assigned_validator = 'VALIDATOR_ID';\"${NC}"
        echo ""
        echo "Option 3: Skip problematic events (if consistently failing):"
        echo -e "${GREEN}sqlite3 $DB_PATH \"UPDATE validation_run_events SET validation_status = 'skipped', completed_date = datetime('now') WHERE validation_run_id = $RUN_ID AND validation_status = 'assigned' AND (julianday('now') - julianday(assigned_date)) * 86400 > $STUCK_THRESHOLD;\"${NC}"
        echo ""

        # Check if this is a persistent issue
        if [ "$STUCK_WARNINGS" -ge 3 ]; then
            echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${RED}⚠️  PERSISTENT STUCK AGENT ISSUE DETECTED${NC}"
            echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            echo "Stuck agents detected for $STUCK_WARNINGS consecutive checks."
            echo "This suggests a systematic issue (likely WebFetch timeout)."
            echo ""
            echo "Recommended Actions:"
            echo "  1. Reset stuck agents using command above"
            echo "  2. Review CLAUDE.md source blacklist (lines 406-444)"
            echo "  3. Ensure agents have explicit instructions to avoid:"
            echo "     - washingtonpost.com"
            echo "     - nytimes.com"
            echo "     - wsj.com"
            echo "  4. Consider reducing batch size or agent count"
            echo ""
        fi
    else
        echo -e "${GREEN}✅ No stuck agents detected${NC}"
        STUCK_WARNINGS=0  # Reset counter
        echo ""
    fi

    # Show active agents
    ACTIVE_AGENTS=$(sqlite3 "$DB_PATH" "
        SELECT
            assigned_validator,
            COUNT(*) as events_assigned,
            MIN(CAST((julianday('now') - julianday(assigned_date)) * 86400 AS INTEGER)) as min_seconds,
            MAX(CAST((julianday('now') - julianday(assigned_date)) * 86400 AS INTEGER)) as max_seconds,
            AVG(CAST((julianday('now') - julianday(assigned_date)) * 86400 AS INTEGER)) as avg_seconds
        FROM validation_run_events
        WHERE validation_run_id = $RUN_ID
        AND validation_status = 'assigned'
        GROUP BY assigned_validator
        ORDER BY assigned_validator;
    ")

    if [ -n "$ACTIVE_AGENTS" ]; then
        ACTIVE_COUNT=$(echo "$ACTIVE_AGENTS" | wc -l)
        echo "Active Agents: $ACTIVE_COUNT / $EXPECTED_AGENTS"
        echo ""

        while IFS='|' read -r VALIDATOR EVENTS MIN_SEC MAX_SEC AVG_SEC; do
            MIN_MIN=$((MIN_SEC / 60))
            MAX_MIN=$((MAX_SEC / 60))
            AVG_MIN=$((AVG_SEC / 60))

            echo "  $VALIDATOR:"
            echo "    Events assigned: $EVENTS"
            echo "    Working time: ${MIN_MIN}-${MAX_MIN} min (avg: ${AVG_MIN} min)"

            # Warn if approaching stuck threshold
            if [ "$MAX_SEC" -gt $((STUCK_THRESHOLD * 70 / 100)) ]; then
                WARN_MIN=$((MAX_SEC / 60))
                echo -e "    ${YELLOW}⚠️  Warning: Approaching stuck threshold (${WARN_MIN} / $(($STUCK_THRESHOLD / 60)) min)${NC}"
            fi
        done <<< "$ACTIVE_AGENTS"
        echo ""

        # Check if fewer agents than expected
        if [ "$ACTIVE_COUNT" -lt "$EXPECTED_AGENTS" ]; then
            MISSING=$((EXPECTED_AGENTS - ACTIVE_COUNT))
            echo -e "${YELLOW}⚠️  Warning: Only $ACTIVE_COUNT of $EXPECTED_AGENTS expected agents are active${NC}"
            echo "   $MISSING agents may have completed their work or failed to start"
            echo ""
        fi
    else
        echo "Active Agents: 0 / $EXPECTED_AGENTS"
        echo -e "${YELLOW}⚠️  No agents currently processing events${NC}"
        echo ""
    fi

    # Estimate completion time
    if [ "$COMPLETED_COUNT" -gt 0 ] && [ "$CHECK_COUNT" -gt 1 ]; then
        REMAINING=$((TARGET_COUNT - COMPLETED_COUNT))
        if [ "$REMAINING" -gt 0 ]; then
            # Simple linear estimate based on current progress
            EVENTS_PER_INTERVAL=$(echo "scale=2; $COMPLETED_COUNT / $CHECK_COUNT" | bc)
            if [ "$(echo "$EVENTS_PER_INTERVAL > 0" | bc)" -eq 1 ]; then
                INTERVALS_REMAINING=$(echo "scale=0; $REMAINING / $EVENTS_PER_INTERVAL" | bc)
                SECONDS_REMAINING=$((INTERVALS_REMAINING * CHECK_INTERVAL))
                MINUTES_REMAINING=$((SECONDS_REMAINING / 60))

                echo "Estimated Completion:"
                echo "  Events remaining: $REMAINING"
                echo "  Average rate: $(printf "%.2f" $EVENTS_PER_INTERVAL) events per check"
                echo "  Estimated time: ~${MINUTES_REMAINING} minutes"
                echo ""
            fi
        fi
    fi

    # Wait for next check
    echo "Next check in ${CHECK_INTERVAL}s..."
    sleep "$CHECK_INTERVAL"
done
