# Kleptocracy Timeline

[![CI/CD Pipeline](https://github.com/markramm/KleptocracyTimeline/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/markramm/KleptocracyTimeline/actions)
[![Timeline Events](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmarkramm%2FKleptocracyTimeline%2Fmain%2Fviewer%2Fpublic%2Fapi%2Fstats.json&query=%24.total_events&label=Timeline%20Events&color=blue)](https://markramm.github.io/KleptocracyTimeline/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
1. Run validation: `cd timeline_data && python validation_app_enhanced.py`
2. Pick any unvalidated event
3. Verify sources confirm the claims
4. Mark as validated if accurate

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

## 📜 License

MIT License - See [LICENSE](LICENSE) file

## 🙏 Acknowledgments

This project relies on the work of journalists, researchers, and citizens who document threats to democracy.

## 📮 Contact

- **Issues**: [GitHub Issues](https://github.com/markramm/KleptocracyTimeline/issues)
- **Discussions**: [GitHub Discussions](https://github.com/markramm/KleptocracyTimeline/discussions)

---

*"Those who would destroy democracy depend on our ignorance. This timeline is our defense."*
