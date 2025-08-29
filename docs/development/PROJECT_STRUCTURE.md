# Project Structure - Kleptocracy Timeline

## Core Directories

### 📊 timeline_data/
The heart of the project - contains all timeline events and processing tools
- `events/` - YAML files for each timeline event
- `generate_full_timeline.py` - Creates complete timeline markdown/JSON
- `validation_app_enhanced.py` - Web UI for event validation
- `validation_tracker.py` - Tracks validation status
- `scrape_sources.py` - Archives source content

### 📝 ai-analysis/
Analysis and narrative content
- `substack-series/` - AI Discovery series (8 parts)
- `capture_cascade/` - Capture Cascade series (7 PDFs)
- Additional analysis documents

### 🌐 viewer/
React-based timeline viewer application
- Modern web interface for exploring the timeline
- Interactive filtering and search
- Visual timeline representation

### 📑 content/
Publishing-ready content
- `ALPHA_RELEASE_CHECKLIST.md` - Launch preparation
- `SUBSTACK_POST_CITED.md` - Epstein financial networks post

### 🔍 analysis/
Pattern analysis and research
- `PATTERN_ANALYSIS.md` - 9 capture lanes analysis
- `CAPTURE_LANES.md` - Detailed capture mechanisms

### 🛠️ scripts/
Timeline processing utilities
- `generate.py` - Static site generation
- `timeline.py` - Timeline processing
- `validate.py` - Event validation

### 🔧 tools/
Additional utilities
- `archiving/` - Archive.org integration
- `generation/` - Content generation tools
- `qa/` - Quality assurance tools
- `validation/` - Extended validation utilities

### 📚 docs/
GitHub Pages documentation site

### 🗄️ archive/
Old and deprecated files (gitignored)

## Key Files

- **README.md** - Main project documentation
- **TOOLS_README.md** - Tool usage guide
- **CONTRIBUTING.md** - Contribution guidelines
- **PROJECT_STATUS.md** - Current project status
- **LICENSE-DATA** - CC BY-SA 4.0 for data
- **LICENSE-MIT** - MIT license for code

## Quick Start

1. **Generate Timeline**: `python timeline_data/generate_full_timeline.py`
2. **Validate Events**: `python timeline_data/validation_app_enhanced.py`
3. **View Timeline**: `cd viewer && npm run dev`
4. **Read Analysis**: Check `ai-analysis/` directories

## Repository Stats

- **394** documented events
- **1,900+** verified sources
- **8** AI Discovery posts
- **7** Capture Cascade papers
- **9** identified capture lanes
- **54 years** of documented capture (1971-2025)

## Ready for Publishing

This repository is now clean and ready for:
- Public GitHub release
- Substack series launch
- Timeline alpha release
- Community contributions

The archive folder contains all old/deprecated files for reference but is gitignored to keep the repo clean.