# Deprecated Tests

Tests in this directory are for modules that have been refactored or removed.
They are kept for reference but not executed in the test suite.

## Files

### test_research_api.py
- **Old module**: `research_api.py` with `ResearchAPI` class
- **Replaced by**: Unified CLI in `cli/research_cli.py`
- **Reason**: Old API wrapper was redundant with TimelineResearchClient
- **Date deprecated**: October 2025

### test_research_cli.py
- **Old module**: `research_cli.py` with `ResearchCLIWrapper` class
- **Replaced by**: Direct CLI implementation in `cli/research_cli.py`
- **Reason**: CLI wrapper was unnecessary abstraction layer
- **Date deprecated**: October 2025

### test_research_client.py
- **Old module**: `research_client.py` with `TimelineResearchClient` class
- **Current module**: `server/research_client.py` with `ResearchMonitorClient`
- **Reason**: Module was renamed and class refactored during SPEC-007 reorganization
- **Date deprecated**: October 2025

## Migration Path

If these modules are needed again:

1. Update class names to match current implementation:
   - `TimelineResearchClient` → `ResearchMonitorClient`
   - `ResearchAPI` → Use direct API calls or CLI
   - `ResearchCLIWrapper` → Use `cli/research_cli.py` directly

2. Update import paths to new structure:
   - `from research_client import TimelineResearchClient` → `from server.research_client import ResearchMonitorClient`
   - Add proper sys.path setup for test imports

3. Update test expectations for new API structure

4. Move back to `tests/` directory and run pytest to verify

## Testing Current Functionality

The current equivalents are tested in:
- Integration tests: `tests/integration/test_integration.py`
- CLI tests: Can be tested via bash commands or create new `test_cli_integration.py`
- Client tests: Test `ResearchMonitorClient` via API integration tests

## Removal Timeline

These files may be removed permanently in a future cleanup (estimated Q1 2026).
