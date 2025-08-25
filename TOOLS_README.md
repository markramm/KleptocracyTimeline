# Timeline Tools Documentation

## Core Tools

### Timeline Generation
- **generate_full_timeline.py** - Generates complete timeline in markdown and JSON formats
  ```bash
  python timeline_data/generate_full_timeline.py
  ```
  Outputs: COMPLETE_TIMELINE.md and timeline_complete.json

### Validation & Source Management
- **validation_app_enhanced.py** - Web interface for validating events and managing sources
  ```bash
  python timeline_data/validation_app_enhanced.py
  # Visit http://localhost:5001
  ```
  
- **scrape_sources.py** - Scrapes source content and submits to Archive.org
  ```bash
  python timeline_data/scrape_sources.py <event_file.yaml>
  ```

- **validation_tracker.py** - Tracks validation status across events
  ```bash
  python timeline_data/validation_tracker.py
  ```

### Analysis Tools
- **add_capture_lanes.py** - Adds capture lane categorization to events
  ```bash
  python timeline_data/add_capture_lanes.py
  ```

### Viewer Application
- React-based timeline viewer in `/viewer` directory
  ```bash
  cd viewer
  npm install
  npm run dev
  ```

## Directory Structure

```
kleptocracy-timeline/
├── timeline_data/         # Core timeline data
│   ├── events/            # YAML event files
│   ├── generate_full_timeline.py
│   ├── validation_app_enhanced.py
│   └── ...
├── ai-analysis/          # Analysis content
│   ├── substack-series/  # AI Discovery series
│   └── capture_cascade/  # Capture Cascade series
├── viewer/               # React timeline viewer
├── content/              # Published content
├── analysis/             # Analysis documents
└── archive/              # Old/deprecated files
```

## Quick Start

1. **View Timeline**: Open `viewer/` and run the React app
2. **Validate Events**: Run `validation_app_enhanced.py`
3. **Generate Full Timeline**: Run `generate_full_timeline.py`
4. **Add New Event**: Create YAML in `timeline_data/events/`

## Key Files

- **README.md** - Main project documentation
- **CONTRIBUTING.md** - How to contribute
- **LICENSE-DATA** - Data license (CC BY-SA 4.0)
- **LICENSE-MIT** - Code license