#!/usr/bin/env python3
"""
In-Repo Restructuring Tool

Reorganizes the repository into two clean directory structures:
1. timeline/ - Timeline data + static viewer
2. research-server/ - Research infrastructure

Keeps old structure intact until validation passes.

Usage:
    python3 scripts/restructure_in_repo.py --dry-run    # Preview
    python3 scripts/restructure_in_repo.py              # Execute
"""

import os
import shutil
import argparse
import json
from pathlib import Path
from typing import List, Tuple, Dict

class InRepoRestructurer:
    def __init__(self, repo_root: str, dry_run: bool = False):
        self.repo_root = Path(repo_root)
        self.dry_run = dry_run

        # New directory structures
        self.timeline_dir = self.repo_root / 'timeline'
        self.research_server_dir = self.repo_root / 'research-server'

        # File mapping: (source, destination, type)
        self.timeline_copies: List[Tuple[Path, Path, str]] = []
        self.research_server_copies: List[Tuple[Path, Path, str]] = []

    def log(self, message: str, prefix: str = ""):
        """Print log message"""
        if prefix:
            print(f"{prefix} {message}")
        else:
            print(message)

    def copy_item(self, src: Path, dest: Path, item_type: str = "file") -> bool:
        """
        Copy a file or directory from src to dest

        Args:
            src: Source path (absolute)
            dest: Destination path (absolute)
            item_type: 'file' or 'directory'

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            self.log(f"{src.relative_to(self.repo_root)} -> {dest.relative_to(self.repo_root)}",
                     "[DRY-RUN]")
            return True

        try:
            # Ensure destination parent directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)

            if item_type == "directory":
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest)
                self.log(f"Copied directory: {src.relative_to(self.repo_root)}", "✓")
            else:
                shutil.copy2(src, dest)
                self.log(f"Copied file: {src.relative_to(self.repo_root)}", "✓")

            return True
        except Exception as e:
            self.log(f"Failed to copy {src}: {e}", "✗")
            return False

    def create_timeline_structure(self):
        """Create timeline/ directory structure"""
        self.log("\n" + "=" * 80)
        self.log("CREATING TIMELINE DIRECTORY STRUCTURE")
        self.log("=" * 80 + "\n")

        # Create directories
        timeline_dirs = [
            self.timeline_dir / 'data' / 'events',
            self.timeline_dir / 'viewer',
            self.timeline_dir / 'schemas',
            self.timeline_dir / 'scripts',
            self.timeline_dir / 'docs',
            self.timeline_dir / 'public' / 'api',
        ]

        for dir_path in timeline_dirs:
            if self.dry_run:
                self.log(f"Would create: {dir_path.relative_to(self.repo_root)}", "[DRY-RUN]")
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.log(f"Created: {dir_path.relative_to(self.repo_root)}", "✓")

        # Copy event files
        self.log("\nCopying timeline events...")
        events_src = self.repo_root / 'timeline_data' / 'events'
        events_dest = self.timeline_dir / 'data' / 'events'
        if events_src.exists():
            self.copy_item(events_src, events_dest, "directory")

        # Copy viewer
        self.log("\nCopying viewer...")
        viewer_src = self.repo_root / 'viewer'
        viewer_dest = self.timeline_dir / 'viewer'
        if viewer_src.exists():
            self.copy_item(viewer_src, viewer_dest, "directory")

        # Copy schemas
        self.log("\nCopying schemas...")
        schemas_src = self.repo_root / 'schemas'
        schemas_dest = self.timeline_dir / 'schemas'
        if schemas_src.exists():
            self.copy_item(schemas_src, schemas_dest, "directory")

        # Copy static API
        self.log("\nCopying static API...")
        api_src = self.repo_root / 'api' / 'static_api'
        api_dest = self.timeline_dir / 'public' / 'api'
        if api_src.exists():
            self.copy_item(api_src, api_dest, "directory")

        # Copy timeline scripts
        self.log("\nCopying timeline scripts...")
        timeline_scripts = [
            'scripts/generate_static_api.py',
            'scripts/generate.py',
            'scripts/generate_csv.py',
            'scripts/generate_yaml_export.py',
            'scripts/validate_existing_events.py',
            'scripts/fix_id_mismatches.py',
            'build_static_site.sh',
        ]

        for script_path in timeline_scripts:
            src = self.repo_root / script_path
            if src.exists():
                dest = self.timeline_dir / 'scripts' / src.name
                self.copy_item(src, dest, "file")

        # Copy script utilities
        scripts_utils_src = self.repo_root / 'scripts' / 'utils'
        scripts_utils_dest = self.timeline_dir / 'scripts' / 'utils'
        if scripts_utils_src.exists():
            self.copy_item(scripts_utils_src, scripts_utils_dest, "directory")

        # Create timeline README
        self.create_timeline_readme()

        # Create timeline package.json (if viewer has one)
        viewer_package_json = self.repo_root / 'viewer' / 'package.json'
        if viewer_package_json.exists():
            dest_package_json = self.timeline_dir / 'package.json'
            if not self.dry_run:
                # Copy and update paths
                with open(viewer_package_json, 'r') as f:
                    package_data = json.load(f)

                # Update any paths that reference old structure
                # (May need customization based on package.json contents)

                with open(dest_package_json, 'w') as f:
                    json.dump(package_data, f, indent=2)
                self.log(f"Created: {dest_package_json.relative_to(self.repo_root)}", "✓")

    def create_research_server_structure(self):
        """Create research-server/ directory structure"""
        self.log("\n" + "=" * 80)
        self.log("CREATING RESEARCH SERVER DIRECTORY STRUCTURE")
        self.log("=" * 80 + "\n")

        # Create directories
        research_dirs = [
            self.research_server_dir / 'server',
            self.research_server_dir / 'mcp',
            self.research_server_dir / 'cli',
            self.research_server_dir / 'client',
            self.research_server_dir / 'data' / 'research_priorities',
            self.research_server_dir / 'scripts' / 'agents',
            self.research_server_dir / 'alembic',
            self.research_server_dir / 'tests',
            self.research_server_dir / 'docs',
        ]

        for dir_path in research_dirs:
            if self.dry_run:
                self.log(f"Would create: {dir_path.relative_to(self.repo_root)}", "[DRY-RUN]")
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.log(f"Created: {dir_path.relative_to(self.repo_root)}", "✓")

        # Copy research_monitor → server
        self.log("\nCopying research_monitor to server...")
        research_monitor_src = self.repo_root / 'research_monitor'
        server_dest = self.research_server_dir / 'server'
        if research_monitor_src.exists():
            # Copy contents, not the directory itself
            for item in research_monitor_src.iterdir():
                if item.name not in ['__pycache__', '.pytest_cache']:
                    dest = server_dest / item.name
                    if item.is_dir():
                        self.copy_item(item, dest, "directory")
                    else:
                        self.copy_item(item, dest, "file")

        # Copy MCP server
        self.log("\nCopying MCP server...")
        mcp_src = self.repo_root / 'mcp_timeline_server_v2.py'
        mcp_dest = self.research_server_dir / 'mcp' / 'mcp_server.py'
        if mcp_src.exists():
            self.copy_item(mcp_src, mcp_dest, "file")

        # Copy CLI tools
        self.log("\nCopying CLI tools...")
        cli_files = ['research_cli.py']
        for cli_file in cli_files:
            src = self.repo_root / cli_file
            if src.exists():
                dest = self.research_server_dir / 'cli' / cli_file
                self.copy_item(src, dest, "file")

        # Copy client library
        self.log("\nCopying client library...")
        client_files = ['research_client.py', 'research_api.py']
        for client_file in client_files:
            src = self.repo_root / client_file
            if src.exists():
                dest = self.research_server_dir / 'client' / client_file
                self.copy_item(src, dest, "file")

        # Copy research priorities
        self.log("\nCopying research priorities...")
        priorities_src = self.repo_root / 'research_priorities'
        priorities_dest = self.research_server_dir / 'data' / 'research_priorities'
        if priorities_src.exists():
            self.copy_item(priorities_src, priorities_dest, "directory")

        # Copy research agent scripts
        self.log("\nCopying research agents...")
        agents_src = self.repo_root / 'scripts' / 'agents'
        agents_dest = self.research_server_dir / 'scripts' / 'agents'
        if agents_src.exists():
            self.copy_item(agents_src, agents_dest, "directory")

        # Copy alembic
        self.log("\nCopying alembic migrations...")
        alembic_src = self.repo_root / 'alembic'
        alembic_dest = self.research_server_dir / 'alembic'
        if alembic_src.exists():
            self.copy_item(alembic_src, alembic_dest, "directory")

        alembic_ini_src = self.repo_root / 'alembic.ini'
        alembic_ini_dest = self.research_server_dir / 'alembic.ini'
        if alembic_ini_src.exists():
            self.copy_item(alembic_ini_src, alembic_ini_dest, "file")

        # Copy research server tests
        self.log("\nCopying research server tests...")
        test_files = [
            'tests/test_research_api.py',
            'tests/test_research_cli.py',
            'tests/test_research_client.py',
            'tests/test_research_monitor_models.py.skip',
        ]
        for test_file in test_files:
            src = self.repo_root / test_file
            if src.exists():
                dest = self.research_server_dir / 'tests' / Path(test_file).name
                self.copy_item(src, dest, "file")

        # Create research server README
        self.create_research_server_readme()

        # Create requirements.txt
        self.create_research_server_requirements()

    def create_timeline_readme(self):
        """Create README for timeline directory"""
        readme_content = """# Kleptocracy Timeline - Timeline Data & Viewer

