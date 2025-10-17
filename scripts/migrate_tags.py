#!/usr/bin/env python3
"""
Tag Migration Script - Normalize all event tags using controlled taxonomy

This script:
1. Reads all timeline event JSON files
2. Normalizes tags using TagTaxonomy
3. Writes back normalized tags
4. Generates detailed migration report

Safety Features:
- Dry-run mode (default)
- Creates backups before modification
- Validates JSON after changes
- Detailed logging of all changes
"""

import json
import sys
import shutil
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from research_monitor.services.tag_taxonomy import TagTaxonomy


class TagMigrator:
    """Migrates event tags to normalized taxonomy"""

    def __init__(self, events_dir: Path, dry_run: bool = True):
        """
        Initialize migrator

        Args:
            events_dir: Path to timeline_data/events directory
            dry_run: If True, don't write changes (default: True)
        """
        self.events_dir = events_dir
        self.dry_run = dry_run
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'files_unchanged': 0,
            'files_error': 0,
            'tags_before': 0,
            'tags_after': 0,
            'tags_normalized': 0,
            'tags_deduplicated': 0,
        }
        self.changes = []  # List of (file, old_tags, new_tags)
        self.tag_changes = Counter()  # Count of each tag change
        self.errors = []

    def migrate_event_file(self, filepath: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Migrate tags in a single event file

        Args:
            filepath: Path to event JSON file

        Returns:
            (modified, old_tags, new_tags)
        """
        try:
            # Read event
            with open(filepath, 'r', encoding='utf-8') as f:
                event = json.load(f)

            old_tags = event.get('tags', [])
            if not isinstance(old_tags, list):
                self.errors.append(f"{filepath.name}: tags field is not a list")
                return (False, [], [])

            # Normalize tags
            new_tags = TagTaxonomy.normalize_tags(old_tags)

            # Update stats
            self.stats['tags_before'] += len(old_tags)
            self.stats['tags_after'] += len(new_tags)

            # Count normalized tags
            for old, new in zip(old_tags, new_tags):
                if old != new:
                    self.stats['tags_normalized'] += 1
                    self.tag_changes[f"{old} → {new}"] += 1

            # Count deduplicated tags
            if len(old_tags) > len(new_tags):
                self.stats['tags_deduplicated'] += len(old_tags) - len(new_tags)

            # Check if modified
            if old_tags != new_tags:
                self.changes.append((filepath.name, old_tags, new_tags))

                if not self.dry_run:
                    # Create backup
                    backup_path = filepath.parent / f"{filepath.stem}.bak"
                    shutil.copy2(filepath, backup_path)

                    # Write updated event
                    event['tags'] = new_tags
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(event, f, indent=2, ensure_ascii=False)

                    # Validate we can read it back
                    with open(filepath, 'r', encoding='utf-8') as f:
                        json.load(f)  # Will raise if invalid

                return (True, old_tags, new_tags)
            else:
                return (False, old_tags, new_tags)

        except json.JSONDecodeError as e:
            self.errors.append(f"{filepath.name}: JSON decode error - {e}")
            return (False, [], [])
        except Exception as e:
            self.errors.append(f"{filepath.name}: Error - {e}")
            return (False, [], [])

    def migrate_all(self) -> Dict:
        """
        Migrate all event files

        Returns:
            Migration report dict
        """
        if not self.events_dir.exists():
            raise FileNotFoundError(f"Events directory not found: {self.events_dir}")

        print(f"{'[DRY RUN] ' if self.dry_run else ''}Migrating tags in {self.events_dir}")
        print(f"Found {len(list(self.events_dir.glob('*.json')))} event files\n")

        for filepath in sorted(self.events_dir.glob('*.json')):
            modified, old_tags, new_tags = self.migrate_event_file(filepath)

            self.stats['files_processed'] += 1
            if modified:
                self.stats['files_modified'] += 1
            elif old_tags:  # Has tags but unchanged
                self.stats['files_unchanged'] += 1

            if self.stats['files_processed'] % 100 == 0:
                print(f"Processed {self.stats['files_processed']} files...")

        if self.errors:
            self.stats['files_error'] = len(self.errors)

        return self.generate_report()

    def generate_report(self) -> Dict:
        """Generate migration report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'statistics': self.stats,
            'taxonomy_stats': TagTaxonomy.get_statistics(),
            'top_changes': self.tag_changes.most_common(50),
            'errors': self.errors[:20],  # Limit errors
            'sample_changes': self.changes[:10]  # Sample changes
        }
        return report

    def print_report(self, report: Dict):
        """Print human-readable report"""
        print("\n" + "=" * 70)
        print(f"TAG MIGRATION REPORT {'(DRY RUN)' if self.dry_run else ''}")
        print("=" * 70)

        stats = report['statistics']
        print(f"\nFiles Processed: {stats['files_processed']}")
        print(f"  Modified: {stats['files_modified']}")
        print(f"  Unchanged: {stats['files_unchanged']}")
        print(f"  Errors: {stats['files_error']}")

        print(f"\nTags:")
        print(f"  Before: {stats['tags_before']} total")
        print(f"  After: {stats['tags_after']} total")
        print(f"  Normalized: {stats['tags_normalized']}")
        print(f"  Deduplicated: {stats['tags_deduplicated']}")
        print(f"  Net change: {stats['tags_after'] - stats['tags_before']}")

        taxonomy = report['taxonomy_stats']
        print(f"\nTaxonomy:")
        print(f"  Canonical tags: {taxonomy['canonical_tags']}")
        print(f"  Migration rules: {taxonomy['migration_rules']}")
        print(f"  Categories: {taxonomy['categories']}")

        if report['top_changes']:
            print(f"\nTop 30 Tag Changes:")
            for change, count in report['top_changes'][:30]:
                print(f"  {count:4d}x - {change}")

        if report['sample_changes']:
            print(f"\nSample File Changes:")
            for filename, old, new in report['sample_changes'][:5]:
                print(f"\n  {filename}")
                print(f"    Before: {old}")
                print(f"    After:  {new}")

        if report['errors']:
            print(f"\nErrors ({len(report['errors'])} shown):")
            for error in report['errors'][:20]:
                print(f"  - {error}")

        print("\n" + "=" * 70)
        if self.dry_run:
            print("DRY RUN - No files were modified")
            print("Run with --apply to apply changes")
        else:
            print("Migration complete!")
            print("Backups created with .bak extension")
        print("=" * 70)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate timeline event tags to normalized taxonomy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (default - no changes made)
  python scripts/migrate_tags.py

  # Apply changes
  python scripts/migrate_tags.py --apply

  # Specify custom events directory
  python scripts/migrate_tags.py --events-dir /path/to/events

  # Save report to JSON
  python scripts/migrate_tags.py --report migration_report.json
        """
    )

    parser.add_argument(
        '--events-dir',
        type=Path,
        default=Path('timeline_data/events'),
        help='Path to events directory (default: timeline_data/events)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply changes (default is dry-run)'
    )
    parser.add_argument(
        '--report',
        type=Path,
        help='Save detailed report to JSON file'
    )

    args = parser.parse_args()

    # Create migrator
    migrator = TagMigrator(
        events_dir=args.events_dir,
        dry_run=not args.apply
    )

    # Run migration
    try:
        report = migrator.migrate_all()
        migrator.print_report(report)

        # Save report if requested
        if args.report:
            with open(args.report, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nDetailed report saved to: {args.report}")

    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
