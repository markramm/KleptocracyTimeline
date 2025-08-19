# Timeline Scripts

Consolidated and refactored scripts for managing the kleptocracy timeline.

## Quick Start

All timeline operations are now available through a single command:

```bash
# Main timeline command
python3 scripts/timeline.py <command> [options]

# Or make it executable
chmod +x scripts/timeline.py
./scripts/timeline.py <command> [options]
```

## Available Commands

### 🔍 Validate
Check all event files for errors and consistency:
```bash
# Basic validation
python3 scripts/timeline.py validate

# Show warnings too
python3 scripts/timeline.py validate --verbose

# Auto-fix simple issues (coming soon)
python3 scripts/timeline.py validate --fix
```

### 📦 Archive
Archive sources to Archive.org to prevent link rot:
```bash
# Archive all sources
python3 scripts/timeline.py archive

# Check archive coverage only
python3 scripts/timeline.py archive --check-coverage

# Retry failed URLs
python3 scripts/timeline.py archive --retry-failed

# Use custom rate limit
python3 scripts/timeline.py archive --rate 5
```

### 🏗️ Generate
Generate various outputs from timeline events:
```bash
# Generate everything
python3 scripts/timeline.py generate --all

# Generate specific outputs
python3 scripts/timeline.py generate --index        # Timeline index
python3 scripts/timeline.py generate --api          # Static API files
python3 scripts/timeline.py generate --citations md # Citations (md/json/html)
python3 scripts/timeline.py generate --stats        # Statistics report
```

### ✅ Quality Assurance
Run comprehensive QA checks:
```bash
python3 scripts/timeline.py qa
```

### 🚀 Serve
Start the development server:
```bash
# API server only
python3 scripts/timeline.py serve

# API server + React viewer
python3 scripts/timeline.py serve --viewer
```

## Individual Scripts

You can also run scripts directly for more control:

### validate.py
```bash
python3 scripts/validate.py [--verbose] [--check-links] [--fix]
```
- Validates event schema
- Checks date consistency
- Verifies source URLs
- Ensures filename format

### archive.py
```bash
python3 scripts/archive.py [--retry-failed] [--check-coverage] [--rate N]
```
- Archives to Archive.org
- Respects rate limits
- Tracks progress
- Handles interruptions gracefully

### generate.py
```bash
python3 scripts/generate.py [--all] [--index] [--api] [--citations FORMAT] [--stats]
```
- Generates timeline_index.json
- Creates static API files
- Produces citations in multiple formats
- Generates statistics reports

## Utilities

The `utils/` directory contains shared functionality:

### utils/io.py
- `load_yaml_file()` - Load YAML files
- `save_json_file()` - Save JSON files
- `get_event_files()` - Get all event files
- `load_event()` - Load single event with error handling

### utils/validation.py
- `validate_date()` - Validate date strings
- `validate_url()` - Validate URLs
- `validate_event_schema()` - Full schema validation
- `validate_sources()` - Validate source requirements

### utils/archive.py
- `RateLimiter` - Handle API rate limiting
- `check_archive_exists()` - Check if URL is archived
- `archive_url()` - Archive a URL
- `extract_urls_from_event()` - Get URLs from event

### utils/logging.py
- `setup_logger()` - Configure logging
- `log_info/warning/error/success()` - Convenience functions
- `print_header()` - Formatted headers
- `print_summary()` - Statistics display
- `progress_bar()` - Progress indicators

## Configuration

Most scripts accept these common arguments:
- `--events-dir PATH` - Events directory (default: timeline_data/events)
- `--output-dir PATH` - Output directory (default: timeline_data)
- `--verbose` - Enable detailed output
- `--help` - Show help message

## Examples

### Daily Workflow
```bash
# 1. Validate new events
python3 scripts/timeline.py validate --verbose

# 2. Generate outputs
python3 scripts/timeline.py generate --all

# 3. Archive new sources
python3 scripts/timeline.py archive

# 4. Run QA checks
python3 scripts/timeline.py qa
```

### Development
```bash
# Start servers for local development
python3 scripts/timeline.py serve --viewer

# In another terminal, make changes and regenerate
python3 scripts/timeline.py generate --index --api
```

### Maintenance
```bash
# Check archive coverage
python3 scripts/timeline.py archive --check-coverage

# Retry failed archives
python3 scripts/timeline.py archive --retry-failed

# Full validation
python3 scripts/timeline.py validate --verbose --check-links
```

## Migration from Old Scripts

| Old Script | New Command |
|------------|-------------|
| `tools/validation/validate_timeline_dates.py` | `scripts/validate.py` |
| `tools/archiving/archive_with_progress.py` | `scripts/archive.py` |
| `tools/generation/build_timeline_index.py` | `scripts/generate.py --index` |
| `tools/generation/build_footnotes.py` | `scripts/generate.py --citations` |
| `tools/qa/timeline_qa_system.py` | `scripts/timeline.py qa` |

## Requirements

- Python 3.8+
- PyYAML
- requests
- See requirements.txt for full list

## Contributing

When adding new functionality:
1. Add shared utilities to `utils/` modules
2. Create focused script if needed
3. Integrate into `timeline.py` main command
4. Update this README
5. Add tests (coming soon)

## License

MIT - See LICENSE file