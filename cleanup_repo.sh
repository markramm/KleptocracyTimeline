#!/bin/bash

# Repository Cleanup Script
# This script helps reorganize the repository structure

set -e  # Exit on error

echo "🧹 Kleptocracy Timeline Repository Cleanup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to create directory structure
create_structure() {
    echo -e "${BLUE}📁 Creating new directory structure...${NC}"
    
    # Create docs subdirectories
    mkdir -p docs/user
    mkdir -p docs/development  
    mkdir -p docs/maintenance
    
    # Create scripts subdirectories
    mkdir -p scripts/generation
    mkdir -p scripts/validation
    mkdir -p scripts/maintenance
    
    # Create tests subdirectories
    mkdir -p tests/unit
    mkdir -p tests/integration
    mkdir -p tests/scripts
    
    echo -e "${GREEN}✅ Directory structure created${NC}"
}

# Function to move documentation files
move_docs() {
    echo -e "${BLUE}📄 Organizing documentation...${NC}"
    
    # User-facing docs
    [ -f "FAQ.md" ] && git mv FAQ.md docs/user/ 2>/dev/null || true
    [ -f "DEPLOYMENT.md" ] && git mv DEPLOYMENT.md docs/user/ 2>/dev/null || true
    [ -f "GITHUB_PAGES_SETUP.md" ] && git mv GITHUB_PAGES_SETUP.md docs/user/ 2>/dev/null || true
    
    # Development docs
    [ -f "DEVELOPMENT_SETUP.md" ] && git mv DEVELOPMENT_SETUP.md docs/development/ 2>/dev/null || true
    [ -f "TESTING.md" ] && git mv TESTING.md docs/development/ 2>/dev/null || true
    [ -f "AI_COLLABORATION_GUIDE.md" ] && git mv AI_COLLABORATION_GUIDE.md docs/development/ 2>/dev/null || true
    [ -f "AI_INTEGRATION.md" ] && git mv AI_INTEGRATION.md docs/development/ 2>/dev/null || true
    [ -f "CLAUDE_CODE_TUTORIAL.md" ] && git mv CLAUDE_CODE_TUTORIAL.md docs/development/ 2>/dev/null || true
    [ -f "PROJECT_STRUCTURE.md" ] && git mv PROJECT_STRUCTURE.md docs/development/ 2>/dev/null || true
    [ -f "AGENT.md" ] && git mv AGENT.md docs/development/ 2>/dev/null || true
    
    # Maintenance docs
    [ -f "REPO_HYGIENE.md" ] && git mv REPO_HYGIENE.md docs/maintenance/ 2>/dev/null || true
    [ -f "LAUNCH_CHECKLIST.md" ] && git mv LAUNCH_CHECKLIST.md docs/maintenance/ 2>/dev/null || true
    [ -f "RESPONSE_TEMPLATES.md" ] && git mv RESPONSE_TEMPLATES.md docs/maintenance/ 2>/dev/null || true
    [ -f "PUSH_INSTRUCTIONS.md" ] && git mv PUSH_INSTRUCTIONS.md docs/maintenance/ 2>/dev/null || true
    
    # Remove outdated docs (preserved in git history)
    [ -f "README_PUBLIC.md" ] && git rm README_PUBLIC.md 2>/dev/null || true
    [ -f "PROJECT_STATUS.md" ] && git rm PROJECT_STATUS.md 2>/dev/null || true
    [ -f "PROJECT_HEALTH.md" ] && git rm PROJECT_HEALTH.md 2>/dev/null || true
    [ -f "PROJECT_STATS.md" ] && git rm PROJECT_STATS.md 2>/dev/null || true
    [ -f "PROJECT_EVALUATION.md" ] && git rm PROJECT_EVALUATION.md 2>/dev/null || true
    [ -f "LAUNCH_READY.md" ] && git rm LAUNCH_READY.md 2>/dev/null || true
    [ -f "INITIAL_COMMIT.md" ] && git rm INITIAL_COMMIT.md 2>/dev/null || true
    [ -f "GITHUB_INTEGRATION.md" ] && git rm GITHUB_INTEGRATION.md 2>/dev/null || true
    [ -f "TOOLS_README.md" ] && git rm TOOLS_README.md 2>/dev/null || true
    [ -f "CODE_OF_CONDUCT.md" ] && git rm CODE_OF_CONDUCT.md 2>/dev/null || true
    
    echo -e "${GREEN}✅ Documentation organized${NC}"
}

