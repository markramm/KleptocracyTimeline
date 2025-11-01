#!/usr/bin/env python3
"""
Unified validation script for timeline events.

This script consolidates all validation functionality:
- Date validation
- Schema validation  
- Link checking
- Source verification
- Filename consistency
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    get_event_files,
    load_event,
    validate_event_schema,
    validate_date,
    validate_url,
    validate_filename,
    setup_logger,
    log_info,
    log_warning,
    log_error,
    log_success,
    print_header,
    print_summary
)


class TimelineValidator:
    """Comprehensive validator for timeline events."""
    
    def __init__(self, events_dir: str = "timeline_data/events", verbose: bool = False):
        """
        Initialize the validator.
        
        Args:
            events_dir: Path to events directory
            verbose: Enable verbose output
        """
        self.events_dir = Path(events_dir)
        self.verbose = verbose
        self.logger = setup_logger('validator', level='DEBUG' if verbose else 'INFO')
        self.issues = defaultdict(list)
        self.stats = {
            'total_files': 0,
            'valid_files': 0,
            'files_with_errors': 0,
            'total_errors': 0,
            'total_warnings': 0
        }
    
    def validate_all(self) -> bool:
        """
        Validate all event files.
        
        Returns:
            True if all files are valid, False otherwise
        """
        print_header("TIMELINE VALIDATION")
        
        event_files = get_event_files(self.events_dir)
        self.stats['total_files'] = len(event_files)
        
        if not event_files:
            log_error(f"No event files found in {self.events_dir}")
            return False
        
        log_info(f"Found {len(event_files)} event files to validate")
        
        for filepath in event_files:
            self.validate_file(filepath)
        
        self._print_results()
        return self.stats['files_with_errors'] == 0
    
    def validate_file(self, filepath: Path) -> bool:
        """
        Validate a single event file.
        
        Args:
            filepath: Path to the event file
            
        Returns:
            True if file is valid, False otherwise
        """
        filename = filepath.name
        errors = []
        warnings = []
        
        # Load the event
        event = load_event(filepath)
        if not event:
            errors.append("Failed to load file")
            self.issues[filename] = {'errors': errors, 'warnings': warnings}
            self.stats['files_with_errors'] += 1
            return False
        
        # Validate schema
        is_valid, schema_errors = validate_event_schema(event)
        errors.extend(schema_errors)
        
        # Validate filename format
        if 'id' in event and 'date' in event:
            valid, error = validate_filename(filepath, event['id'], str(event['date'])[:10])
            if not valid:
                warnings.append(error)
        
        # Check for future dates - treat as warnings
        if 'date' in event:
            valid, error = validate_date(event['date'], allow_future=False)
            if not valid and 'future' in error.lower():
                # Future dates are warnings, not errors
                if event.get('status') == 'confirmed':
                    warnings.append(f"Future date ({event['date']}) with 'confirmed' status - verify this is a real scheduled event")
                else:
                    warnings.append(f"Future date: {event['date']} - verify this is a real scheduled/projected event")
        
        # Check for duplicate IDs (would need to track across files)
        # This is handled in a separate pass
        
        # Check source count
        sources = event.get('sources', [])
        if len(sources) < 2:
            warnings.append(f"Only {len(sources)} source(s) - consider adding more")
        
        # Store issues
        if errors or warnings:
            self.issues[filename] = {'errors': errors, 'warnings': warnings}
            if errors:
                self.stats['files_with_errors'] += 1
                self.stats['total_errors'] += len(errors)
            if warnings:
                self.stats['total_warnings'] += len(warnings)
        else:
            self.stats['valid_files'] += 1
            if self.verbose:
                log_success(f"{filename}: Valid")
        
        return len(errors) == 0
    
    def check_duplicate_ids(self) -> None:
        """Check for duplicate event IDs across all files."""
        id_map = {}
        
        for filepath in get_event_files(self.events_dir):
            event = load_event(filepath)
            if event and 'id' in event:
                event_id = event['id']
                if event_id in id_map:
                    # Duplicate found
                    error = f"Duplicate ID '{event_id}' also in {id_map[event_id]}"
                    if filepath.name not in self.issues:
                        self.issues[filepath.name] = {'errors': [], 'warnings': []}
                    self.issues[filepath.name]['errors'].append(error)
                    self.stats['total_errors'] += 1
                else:
                    id_map[event_id] = filepath.name
    
    def _print_results(self) -> None:
        """Print validation results."""
        print()
        
        # Print issues if any
        if self.issues:
            print_header("VALIDATION ISSUES", width=60)
            
            for filename, file_issues in sorted(self.issues.items()):
                errors = file_issues.get('errors', [])
                warnings = file_issues.get('warnings', [])
                
                if errors:
                    log_error(f"{filename}:")
                    for error in errors:
                        print(f"    ❌ {error}")
                
                if warnings and self.verbose:
                    if not errors:
                        log_warning(f"{filename}:")
                    for warning in warnings:
                        print(f"    ⚠️  {warning}")
                
                if errors or (warnings and self.verbose):
                    print()
        
        # Print summary
        print_summary({
            'Total Files': self.stats['total_files'],
            'Valid Files': self.stats['valid_files'],
            'Files With Errors': self.stats['files_with_errors'],
            'Total Errors': self.stats['total_errors'],
            'Total Warnings': self.stats['total_warnings']
        })
        
        # Overall status
        if self.stats['files_with_errors'] == 0:
            log_success("All files passed validation!")
        else:
            log_error(f"{self.stats['files_with_errors']} file(s) have validation errors")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate timeline event files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Validate all events
  %(prog)s --verbose          # Show warnings and detailed output
  %(prog)s --check-links      # Also check if URLs are accessible
  %(prog)s --fix              # Attempt to fix simple issues
        """
    )
    
    parser.add_argument(
        '--events-dir',
        default='timeline_data/events',
        help='Path to events directory (default: timeline_data/events)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output (show warnings)'
    )
    
    parser.add_argument(
        '--check-links',
        action='store_true',
        help='Check if source URLs are accessible (slow)'
    )
    
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to fix simple validation issues'
    )
    
    args = parser.parse_args()
    
    # Run validation
    validator = TimelineValidator(args.events_dir, verbose=args.verbose)
    
    # Check for duplicate IDs
    validator.check_duplicate_ids()
    
    # Validate all files
    success = validator.validate_all()
    
    # Additional checks if requested
    if args.check_links:
        log_info("\nChecking links is not yet implemented in this version")
        # TODO: Implement link checking
    
    if args.fix:
        log_info("\nAuto-fix is not yet implemented in this version")
        # TODO: Implement auto-fix functionality
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()