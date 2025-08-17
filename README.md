# Kleptocracy Timeline

An open-source, collaborative timeline documenting democratic erosion and kleptocratic capture in the United States (1972-present).

## 🎯 Purpose

This repository provides a factual, verified, and archived timeline of events showing patterns of institutional capture, democratic backsliding, and systemic corruption. Every event is:

- 📅 **Dated** - Specific dates, no speculation
- 📋 **Documented** - Multiple sources required  
- 🔒 **Archived** - Protected against link rot
- ✅ **Verified** - Community-reviewed for accuracy
- 🔍 **Neutral** - Facts only, no editorializing

## 🚀 Quick Start

### View the Timeline

**Option 1: React App (Full Interactive Experience)**
```bash
# Terminal 1: Start the API server
cd api && python3 server.py
# Runs on http://localhost:5173

# Terminal 2: Start the React app  
cd viewer && npm install && npm start
# Opens at http://localhost:3000
```

**Option 2: Enhanced Server (Simple Browsing)**
```bash
python3 api/enhanced_server.py
# Visit http://localhost:8080
```

### Add an Event

1. Fork this repository
2. Create a new YAML file in `timeline_data/events/`
3. Follow the schema in [`timeline_data/README.md`](timeline_data/README.md)
4. Submit a pull request

## 📊 Statistics

- **Events**: 303+ documented incidents
- **Date Range**: 1972-2025
- **Sources**: 500+ verified sources
- **Archive Coverage**: 60%+ protection against link rot
- **Tags**: 548 unique categorizations

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Event criteria and standards
- Verification requirements
- Source documentation guidelines
- Archive process

### Quick Contribution Guide

Events must:
- Impact democratic institutions or norms
- Be part of documented patterns
- Have verifiable sources
- Represent systemic issues (not isolated incidents)

## 📁 Repository Structure

```
kleptocracy-timeline/
├── timeline_data/
│   ├── events/         # 303+ YAML event files
│   ├── archive/        # Archived sources (coming soon)
│   ├── reports/        # Validation reports
│   ├── README.md       # Event schema documentation
│   └── agent.md        # AI/verification guidance
├── tools/
│   ├── validation/     # Data quality tools
│   ├── archiving/      # Link rot prevention
│   └── generation/     # Index and footnote generation
├── viewer/             # React timeline visualization
├── api/               # Python API server
└── .github/
    └── workflows/     # Automated validation
```

## 🛠️ Tools Included

### Validation
- `validate_timeline_dates.py` - Check for future-dated confirmed events
- `check_whitespace.py` - Code quality checks
- `fix_timeline_ids.py` - Ensure ID/filename consistency

### Archiving
- `link_check.py` - Detect broken links
- `gen_archive_qa.py` - Archive quality assurance

### Generation
- `build_timeline_index.py` - Generate searchable JSON index
- `build_footnotes.py` - Create citations for research

## 📜 License

- **Data** (timeline events): [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/) - Share and adapt with attribution
- **Code** (tools, viewer): [MIT](LICENSE-MIT) - Use freely in your projects

## 🔗 Use Cases

This timeline can be used for:
- **Journalism** - Source for investigative reporting
- **Research** - Academic study of democratic erosion
- **Education** - Teaching about institutional capture
- **Advocacy** - Evidence for policy reform
- **Analysis** - Pattern recognition and trend analysis

## 🛡️ Preservation

All sources are being archived using:
- Internet Archive Wayback Machine
- Archive.today
- Local text extraction
- Screenshot preservation

## 🚦 Verification Status Levels

- **confirmed** - Multiple sources verified, date in past
- **pending** - Awaiting verification
- **predicted** - Future events based on announcements
- **disputed** - Conflicting accounts exist

## 🏷️ Key Pattern Tags

- `democratic-erosion` - Weakening of democratic norms
- `kleptocratic-capture` - Corruption for private gain
- `regulatory-capture` - Agencies serving special interests
- `judicial-capture` - Court system compromise
- `electoral-manipulation` - Voting/election interference
- `disinformation` - Coordinated false information
- `institutional-decay` - Breakdown of governing norms

## 📈 Getting Started with Analysis

1. **Load the data**: `python3 tools/generation/build_timeline_index.py`
2. **Search by pattern**: Events are tagged for pattern analysis
3. **Generate citations**: Use `build_footnotes.py` for your research
4. **Track changes**: Watch this repo for updates

## 🤲 Support This Project

- ⭐ Star this repository
- 🔄 Share with researchers and journalists
- 📝 Contribute events you've researched
- 🐛 Report issues or broken links
- 💬 Join discussions on verification

## 📮 Contact

- **Issues**: Use GitHub Issues for event proposals
- **Security**: Report sensitive issues privately
- **Discussion**: Use GitHub Discussions for research coordination

---

*This is a living document. The timeline grows through collaborative effort. Every contribution helps preserve the historical record.*