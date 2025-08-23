# Event Validation System

## Quick Start

### 1. Check Current Status
```bash
cd timeline_data
python3 validation_tracker.py stats
```

### 2. View Validation Queue
```bash
python3 validation_tracker.py queue --limit 20
```

### 3. Launch Web UI for Validation
```bash
python3 validation_app.py
# Then open http://localhost:8080
```

### 4. Command Line Validation
```bash
# Mark as validated
python3 validation_tracker.py validate --event-id "2025-01-20--doge-established-musk-ramaswamy" --validator "your-name"

# Mark as problematic
python3 validation_tracker.py problem --event-id "2025-01-20--doge-established-musk-ramaswamy" --issues broken_links incorrect_date --validator "your-name"

# Generate report
python3 validation_tracker.py report
```

## Current Status (2025-08-23)

- **Total Events**: 395
- **Validated**: 0 (0%)
- **Critical Events (8+)**: 116
- **Critical Validated**: 0

## Priority Queue

The validation system prioritizes events by importance (10 to 5):
- **Level 10**: 32 events (Most Critical)
- **Level 9**: 29 events
- **Level 8**: 55 events
- **Level 7**: 15 events
- **Level 6**: 190 events
- **Level 5**: 74 events

## Validation Criteria

An event should be marked as **VALIDATED** if:
1. ✅ Date is correct
2. ✅ Sources support the claims made
3. ✅ At least one source link works
4. ✅ Summary accurately reflects the event
5. ✅ Importance level is appropriate
6. ✅ No duplicate events exist

An event should be marked as **PROBLEMATIC** if:
1. ❌ Broken source links (all sources)
2. ❌ Incorrect date
3. ❌ Sources don't support claims
4. ❌ Missing critical sources
5. ❌ Inaccurate or misleading summary
6. ❌ Wrong importance level
7. ❌ Duplicate event

## Web UI Features

The validation web app provides:
- Visual review of events in priority order
- One-click validation
- Problem reporting with checkboxes
- Progress tracking
- Skip functionality
- Sources with archive status
- Real-time statistics

## Files Created

1. **validation_tracker.py** - Core validation tracking system
2. **validation_app.py** - Web UI for human validation
3. **validation_status.json** - Persistent validation state (created on first run)
4. **validation_report.md** - Generated validation report

## Recommended Workflow

### Phase 1: Critical Events (Week 1)
1. Validate all Level 10 events (32)
2. Validate all Level 9 events (29)
3. Validate all Level 8 events (55)
Total: 116 critical events

### Phase 2: High Priority (Week 2)
1. Validate Level 7 events (15)
2. Start Level 6 events (190)

### Phase 3: Remaining (Week 3-4)
1. Complete Level 6 events
2. Validate Level 5 events (74)

## Integration with Main App

The validation status can be:
1. Added to event YAML files as a `validated: true` field
2. Used to filter events in the timeline viewer
3. Displayed as badges in the UI
4. Used for deployment readiness checks

## Next Steps

1. **Start Validation**: Launch the web UI and begin with Level 10 events
2. **Archive Sources**: Continue running archive process
3. **Fix Issues**: Address problematic events as they're identified
4. **Track Progress**: Generate weekly reports
5. **Deploy When Ready**: Aim for 100% validation of critical events before launch