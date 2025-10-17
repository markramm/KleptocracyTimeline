#!/usr/bin/env python3
"""
Repository Split Analysis Tool

Analyzes the current repository and generates detailed file lists for:
1. kleptocracy-timeline-core (timeline + viewer)
2. kleptocracy-timeline-research-server (research infrastructure)

Based on: docs/REPOSITORY_SPLIT_MANIFEST.md
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

class RepositorySplitAnalyzer:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.core_files: List[Path] = []
        self.server_files: List[Path] = []
        self.undecided_files: List[Path] = []
        self.excluded_files: List[Path] = []

        # Directories to completely skip
        self.skip_dirs = {
            '.git', '__pycache__', '.pytest_cache', '.mypy_cache',
            'node_modules', 'venv', 'htmlcov', 'coverage_html',
            '.claude', '.specify', 'tmp'
        }

        # File patterns to exclude
        self.exclude_patterns = {
            '.pyc', '.pyo', '.coverage', '.DS_Store',
            '.log', '.swp', '.swo'
        }

    def should_skip(self, path: Path) -> bool:
        """Check if a path should be skipped entirely"""
        # Skip if any parent directory is in skip_dirs
        for part in path.parts:
            if part in self.skip_dirs:
                return True

        # Skip if file matches exclude patterns
        if any(path.name.endswith(pattern) for pattern in self.exclude_patterns):
            return True

        return False

    def categorize_file(self, rel_path: Path) -> str:
        """
        Categorize a file as 'core', 'server', 'undecided', or 'exclude'

        Returns: 'core' | 'server' | 'undecided' | 'exclude'
        """
        path_str = str(rel_path)
        parts = rel_path.parts

        # === CORE TIMELINE FILES ===

        # Timeline events (authoritative source)
        if 'timeline_data' in parts and 'events' in parts and path_str.endswith('.json'):
            return 'core'

        # Viewer (entire React app)
        if parts[0] == 'viewer':
            return 'core'

        # Schemas (validation)
        if parts[0] == 'schemas':
            return 'core'

        # Static API files
        if parts[0] == 'api' and not path_str.endswith('.py'):
            return 'core'

        # Core scripts
        core_scripts = {
            'generate.py', 'generate_csv.py', 'generate_yaml_export.py',
            'validate_existing_events.py', 'fix_id_mismatches.py'
        }
        if parts[0] == 'scripts' and rel_path.name in core_scripts:
            return 'core'

        # Core script utilities
        if parts[0] == 'scripts' and 'utils' in parts:
            if rel_path.name in {'events.py', 'io.py', 'logging.py'}:
                return 'core'

        # Build script for viewer
        if rel_path.name == 'build_static_site.sh':
            return 'core'

        # === RESEARCH SERVER FILES ===

        # Research monitor (entire Flask app)
        if parts[0] == 'research_monitor':
            return 'server'

        # Research priorities (metadata, not events)
        if parts[0] == 'research_priorities':
            return 'server'

        # Research CLI, client, API
        if rel_path.name in {'research_cli.py', 'research_client.py', 'research_api.py'}:
            return 'server'

        # MCP server (v2 only)
        if rel_path.name == 'mcp_timeline_server_v2.py':
            return 'server'

        # Alembic (database migrations)
        if parts[0] == 'alembic' or rel_path.name == 'alembic.ini':
            return 'server'

        # Research agent scripts
        if parts[0] == 'scripts' and 'agents' in parts:
            return 'server'

        # Research-related scripts in root
        research_scripts = {
            'add_expansion_priorities.py', 'add_research_priorities.py',
            'create_doj_weaponization_events.py', 'create_fed_corruption_events_fixed.py',
            'create_fed_corruption_events.py', 'improved_research_agent_template.py',
            'orchestrator_server_manager.py', 'populate_validation_run_13.py',
            'process_ttt_batch6.py', 'submit_cyber_mercenary_events.py',
            'submit_truth_social_spac_events.py', 'summarize_priorities.py',
            'sync_priority_status.py', 'test_api_workflow.py',
            'test_campaign_finance_research.py', 'tiered_orchestrator.py',
            'timeline_event_manager.py', 'validate_event.py',
            'validation_workflow.py'
        }
        if rel_path.name in research_scripts:
            return 'server'

        # Validation reports
        if parts[0] == 'validation_reports':
            return 'server'

        # Server-specific utils
        if parts[0] == 'scripts' and 'utils' in parts:
            if rel_path.name == 'update_rag_index.py':
                return 'server'

        # === EXCLUDE ===

        # Archive directory
        if parts[0] == 'archive':
            return 'exclude'

        # Old MCP server version
        if rel_path.name == 'mcp_timeline_server.py':
            return 'exclude'

        # Development artifacts
        if rel_path.name in {'all_python_files.txt'}:
            return 'exclude'

        # Nested timeline_data (appears to be error)
        if len(parts) >= 3 and parts[0] == 'timeline_data' and parts[1] == 'timeline_data':
            return 'exclude'

        # Test files - need to split by what they test
        if parts[0] == 'tests':
            # For now, mark as undecided - need manual review
            return 'undecided'

        # Docs - need to be rewritten for each repo
        if parts[0] == 'docs':
            # Keep manifest and analysis in current repo only
            if rel_path.name in {'REPOSITORY_SPLIT_MANIFEST.md', 'REPOSITORY_RESTRUCTURING_ANALYSIS.md'}:
                return 'exclude'
            # Other docs need review
            return 'undecided'

        # Root config files
        root_configs = {
            'LICENSE', '.gitignore', 'README.md',
            'requirements.txt', '.env.example',
            'package.json', '.pylintrc'
        }
        if len(parts) == 1 and rel_path.name in root_configs:
            # These will be in both repos but customized
            return 'undecided'

        # GitHub workflows
        if parts[0] == '.github':
            return 'undecided'

        # Everything else needs review
        return 'undecided'

    def analyze(self) -> Dict:
        """Analyze the repository and categorize all files"""
        print(f"Analyzing repository: {self.repo_root}")
        print(f"Skipping directories: {', '.join(self.skip_dirs)}")
        print()

        file_count = 0

        for root, dirs, files in os.walk(self.repo_root):
            # Remove skip_dirs from dirs to prevent os.walk from descending
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]

            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.repo_root)

                if self.should_skip(rel_path):
                    continue

                file_count += 1
                category = self.categorize_file(rel_path)

                if category == 'core':
                    self.core_files.append(rel_path)
                elif category == 'server':
                    self.server_files.append(rel_path)
                elif category == 'undecided':
                    self.undecided_files.append(rel_path)
                elif category == 'exclude':
                    self.excluded_files.append(rel_path)

        print(f"Analyzed {file_count} files")
        print(f"  Core: {len(self.core_files)}")
        print(f"  Server: {len(self.server_files)}")
        print(f"  Undecided: {len(self.undecided_files)}")
        print(f"  Excluded: {len(self.excluded_files)}")
        print()

        return {
            'total_files': file_count,
            'core_count': len(self.core_files),
            'server_count': len(self.server_files),
            'undecided_count': len(self.undecided_files),
            'excluded_count': len(self.excluded_files)
        }

    def get_size_stats(self, files: List[Path]) -> Dict:
        """Calculate total size and file count for a list of files"""
        total_size = 0
        by_extension = defaultdict(lambda: {'count': 0, 'size': 0})

        for rel_path in files:
            full_path = self.repo_root / rel_path
            try:
                size = full_path.stat().st_size
                total_size += size

                ext = rel_path.suffix or '(no extension)'
                by_extension[ext]['count'] += 1
                by_extension[ext]['size'] += size
            except (OSError, FileNotFoundError):
                pass

        return {
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': len(files),
            'by_extension': dict(by_extension)
        }

    def print_report(self):
        """Print a detailed analysis report"""
        print("=" * 80)
        print("REPOSITORY SPLIT ANALYSIS REPORT")
        print("=" * 80)
        print()

        # Core Timeline Repository
        print("1. KLEPTOCRACY-TIMELINE-CORE")
        print("-" * 80)
        core_stats = self.get_size_stats(self.core_files)
        print(f"   Files: {core_stats['file_count']}")
        print(f"   Total Size: {core_stats['total_size_mb']} MB")
        print()
        print("   Top directories:")
        core_dirs = defaultdict(int)
        for f in self.core_files:
            if len(f.parts) > 0:
                core_dirs[f.parts[0]] += 1
        for dir_name, count in sorted(core_dirs.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"     {dir_name}: {count} files")
        print()

        # Research Server Repository
        print("2. KLEPTOCRACY-TIMELINE-RESEARCH-SERVER")
        print("-" * 80)
        server_stats = self.get_size_stats(self.server_files)
        print(f"   Files: {server_stats['file_count']}")
        print(f"   Total Size: {server_stats['total_size_mb']} MB")
        print()
        print("   Top directories:")
        server_dirs = defaultdict(int)
        for f in self.server_files:
            if len(f.parts) > 0:
                server_dirs[f.parts[0]] += 1
        for dir_name, count in sorted(server_dirs.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"     {dir_name}: {count} files")
        print()

        # Undecided Files
        print("3. FILES REQUIRING MANUAL DECISION")
        print("-" * 80)
        print(f"   Count: {len(self.undecided_files)}")
        print()
        if self.undecided_files:
            print("   Files:")
            for f in sorted(self.undecided_files)[:20]:
                print(f"     {f}")
            if len(self.undecided_files) > 20:
                print(f"     ... and {len(self.undecided_files) - 20} more")
        print()

        # Excluded Files
        print("4. EXCLUDED FILES")
        print("-" * 80)
        excluded_stats = self.get_size_stats(self.excluded_files)
        print(f"   Files: {len(self.excluded_files)}")
        print(f"   Total Size: {excluded_stats['total_size_mb']} MB")
        print()

        print("=" * 80)
        print()

    def save_manifests(self, output_dir: str = 'docs'):
        """Save detailed file lists to JSON files"""
        output_path = self.repo_root / output_dir
        output_path.mkdir(exist_ok=True)

        # Core files
        core_manifest = {
            'repository': 'kleptocracy-timeline-core',
            'description': 'Forkable timeline + viewer',
            'file_count': len(self.core_files),
            'total_size_mb': self.get_size_stats(self.core_files)['total_size_mb'],
            'files': [str(f) for f in sorted(self.core_files)]
        }
        core_path = output_path / 'core_files_manifest.json'
        with open(core_path, 'w') as f:
            json.dump(core_manifest, f, indent=2)
        print(f"Saved core manifest: {core_path}")

        # Server files
        server_manifest = {
            'repository': 'kleptocracy-timeline-research-server',
            'description': 'Shared research infrastructure',
            'file_count': len(self.server_files),
            'total_size_mb': self.get_size_stats(self.server_files)['total_size_mb'],
            'files': [str(f) for f in sorted(self.server_files)]
        }
        server_path = output_path / 'server_files_manifest.json'
        with open(server_path, 'w') as f:
            json.dump(server_manifest, f, indent=2)
        print(f"Saved server manifest: {server_path}")

        # Undecided files
        undecided_manifest = {
            'description': 'Files requiring manual decision',
            'file_count': len(self.undecided_files),
            'files': [str(f) for f in sorted(self.undecided_files)]
        }
        undecided_path = output_path / 'undecided_files_manifest.json'
        with open(undecided_path, 'w') as f:
            json.dump(undecided_manifest, f, indent=2)
        print(f"Saved undecided manifest: {undecided_path}")

        # Excluded files
        excluded_manifest = {
            'description': 'Files to exclude from both repositories',
            'file_count': len(self.excluded_files),
            'total_size_mb': self.get_size_stats(self.excluded_files)['total_size_mb'],
            'files': [str(f) for f in sorted(self.excluded_files)]
        }
        excluded_path = output_path / 'excluded_files_manifest.json'
        with open(excluded_path, 'w') as f:
            json.dump(excluded_manifest, f, indent=2)
        print(f"Saved excluded manifest: {excluded_path}")
        print()


def main():
    """Main entry point"""
    import sys

    # Get repository root (assume script is in scripts/)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    analyzer = RepositorySplitAnalyzer(str(repo_root))

    # Run analysis
    analyzer.analyze()

    # Print report
    analyzer.print_report()

    # Save manifests
    analyzer.save_manifests()

    print("Analysis complete!")
    print()
    print("Next steps:")
    print("1. Review undecided_files_manifest.json and categorize files")
    print("2. Update this script with new categorizations")
    print("3. Re-run analysis to verify")
    print("4. Create migration scripts to perform the split")


if __name__ == '__main__':
    main()
