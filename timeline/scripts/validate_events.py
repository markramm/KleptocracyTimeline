#!/usr/bin/env python3
"""
Validate timeline event files (JSON and Markdown formats).

This script validates both JSON and Markdown event files using the
unified parser infrastructure, ensuring all events meet quality standards.

Usage:
    python3 validate_events.py                    # Validate all events
    python3 validate_events.py event.json         # Validate specific file
    python3 validate_events.py --staged           # Validate only staged files
"""

import sys
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Add research-server to path for parser access
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / 'research-server' / 'server'))

try:
    from parsers.factory import EventParserFactory
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False


def validate_event_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate a single event file.

    Args:
        file_path: Path to event file (.json or .md)

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check file exists
    if not file_path.exists():
        return False, [f"File not found: {file_path}"]

    # Skip README
    if file_path.name.upper() == 'README.MD':
        return True, []

    # Use parser factory if available
    if PARSER_AVAILABLE:
        factory = EventParserFactory()

        # Check if format is supported
        parser = factory.get_parser(file_path)
        if parser is None:
            return False, [f"Unsupported file format: {file_path.suffix}"]

        # Validate format
        format_errors = factory.validate_event_format(file_path)
        if format_errors:
            return False, format_errors

        # Try to parse
        try:
            data = factory.parse_event(file_path)
        except Exception as e:
            return False, [f"Parse error: {str(e)}"]

    else:
        # Fallback to basic JSON validation
        if file_path.suffix.lower() == '.json':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                return False, [f"Invalid JSON: {str(e)}"]
            except Exception as e:
                return False, [f"Error reading file: {str(e)}"]
        else:
            # Can't validate markdown without parser
            return True, []

    # Validate required fields
    required_fields = ['id', 'date', 'title']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing or empty required field: {field}")

    # Validate ID format
    if 'id' in data:
        event_id = data['id']
        if not isinstance(event_id, str):
            errors.append(f"ID must be a string, got: {type(event_id).__name__}")
        elif '--' not in event_id:
            errors.append(f"ID must contain '--' separator: {event_id}")
        elif event_id != file_path.stem:
            errors.append(f"ID '{event_id}' must match filename '{file_path.stem}'")

    # Validate date format
    if 'date' in data:
        date_str = str(data['date'])
        parts = date_str.split('-')
        if len(parts) != 3:
            errors.append(f"Date must be in YYYY-MM-DD format: {date_str}")
        else:
            try:
                year, month, day = parts
                if len(year) != 4 or not year.isdigit():
                    errors.append(f"Invalid year in date: {year}")
                if len(month) != 2 or not month.isdigit() or not (1 <= int(month) <= 12):
                    errors.append(f"Invalid month in date: {month}")
                if len(day) != 2 or not day.isdigit() or not (1 <= int(day) <= 31):
                    errors.append(f"Invalid day in date: {day}")
            except (ValueError, AttributeError) as e:
                errors.append(f"Invalid date format: {date_str}")

    # Validate importance if present
    if 'importance' in data:
        importance = data['importance']
        if not isinstance(importance, (int, float)):
            errors.append(f"Importance must be a number, got: {type(importance).__name__}")
        elif not (1 <= importance <= 10):
            errors.append(f"Importance must be between 1-10, got: {importance}")

    # Validate summary exists
    if 'summary' not in data or not data['summary']:
        errors.append("Missing or empty summary")

    return len(errors) == 0, errors


def get_staged_files() -> List[Path]:
    """Get list of staged event files using git."""
    import subprocess

    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )

        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                path = Path(line)
                # Check if it's an event file
                if path.parent.name == 'events' and path.suffix.lower() in ['.json', '.md']:
                    if path.name.upper() != 'README.MD':
                        files.append(path)

        return files
    except subprocess.CalledProcessError:
        return []


def main():
    """Main validation entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate timeline event files')
    parser.add_argument('files', nargs='*', help='Specific files to validate')
    parser.add_argument('--staged', action='store_true', help='Validate only staged files')
    args = parser.parse_args()

    # Determine which files to validate
    if args.staged:
        files = get_staged_files()
        if not files:
            print("✅ No staged event files to validate")
            return 0
        print(f"Validating {len(files)} staged event files...")
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        # Validate all events in timeline/data/events/
        events_dir = REPO_ROOT / 'timeline' / 'data' / 'events'
        if not events_dir.exists():
            print(f"❌ Events directory not found: {events_dir}")
            return 1

        files = []
        for pattern in ['*.json', '*.md']:
            files.extend([
                f for f in events_dir.glob(pattern)
                if f.name.upper() != 'README.MD' and not f.name.startswith('.')
            ])

        print(f"Validating {len(files)} event files...")

    if not files:
        print("❌ No event files found to validate")
        return 1

    # Validate each file
    all_valid = True
    error_count = 0

    for file_path in files:
        is_valid, errors = validate_event_file(file_path)

        if is_valid:
            print(f"✅ {file_path.name}")
        else:
            all_valid = False
            error_count += len(errors)
            print(f"❌ {file_path.name}")
            for error in errors:
                print(f"   - {error}")

    # Summary
    print()
    if all_valid:
        print(f"✨ All {len(files)} event files are valid!")
        return 0
    else:
        print(f"❌ Validation failed: {error_count} errors found in {len([f for f in files if not validate_event_file(f)[0]])} files")
        return 1


if __name__ == '__main__':
    sys.exit(main())
