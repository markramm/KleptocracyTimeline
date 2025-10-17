# Architectural Cleanup - Quick Reference

**Full Analysis**: See `ARCHITECTURAL_CLEANUP.md`

## Top 5 Priorities (Do First)

### 1. 🔴 Remove Legacy App Files (2 hours)
**Why**: Causing confusion, wasting space
**What**: Archive app.py, app_enhanced.py, app_threadsafe.py
```bash
mkdir -p archive/legacy_apps_20251016
git mv research_monitor/app.py archive/legacy_apps_20251016/
git mv research_monitor/app_enhanced.py archive/legacy_apps_20251016/
git mv research_monitor/app_threadsafe.py archive/legacy_apps_20251016/
```

### 2. 🔴 Database Migrations (8 hours)
**Why**: Cannot safely evolve schema, risk data loss
**What**: Install and configure Alembic
```bash
pip install alembic
alembic init alembic
# Configure alembic.ini
alembic revision --autogenerate -m "Initial schema"
```

### 3. 🔴 Fix Exception Handling (6 hours)
**Why**: 226 broad `except Exception:` handlers mask bugs
**What**: Create custom exceptions, use specific catches
```python
# Create: research_monitor/errors.py
class ValidationError(Exception): pass
class DatabaseError(Exception): pass
# Replace broad catches with specific ones
```

### 4. 🟠 Consolidate Blueprint Helpers (2 hours)
**Why**: Duplicate code in 8 files
**What**: Create shared utilities module
```bash
# Create: research_monitor/blueprint_utils.py
# Update: All 8 blueprint files
```

### 5. 🟠 Centralize Config (4 hours)
**Why**: Configuration scattered, no validation
**What**: Create Config class with validation
```python
# Update: research_monitor/config.py
# Add dataclass with validation
```

## Quick Wins (< 2 hours each)

- ✅ Replace 34 print statements with logger calls
- ✅ Clean up __pycache__ directories
- ✅ Add .gitignore entries for Python cache
- ✅ Document which app file is canonical (app_v2.py)

## Metrics Dashboard

| Metric | Current | Target |
|--------|---------|--------|
| Legacy app files | 4 | 0 |
| Global variables | 2 | 0 |
| Broad exceptions | 226 | <20 |
| Print statements | 34 | 0 |
| Test coverage | ~16% | 80%+ |
| Blueprint helpers duplicated | 8x | 0 |

## Effort Summary

**Total Estimated Effort**: ~80 hours

**By Priority:**
- Critical: 21 hours
- High: 20 hours
- Medium: 21 hours
- Low: 18+ hours

**By Sprint:**
- Sprint 1 (Immediate): 21 hours
- Sprint 2 (Next 2 weeks): 20 hours
- Sprint 3 (Following 2 weeks): 21 hours
- Future: 18+ hours

## Key Benefits After Cleanup

1. **Safer deployments** - Database migrations, proper error handling
2. **Easier testing** - Dependency injection, no global state
3. **Better debugging** - Specific exceptions, structured logging
4. **Faster development** - Clear configuration, consolidated helpers
5. **Production ready** - Monitoring, rate limiting, API versioning
