#!/usr/bin/env python3
"""
YAML validator for timeline events
Checks for common issues and enforces schema
"""

import os
import sys
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional

class TimelineEventValidator:
    """Validates timeline event YAML files against schema"""
    
    REQUIRED_FIELDS = ['id', 'date', 'title', 'summary', 'sources', 'status']
    OPTIONAL_FIELDS = ['location', 'actors', 'tags', 'capture_lanes', 'notes', 'citations']
    VALID_STATUSES = ['confirmed', 'disputed', 'developing', 'retracted', 'pending', 'predicted', 'reported', 'reported/contested']
    VALID_CAPTURE_LANES = [
        'Executive Power & Emergency Authority',
        'Judicial Capture & Corruption', 
        'Financial Corruption & Kleptocracy',
        'Foreign Influence Operations',
        'Federal Workforce Capture',
        'Corporate Capture & Regulatory Breakdown',
        'Law Enforcement Weaponization',
        'Election System Attack',
        'Information & Media Control',
        'Constitutional & Democratic Breakdown',
        'Epstein Network & Kompromat',
        'Immigration & Border Militarization',
        'International Democracy Impact'
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def validate_file(self, filepath: str) -> bool:
        """Validate a single YAML file"""
        self.errors = []
        self.warnings = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parsing error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"File read error: {e}")
            return False
            
        if not data:
            self.errors.append("Empty YAML file")
            return False
            
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                self.errors.append(f"Missing required field: {field}")
                
        # Validate date format
        if 'date' in data:
            if isinstance(data['date'], str):
                try:
                    datetime.strptime(data['date'], '%Y-%m-%d')
                except ValueError:
                    self.errors.append(f"Invalid date format: {data['date']} (expected YYYY-MM-DD)")
            elif not isinstance(data['date'], datetime):
                # It's already a datetime object, which is fine
                pass
                
        # Validate status
        if 'status' in data and data['status'] not in self.VALID_STATUSES:
            self.errors.append(f"Invalid status: {data['status']} (must be one of {self.VALID_STATUSES})")
            
        # Validate sources
        if 'sources' in data:
            if not isinstance(data['sources'], list):
                self.errors.append("Sources must be a list")
            elif len(data['sources']) == 0:
                self.errors.append("At least one source is required")
            else:
                for i, source in enumerate(data['sources']):
                    self._validate_source(source, i)
        
        # Check for "Research Document" placeholders
        if 'sources' in data:
            for source in data['sources']:
                if isinstance(source, dict) and source.get('url') == 'Research Document':
                    self.warnings.append("Source contains 'Research Document' placeholder - needs real URL")
                    
        # Validate lists are actually lists
        list_fields = ['actors', 'tags', 'citations', 'capture_lanes']
        for field in list_fields:
            if field in data and data[field] is not None and not isinstance(data[field], list):
                self.errors.append(f"{field} must be a list")
                
        # Validate capture_lanes values
        if 'capture_lanes' in data and data['capture_lanes'] is not None:
            if isinstance(data['capture_lanes'], list):
                for lane in data['capture_lanes']:
                    if lane not in self.VALID_CAPTURE_LANES:
                        self.errors.append(f"Invalid capture lane: '{lane}' (must be one of {self.VALID_CAPTURE_LANES})")
            else:
                self.errors.append("capture_lanes must be a list")
                
        # Check for vulnerable single sources
        if 'sources' in data and isinstance(data['sources'], list) and len(data['sources']) == 1:
            self.warnings.append("Event has only one source - consider adding more for robustness")
            
        # Check for unescaped quotes in strings
        self._check_quote_issues(data)
        
        return len(self.errors) == 0
    
    def _validate_source(self, source: Dict, index: int) -> None:
        """Validate a single source entry"""
        if not isinstance(source, dict):
            self.errors.append(f"Source {index} must be a dictionary")
            return
            
        required_source_fields = ['title', 'url', 'outlet', 'date']
        for field in required_source_fields:
            if field not in source:
                self.errors.append(f"Source {index} missing required field: {field}")
                
        # Check URL format
        if 'url' in source:
            url = source['url']
            if url != 'Research Document' and not (url.startswith('http://') or url.startswith('https://')):
                self.warnings.append(f"Source {index} URL should start with http:// or https://")
                
    def _check_quote_issues(self, data: Any, path: str = "") -> None:
        """Recursively check for potential quote escaping issues"""
        if isinstance(data, str):
            # Check for unescaped quotes that might break YAML
            if '"' in data and not (data.startswith('"') and data.endswith('"')):
                if data.count('"') % 2 != 0:
                    self.warnings.append(f"Potential unescaped quote issue at {path}")
        elif isinstance(data, dict):
            for key, value in data.items():
                self._check_quote_issues(value, f"{path}.{key}" if path else key)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._check_quote_issues(item, f"{path}[{i}]")
                
    def print_report(self, filepath: str) -> None:
        """Print validation report for a file"""
        filename = os.path.basename(filepath)
        if self.errors:
            print(f"\n❌ {filename}")
            for error in self.errors:
                print(f"  ERROR: {error}")
        elif self.warnings:
            print(f"\n⚠️  {filename}")
            for warning in self.warnings:
                print(f"  WARNING: {warning}")
        else:
            print(f"✅ {filename}")


def validate_all_events():
    """Validate all event files in the events directory"""
    validator = TimelineEventValidator()
    events_dir = 'events'
    
    if not os.path.exists(events_dir):
        print(f"Events directory not found: {events_dir}")
        return
        
    files = sorted([f for f in os.listdir(events_dir) if f.endswith('.yaml')])
    
    total = len(files)
    valid = 0
    with_errors = 0
    with_warnings = 0
    
    print(f"Validating {total} YAML files...")
    print("=" * 60)
    
    error_files = []
    warning_files = []
    
    for filename in files:
        filepath = os.path.join(events_dir, filename)
        is_valid = validator.validate_file(filepath)
        
        if not is_valid:
            with_errors += 1
            error_files.append(filename)
            validator.print_report(filepath)
        elif validator.warnings:
            with_warnings += 1
            warning_files.append(filename)
            if len(warning_files) <= 10:  # Only show first 10 warnings
                validator.print_report(filepath)
        else:
            valid += 1
            
    print("\n" + "=" * 60)
    print(f"VALIDATION SUMMARY:")
    print(f"  Total files: {total}")
    print(f"  ✅ Valid: {valid}")
    print(f"  ❌ With errors: {with_errors}")
    print(f"  ⚠️  With warnings: {with_warnings}")
    
    if error_files:
        print(f"\nFiles with errors ({len(error_files)}):")
        for f in error_files[:20]:  # Show first 20
            print(f"  - {f}")
        if len(error_files) > 20:
            print(f"  ... and {len(error_files) - 20} more")
            
    if warning_files and len(warning_files) > 10:
        print(f"\nFiles with warnings ({len(warning_files)} total, showing sample):")
        for f in warning_files[10:20]:  # Show sample
            print(f"  - {f}")
        print(f"  ... and {len(warning_files) - 10} more")
            
    return with_errors == 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Validate specific file
        validator = TimelineEventValidator()
        filepath = sys.argv[1]
        is_valid = validator.validate_file(filepath)
        validator.print_report(filepath)
        sys.exit(0 if is_valid else 1)
    else:
        # Validate all files
        success = validate_all_events()
        sys.exit(0 if success else 1)