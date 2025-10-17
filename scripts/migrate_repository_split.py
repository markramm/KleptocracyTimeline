#!/usr/bin/env python3
"""
Repository Split Migration Tool

Creates two new repository directories from the current repository:
1. kleptocracy-timeline-core (timeline + viewer)
2. kleptocracy-timeline-research-server (research infrastructure)

Usage:
    python3 scripts/migrate_repository_split.py --dry-run    # Preview changes
    python3 scripts/migrate_repository_split.py              # Execute migration
"""

import os
import shutil
import json
import argparse
from pathlib import Path
from typing import List, Dict

class RepositoryMigrator:
    def __init__(self, repo_root: str, dry_run: bool = False):
        self.repo_root = Path(repo_root)
        self.dry_run = dry_run

        # Output directories (relative to repo_root parent)
        self.core_repo_dir = self.repo_root.parent / 'kleptocracy-timeline-core'
        self.server_repo_dir = self.repo_root.parent / 'kleptocracy-timeline-research-server'

        # Load manifests
        self.core_files = self._load_manifest('docs/core_files_manifest.json')
        self.server_files = self._load_manifest('docs/server_files_manifest.json')

    def _load_manifest(self, manifest_path: str) -> List[str]:
        """Load file list from manifest"""
        full_path = self.repo_root / manifest_path
        with open(full_path, 'r') as f:
            data = json.load(f)
            return data.get('files', [])

    def _copy_file(self, src_rel_path: str, dest_repo_dir: Path,
                   path_transforms: Dict[str, str] = None) -> bool:
        """
        Copy a file from source to destination, applying path transforms if specified

        Args:
            src_rel_path: Relative path in source repo
            dest_repo_dir: Destination repository root
            path_transforms: Dict mapping source path prefixes to destination prefixes

        Returns:
            True if copied successfully, False otherwise
        """
        src_path = self.repo_root / src_rel_path

        # Apply path transforms
        dest_rel_path = src_rel_path
        if path_transforms:
            for src_prefix, dest_prefix in path_transforms.items():
                if src_rel_path.startswith(src_prefix):
                    dest_rel_path = dest_prefix + src_rel_path[len(src_prefix):]
                    break

        dest_path = dest_repo_dir / dest_rel_path

        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if self.dry_run:
            print(f"  [DRY-RUN] Would copy: {src_rel_path} -> {dest_rel_path}")
            return True

        try:
            shutil.copy2(src_path, dest_path)
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to copy {src_rel_path}: {e}")
            return False

    def create_core_repository(self) -> Dict:
        """Create the core timeline repository"""
        print("=" * 80)
        print("CREATING KLEPTOCRACY-TIMELINE-CORE REPOSITORY")
        print("=" * 80)
        print()

        if self.dry_run:
            print(f"[DRY-RUN] Would create directory: {self.core_repo_dir}")
        else:
            self.core_repo_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {self.core_repo_dir}")
        print()

        # Copy files
        print(f"Copying {len(self.core_files)} files...")
        success_count = 0

        for file_path in self.core_files:
            if self._copy_file(file_path, self.core_repo_dir):
                success_count += 1

        print()
        print(f"Copied {success_count}/{len(self.core_files)} files successfully")

        # Create new README
        if not self.dry_run:
            self._create_core_readme()
            self._create_core_gitignore()

        return {
            'repository': 'kleptocracy-timeline-core',
            'total_files': len(self.core_files),
            'copied_files': success_count,
            'path': str(self.core_repo_dir)
        }

    def create_server_repository(self) -> Dict:
        """Create the research server repository"""
        print()
        print("=" * 80)
        print("CREATING KLEPTOCRACY-TIMELINE-RESEARCH-SERVER REPOSITORY")
        print("=" * 80)
        print()

        if self.dry_run:
            print(f"[DRY-RUN] Would create directory: {self.server_repo_dir}")
        else:
            self.server_repo_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {self.server_repo_dir}")
        print()

        # Path transforms for server repository
        # research_monitor/ -> server/
        path_transforms = {
            'research_monitor/': 'server/',
        }

        # Copy files with transforms
        print(f"Copying {len(self.server_files)} files...")
        success_count = 0

        for file_path in self.server_files:
            if self._copy_file(file_path, self.server_repo_dir, path_transforms):
                success_count += 1

        # Copy CLI/client/API to dedicated directories
        cli_files = ['research_cli.py', 'research_client.py', 'research_api.py']
        for cli_file in cli_files:
            if self._copy_file(cli_file, self.server_repo_dir):
                success_count += 1

        print()
        print(f"Copied {success_count}/{len(self.server_files) + 3} files successfully")

        # Create new README and configs
        if not self.dry_run:
            self._create_server_readme()
            self._create_server_gitignore()
            self._create_server_requirements()
            self._create_docker_config()

        return {
            'repository': 'kleptocracy-timeline-research-server',
            'total_files': len(self.server_files) + 3,
            'copied_files': success_count,
            'path': str(self.server_repo_dir)
        }

    def _create_core_readme(self):
        """Create README for core repository"""
        readme_content = """# Kleptocracy Timeline - Core Repository

A forkable timeline documenting patterns of institutional capture, regulatory capture, and kleptocracy in the United States and globally.

## What This Is

This repository contains:
- **Timeline Events**: 1,500+ documented events with sources
- **Interactive Viewer**: React-based timeline visualization
- **Event Schemas**: Validation schemas for event data quality
- **Static API**: Auto-generated JSON API for event data

## Quick Start

### View the Timeline

1. Clone this repository:
```bash
git clone https://github.com/yourusername/kleptocracy-timeline-core.git
cd kleptocracy-timeline-core
```

2. Run the viewer:
```bash
cd viewer
npm install
npm start
```

3. Open http://localhost:3000 in your browser

### Fork for Your Own Timeline

See [FORKING_GUIDE.md](docs/FORKING_GUIDE.md) for detailed instructions on creating your own domain-specific timeline.

## Repository Structure

```
kleptocracy-timeline-core/
├── timeline_data/events/    # Event JSON files (1,500+)
├── viewer/                  # React timeline viewer
├── schemas/                 # Event validation schemas
├── api/                     # Generated static API
├── scripts/                 # Utility scripts
└── docs/                    # Documentation
```

## Event Format

Events are stored as JSON files in `timeline_data/events/`:

```json
{
  "id": "YYYY-MM-DD--event-slug",
  "date": "YYYY-MM-DD",
  "title": "Event Title",
  "summary": "Detailed description with context",
  "importance": 8,
  "tags": ["tag1", "tag2"],
  "sources": [
    {
      "url": "https://example.com/article",
      "title": "Source Title",
      "publisher": "Publisher Name",
      "tier": 1
    }
  ]
}
```

See [docs/EVENT_FORMAT.md](docs/EVENT_FORMAT.md) for complete schema documentation.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Research Infrastructure

For advanced research tools including AI-powered event enhancement, multi-timeline support, and automated quality assurance, see the [Kleptocracy Timeline Research Server](https://github.com/yourusername/kleptocracy-timeline-research-server).

## License

- Event data: [CC0 1.0 Universal](LICENSE-DATA)
- Code: [MIT License](LICENSE-MIT)

## Related Projects

- **Research Server**: AI-powered research infrastructure for timeline enhancement
- **MCP Server**: Model Context Protocol server for LLM integration
- **n8n Workflows**: Automation templates for timeline research
"""

        readme_path = self.core_repo_dir / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        print(f"Created: {readme_path}")

    def _create_core_gitignore(self):
        """Create .gitignore for core repository"""
        gitignore_content = """# Dependencies
node_modules/
package-lock.json

# Build outputs
dist/
build/
viewer/build/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Python (for utility scripts)
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.mypy_cache/

# Logs
*.log
npm-debug.log*

# Generated API
api/*.json
!api/.gitkeep
"""

        gitignore_path = self.core_repo_dir / '.gitignore'
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        print(f"Created: {gitignore_path}")

    def _create_server_readme(self):
        """Create README for server repository"""
        readme_content = """# Kleptocracy Timeline - Research Server

Shared research infrastructure providing API, MCP server, CLI tools, and database services for timeline research and enhancement.

## Features

- **REST API**: Full-featured API for timeline event management
- **MCP Server**: Model Context Protocol server for LLM integration
- **CLI Tools**: Command-line interface for research workflows
- **Python Client**: Comprehensive Python library for programmatic access
- **Multi-Timeline Support**: Serve multiple timeline forks from one server
- **Quality Assurance**: Automated source validation and fact-checking
- **n8n Integration**: Pre-built workflow templates

## Quick Start

### Run with Docker (Recommended)

```bash
docker-compose up
```

Server runs at http://localhost:5558

### Run Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Run server:
```bash
cd server
python3 app.py
```

### CLI Usage

```bash
# Search events
python3 research_cli.py search-events --query "Trump"

# Get next research priority
python3 research_cli.py get-next-priority

# Validate event
python3 research_cli.py validate-event --file event.json
```

See [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md) for complete documentation.

## Architecture

```
kleptocracy-timeline-research-server/
├── server/              # Flask REST API
├── mcp/                 # MCP server
├── cli/                 # CLI tools
├── client/              # Python client library
├── docker/              # Docker configuration
├── n8n/                 # Workflow templates
└── docs/                # Documentation
```

## Timeline Registration

To connect your timeline fork to the research server:

```bash
python3 research_cli.py register-timeline \\
  --name "Supreme Court Capture" \\
  --git-url "https://github.com/username/scotus-capture-timeline" \\
  --branch "main"
```

See [docs/TIMELINE_REGISTRATION.md](docs/TIMELINE_REGISTRATION.md) for details.

## n8n Integration

Import pre-built workflows from `n8n/workflows/`:

1. Open n8n
2. Import workflow JSON
3. Configure credentials
4. Activate workflow

See [docs/N8N_INTEGRATION.md](docs/N8N_INTEGRATION.md) for examples.

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment guide.

## License

[MIT License](LICENSE)

## Related Projects

- **Core Timeline**: Forkable timeline + viewer repository
"""

        readme_path = self.server_repo_dir / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        print(f"Created: {readme_path}")

    def _create_server_gitignore(self):
        """Create .gitignore for server repository"""
        gitignore_content = """# Environment
.env
.env.local
.env.*.local

# Database
*.db
*.db-wal
*.db-shm
*.sqlite
*.sqlite3

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.pytest_cache/
.mypy_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Uploads
uploads/

# Docker
.dockerignore
docker-compose.override.yml

# Generated
*.pyc
__pycache__/
"""

        gitignore_path = self.server_repo_dir / '.gitignore'
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        print(f"Created: {gitignore_path}")

    def _create_server_requirements(self):
        """Create requirements.txt for server"""
        requirements_content = """# Flask web framework
Flask==3.0.0
Flask-CORS==4.0.0

# Database
SQLAlchemy==2.0.23
alembic==1.13.0

# API utilities
marshmallow==3.20.1

# MCP server
anthropic-mcp==0.1.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0

# Code quality
pylint==3.0.3
mypy==1.7.1

# CLI utilities
click==8.1.7

# Date/time
python-dateutil==2.8.2
"""

        requirements_path = self.server_repo_dir / 'requirements.txt'
        with open(requirements_path, 'w') as f:
            f.write(requirements_content)
        print(f"Created: {requirements_path}")

    def _create_docker_config(self):
        """Create Docker configuration"""
        dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY server/ ./server/
