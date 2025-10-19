# Kleptocracy Timeline

A comprehensive timeline documenting patterns of institutional capture, regulatory capture, and kleptocracy across 50+ years with 1,580+ verified events.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/kleptocracy-timeline.git
cd kleptocracy-timeline

# Start the research server
./research server-start

# Verify it's working
./research get-stats
```

See [INSTALLATION.md](INSTALLATION.md) for detailed setup instructions.

## Repository Structure

This repository is organized into two main components:

### 📊 [timeline/](timeline/) - Timeline Data & Viewer
- **1,580+ verified events** from 1970-2025
- React-based interactive viewer
- Dual-format support (JSON + Markdown)
- Event validation schemas
- Static API generation

**Quick start**: `cd timeline/viewer && npm install && npm start`

### 🔬 [research-server/](research-server/) - Research Infrastructure
- REST API for event management (Flask)
- **CLI wrapper** for simplified usage
- MCP server for AI agent integration
- **Validation runs system** for parallel QA processing
- Quality assurance & research priority tracking

**Quick start**: `./research server-start`

## Key Features

### Timeline System
- **1,580+ Events**: Verified events spanning 1970-2025
- **Dual Format**: JSON and Markdown support
- **Rich Metadata**: Sources, actors, tags, importance scores
- **Interactive Viewer**: React-based web interface

### Research Infrastructure
- **Validation Runs**: Parallel QA processing with unique event distribution
- **CLI Wrapper**: Simple `./research <command>` interface
- **Event Search**: Full-text search across all events
- **Quality Assurance**: Automated source quality checking
- **MCP Integration**: AI agent support via Model Context Protocol

## Documentation

### Getting Started
- **[INSTALLATION.md](INSTALLATION.md)** - Complete setup guide
- **[CLAUDE.md](CLAUDE.md)** - CLI command reference for AI agents
- **[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)** - Maintenance & cleanup guide

### Component Documentation
- [Timeline Documentation](timeline/docs/)
- [Research Server API](research-server/server/API_DOCUMENTATION.md)
- [Architecture Overview](research-server/server/ARCHITECTURE.md)

## Command-Line Interface

The research server includes a convenient CLI wrapper:

```bash
# Server management
./research server-start
./research server-status
./research server-stop

# Event operations
./research search-events --query "Trump crypto"
./research get-stats
./research list-tags

# Validation runs (QA system)
./research validation-runs-create --run-type source_quality --target-count 20
./research validation-runs-next --run-id 1 --validator-id "agent-1"
./research validation-runs-complete --run-id 1 --run-event-id 1 --status validated

# Help
./research help
```

See [CLAUDE.md](CLAUDE.md) for complete command reference.

## License

- Timeline Data: CC0 1.0 Universal (Public Domain)
- Code: MIT License

## About

This timeline serves as empirical documentation for patterns of institutional capture spanning 50+ years. It is designed to support both academic research and public awareness.

For questions or contributions, see [CONTRIBUTING.md](CONTRIBUTING.md).
