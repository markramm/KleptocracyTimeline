#!/usr/bin/env python3
"""
Migrate all timeline YAML files to JSON format
Handles date serialization and formatting issues
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime, date
from typing import Any, Dict, List
import shutil
import argparse

class DateAwareJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles date/datetime objects"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def convert_dates_to_strings(data: Any) -> Any:
    """Recursively convert all date/datetime objects to ISO format strings"""
    if isinstance(data, dict):
        return {key: convert_dates_to_strings(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_dates_to_strings(item) for item in data]
    elif isinstance(data, (datetime, date)):
        return data.isoformat() if isinstance(data, datetime) else str(data)
    else:
        return data

def validate_event_structure(event: Dict) -> List[str]:
    """Validate event has required fields and correct structure"""
    errors = []
    
    # Required fields
    required_fields = ['id', 'date', 'title', 'summary', 'importance', 'actors', 'tags', 'sources']
    for field in required_fields:
        if field not in event:
            errors.append(f"Missing required field: {field}")
    
    # Type validation
    if 'importance' in event and not isinstance(event['importance'], (int, float)):
        errors.append(f"Importance must be a number, got: {type(event['importance']).__name__}")
    
    if 'actors' in event and not isinstance(event['actors'], list):
        errors.append(f"Actors must be a list, got: {type(event['actors']).__name__}")
        
    if 'tags' in event and not isinstance(event['tags'], list):
        errors.append(f"Tags must be a list, got: {type(event['tags']).__name__}")
        
    if 'sources' in event and not isinstance(event['sources'], list):
        errors.append(f"Sources must be a list, got: {type(event['sources']).__name__}")
    
    # Validate sources structure
    if 'sources' in event and isinstance(event['sources'], list):
        for i, source in enumerate(event['sources']):
            if not isinstance(source, dict):
                errors.append(f"Source {i} must be a dictionary")
            elif 'title' not in source or 'url' not in source:
                errors.append(f"Source {i} missing required fields (title, url)")
    
    return errors

def migrate_yaml_to_json(yaml_path: Path, json_path: Path, backup: bool = True) -> Dict[str, Any]:
    """
    Convert a single YAML file to JSON
    Returns: {'success': bool, 'errors': List[str], 'warnings': List[str]}
    """
    result = {'success': False, 'errors': [], 'warnings': [], 'event_id': None}
    
    try:
        # Read YAML file
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
            event_data = yaml.safe_load(yaml_content)
        
        if not event_data:
            result['errors'].append("Empty YAML file")
            return result
        
        # Extract ID from filename if not in data
        if 'id' not in event_data:
            event_data['id'] = yaml_path.stem
            result['warnings'].append("ID extracted from filename")
        
        result['event_id'] = event_data.get('id', 'unknown')
        
        # Validate structure
        validation_errors = validate_event_structure(event_data)
        if validation_errors:
            result['errors'].extend(validation_errors)
            # Continue anyway for migration purposes
        
        # Convert all dates to strings
        event_data = convert_dates_to_strings(event_data)
        
        # Ensure date is a string
        if 'date' in event_data:
            if isinstance(event_data['date'], str):
                # Validate date format
                try:
                    datetime.strptime(event_data['date'], '%Y-%m-%d')
                except ValueError:
                    result['warnings'].append(f"Non-standard date format: {event_data['date']}")
            else:
                result['warnings'].append(f"Date converted from {type(event_data['date']).__name__} to string")
        
        # Ensure status has a default value
        if 'status' not in event_data:
            event_data['status'] = 'confirmed'
            result['warnings'].append("Added default status: confirmed")
        
        # Clean up None values
        def remove_nones(data):
            if isinstance(data, dict):
                return {k: remove_nones(v) for k, v in data.items() if v is not None}
            elif isinstance(data, list):
                return [remove_nones(item) for item in data if item is not None]
            else:
                return data
        
        event_data = remove_nones(event_data)
        
        # Create backup if requested
        if backup:
            backup_path = yaml_path.with_suffix('.yaml.bak')
            shutil.copy2(yaml_path, backup_path)
        
        # Write JSON file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(event_data, f, indent=2, ensure_ascii=False, cls=DateAwareJSONEncoder)
            f.write('\n')  # Add trailing newline for git
        
        result['success'] = True
        
    except yaml.YAMLError as e:
        result['errors'].append(f"YAML parse error: {e}")
    except json.JSONEncodeError as e:
        result['errors'].append(f"JSON encode error: {e}")
    except Exception as e:
        result['errors'].append(f"Unexpected error: {e}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Migrate YAML timeline files to JSON')
    parser.add_argument('--input-dir', default='timeline_data/events', 
                       help='Directory containing YAML files')
    parser.add_argument('--output-dir', default='timeline_data/events', 
                       help='Directory for JSON files (default: same as input)')
    parser.add_argument('--backup', action='store_true', default=True,
                       help='Create .bak files before conversion')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--delete-yaml', action='store_true',
                       help='Delete YAML files after successful conversion')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed progress')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    
    if not input_path.exists():
        print(f"❌ Input directory does not exist: {input_path}")
        return 1
    
    # Create output directory if needed
    if not args.dry_run:
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all YAML files
    yaml_files = list(input_path.glob('*.yaml')) + list(input_path.glob('*.yml'))
    
    if not yaml_files:
        print(f"❌ No YAML files found in {input_path}")
        return 1
    
    print(f"🔄 Found {len(yaml_files)} YAML files to migrate")
    
    # Statistics
    successful = 0
    failed = 0
    warnings_count = 0
    all_errors = []
    all_warnings = []
    
    # Process each file
    for yaml_file in yaml_files:
        json_file = output_path / yaml_file.with_suffix('.json').name
        
        if args.verbose:
            print(f"  Processing: {yaml_file.name}")
        
        if args.dry_run:
            print(f"  Would convert: {yaml_file} → {json_file}")
            successful += 1
            continue
        
        result = migrate_yaml_to_json(yaml_file, json_file, backup=args.backup)
        
        if result['success']:
            successful += 1
            if result['warnings']:
                warnings_count += 1
                if args.verbose:
                    for warning in result['warnings']:
                        print(f"    ⚠️  {warning}")
                all_warnings.append((yaml_file.name, result['warnings']))
            
            # Delete YAML file if requested
            if args.delete_yaml:
                yaml_file.unlink()
                if args.verbose:
                    print(f"    🗑️  Deleted: {yaml_file.name}")
        else:
            failed += 1
            print(f"  ❌ Failed: {yaml_file.name}")
            for error in result['errors']:
                print(f"    Error: {error}")
            all_errors.append((yaml_file.name, result['errors']))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Migration Summary:")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⚠️  With warnings: {warnings_count}")
    
    if all_errors:
        print("\n❌ Files with errors:")
        for filename, errors in all_errors[:10]:  # Show first 10
            print(f"  {filename}:")
            for error in errors[:3]:  # Show first 3 errors per file
                print(f"    - {error}")
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more files with errors")
    
    if all_warnings and args.verbose:
        print("\n⚠️  Files with warnings:")
        for filename, warnings in all_warnings[:10]:
            print(f"  {filename}:")
            for warning in warnings:
                print(f"    - {warning}")
    
    # Write summary report
    if not args.dry_run:
        report_path = output_path / 'migration_report.json'
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_files': len(yaml_files),
                'successful': successful,
                'failed': failed,
                'warnings': warnings_count
            },
            'errors': dict(all_errors),
            'warnings': dict(all_warnings)
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
    
    if args.backup and not args.dry_run:
        print(f"\n💾 Backup files created with .bak extension")
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    exit(main())