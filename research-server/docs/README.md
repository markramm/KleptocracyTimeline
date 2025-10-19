# Research Server Documentation

## Getting Started
- [Installation Guide](../../INSTALLATION.md)
- [Quick Start](../README.md)

## API Reference
- [REST API](API.md) - Complete API endpoint reference
- [CLI Tool](../../CLAUDE.md) - Command-line interface guide (see research-server section)

## Architecture & Development
- [System Architecture](ARCHITECTURE.md) - Design overview and data flow

## Additional Resources
- [Root Documentation](../../README.md)
- [Release Checklist](../../RELEASE_CHECKLIST.md)
- [Architecture Review](../../ARCHITECTURE_REVIEW.md)
- [Improvements Summary](../../IMPROVEMENTS_SUMMARY.md)

## Quick Links

### API Endpoints
See [API.md](API.md) for complete reference.

### CLI Commands
```bash
# Server management
./research server-start
./research server-status
./research server-stop

# Event operations
./research search-events --query "Trump"
./research get-stats

# Validation runs
./research validation-runs-create --run-type source_quality --target-count 20
```

See [CLAUDE.md](../../CLAUDE.md) for complete CLI reference.

### Architecture Diagrams
See [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture diagrams and data flow.
