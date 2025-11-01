# Kleptocracy Timeline - Timeline Data & Viewer

This directory contains the core timeline data and React viewer application.

**Note**: Hugo static site generator was removed on 2025-10-19 in favor of React-only architecture. See [docs/HUGO_REMOVAL.md](docs/HUGO_REMOVAL.md) for details.

## Quick Start

### View Timeline Locally

```bash
cd viewer
npm install
npm start
```

Open http://localhost:3000

### Generate Static API

```bash
cd scripts
python3 generate_static_api.py
```

### Validate Events

```bash
cd scripts
python3 validate_existing_events.py
```

## Directory Structure

```
timeline/
├── data/
│   └── events/              # 1,581+ timeline event JSON files
├── viewer/                  # React viewer application
├── schemas/                 # Event validation schemas
├── scripts/                 # Timeline utilities
├── public/                  # Static site output
│   └── api/                 # Generated JSON API
└── docs/                    # Timeline documentation
```

## Event Format

Events are stored in `data/events/` as JSON files:

```json
{
  "id": "YYYY-MM-DD--event-slug",
  "date": "YYYY-MM-DD",
  "title": "Event Title",
  "summary": "Detailed description",
  "importance": 8,
  "tags": ["tag1", "tag2"],
  "sources": [...]
}
```

See `schemas/timeline_event_schema.json` for complete specification.

## Deployment

The static viewer is deployed to GitHub Pages from the `public/` directory.

## License

- Data: CC0 1.0 Universal
- Code: MIT License
