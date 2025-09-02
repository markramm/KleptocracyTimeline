# Implementation Strategy - Efficient Execution Plan

## Phase 1: Critical Source Fixes (Today - 2 hours)
Focus on the highest-impact single-source events first.

### Batch 1: Foreign Influence (30 min)
1. **Qatar $400M jet** - Add 5 sources
2. **Vietnam resort** - Add 4 sources

### Batch 2: Enforcement (30 min)
3. **ICE 100-day milestone** - Add 3 sources
4. **DOJ/FBI corruption units** - Add 2 sources
5. **Operation At Large** - Add 4 sources, flag as partial

### Batch 3: Media/Corporate (30 min)
6. **Paramount settlement** - Add 2 sources
7. **Megadonor access** - Find primary or mark needs-primary

### Batch 4: Automated fixes (30 min)
- Script to find all single-source events
- Batch update status fields
- Generate archive URLs

---

## Phase 2: Systematic Improvements (Day 2-3)

### Data Quality Script (2 hours)
Create Python script to:
- Identify all single-source events
- Flag future-dated events
- Check for placeholder sources
- Generate source addition templates

### Source Template System (1 hour)
- Create YAML templates for common source types
- Standardize official vs independent format
- Archive URL generation

### Batch Processing (3 hours)
- Process remaining 34 single-source events
- Apply standardized formatting
- Update status fields

---

## Phase 3: Viewer Updates (Day 4)

### Statistics Update
- Update event count to 882
- Fix "Democracy Timeline" → "The Kleptocracy Timeline"
- Update acceleration metrics

### Visual Improvements
- Enhance actor graph connections
- Add source quality indicators
- Show official vs independent balance

---

## Execution Approach

### 1. Start with High-Impact Quick Wins
- Events with sources already identified
- Can add 20+ sources in first hour

### 2. Use Batch Processing
- Group similar events
- Apply templates
- Automate repetitive tasks

### 3. Track Progress Systematically
- Check off completed items
- Update status in real-time
- Document any blockers

### 4. Quality Control
- Verify each source works
- Ensure balanced perspective
- Archive everything

---

## Tools & Scripts Needed

1. **Source Addition Script**
```python
# Finds events, adds sources, updates status
python scripts/add_sources_batch.py
```

2. **Future Event Flagger**
```python
# Flags events after Sept 2, 2025
python scripts/flag_future_events.py
```

3. **Archive URL Generator**
```python
# Creates Wayback Machine archives
python scripts/archive_sources.py
```

---

## Success Metrics

### Today:
- [ ] 7 highest-impact events fixed
- [ ] Scripts created for automation
- [ ] 20+ sources added total

### This Week:
- [ ] All 41 single-source events fixed
- [ ] All future events flagged
- [ ] Archive URLs for everything
- [ ] Viewer statistics updated

### Quality Targets:
- Zero single-source events (importance ≥ 8)
- 100% archive coverage
- Clear official/independent balance
- Accurate dataset statistics