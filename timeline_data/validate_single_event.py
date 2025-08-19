#!/usr/bin/env python3
"""
Single event YAML validator - validates one file against schema
For use after editing individual event files
"""

import os
import sys
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional

class SingleEventValidator:
    """Validates a single timeline event YAML file against schema"""
    
    REQUIRED_FIELDS = ['id', 'date', 'title', 'summary', 'sources', 'status']
    OPTIONAL_FIELDS = ['location', 'actors', 'tags', 'notes', 'citations']
    VALID_STATUSES = ['confirmed', 'disputed', 'developing', 'retracted']
    
    def validate_event(self, filepath: str) -> tuple[bool, List[str], List[str]]:
        """
        Validate a single YAML event file
        Returns: (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        if not os.path.exists(filepath):
            return False, [f"File not found: {filepath}"], []
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return False, [f"YAML parsing error: {e}"], []
        except Exception as e:
            return False, [f"File read error: {e}"], []
            
        if not data:
            return False, ["Empty YAML file"], []
            
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field}")
                
        # Validate date format
        if 'date' in data:
            if isinstance(data['date'], str):
                try:
                    datetime.strptime(data['date'], '%Y-%m-%d')
                except ValueError:
                    errors.append("Date must be in YYYY-MM-DD format")
            else:
                errors.append("Date must be a string")
                
        # Validate status
        if 'status' in data and data['status'] not in self.VALID_STATUSES:
            errors.append(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
            
        # Validate sources
        if 'sources' in data:
            sources = data['sources']
            if not isinstance(sources, list):
                errors.append("Sources must be a list")
            elif len(sources) == 0:
                errors.append("Sources list cannot be empty")
            elif len(sources) == 1:
                warnings.append("Event has only one source - consider adding more for robustness")
            else:
                # Validate each source
                for i, source in enumerate(sources):
                    if not isinstance(source, dict):
                        errors.append(f"Source {i+1} must be a dictionary")
                        continue
                        
                    required_source_fields = ['title', 'url', 'outlet', 'date']
                    for field in required_source_fields:
                        if field not in source:
                            errors.append(f"Source {i+1} missing required field: {field}")
                            
                    # Validate source date format
                    if 'date' in source and isinstance(source['date'], str):
                        try:
                            datetime.strptime(source['date'], '%Y-%m-%d')
                        except ValueError:
                            errors.append(f"Source {i+1} date must be in YYYY-MM-DD format")
        
        # Check for unknown fields (not strictly an error, but good to know)
        all_valid_fields = set(self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS)
        unknown_fields = set(data.keys()) - all_valid_fields
        if unknown_fields:
            warnings.append(f"Unknown fields: {', '.join(unknown_fields)}")
            
        is_valid = len(errors) == 0
        return is_valid, errors, warnings

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate_single_event.py <event_file.yaml>")
        sys.exit(1)
        
    filepath = sys.argv[1]
    validator = SingleEventValidator()
    is_valid, errors, warnings = validator.validate_event(filepath)
    
    filename = os.path.basename(filepath)
    
    if errors:
        print(f"❌ {filename}")
        for error in errors:
            print(f"  ERROR: {error}")
    elif warnings:
        print(f"⚠️  {filename}")
        for warning in warnings:
            print(f"  WARNING: {warning}")
    else:
        print(f"✅ {filename}")
        print("  All validations passed")
    
    if not is_valid:
        sys.exit(1)

if __name__ == "__main__":
    main()