# Kleptocracy Timeline

An open-source, collaborative timeline documenting democratic erosion and kleptocratic capture in the United States (1970-present).

**📊 Current Status: 753 documented events**

**🌐 View the timeline: [https://markramm.github.io/KleptocracyTimeline/](https://markramm.github.io/KleptocracyTimeline/)**

## 🎯 Purpose

This repository provides a factual, verified, and archived timeline of events showing patterns of institutional capture, democratic backsliding, and systemic corruption. Every event is:

- 📅 **Dated** - Specific dates, no speculation
- 📋 **Documented** - Multiple sources required  
- 🔒 **Archived** - Protected against link rot
- ✅ **Verified** - Community-reviewed for accuracy
- 🔍 **Neutral** - Facts only, no editorializing

## 🚀 Quick Start

### Development Setup

See [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for detailed setup instructions including:
- Python virtual environment setup
- Installing dependencies
- Running tests
- Troubleshooting

### YAML Management Tools

The project includes powerful YAML management tools for working with timeline events:

```bash
# Search for events
python yaml_tools.py search "keyword" --date-from 2024-01-01 --date-to 2024-12-31

# Validate events
python yaml_tools.py validate  # All files
python yaml_tools.py validate timeline_data/events/specific-event.yaml

# Manage sources
python yaml_tools.py sources timeline_data/events/event.yaml --action validate
python yaml_tools.py sources timeline_data/events/event.yaml --action check-urls

# Edit events (with automatic backup and validation)
python yaml_tools.py edit timeline_data/events/event.yaml --field importance --value 8
```

See `yaml_tools.py --help` for full documentation.

### View the Timeline

**Option 1: React App (Full Interactive Experience)**
```bash
# Setup virtual environment first (see DEVELOPMENT_SETUP.md)
source venv/bin/activate

# Terminal 1: Start the API server
python api/server.py
# Runs on http://localhost:5000

# Terminal 2: Start the React app  
cd viewer && npm install && npm start
# Opens at http://localhost:3000
```

**Option 2: Enhanced Server (Simple Browsing)**
```bash
source venv/bin/activate
python api/enhanced_server.py
# Visit http://localhost:8080
```

### Validate Events (NEW!)

**Community Validation Tool**
```bash
# Start the validation interface
cd timeline_data && python3 validation_app_enhanced.py
# Visit http://localhost:8082
```

This tool allows you to:
- ✅ Verify each event against its sources
- 🔍 Check if sources are still accessible
- 📁 Cache sources locally to prevent link rot
- 🗄️ Submit sources to Archive.org
- 📊 Track validation progress

### Add an Event

1. Fork this repository
2. Create a new YAML file in `timeline_data/events/`
3. Follow the schema in [`timeline_data/README.md`](timeline_data/README.md)
4. Submit a pull request

## ✅ Community Validation Initiative

**Help us verify every event!** We've built tools to make validation easy:

### How to Validate

1. **Start the validation tool**:
   ```bash
   cd timeline_data
   python3 validation_app_enhanced.py
   # Open http://localhost:8082
   ```

2. **Pick an event** - Filter by "Not Validated" to find events needing review

3. **Check each source**:
   - Click "View Live" to open the source
   - Verify it confirms the event's key claims
   - Use "Check Status" to see if sources are accessible
   - "Scrape" sources locally to prevent link rot
   - "Archive" to submit to Archive.org

4. **Mark as validated** once all sources check out

### Validation Features

- 🌐 **Click-through verification** - Direct links to all sources
- 📊 **Progress tracking** - See validation statistics in real-time
- 📁 **Local caching** - Scrape sources to `.sources/` folder
- 🗄️ **Archive.org integration** - Preserve sources permanently
- 🎚️ **Smart filters** - Find events by validation status or importance
- 💾 **Persistent tracking** - Your work is saved in `validation_status.json`

### Why This Matters

Independent verification by multiple community members:
- Ensures accuracy of the historical record
- Protects against misinformation
- Creates redundant source preservation
- Builds trust through transparency

## 📊 Statistics

- **Events**: 399 documented incidents
- **Date Range**: 1970-2025
- **Sources**: 1,251 verified sources
- **Validation Progress**: Community validation in progress
- **Archive Coverage**: 21.6% protection against link rot
- **Tags**: 1,094 unique categorizations

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

📖 **Have questions?** Check our [FAQ.md](FAQ.md) for common questions about the project, data, contributing, and technical details.

### 🔍 Help Validate Events!

**Easy way to contribute**: Help validate existing events!

1. Run the validation tool: `cd timeline_data && python3 validation_app_enhanced.py`
2. Pick any unvalidated event
3. Click through to each source
4. Verify the source confirms the event's claims
5. Mark as validated if all sources check out

Your validation work is tracked in `validation_status.json` and helps ensure accuracy.

### ⚠️ IMPORTANT: Naming Convention
**All event IDs and filenames must use HYPHENS (-) only. NO UNDERSCORES (_) allowed.**

Example: `2024-01-15--trump-cabinet-wealth.yaml` ✅
NOT: `2024-01-15--trump_cabinet_wealth.yaml` ❌

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
│   ├── events/         # 395+ YAML event files
│   │   └── .sources/   # Locally cached source HTML
│   ├── static/         # CSS/JS for validation app
│   ├── reports/        # Validation reports
│   ├── validation_status.json  # Community validation tracking
│   ├── validation_app_enhanced.py  # Web validation interface
│   ├── README.md       # Event schema documentation
│   └── AGENT.md        # AI/verification guidance
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

### Interactive Validation Tool (NEW!)
- `validation_app_enhanced.py` - Web interface for community validation
  - View all events with their sources
  - Click through to verify each source
  - Track validation progress
  - Scrape and archive sources
  - Filter by validation status

### Validation Scripts
- `validate_timeline_dates.py` - Check for future-dated confirmed events
- `check_whitespace.py` - Code quality checks
- `fix_timeline_ids.py` - Ensure ID/filename consistency

### Archiving
- `link_check.py` - Detect broken links
- `gen_archive_qa.py` - Archive quality assurance
- `scrape_sources.py` - Bulk scrape sources to local cache
- `archive_links_slow.py` - Submit sources to Archive.org

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

### Event Status
- **confirmed** - Multiple sources verified, date in past
- **pending** - Awaiting verification
- **predicted** - Future events based on announcements
- **disputed** - Conflicting accounts exist

### Validation Status (Community Review)
- **validated** ✅ - Sources manually checked and confirm claims
- **in_review** 🔍 - Currently being validated
- **needs_review** ⚠️ - Flagged for additional review
- **problematic** ❌ - Issues found with sources

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