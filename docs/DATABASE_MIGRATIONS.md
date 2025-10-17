# Database Migrations Guide

**Version**: 1.0
**Date**: 2025-10-16
**Migration Tool**: Alembic

## Overview

The Kleptocracy Timeline uses [Alembic](https://alembic.sqlalchemy.org/) for database schema migrations. This ensures safe, version-controlled evolution of the database schema without data loss.

## Why Migrations?

Before migrations were implemented (pre-Sprint 1), schema changes required:
1. Manually deleting `unified_research.db`
2. Restarting the server to rebuild from filesystem
3. Risk of data loss for database-authoritative tables (research_priorities, validation_logs, etc.)

With Alembic migrations:
- ✅ Schema changes are tracked in version control
- ✅ Database evolves safely without data loss
- ✅ Changes are reversible (can rollback)
- ✅ Team members stay in sync automatically

## Quick Reference

```bash
# Create a new migration after changing models.py
alembic revision --autogenerate -m "Add new column to events"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current migration status
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic show head
```

## Directory Structure

```
kleptocracy-timeline/
├── alembic/                    # Alembic configuration
│   ├── versions/              # Migration scripts
│   │   └── dad4e4a50d02_...py # Initial schema capture
│   ├── env.py                 # Migration environment config
│   ├── script.py.mako         # Migration template
│   └── README                 # Alembic readme
├── alembic.ini                # Alembic configuration file
└── unified_research.db        # SQLite database
```

## Common Workflows

### 1. Adding a New Column to a Table

```bash
# 1. Edit research_monitor/models.py
# Add new column to model, e.g.:
# class TimelineEvent(Base):
#     ...
#     new_field = Column(String)

# 2. Generate migration
alembic revision --autogenerate -m "Add new_field to timeline_events"

# 3. Review generated migration in alembic/versions/
# Make sure it does what you expect

# 4. Apply migration
alembic upgrade head

# 5. Commit migration to git
git add alembic/versions/*.py
git commit -m "Add new_field column to timeline_events"
```

### 2. Creating a New Table

```bash
# 1. Edit research_monitor/models.py
# Add new model class, e.g.:
# class NewTable(Base):
#     __tablename__ = 'new_table'
#     id = Column(Integer, primary_key=True)
#     ...

# 2. Generate migration
alembic revision --autogenerate -m "Create new_table"

# 3. Review and apply
alembic upgrade head

# 4. Commit
git add alembic/versions/*.py research_monitor/models.py
git commit -m "Add new_table for feature X"
```

### 3. Renaming a Column

```bash
# 1. Edit research_monitor/models.py
# Rename column

# 2. Generate migration
alembic revision --autogenerate -m "Rename old_name to new_name"

# 3. IMPORTANT: Edit migration to preserve data
# Alembic might generate drop + create instead of rename
# Edit to use op.alter_column() with new_column_name parameter

# 4. Apply and test
alembic upgrade head

# 5. Commit
git add alembic/versions/*.py research_monitor/models.py
git commit -m "Rename column for clarity"
```

### 4. Rollback a Migration

```bash
# Check current version
alembic current

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all migrations (dangerous!)
alembic downgrade base
```

## Migration Best Practices

### 1. Always Review Auto-Generated Migrations

Alembic's `--autogenerate` is powerful but not perfect. Always:
- ✅ Review the generated migration file
- ✅ Check that it matches your intent
- ✅ Test the upgrade and downgrade paths
- ✅ Add data migration logic if needed

### 2. Write Reversible Migrations

Every migration should have both `upgrade()` and `downgrade()`:

```python
def upgrade() -> None:
    """Add new column."""
    op.add_column('timeline_events', sa.Column('new_field', sa.String()))

def downgrade() -> None:
    """Remove new column."""
    op.drop_column('timeline_events', 'new_field')
```

### 3. Handle Data Migrations

If you need to transform existing data:

```python
def upgrade() -> None:
    """Add status column with default values."""
    # Add column
    op.add_column('timeline_events',
                  sa.Column('status', sa.String(), nullable=True))

    # Populate existing rows
    op.execute("UPDATE timeline_events SET status = 'active' WHERE status IS NULL")

    # Make non-nullable after populating
    op.alter_column('timeline_events', 'status', nullable=False)
```

### 4. Test Migrations Before Committing

```bash
# 1. Apply migration
alembic upgrade head

# 2. Test that app still works
python3 research_cli.py server-start
# ... run some tests ...

# 3. Test downgrade
alembic downgrade -1

# 4. Test app still works after downgrade
# ... run tests again ...

# 5. Re-apply migration
alembic upgrade head
```

### 5. Commit Migrations to Git

```bash
# Always commit migrations with related code changes
git add alembic/versions/*.py research_monitor/models.py
git commit -m "Add new feature: descriptive message"
```

## Special Considerations for This Project

### FTS5 Virtual Tables

The `events_fts` full-text search table and related tables are **not managed by Alembic**:
- Created by SQLite triggers in `app_v2.py`
- Automatically maintained by SQLite
- Do not include in migrations

If you see FTS tables in auto-generated migrations, remove those operations.

### Filesystem-Authoritative Tables

`timeline_events` table is **read-only** - synced from JSON files:
- Migrations can change schema
- Data comes from `timeline_data/events/*.json`
- Don't add migrations that transform event data

### Database-Authoritative Tables

These tables are **safe to migrate**:
- `research_priorities` - Research task tracking
- `validation_logs` - QA validation history
- `validation_runs` - Validation workflow tracking
- `validation_run_events` - Individual validation items
- `activity_logs` - System activity tracking
- `event_update_failures` - Failed event save tracking

## Troubleshooting

### "Database is not up to date"

```bash
# Check current version
alembic current

# Show what migrations are pending
alembic heads
alembic show head

# Apply pending migrations
alembic upgrade head
```

### "Multiple heads detected"

This means migration history has branched. Merge the branches:

```bash
# Create a merge migration
alembic merge -m "Merge migration branches" <rev1> <rev2>

# Apply merge
alembic upgrade head
```

### "Can't locate revision"

The database might be out of sync. Check:

```bash
# What does the database think the current version is?
alembic current

# What migrations exist?
alembic history
```

If completely stuck, you can re-stamp the database:

```bash
# Mark database as being at specific version (use carefully!)
alembic stamp <revision_id>
```

### Starting Fresh (Development Only)

If you need to completely reset the database:

```bash
# 1. Stop the server
python3 research_cli.py server-stop

# 2. Delete database
rm unified_research.db unified_research.db-wal unified_research.db-shm

# 3. Apply all migrations
alembic upgrade head

# 4. Restart server (will re-sync from filesystem)
python3 research_cli.py server-start
```

## Configuration Files

### alembic.ini

Main configuration file:
- Database URL: `sqlite:///%(here)s/unified_research.db`
- Script location: `%(here)s/alembic`
- File template for migration names

### alembic/env.py

Migration environment configuration:
- Imports SQLAlchemy models from `research_monitor.models`
- Configures target_metadata for autogenerate
- Handles online and offline migrations

## Migration Template

When creating manual migrations:

```bash
# Create empty migration
alembic revision -m "Description of change"
```

Template structure:

```python
"""Description of change

Revision ID: <auto-generated>
Revises: <previous-revision>
Create Date: <timestamp>
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '<auto-generated>'
down_revision: Union[str, None] = '<previous-revision>'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply changes."""
    pass


def downgrade() -> None:
    """Revert changes."""
    pass
```

## Resources

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic Auto Generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2025-10-16 | Initial migration system setup (Sprint 1) |

## Related Documentation

- `research_monitor/models.py` - SQLAlchemy model definitions
- `specs/PROJECT_EVALUATION.md` - Project evaluation (Sprint 1 tasks)
- `specs/ARCHITECTURAL_CLEANUP.md` - Architectural cleanup priorities
