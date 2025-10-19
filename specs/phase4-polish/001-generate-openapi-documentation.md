# SPEC-010: Generate OpenAPI Documentation

**Status**: Ready
**Priority**: Medium
**Estimated Time**: 2-3 hours
**Risk**: Low
**Dependencies**: Phase 3 complete (service layer extracted)

## Problem

API documentation manually maintained in multiple markdown files:
- Quickly becomes outdated
- No automatic request/response validation
- No interactive testing UI
- Hard to keep in sync with code changes

## Goal

Generate OpenAPI 3.0 specification from code, serve Swagger UI for testing.

## Success Criteria

- [ ] OpenAPI 3.0 spec generated automatically
- [ ] Swagger UI available at `/api/docs`
- [ ] All endpoints documented
- [ ] Request/response schemas defined
- [ ] Interactive testing works
- [ ] Remove manual API_DOCUMENTATION.md

## Implementation Steps

### Step 1: Choose OpenAPI Library

**Recommendation**: `flask-smorest` (marshmallow + OpenAPI)

```bash
pip install flask-smorest
```

**Alternative**: `flask-restx` (older but simpler)

### Step 2: Define Schemas with Marshmallow

**`src/api/schemas/event_schema.py`**:
```python
from marshmallow import Schema, fields, validate

class SourceSchema(Schema):
    url = fields.Url(required=True)
    title = fields.Str(required=True)
    publisher = fields.Str()
    date = fields.Date()
    tier = fields.Int(validate=validate.Range(min=1, max=3))

class EventSchema(Schema):
    id = fields.Str(
        required=True,
        validate=validate.Regexp(r'^\d{4}-\d{2}-\d{2}--[\w-]+$'),
        metadata={'description': 'Event ID in format YYYY-MM-DD--slug'}
    )
    date = fields.Date(required=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    summary = fields.Str(required=True)
    importance = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=10),
        metadata={'description': 'Importance score 1-10'}
    )
    tags = fields.List(fields.Str())
    sources = fields.List(fields.Nested(SourceSchema))
    status = fields.Str(validate=validate.OneOf(['draft', 'confirmed', 'disputed']))

    class Meta:
        ordered = True
```

### Step 3: Update Routes to Use Schemas

**Before**:
```python
@events_bp.route('/', methods=['POST'])
def create_event():
    data = request.json or {}
    # Manual validation...
    return success_response(event)
```

**After**:
```python
from flask_smorest import Blueprint, abort
from .schemas import EventSchema

events_bp = Blueprint(
    'events', __name__, url_prefix='/api/v1/events',
    description='Timeline event operations'
)

@events_bp.route('/')
@events_bp.arguments(EventSchema)
@events_bp.response(201, EventSchema)
def create_event(event_data):
    """Create a new timeline event.

    Validates event data against schema and creates new event.
    Returns created event with 201 status.
    """
    event = event_service.create(event_data)
    return event
```

### Step 4: Configure OpenAPI

**`src/api/app_v2.py`**:
```python
from flask import Flask
from flask_smorest import Api

def create_app(config=None):
    app = Flask(__name__)
    app.config.update({
        'API_TITLE': 'Timeline Research API',
        'API_VERSION': 'v1',
        'OPENAPI_VERSION': '3.0.2',
        'OPENAPI_URL_PREFIX': '/api/docs',
        'OPENAPI_SWAGGER_UI_PATH': '/swagger',
        'OPENAPI_SWAGGER_UI_URL': 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/',
    })

    api = Api(app)

    # Register blueprints
    from .routes.events import events_bp
    api.register_blueprint(events_bp)

    return app
```

### Step 5: Add Response Schemas

```python
class EventListSchema(Schema):
    total = fields.Int()
    events = fields.List(fields.Nested(EventSchema))
    pagination = fields.Dict()

@events_bp.route('/')
@events_bp.response(200, EventListSchema)
def list_events():
    """List all timeline events.

    Returns paginated list of events.
    """
    events = event_service.list(limit=100)
    return {
        'total': len(events),
        'events': events,
        'pagination': {'page': 1, 'per_page': 100}
    }
```

### Step 6: Add API Metadata

```python
app.config.update({
    'API_TITLE': 'Timeline Research API',
    'API_VERSION': 'v1',
    'OPENAPI_VERSION': '3.0.2',
    'API_SPEC_OPTIONS': {
        'info': {
            'description': 'Research infrastructure for Kleptocracy Timeline',
            'contact': {
                'email': 'contact@example.com'
            },
            'license': {
                'name': 'MIT',
                'url': 'https://opensource.org/licenses/MIT'
            }
        },
        'servers': [
            {'url': 'http://localhost:5558', 'description': 'Development'},
            {'url': 'https://api.example.com', 'description': 'Production'}
        ],
        'tags': [
            {'name': 'events', 'description': 'Timeline event operations'},
            {'name': 'priorities', 'description': 'Research priority management'},
            {'name': 'validation', 'description': 'Validation run operations'}
        ]
    }
})
```

### Step 7: Add Authentication Docs

```python
from flask_smorest import abort

# Define security scheme
app.config['API_SPEC_OPTIONS']['components'] = {
    'securitySchemes': {
        'ApiKeyAuth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key'
        }
    }
}

# Apply to routes
@events_bp.route('/', methods=['POST'])
@events_bp.doc(security=[{'ApiKeyAuth': []}])
@events_bp.arguments(EventSchema)
def create_event(event_data):
    """Create event (requires API key)."""
    pass
```

### Step 8: Test Documentation

```bash
# Start server
./research server-start

# Open Swagger UI
open http://localhost:5558/api/docs/swagger

# Download OpenAPI spec
curl http://localhost:5558/api/docs/openapi.json > openapi.json
```

### Step 9: Remove Manual Docs

```bash
# Remove manual API documentation
rm docs/API_DOCUMENTATION.md

# Update README to point to /api/docs/swagger
```

## Validation

- [ ] Swagger UI loads at `/api/docs/swagger`
- [ ] All endpoints documented
- [ ] "Try it out" works for GET requests
- [ ] Request validation enforced
- [ ] Response schemas accurate
- [ ] OpenAPI spec valid (test with validator)

## Benefits

1. **Always Up to Date**: Docs generated from code
2. **Interactive Testing**: Try API calls in browser
3. **Request Validation**: Marshmallow validates automatically
4. **Type Safety**: Schemas enforce structure
5. **Client Generation**: Can generate SDKs from spec

## Acceptance Criteria

- [x] OpenAPI 3.0 spec generated
- [x] Swagger UI accessible
- [x] All routes documented with schemas
- [x] Request validation works
- [x] Response validation works
- [x] Manual API docs removed
- [x] README updated to reference /api/docs