This directory contains the core timeline data and static viewer application.

## Quick Start

### View Timeline Locally

```bash
cd viewer
npm install
npm start
```

Open http://localhost:3000

### Generate Static API

```bash
cd scripts
python3 generate_static_api.py
```

### Validate Events

```bash
cd scripts
python3 validate_existing_events.py
```

## Directory Structure

```
timeline/
├── data/
│   └── events/              # 1,581+ timeline event JSON files
├── viewer/                  # React viewer application
├── schemas/                 # Event validation schemas
├── scripts/                 # Timeline utilities
├── public/                  # Static site output
│   └── api/                 # Generated JSON API
└── docs/                    # Timeline documentation
```

## Event Format

Events are stored in `data/events/` as JSON files:

```json
{
  "id": "YYYY-MM-DD--event-slug",
  "date": "YYYY-MM-DD",
  "title": "Event Title",
  "summary": "Detailed description",
  "importance": 8,
  "tags": ["tag1", "tag2"],
  "sources": [...]
}
```

See `schemas/timeline_event_schema.json` for complete specification.

## Deployment

The static viewer is deployed to GitHub Pages from the `public/` directory.

## License

- Data: CC0 1.0 Universal
- Code: MIT License
"""

        readme_path = self.timeline_dir / 'README.md'
        if not self.dry_run:
            with open(readme_path, 'w') as f:
                f.write(readme_content)
            self.log(f"Created: {readme_path.relative_to(self.repo_root)}", "✓")
        else:
            self.log(f"Would create: {readme_path.relative_to(self.repo_root)}", "[DRY-RUN]")

    def create_research_server_readme(self):
        """Create README for research-server directory"""
        readme_content = """# Kleptocracy Timeline - Research Server

