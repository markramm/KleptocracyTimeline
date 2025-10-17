# The Kleptocracy Timeline

[![CI/CD Pipeline](https://github.com/markramm/KleptocracyTimeline/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/markramm/KleptocracyTimeline/actions)
[![Timeline Events](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmarkramm%2FKleptocracyTimeline%2Fmain%2Fviewer%2Fpublic%2Fapi%2Fstats.json&query=%24.total_events&label=Timeline%20Events&color=blue)](https://markramm.github.io/KleptocracyTimeline/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **In Memoriam**: This project is dedicated to the journalists and researchers who have paid the ultimate price exposing corruption. See [IN_MEMORIAM.md](IN_MEMORIAM.md) for those we honor. Their courage is why this project must remain open, decentralized, and resilient.

Open-source timeline documenting democratic erosion and institutional capture in the United States (1972-present).

🌐 **[View the Interactive Timeline](https://markramm.github.io/KleptocracyTimeline/)**

## 📊 Project Overview

This project tracks and documents the systematic undermining of democratic institutions through:
- **Financial Corruption & Kleptocracy** - Dark money, shell companies, and financial crimes
- **Judicial Capture** - Court stacking and judicial corruption
- **Foreign Influence Operations** - Election interference and infiltration
- **Information Warfare** - Disinformation campaigns and media manipulation
- **Constitutional Erosion** - Attacks on democratic norms and rule of law

Every event is:
- 📅 **Dated** - Precise timeline placement
- 📄 **Documented** - Multiple credible sources required
- 🔍 **Verified** - Community validation process
- 📦 **Archived** - Protection against link rot

## 🚀 Quick Start

### View the Timeline
Visit [markramm.github.io/KleptocracyTimeline](https://markramm.github.io/KleptocracyTimeline/)

### Run Locally
```bash
# Clone the repository
git clone https://github.com/markramm/KleptocracyTimeline.git
cd KleptocracyTimeline

# Install dependencies
cd viewer
npm install

# Generate API data
cd ..
python timeline_data/generate_static_api.py

# Start development server
cd viewer
npm start
```

## 🛠️ Developer Tools

### Creating and Validating Events

⚠️ **IMPORTANT**: Always use the `timeline_event_manager.py` tool instead of manually creating/editing JSON files. This prevents common errors and ensures consistency.

#### Why Use the Event Manager?
- **Automatic ID generation** - IDs always match filenames
- **Date validation** - Ensures YYYY-MM-DD format
- **Status validation** - Only allows valid status values
- **Future date checks** - Prevents marking future events as "confirmed"
- **Source validation** - Ensures all sources have required fields
- **Duplicate detection** - Prevents creating duplicate events

#### Interactive Creation (Recommended for humans)
```bash
python create_event.py
```
This will guide you through creating a properly formatted event with validation.

#### Programmatic Creation (For scripts/agents)
```python
from timeline_event_manager import TimelineEventManager

manager = TimelineEventManager()

# Create an event with validation
event = manager.create_event(
    date="2025-01-20",
    title="Event Title",
    summary="Detailed description of what happened",
    importance=7,
    actors=["Person A", "Organization B"],
    tags=["corruption", "foreign-influence"],
    sources=[
        manager.create_source(
            title="Article Title",
            url="https://example.com/article",
            outlet="News Outlet",
            source_date="2025-01-20"
        )
    ]
)

# Save the event
filepath = manager.save_event(event)
```

#### Command-Line Creation (For automation)
```bash
# Via JSON
python create_event_agent.py --json '{
  "date": "2025-01-20",
  "title": "Event Title",
  "summary": "Description",
  "importance": 7,
  "actors": ["Actor1"],
  "tags": ["tag1"],
  "sources": [{"title": "Source", "url": "https://...", "outlet": "Outlet"}]
}'

# Batch import from CSV
python import_events.py events.csv
```

### Event Validation

Run validation before committing any changes:

```bash
# Quick validation check
python3 -m pytest tests/test_timeline_validation.py

# Or use the validation script directly
python3 tools/validation/validate_timeline_dates.py

# Fix ID/filename mismatches automatically
python3 timeline_event_manager.py --fix-ids
```

The repository includes pre-commit hooks that automatically validate:
- ID/filename matching
- Required fields presence
- Date format (YYYY-MM-DD)
- Status values
- Future events cannot be "confirmed"
- ESLint checks (no unused variables, proper imports)
- React build with CI settings (treats warnings as errors)

### JSON Event Management
The timeline now uses JSON format for all events. Use the `timeline_event_manager.py` for all event operations:

```python
from timeline_event_manager import TimelineEventManager
manager = TimelineEventManager()

# Create a new event with validation
event = manager.create_event(
    date="2025-01-20",
    title="Event Title",
    summary="Description",
    importance=7,
    actors=["Actor Name"],
    tags=["tag1", "tag2"],
    sources=[...]
)

# Save the event to JSON
filepath = manager.save_event(event)
```

These tools provide:
- Automatic ID generation and validation
- Schema enforcement
- Source deduplication
- Date format validation
- Importance range checking

## 📁 Repository Structure

```
├── timeline_data/          # Timeline events in YAML format
│   └── events/            # Individual event files
├── viewer/                # React-based timeline viewer
├── scripts/               # Data processing and validation
├── docs/                  # Documentation
│   ├── user/             # User guides
│   ├── development/      # Developer documentation
│   └── maintenance/      # Maintenance guides
├── tests/                # Test suites
└── .github/workflows/    # CI/CD pipelines
```

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Ways to Contribute
- **Validate Events** - Help verify sources and fact-check
- **Submit New Events** - Add documented events with sources
- **Improve Code** - Enhance the viewer or tools
- **Report Issues** - Flag errors or broken links

### Validation Process
1. Run validation: `python3 research_cli.py qa-queue --limit 10`
2. Pick any unvalidated event
3. Verify sources confirm the claims
4. Mark as validated: `python3 research_cli.py qa-validate --event-id <event-id> --score <score> --notes "<notes>"`

## 📖 Documentation

- [FAQ](docs/user/FAQ.md) - Common questions
- [Development Setup](docs/development/DEVELOPMENT_SETUP.md) - Set up your dev environment
- [Testing Guide](docs/development/TESTING.md) - How to run tests
- [Deployment](docs/user/DEPLOYMENT.md) - Deploy your own instance

## 🧪 Testing

Run all tests before committing:
```bash
./tests/scripts/test-before-commit.sh
```

## 📊 Data Format

Events are stored as YAML files with this structure:
```yaml
id: unique-event-id
date: YYYY-MM-DD
title: Event Title
summary: Brief description
importance: 1-10
tags: [tag1, tag2]
sources:
  - outlet: Source Name
    url: https://...
    date: YYYY-MM-DD
```

**Never create event YAML files manually!** Use the event creation tools:
- `python create_event.py` - Interactive creation with validation
- `python timeline_event_manager.py` - Python API for scripts
- `python create_event_agent.py` - CLI for automation

## 📜 License

MIT License - See [LICENSE](LICENSE) file

## 🙏 Acknowledgments

This project relies on the work of journalists, researchers, and citizens who document threats to democracy.

## 📮 Contact

- **Issues**: [GitHub Issues](https://github.com/markramm/KleptocracyTimeline/issues)
- **Discussions**: [GitHub Discussions](https://github.com/markramm/KleptocracyTimeline/discussions)

---

*"Those who would destroy democracy depend on our ignorance. This timeline is our defense."*
