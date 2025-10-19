# SPEC-007: Extract Services from app_v2.py

**Status**: Ready
**Priority**: High
**Estimated Time**: 4-6 hours
**Risk**: Medium
**Dependencies**: Phase 2 complete

## Problem

`app_v2.py` is 4,708 lines - should be <500 lines (just app factory).

Contains:
- Route definitions
- Business logic
- Database queries
- Validation logic
- Background services
- Configuration

## Goal

Extract business logic into service layer, reduce app_v2.py to app factory only.

## Target Structure

```
src/api/
├── app_v2.py               # <500 lines - app factory only
├── services/
│   ├── __init__.py
│   ├── event_service.py    # Event operations
│   ├── priority_service.py # Priority management
│   ├── validation_service.py # Validation runs
│   ├── search_service.py   # Full-text search
│   └── sync_service.py     # Filesystem sync
├── repositories/
│   ├── __init__.py
│   ├── base.py            # Base repository
│   ├── event_repository.py
│   └── priority_repository.py
└── routes/                 # (already exists)
```

## Implementation Steps

### Step 1: Create Service Base Class

**`src/api/services/base_service.py`**:
```python
"""Base service class for dependency injection."""

class BaseService:
    """Base class for all services."""

    def __init__(self, db_session):
        self.db = db_session

    def commit(self):
        """Commit database transaction."""
        self.db.commit()

    def rollback(self):
        """Rollback database transaction."""
        self.db.rollback()
```

### Step 2: Create Event Service

**`src/api/services/event_service.py`**:
```python
"""Event management service."""
from .base_service import BaseService
from ..models import TimelineEvent, EventMetadata
from ..repositories.event_repository import EventRepository

class EventService(BaseService):
    """Handles event business logic."""

    def __init__(self, db_session):
        super().__init__(db_session)
        self.event_repo = EventRepository(db_session)

    def get_by_id(self, event_id: str) -> dict:
        """Get event by ID."""
        event = self.event_repo.find_by_id(event_id)
        if not event:
            raise NotFoundError(f"Event {event_id} not found")
        return event.to_dict()

    def search(self, query: str, limit: int = 50) -> list:
        """Search events."""
        return self.event_repo.search(query, limit)

    def create(self, data: dict) -> dict:
        """Create new event."""
        # Validation logic here
        event = self.event_repo.create(data)
        self.commit()
        return event.to_dict()
```

### Step 3: Create Repository Layer

**`src/api/repositories/event_repository.py`**:
```python
"""Event data access layer."""
from sqlalchemy import text
from .base import BaseRepository
from ..models import TimelineEvent

class EventRepository(BaseRepository):
    """Event database operations."""

    def __init__(self, db_session):
        super().__init__(db_session, TimelineEvent)

    def find_by_id(self, event_id: str):
        """Find event by ID."""
        return self.db.query(TimelineEvent).filter_by(id=event_id).first()

    def search(self, query: str, limit: int = 50):
        """Full-text search."""
        # Implementation...
        pass
```

### Step 4: Update Routes to Use Services

**Before**:
```python
@app.route('/api/events/<event_id>')
def get_event(event_id):
    db = get_db()
    event = db.query(TimelineEvent).filter_by(id=event_id).first()
    if not event:
        return error_response('Not found'), 404
    return success_response(event.to_dict())
```

**After**:
```python
from flask_injector import inject
from ..services.event_service import EventService

@events_bp.route('/<event_id>')
@inject
def get_event(event_id: str, event_service: EventService):
    event = event_service.get_by_id(event_id)
    return success_response(event)
```

### Step 5: Configure Dependency Injection

**`src/api/dependencies.py`**:
```python
"""Dependency injection configuration."""
from injector import Module, provider, singleton
from .database import get_db_session
from .services.event_service import EventService

class ServiceModule(Module):
    @provider
    @singleton
    def provide_db_session(self):
        return get_db_session()

    @provider
    def provide_event_service(self, db_session) -> EventService:
        return EventService(db_session)
```

### Step 6: Simplify app_v2.py

**New structure** (~400 lines):
```python
from flask import Flask
from flask_injector import FlaskInjector
from config import get_config
from dependencies import ServiceModule
from routes import register_blueprints

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or get_config())

    # Initialize extensions
    init_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Setup dependency injection
    FlaskInjector(app=app, modules=[ServiceModule()])

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=app.config['PORT'])
```

### Step 7: Extract Background Services

Move filesystem sync to service:

**`src/api/services/sync_service.py`**:
```python
"""Filesystem sync background service."""
import threading
import time
from pathlib import Path

class FilesystemSyncService:
    """Syncs filesystem events to database."""

    def __init__(self, app, event_service):
        self.app = app
        self.event_service = event_service
        self.running = False
        self.thread = None

    def start(self):
        """Start background sync thread."""
        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop background sync."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _sync_loop(self):
        """Background sync loop."""
        while self.running:
            self._sync_events()
            time.sleep(30)
```

## Testing Strategy

### Step 1: Test Services Independently

```python
def test_event_service_get_by_id(db_session):
    service = EventService(db_session)
    event = service.get_by_id("2024-01-15--test")
    assert event['id'] == "2024-01-15--test"

def test_event_service_search(db_session):
    service = EventService(db_session)
    results = service.search("Trump", limit=10)
    assert len(results) <= 10
```

### Step 2: Test Repositories

```python
def test_event_repository_find_by_id(db_session):
    repo = EventRepository(db_session)
    event = repo.find_by_id("2024-01-15--test")
    assert event is not None
```

### Step 3: Integration Tests

```python
def test_api_with_services(client):
    """Test full API with new service layer."""
    response = client.get('/api/v1/events/2024-01-15--test')
    assert response.status_code == 200
```

## Validation

- [ ] app_v2.py reduced to <500 lines
- [ ] All services extracted and tested
- [ ] All routes use dependency injection
- [ ] All tests pass
- [ ] No business logic in routes
- [ ] No database queries in routes

## Rollback

Create feature branch, test thoroughly before merging:

```bash
git checkout -b refactor/extract-services
# Make changes
# Test extensively
# Only merge if all tests pass
```

## Acceptance Criteria

- [x] Service layer created (5+ service classes)
- [x] Repository layer created
- [x] Dependency injection configured
- [x] app_v2.py < 500 lines
- [x] All routes updated to use services
- [x] Unit tests for all services
- [x] Integration tests pass
- [x] No regression in functionality
