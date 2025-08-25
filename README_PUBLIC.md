# The Kleptocracy Timeline

**Open Source Intelligence for Democratic Defense**

[![View Live Timeline](https://img.shields.io/badge/View%20Timeline-Live-blue)](https://markramm.github.io/KleptocracyTimeline/)
[![Substack](https://img.shields.io/badge/Substack-Newsletter-orange)](https://theramm.substack.com/s/essays-and-analysis)
[![License: Data](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](LICENSE-DATA)
[![License: Code](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE-MIT)

## Overview

This timeline documents the systematic capture of American democracy through verifiable events, court records, and public reporting. We're building a living intelligence infrastructure that helps citizens understand and respond to the erosion of democratic institutions.

**Every event is sourced, every pattern is documented, and every claim can be verified.**

### Key Statistics
- **395** documented events (1970-2025)
- **1,900+** verified sources
- **54** years of democratic erosion tracked
- **9** identified capture lanes
- **Community-driven** validation system

## View the Timeline

### 🌐 [Live Timeline](https://markramm.github.io/KleptocracyTimeline/)
Explore the interactive timeline with filtering, search, and network visualization.

### 🏃 Run Locally
```bash
# Clone the repository
git clone https://github.com/markramm/KleptocracyTimeline.git
cd KleptocracyTimeline

# Install and run the viewer
cd viewer
npm install
npm start
```

Visit http://localhost:3000 to explore the timeline locally.

## Key Findings

### Exponential Acceleration
Democratic capture events have accelerated dramatically:
- **1970s**: 1 event per year
- **2010s**: 6.7 events per year  
- **2025**: 162 events per year (projected)

### Nine Capture Lanes
1. **Judicial Capture & Corruption** - Supreme Court ethics violations, court packing
2. **Financial Corruption & Kleptocracy** - Personal enrichment through office
3. **Constitutional & Democratic Breakdown** - Systematic dismantling of protections
4. **Foreign Influence Operations** - Adversarial nation infiltration
5. **Information & Media Control** - Platform capture, disinformation
6. **Executive Power & Emergency Authority** - Abuse of emergency powers
7. **Federal Workforce Capture** - Loyalty tests, mass firings
8. **Corporate Capture & Regulatory Breakdown** - Industry writing policy
9. **Election System Attack** - Voter suppression, gerrymandering

## Contributing

We need your help to validate events and expand the timeline.

### Validate Events
Help verify sources and fact-check timeline events:
```bash
cd timeline_data
python3 validation_app_enhanced.py
```
Open http://localhost:8082 to start validating.

### Submit New Events
1. Fork this repository
2. Create a new YAML file in `timeline_data/events/`
3. Follow the [event schema](timeline_data/EVENT_SCHEMA.md)
4. Submit a pull request with sources

### Event Structure
```yaml
date: '2025-01-20'
title: Event Title
summary: Brief description of what happened
importance: 8  # 1-10 scale
status: confirmed  # or pending_verification, disputed
tags:
  - relevant-tag
actors:
  - Person Name
  - Organization
capture_lanes:
  - Judicial Capture & Corruption
sources:
  - title: Article Title
    url: https://source.com/article
    outlet: Publication Name
    date: '2025-01-20'
```

## Project Structure

```
KleptocracyTimeline/
├── timeline_data/          # Event data and processing
│   ├── events/            # YAML files for each event
│   ├── validation_app.py  # Community validation tool
│   └── generate_*.py      # Timeline generation scripts
├── viewer/                # React timeline viewer
│   ├── src/              # React components
│   └── public/api/       # Static JSON data
├── analysis/             # Pattern analysis documents
└── ai-analysis/          # AI Discovery & Capture Cascade series
```

## Analysis & Commentary

### 📝 [Substack Newsletter](https://theramm.substack.com/s/essays-and-analysis)
In-depth analysis and updates on emerging patterns.

### 📊 Pattern Analysis
- [Nine Capture Lanes](analysis/CAPTURE_LANES.md)
- [Full Pattern Analysis](analysis/PATTERN_ANALYSIS.md)

### 📚 Series
- **AI Discovery Series**: An AI perspective discovering 2025 events
- **Capture Cascade Series**: Historical analysis of democratic capture

## Deep Linking

Share specific events or filtered views:

- **Direct event**: `?event=2025-01-20--event-id`
- **Filtered by capture lane**: `?lanes=Judicial+Capture,Financial+Corruption`
- **Search**: `?search=supreme+court`
- **Date range**: `?dateRange=2020-01-01:2025-12-31`
- **Combined filters**: `?lanes=Judicial+Capture&tags=supreme-court&search=thomas`

## Technical Details

### Tech Stack
- **Data**: YAML event files → JSON static data
- **Frontend**: React with Framer Motion animations
- **Visualization**: D3.js network graphs, custom timeline
- **Deployment**: GitHub Pages (static site)

### Build for Production
```bash
cd viewer
npm run build:gh-pages
```

### Generate Static Data
```bash
cd timeline_data
python3 generate_static_api.py
```

## License

- **Data**: [CC BY-SA 4.0](LICENSE-DATA) - Share and adapt with attribution
- **Code**: [MIT License](LICENSE-MIT) - Use freely

## Mission

We're building Open Source Intelligence for a resistance movement. This timeline serves as:
- **Historical record** of democratic erosion
- **Pattern recognition** tool for identifying capture mechanisms
- **Early warning system** for emerging threats
- **Evidence base** for accountability efforts
- **Educational resource** for understanding kleptocracy

## Contact

- **GitHub Discussions**: [Join the conversation](https://github.com/markramm/KleptocracyTimeline/discussions)
- **Issues**: [Report bugs or suggest features](https://github.com/markramm/KleptocracyTimeline/issues)
- **Substack**: [Subscribe for updates](https://theramm.substack.com/s/essays-and-analysis)

---

*"Those who would destroy democracy depend on our ignorance. This timeline is our defense."*