# Function to move test scripts
move_tests() {
    echo -e "${BLUE}🧪 Organizing test files...${NC}"
    
    # Move test scripts from root
    [ -f "test_yaml_tools.py" ] && git mv test_yaml_tools.py tests/ 2>/dev/null || true
    [ -f "pre_launch_check.sh" ] && git mv pre_launch_check.sh tests/scripts/ 2>/dev/null || true
    [ -f "test_static_site.sh" ] && git mv test_static_site.sh tests/scripts/ 2>/dev/null || true
    
    # Move test script from tools
    [ -f "tools/test-before-commit.sh" ] && git mv tools/test-before-commit.sh tests/scripts/ 2>/dev/null || true
    
    echo -e "${GREEN}✅ Test files organized${NC}"
}

# Function to consolidate scripts
consolidate_scripts() {
    echo -e "${BLUE}🔧 Consolidating scripts...${NC}"
    
    # Move generation scripts
    if [ -f "timeline_data/generate_static_api.py" ]; then
        cp timeline_data/generate_static_api.py scripts/generation/
        echo "  Copied generate_static_api.py to scripts/generation/"
    fi
    
    # Keep only the latest version of duplicate scripts
    if [ -f "scripts/generate_csv_v2.py" ]; then
        git mv scripts/generate_csv_v2.py scripts/generation/generate_csv.py 2>/dev/null || true
        [ -f "scripts/generate_csv.py" ] && git rm scripts/generate_csv.py 2>/dev/null || true
    fi
    
    if [ -f "scripts/find_duplicates_v2.py" ]; then
        git mv scripts/find_duplicates_v2.py scripts/maintenance/find_duplicates.py 2>/dev/null || true
        [ -f "scripts/find_duplicates.py" ] && git rm scripts/find_duplicates.py 2>/dev/null || true
    fi
    
    if [ -f "scripts/analyze_sources_v2.py" ]; then
        git mv scripts/analyze_sources_v2.py scripts/maintenance/analyze_sources.py 2>/dev/null || true
        [ -f "scripts/analyze_sources.py" ] && git rm scripts/analyze_sources.py 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Scripts consolidated${NC}"
}

# Function to update README
update_readme() {
    echo -e "${BLUE}📝 Creating updated README...${NC}"
    
    cat > README_NEW.md << 'EOF'
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
EOF
    
    echo -e "${GREEN}✅ New README created as README_NEW.md${NC}"
    echo -e "${YELLOW}   Review and rename to README.md when ready${NC}"
}

# Main execution
echo "This script will reorganize the repository structure."
echo "It uses 'git mv' to preserve history."
echo ""
read -p "Do you want to proceed? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    create_structure
    move_docs
    move_tests
    consolidate_scripts
    update_readme
    
    echo ""
    echo -e "${GREEN}✨ Cleanup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review changes with 'git status'"
    echo "2. Update any broken imports/references"
    echo "3. Test that everything still works"
    echo "4. Commit changes when ready"
    echo ""
    echo -e "${YELLOW}Note: Removed files are preserved in git history${NC}"
    echo -e "${YELLOW}      Use 'git log --follow <filename>' to see history${NC}"
    echo -e "${YELLOW}      Use 'git checkout <commit> <filename>' to recover if needed${NC}"
else
    echo -e "${RED}Cleanup cancelled${NC}"
fi