Research infrastructure for timeline enhancement, validation, and multi-timeline support.

## Quick Start

### Start Server

```bash
cd server
RESEARCH_MONITOR_PORT=5558 python3 app_v2.py
```

### Use CLI

```bash
cd cli
python3 research_cli.py help
python3 research_cli.py search-events --query "Trump"
```

### Use Python Client

```python
from client.research_client import TimelineResearchClient

client = TimelineResearchClient()
events = client.search_events("surveillance")
```

## Directory Structure

```
research-server/
├── server/                  # Flask REST API
├── mcp/                     # MCP server for LLM integration
├── cli/                     # CLI tools
├── client/                  # Python client library
├── data/
│   └── research_priorities/ # Research priority files
├── scripts/
│   └── agents/             # Research agent scripts
├── alembic/                # Database migrations
├── tests/                  # Server tests
└── docs/                   # Research server documentation
```

## Features

- REST API for timeline event management
- MCP server for Claude Code integration
- CLI tools for research workflows
- Quality assurance system
- Multi-timeline support (planned)
- Research priority tracking

## Database

SQLite database with automatic sync from timeline event files.

## License

MIT License
"""

        readme_path = self.research_server_dir / 'README.md'
        if not self.dry_run:
            with open(readme_path, 'w') as f:
                f.write(readme_content)
            self.log(f"Created: {readme_path.relative_to(self.repo_root)}", "✓")
        else:
            self.log(f"Would create: {readme_path.relative_to(self.repo_root)}", "[DRY-RUN]")

    def create_research_server_requirements(self):
        """Create requirements.txt for research server"""
        # Copy from root if exists, otherwise create minimal
        root_requirements = self.repo_root / 'requirements.txt'
        dest_requirements = self.research_server_dir / 'requirements.txt'

        if root_requirements.exists() and not self.dry_run:
            shutil.copy2(root_requirements, dest_requirements)
            self.log(f"Copied: requirements.txt", "✓")
        elif not self.dry_run:
            # Create minimal requirements
            requirements_content = """Flask==3.0.0