COPY mcp/ ./mcp/
COPY research_cli.py .
COPY research_client.py .
COPY research_api.py .

# Expose port
EXPOSE 5558

# Run server
CMD ["python3", "server/app.py"]
"""

        docker_compose_content = """version: '3.8'

services:
  server:
    build: .
    ports:
      - "5558:5558"
    environment:
      - RESEARCH_MONITOR_PORT=5558
      - DATABASE_URL=sqlite:///unified_research.db
    volumes:
      - ./data:/app/data
      - ./unified_research.db:/app/unified_research.db
    restart: unless-stopped
"""

        docker_dir = self.server_repo_dir / 'docker'
        docker_dir.mkdir(parents=True, exist_ok=True)

        dockerfile_path = docker_dir / 'Dockerfile'
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        print(f"Created: {dockerfile_path}")

        compose_path = docker_dir / 'docker-compose.yml'
        with open(compose_path, 'w') as f:
            f.write(docker_compose_content)
        print(f"Created: {compose_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Migrate repository to split structure'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without executing'
    )
    parser.add_argument(
        '--core-only',
        action='store_true',
        help='Only create core repository'
    )
    parser.add_argument(
        '--server-only',
        action='store_true',
        help='Only create server repository'
    )
    args = parser.parse_args()

    # Get repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    print("=" * 80)
    print("REPOSITORY SPLIT MIGRATION")
    print("=" * 80)
    print()
    print(f"Source repository: {repo_root}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'EXECUTE'}")
    print()

    if args.dry_run:
        print("*** DRY-RUN MODE ***")
        print("No files will be copied or modified")
        print()

    # Create migrator
    migrator = RepositoryMigrator(str(repo_root), dry_run=args.dry_run)

    results = {}

    # Create repositories
    if not args.server_only:
        results['core'] = migrator.create_core_repository()

    if not args.core_only:
        results['server'] = migrator.create_server_repository()

    # Print summary
    print()
    print("=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print()

    for repo_name, result in results.items():
        print(f"{result['repository']}:")
        print(f"  Files copied: {result['copied_files']}/{result['total_files']}")
        print(f"  Location: {result['path']}")
        print()

    if args.dry_run:
        print("*** DRY-RUN MODE ***")
        print("To execute migration, run without --dry-run flag")
    else:
        print("Migration complete!")
        print()
        print("Next steps:")
        print("1. Review generated repositories")
        print("2. Initialize git repositories:")
        for repo_name, result in results.items():
            print(f"   cd {result['path']} && git init")
        print("3. Test functionality in both repositories")
        print("4. Push to GitHub when ready")


if __name__ == '__main__':
    main()
