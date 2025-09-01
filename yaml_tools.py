#!/usr/bin/env python3
"""
YAML Event Management Tools

A unified tool system for managing timeline event YAML files with built-in validation,
search capabilities, and batch operations.
"""

import os
import sys
import yaml
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Literal
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import shutil
import difflib
import urllib.request
import urllib.error
from urllib.parse import urlparse


@dataclass
class EditResult:
    """Result of an edit operation"""
    success: bool
    validation_errors: List[str]
    diff: str
    backup_path: Optional[str] = None
    file_path: Optional[str] = None


@dataclass
class SourceResult:
    """Result of source management operation"""
    success: bool
    added: List[Dict]
    removed: List[Dict]
    duplicates_found: List[Dict]
    url_checks: Dict[str, bool]
    suggestions: List[str]


@dataclass
class BulkEditResult:
    """Result of bulk edit operation"""
    success: bool
    files_updated: List[str]
    files_failed: List[str]
    total_changes: int
    validation_errors: Dict[str, List[str]]


class YamlEventManager:
    """
    Main class for managing timeline event YAML files.
    Provides unified search, edit, validate, and bulk operations.
    """
    
    def __init__(self, base_path: str = "timeline_data/events"):
        """Initialize the manager with the base path to event files"""
        self.base_path = Path(base_path)
        self.cache = {}  # Cache for parsed YAML files
        self.backup_dir = self.base_path.parent / ".backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Load schema if available
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Optional[Dict]:
        """Load event schema from schema.yaml if it exists"""
        schema_path = self.base_path.parent / "schema.yaml"
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None
        
    def _parse_date_query(self, date_str: str) -> str:
        """Parse flexible date strings into YYYY-MM-DD format"""
        date_str = date_str.lower().strip()
        today = datetime.now()
        
        # Handle relative dates
        if date_str == 'today':
            return today.strftime('%Y-%m-%d')
        elif date_str == 'yesterday':
            return (today - timedelta(days=1)).strftime('%Y-%m-%d')
        elif date_str == 'last week':
            return (today - timedelta(weeks=1)).strftime('%Y-%m-%d')
        elif date_str == 'last month':
            return (today - timedelta(days=30)).strftime('%Y-%m-%d')
        elif date_str == 'last year':
            return (today - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Handle year-only format
        if re.match(r'^\d{4}$', date_str):
            return f"{date_str}-01-01"
        
        # Handle month-year format
        if re.match(r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}$', date_str):
            months = {'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 
                     'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                     'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'}
            parts = date_str.split()
            month = months.get(parts[0][:3])
            return f"{parts[1]}-{month}-01"
        
        # Return as-is if already in correct format or unparseable
        return date_str
    
    def _load_event(self, file_path: Path) -> Optional[Dict]:
        """Load and cache a YAML event file"""
        path_str = str(file_path)
        
        # Check cache first
        if path_str in self.cache:
            file_mtime = file_path.stat().st_mtime
            if self.cache[path_str]['mtime'] == file_mtime:
                return self.cache[path_str]['data']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            # Update cache
            self.cache[path_str] = {
                'data': data,
                'mtime': file_path.stat().st_mtime
            }
            return data
        except Exception as e:
            print(f"Error loading {file_path}: {e}", file=sys.stderr)
            return None
    
    def _validate_event(self, event: Dict) -> List[str]:
        """Validate an event against schema and business rules"""
        errors = []
        
        # Required fields
        required_fields = ['id', 'date', 'title', 'summary', 'importance', 'status']
        for field in required_fields:
            if field not in event:
                errors.append(f"Missing required field: {field}")
        
        # Date format validation
        if 'date' in event:
            date_val = event['date']
            # Convert date object to string if needed
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)
            
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                errors.append(f"Invalid date format: {date_str} (expected YYYY-MM-DD)")
        
        # Importance range
        if 'importance' in event:
            imp = event['importance']
            if not isinstance(imp, int) or imp < 1 or imp > 10:
                errors.append(f"Importance must be integer 1-10, got: {imp}")
        
        # Status values
        if 'status' in event:
            valid_statuses = ['confirmed', 'reported', 'disputed', 'developing']
            if event['status'] not in valid_statuses:
                errors.append(f"Invalid status: {event['status']} (must be one of {valid_statuses})")
        
        # Source validation
        if 'sources' in event:
            if not isinstance(event['sources'], list):
                errors.append("Sources must be a list")
            elif len(event['sources']) == 0:
                errors.append("Event has no sources")
            elif len(event['sources']) == 1:
                errors.append("Warning: Event has only one source - consider adding more")
            
            for i, source in enumerate(event.get('sources', [])):
                if not isinstance(source, dict):
                    errors.append(f"Source {i+1} is not a dictionary")
                    continue
                if 'title' not in source:
                    errors.append(f"Source {i+1} missing title")
                if 'outlet' not in source:
                    errors.append(f"Source {i+1} missing outlet")
        
        return errors
    
    def _suggest_improvements(self, event: Dict) -> List[str]:
        """AI-powered suggestions for event quality improvement"""
        suggestions = []
        
        # Check source diversity
        if 'sources' in event:
            outlets = [s.get('outlet', '') for s in event['sources']]
            if len(set(outlets)) < len(outlets):
                suggestions.append("Consider diversifying sources - multiple from same outlet")
            
            # Check for primary sources
            primary_indicators = ['court', 'filing', 'opinion', 'order', 'decision', 
                                'testimony', 'hearing', 'deposition', 'report']
            has_primary = any(
                any(ind in str(s).lower() for ind in primary_indicators)
                for s in event['sources']
            )
            if not has_primary:
                suggestions.append("Consider adding primary sources (court docs, official reports)")
        
        # Check summary length
        if 'summary' in event:
            summary_len = len(event['summary'].split())
            if summary_len < 20:
                suggestions.append("Summary may be too brief - consider adding more context")
            elif summary_len > 200:
                suggestions.append("Summary may be too long - consider being more concise")
        
        # Check for actor diversity
        if 'actors' in event and len(event['actors']) < 2:
            suggestions.append("Consider identifying additional actors involved")
        
        return suggestions
    
    def _create_backup(self, file_path: Path) -> str:
        """Create a backup of the file before editing"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path.stem}_{timestamp}.yaml"
        backup_path = self.backup_dir / backup_name
        shutil.copy2(file_path, backup_path)
        return str(backup_path)
    
    def _create_diff(self, original: Dict, modified: Dict) -> str:
        """Create a readable diff between original and modified events"""
        original_yaml = yaml.dump(original, default_flow_style=False, sort_keys=False)
        modified_yaml = yaml.dump(modified, default_flow_style=False, sort_keys=False)
        
        diff = difflib.unified_diff(
            original_yaml.splitlines(keepends=True),
            modified_yaml.splitlines(keepends=True),
            fromfile='original',
            tofile='modified',
            n=3
        )
        return ''.join(diff)
    
    def yaml_search(self,
                   query: str = None,
                   fields: List[str] = None,
                   date_range: Tuple[str, str] = None,
                   importance: Tuple[int, int] = None,
                   status: List[str] = None,
                   tags: List[str] = None,
                   actors: List[str] = None,
                   max_results: int = 10,
                   return_full: bool = True) -> List[Dict]:
        """
        Search for events matching specified criteria.
        
        Args:
            query: Text to search for in any field
            fields: Specific fields to search in
            date_range: Tuple of (start_date, end_date)
            importance: Tuple of (min, max) importance values
            status: List of statuses to filter by
            tags: List of tags to filter by
            actors: List of actors to filter by
            max_results: Maximum number of results to return
            return_full: Return full event data or just metadata
            
        Returns:
            List of matching events
        """
        results = []
        
        # Get all YAML files
        yaml_files = sorted(self.base_path.glob("*.yaml"))
        
        for file_path in yaml_files:
            event = self._load_event(file_path)
            if not event:
                continue
            
            # Apply filters
            matches = True
            
            # Text query
            if query:
                query_lower = query.lower()
                if fields:
                    # Search specific fields
                    found = False
                    for field in fields:
                        if field in event:
                            field_value = str(event[field]).lower()
                            if query_lower in field_value:
                                found = True
                                break
                    matches = found
                else:
                    # Search all text fields
                    # Convert dates to strings for JSON serialization
                    def serialize_dates(obj):
                        if isinstance(obj, dict):
                            return {k: serialize_dates(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [serialize_dates(v) for v in obj]
                        elif hasattr(obj, 'isoformat'):  # date/datetime objects
                            return obj.isoformat()
                        elif hasattr(obj, '__str__') and 'date' in type(obj).__name__.lower():
                            return str(obj)
                        else:
                            return obj
                    
                    event_serializable = serialize_dates(event)
                    event_str = json.dumps(event_serializable, default=str).lower()
                    matches = query_lower in event_str
            
            if not matches:
                continue
            
            # Date range filter
            if date_range and 'date' in event:
                event_date = event['date']
                start_date = self._parse_date_query(date_range[0])
                end_date = self._parse_date_query(date_range[1])
                if not (start_date <= event_date <= end_date):
                    continue
            
            # Importance filter
            if importance and 'importance' in event:
                if not (importance[0] <= event['importance'] <= importance[1]):
                    continue
            
            # Status filter
            if status and 'status' in event:
                if event['status'] not in status:
                    continue
            
            # Tags filter
            if tags and 'tags' in event:
                event_tags = set(event['tags'])
                if not any(tag in event_tags for tag in tags):
                    continue
            
            # Actors filter
            if actors and 'actors' in event:
                event_actors = set(actor.lower() for actor in event['actors'])
                if not any(actor.lower() in event_actors for actor in actors):
                    continue
            
            # Add to results
            if return_full:
                event['_file_path'] = str(file_path)
                results.append(event)
            else:
                results.append({
                    'id': event.get('id'),
                    'date': event.get('date'),
                    'title': event.get('title'),
                    'importance': event.get('importance'),
                    'status': event.get('status'),
                    '_file_path': str(file_path)
                })
            
            if len(results) >= max_results:
                break
        
        return results
    
    def yaml_edit(self,
                 file_path: str,
                 updates: Dict[str, Any],
                 validate_before_save: bool = True,
                 create_backup: bool = True,
                 dry_run: bool = False) -> EditResult:
        """
        Edit a YAML event file with field-level updates.
        
        Args:
            file_path: Path to the YAML file to edit
            updates: Dictionary of field updates to apply
            validate_before_save: Whether to validate before saving
            create_backup: Whether to create a backup before editing
            dry_run: Preview changes without saving
            
        Returns:
            EditResult with success status, validation errors, diff, and backup path
        """
        file_path = Path(file_path)
        
        # Load original event
        original_event = self._load_event(file_path)
        if not original_event:
            return EditResult(
                success=False,
                validation_errors=[f"Failed to load {file_path}"],
                diff="",
                backup_path=None,
                file_path=str(file_path)
            )
        
        # Create modified event
        modified_event = original_event.copy()
        
        # Apply updates
        for key, value in updates.items():
            if value is None and key in modified_event:
                # Remove field if value is None
                del modified_event[key]
            else:
                # Update or add field
                modified_event[key] = value
        
        # Validate if requested
        validation_errors = []
        if validate_before_save:
            validation_errors = self._validate_event(modified_event)
            if validation_errors and any('Error' in e or 'Missing' in e for e in validation_errors):
                return EditResult(
                    success=False,
                    validation_errors=validation_errors,
                    diff=self._create_diff(original_event, modified_event),
                    backup_path=None,
                    file_path=str(file_path)
                )
        
        # Create diff
        diff = self._create_diff(original_event, modified_event)
        
        # Dry run - return without saving
        if dry_run:
            return EditResult(
                success=True,
                validation_errors=validation_errors,
                diff=diff,
                backup_path=None,
                file_path=str(file_path)
            )
        
        # Create backup if requested
        backup_path = None
        if create_backup:
            backup_path = self._create_backup(file_path)
        
        # Save the modified event
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(modified_event, f, default_flow_style=False, 
                         sort_keys=False, allow_unicode=True, width=80)
            
            # Clear cache for this file
            if str(file_path) in self.cache:
                del self.cache[str(file_path)]
            
            return EditResult(
                success=True,
                validation_errors=validation_errors,
                diff=diff,
                backup_path=backup_path,
                file_path=str(file_path)
            )
        except Exception as e:
            return EditResult(
                success=False,
                validation_errors=[f"Failed to save: {str(e)}"],
                diff=diff,
                backup_path=backup_path,
                file_path=str(file_path)
            )
    
    def yaml_bulk_edit(self,
                      search_criteria: Dict = None,
                      updates: Dict[str, Any] = None,
                      interactive: bool = True,
                      max_files: int = None) -> BulkEditResult:
        """
        Apply the same updates to multiple files matching search criteria.
        
        Args:
            search_criteria: Same parameters as yaml_search
            updates: Updates to apply to all matching files
            interactive: Whether to show preview and confirm
            max_files: Safety limit on number of files to update
            
        Returns:
            BulkEditResult with summary of changes
        """
        if not search_criteria:
            search_criteria = {}
        
        # Remove max_results from search to get all matches
        search_criteria.pop('max_results', None)
        search_criteria['return_full'] = True
        
        # Find matching events
        matches = self.yaml_search(**search_criteria)
        
        if max_files and len(matches) > max_files:
            matches = matches[:max_files]
        
        # Interactive confirmation
        if interactive and matches:
            print(f"Found {len(matches)} files to update:")
            for event in matches[:5]:
                print(f"  - {event.get('date')} {event.get('title')[:50]}...")
            if len(matches) > 5:
                print(f"  ... and {len(matches) - 5} more")
            
            print(f"\nUpdates to apply: {updates}")
            response = input("\nProceed? (y/n): ")
            if response.lower() != 'y':
                return BulkEditResult(
                    success=False,
                    files_updated=[],
                    files_failed=[],
                    total_changes=0,
                    validation_errors={"cancelled": ["User cancelled operation"]}
                )
        
        # Apply updates
        files_updated = []
        files_failed = []
        validation_errors = {}
        
        for event in matches:
            file_path = event['_file_path']
            result = self.yaml_edit(
                file_path=file_path,
                updates=updates,
                validate_before_save=True,
                create_backup=True,
                dry_run=False
            )
            
            if result.success:
                files_updated.append(file_path)
            else:
                files_failed.append(file_path)
                validation_errors[file_path] = result.validation_errors
        
        return BulkEditResult(
            success=len(files_failed) == 0,
            files_updated=files_updated,
            files_failed=files_failed,
            total_changes=len(files_updated),
            validation_errors=validation_errors
        )
    
    def manage_sources(self,
                      file_path: str,
                      action: Literal["add", "replace", "remove", "validate"],
                      sources: List[Dict] = None,
                      check_duplicates: bool = True,
                      check_urls: bool = False,
                      prefer_free: bool = True) -> SourceResult:
        """
        Specialized tool for managing event sources.
        
        Args:
            file_path: Path to the YAML file
            action: Operation to perform on sources
            sources: List of source dictionaries
            check_duplicates: Whether to check for duplicate sources
            check_urls: Whether to verify URLs are accessible
            prefer_free: Whether to suggest free alternatives
            
        Returns:
            SourceResult with operation summary
        """
        file_path = Path(file_path)
        
        # Load event
        event = self._load_event(file_path)
        if not event:
            return SourceResult(
                success=False,
                added=[],
                removed=[],
                duplicates_found=[],
                url_checks={},
                suggestions=["Failed to load event file"]
            )
        
        current_sources = event.get('sources', [])
        added = []
        removed = []
        duplicates_found = []
        url_checks = {}
        suggestions = []
        
        if action == "validate":
            # Validate existing sources
            for source in current_sources:
                if 'url' in source and check_urls:
                    url = source['url']
                    url_checks[url] = self._check_url(url)
                    if not url_checks[url]:
                        suggestions.append(f"URL may be broken: {url}")
            
            # Check for single source
            if len(current_sources) == 1:
                suggestions.append("Event has only one source - consider adding more")
            
            # Check for paywalled sources
            if prefer_free:
                paywalled_outlets = ['Wall Street Journal', 'WSJ', 'Financial Times', 
                                   'The Information', 'Bloomberg']
                for source in current_sources:
                    outlet = source.get('outlet', '')
                    if any(p in outlet for p in paywalled_outlets):
                        suggestions.append(f"Consider adding free alternative to: {outlet}")
            
        elif action == "add":
            if not sources:
                return SourceResult(
                    success=False,
                    added=[],
                    removed=[],
                    duplicates_found=[],
                    url_checks={},
                    suggestions=["No sources provided to add"]
                )
            
            # Check for duplicates
            new_sources = []
            for source in sources:
                is_duplicate = False
                
                if check_duplicates:
                    for existing in current_sources:
                        if source.get('url') == existing.get('url'):
                            duplicates_found.append(source)
                            is_duplicate = True
                            break
                        if (source.get('title') == existing.get('title') and 
                            source.get('outlet') == existing.get('outlet')):
                            duplicates_found.append(source)
                            is_duplicate = True
                            break
                
                if not is_duplicate:
                    # Check URL if requested
                    if 'url' in source and check_urls:
                        url_checks[source['url']] = self._check_url(source['url'])
                    
                    new_sources.append(source)
                    added.append(source)
            
            # Update event sources
            event['sources'] = current_sources + new_sources
            
        elif action == "replace":
            if not sources:
                return SourceResult(
                    success=False,
                    added=[],
                    removed=[],
                    duplicates_found=[],
                    url_checks={},
                    suggestions=["No sources provided to replace with"]
                )
            
            removed = current_sources.copy()
            added = sources.copy()
            
            # Check URLs if requested
            if check_urls:
                for source in sources:
                    if 'url' in source:
                        url_checks[source['url']] = self._check_url(source['url'])
            
            event['sources'] = sources
            
        elif action == "remove":
            # Remove sources matching criteria
            if not sources:
                return SourceResult(
                    success=False,
                    added=[],
                    removed=[],
                    duplicates_found=[],
                    url_checks={},
                    suggestions=["No sources specified to remove"]
                )
            
            new_sources = []
            for existing in current_sources:
                should_remove = False
                for to_remove in sources:
                    if all(existing.get(k) == v for k, v in to_remove.items()):
                        should_remove = True
                        removed.append(existing)
                        break
                
                if not should_remove:
                    new_sources.append(existing)
            
            event['sources'] = new_sources
        
        # Save if action is not just validate
        if action != "validate":
            result = self.yaml_edit(
                file_path=str(file_path),
                updates={'sources': event['sources']},
                validate_before_save=True,
                create_backup=True,
                dry_run=False
            )
            
            if not result.success:
                return SourceResult(
                    success=False,
                    added=added,
                    removed=removed,
                    duplicates_found=duplicates_found,
                    url_checks=url_checks,
                    suggestions=result.validation_errors
                )
        
        return SourceResult(
            success=True,
            added=added,
            removed=removed,
            duplicates_found=duplicates_found,
            url_checks=url_checks,
            suggestions=suggestions
        )
    
    def _check_url(self, url: str) -> bool:
        """Check if a URL is accessible"""
        try:
            # Parse URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Try to access the URL
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except:
            return False


# CLI Interface
def main():
    """Command-line interface for YAML tools"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YAML Event Management Tools')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for events')
    search_parser.add_argument('query', nargs='?', help='Search query')
    search_parser.add_argument('--fields', nargs='+', help='Fields to search')
    search_parser.add_argument('--date-from', help='Start date')
    search_parser.add_argument('--date-to', help='End date')
    search_parser.add_argument('--importance-min', type=int, help='Minimum importance')
    search_parser.add_argument('--importance-max', type=int, help='Maximum importance')
    search_parser.add_argument('--status', nargs='+', help='Status values')
    search_parser.add_argument('--tags', nargs='+', help='Tags to filter')
    search_parser.add_argument('--actors', nargs='+', help='Actors to filter')
    search_parser.add_argument('--max-results', type=int, default=10, help='Maximum results')
    search_parser.add_argument('--summary', action='store_true', help='Show summary only')
    
    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit an event')
    edit_parser.add_argument('file', help='File path to edit')
    edit_parser.add_argument('--field', required=True, help='Field to update')
    edit_parser.add_argument('--value', required=True, help='New value')
    edit_parser.add_argument('--dry-run', action='store_true', help='Preview changes')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate events')
    validate_parser.add_argument('file', nargs='?', help='File to validate (or all)')
    
    # Source management command
    source_parser = subparsers.add_parser('sources', help='Manage event sources')
    source_parser.add_argument('file', help='File path')
    source_parser.add_argument('--action', choices=['add', 'validate', 'check-urls'],
                              default='validate', help='Action to perform')
    source_parser.add_argument('--url', help='Source URL')
    source_parser.add_argument('--title', help='Source title')
    source_parser.add_argument('--outlet', help='Source outlet')
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = YamlEventManager()
    
    if args.command == 'search':
        # Build search criteria
        criteria = {}
        if args.query:
            criteria['query'] = args.query
        if args.fields:
            criteria['fields'] = args.fields
        if args.date_from and args.date_to:
            criteria['date_range'] = (args.date_from, args.date_to)
        if args.importance_min and args.importance_max:
            criteria['importance'] = (args.importance_min, args.importance_max)
        if args.status:
            criteria['status'] = args.status
        if args.tags:
            criteria['tags'] = args.tags
        if args.actors:
            criteria['actors'] = args.actors
        criteria['max_results'] = args.max_results
        criteria['return_full'] = not args.summary
        
        # Search
        results = manager.yaml_search(**criteria)
        
        # Display results
        for event in results:
            print(f"\n{event.get('date')} - {event.get('title')}")
            if not args.summary:
                print(f"  Status: {event.get('status')}")
                print(f"  Importance: {event.get('importance')}")
                print(f"  File: {event.get('_file_path')}")
    
    elif args.command == 'edit':
        result = manager.yaml_edit(
            file_path=args.file,
            updates={args.field: args.value},
            dry_run=args.dry_run
        )
        
        if result.diff:
            print("Changes:")
            print(result.diff)
        
        if result.validation_errors:
            print("\nValidation issues:")
            for error in result.validation_errors:
                print(f"  - {error}")
        
        if result.success and not args.dry_run:
            print(f"\nFile updated successfully")
            if result.backup_path:
                print(f"Backup saved to: {result.backup_path}")
    
    elif args.command == 'validate':
        if args.file:
            # Validate single file
            event = manager._load_event(Path(args.file))
            if event:
                errors = manager._validate_event(event)
                suggestions = manager._suggest_improvements(event)
                
                if errors:
                    print("Validation errors:")
                    for error in errors:
                        print(f"  - {error}")
                else:
                    print("✓ Validation passed")
                
                if suggestions:
                    print("\nSuggestions:")
                    for suggestion in suggestions:
                        print(f"  - {suggestion}")
        else:
            # Validate all files
            yaml_files = sorted(manager.base_path.glob("*.yaml"))
            total_errors = 0
            
            for file_path in yaml_files:
                event = manager._load_event(file_path)
                if event:
                    errors = manager._validate_event(event)
                    if errors:
                        print(f"\n{file_path.name}:")
                        for error in errors:
                            print(f"  - {error}")
                        total_errors += len(errors)
            
            if total_errors == 0:
                print(f"✓ All {len(yaml_files)} files validated successfully")
            else:
                print(f"\n✗ Found {total_errors} errors across files")
    
    elif args.command == 'sources':
        if args.action == 'add':
            source = {}
            if args.url:
                source['url'] = args.url
            if args.title:
                source['title'] = args.title
            if args.outlet:
                source['outlet'] = args.outlet
            
            result = manager.manage_sources(
                file_path=args.file,
                action='add',
                sources=[source] if source else None
            )
        elif args.action == 'check-urls':
            result = manager.manage_sources(
                file_path=args.file,
                action='validate',
                check_urls=True
            )
        else:
            result = manager.manage_sources(
                file_path=args.file,
                action='validate'
            )
        
        if result.success:
            print("✓ Source operation completed")
            if result.added:
                print(f"  Added {len(result.added)} sources")
            if result.removed:
                print(f"  Removed {len(result.removed)} sources")
            if result.duplicates_found:
                print(f"  Skipped {len(result.duplicates_found)} duplicates")
            if result.url_checks:
                broken = [url for url, ok in result.url_checks.items() if not ok]
                if broken:
                    print(f"  Found {len(broken)} broken URLs")
            if result.suggestions:
                print("\nSuggestions:")
                for suggestion in result.suggestions:
                    print(f"  - {suggestion}")
        else:
            print("✗ Source operation failed")
            for suggestion in result.suggestions:
                print(f"  - {suggestion}")


if __name__ == '__main__':
    main()