Flask-CORS==4.0.0
SQLAlchemy==2.0.23
alembic==1.13.0
marshmallow==3.20.1
pytest==7.4.3
click==8.1.7
python-dateutil==2.8.2
"""
            with open(dest_requirements, 'w') as f:
                f.write(requirements_content)
            self.log(f"Created: {dest_requirements.relative_to(self.repo_root)}", "✓")
        else:
            self.log(f"Would create: requirements.txt", "[DRY-RUN]")

    def create_root_readme(self):
        """Update root README to explain new structure"""
        readme_content = """# Kleptocracy Timeline

A comprehensive timeline documenting patterns of institutional capture, regulatory capture, and kleptocracy.

## Repository Structure

This repository is organized into two main components:

### 📊 [timeline/](timeline/) - Timeline Data & Viewer
- Timeline event data (1,581+ events)
- React-based interactive viewer
- Event validation schemas
- Static API generation

**Quick start**: `cd timeline/viewer && npm install && npm start`

### 🔬 [research-server/](research-server/) - Research Infrastructure
- REST API for event management
- MCP server for AI integration
- CLI tools for research workflows
- Quality assurance system
- Research priority tracking

**Quick start**: `cd research-server/server && python3 app_v2.py`

## Documentation

- [Timeline Documentation](timeline/docs/)
- [Research Server Documentation](research-server/docs/)
- [Full Documentation](docs/)

## License

- Timeline Data: CC0 1.0 Universal (Public Domain)
- Code: MIT License

## About

This timeline serves as empirical documentation for patterns of institutional capture spanning 50+ years. It is designed to support both academic research and public awareness.

For questions or contributions, see [CONTRIBUTING.md](CONTRIBUTING.md).
"""

        readme_path = self.repo_root / 'README.md'
        if not self.dry_run:
            # Backup existing README
            if readme_path.exists():
                backup_path = self.repo_root / 'README.md.backup'
                shutil.copy2(readme_path, backup_path)
                self.log(f"Backed up: README.md -> README.md.backup", "✓")

            with open(readme_path, 'w') as f:
                f.write(readme_content)
            self.log(f"Updated: README.md", "✓")
        else:
            self.log(f"Would update: README.md", "[DRY-RUN]")

    def restructure(self):
        """Execute full restructuring"""
        self.log("=" * 80)
        self.log("IN-REPO RESTRUCTURING")
        self.log("=" * 80)
        self.log(f"Repository: {self.repo_root}")
        self.log(f"Mode: {'DRY-RUN' if self.dry_run else 'EXECUTE'}")
        self.log("")

        if self.dry_run:
            self.log("*** DRY-RUN MODE - No files will be modified ***\n")

        # Create timeline structure
        self.create_timeline_structure()

        # Create research server structure
        self.create_research_server_structure()

        # Update root README
        self.log("\n" + "=" * 80)
        self.log("UPDATING ROOT README")
        self.log("=" * 80 + "\n")
        self.create_root_readme()

        # Summary
        self.log("\n" + "=" * 80)
        self.log("RESTRUCTURING SUMMARY")
        self.log("=" * 80 + "\n")
        self.log(f"Timeline directory: {self.timeline_dir}")
        self.log(f"Research server directory: {self.research_server_dir}")
        self.log("")

        if self.dry_run:
            self.log("*** DRY-RUN MODE ***")
            self.log("To execute restructuring, run without --dry-run flag")
        else:
            self.log("✓ Restructuring complete!")
            self.log("")
            self.log("Next steps:")
            self.log("1. Test timeline viewer: cd timeline/viewer && npm install && npm start")
            self.log("2. Test research server: cd research-server/server && python3 app_v2.py")
            self.log("3. Update import paths if needed")
            self.log("4. Run tests to validate both sides")
            self.log("5. Update GitHub Actions workflows")
            self.log("6. Once validated, can remove old directory structure")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Reorganize repository into timeline/ and research-server/ directories'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without executing'
    )
    args = parser.parse_args()

    # Get repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    # Create restructurer
    restructurer = InRepoRestructurer(str(repo_root), dry_run=args.dry_run)

    # Execute restructuring
    restructurer.restructure()


if __name__ == '__main__':
    main()
