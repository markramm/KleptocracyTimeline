#!/usr/bin/env python3
"""
Validation Handler with Auto-Fix and Retry Logic
Handles schema validation errors by automatically fixing common issues
"""

import json
import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ValidationHandler:
    """Handle validation errors with automatic fixes and retries"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.known_fixes = {
            "research_priority": self._fix_research_priority,
            "timeline_event": self._fix_timeline_event
        }
        
    def validate_and_fix(self, data: Dict, entity_type: str, 
                        validator_func: callable) -> Tuple[bool, Dict, List[str]]:
        """
        Validate data and attempt to fix validation errors
        
        Returns:
            (success, fixed_data, remaining_errors)
        """
        attempts = 0
        current_data = data.copy()
        
        while attempts < self.max_retries:
            attempts += 1
            
            # Try validation
            is_valid, errors = validator_func(current_data)
            
            if is_valid:
                return True, current_data, []
            
            # Log validation attempt
            logger.info(f"Validation attempt {attempts}/{self.max_retries} failed with {len(errors)} errors")
            
            # Try to fix errors
            fixed_data = self._apply_fixes(current_data, errors, entity_type)
            
            if fixed_data == current_data:
                # No fixes were applied, can't proceed
                logger.warning(f"Unable to fix validation errors after {attempts} attempts")
                break
                
            current_data = fixed_data
            
        # Final validation check
        is_valid, errors = validator_func(current_data)
        return is_valid, current_data, errors
    
    def _apply_fixes(self, data: Dict, errors: List[str], entity_type: str) -> Dict:
        """Apply automatic fixes based on error messages"""
        fixed_data = data.copy()
        
        for error in errors:
            # Fix additional properties errors
            if "Additional properties are not allowed" in error:
                fixed_data = self._remove_additional_properties(fixed_data, error)
            
            # Fix missing required fields
            elif "is a required property" in error:
                fixed_data = self._add_required_field(fixed_data, error, entity_type)
            
            # Fix pattern mismatches
            elif "does not match" in error and "pattern" in error:
                fixed_data = self._fix_pattern_mismatch(fixed_data, error, entity_type)
            
            # Fix type errors
            elif "is not of type" in error:
                fixed_data = self._fix_type_error(fixed_data, error)
            
            # Fix minimum length errors
            elif "is too short" in error or "minLength" in error:
                fixed_data = self._fix_min_length(fixed_data, error)
            
            # Fix enum errors
            elif "is not one of" in error:
                fixed_data = self._fix_enum_error(fixed_data, error)
        
        # Apply entity-specific fixes
        if entity_type in self.known_fixes:
            fixed_data = self.known_fixes[entity_type](fixed_data)
        
        return fixed_data
    
    def _remove_additional_properties(self, data: Dict, error: str) -> Dict:
        """Remove properties that aren't allowed by schema"""
        # Extract field names from error message
        match = re.search(r"'([^']+)'.*were unexpected", error)
        if match:
            unexpected_fields = match.group(1).split("', '")
            for field in unexpected_fields:
                if field in data:
                    logger.info(f"Removing unexpected field: {field}")
                    del data[field]
        return data
    
    def _add_required_field(self, data: Dict, error: str, entity_type: str) -> Dict:
        """Add missing required fields with sensible defaults"""
        match = re.search(r"'([^']+)' is a required property", error)
        if match:
            field = match.group(1)
            logger.info(f"Adding missing required field: {field}")
            
            # Add sensible defaults based on field name
            if field == "id":
                if entity_type == "research_priority":
                    data[field] = f"RT-AUTO-{datetime.now():%Y%m%d%H%M%S}"
                else:
                    data[field] = f"{datetime.now():%Y-%m-%d}--auto-generated"
            
            elif field == "title":
                data[field] = data.get("description", "Auto-generated title")[:100]
            
            elif field == "description":
                data[field] = data.get("title", "Auto-generated description") + " - Additional details pending."
            
            elif field == "date":
                data[field] = datetime.now().strftime('%Y-%m-%d')
            
            elif field == "priority":
                data[field] = 5  # Medium priority
            
            elif field == "status":
                data[field] = "pending"
            
            else:
                # Generic default
                data[field] = "TBD"
        
        return data
    
    def _fix_pattern_mismatch(self, data: Dict, error: str, entity_type: str) -> Dict:
        """Fix fields that don't match required patterns"""
        # Check for pattern errors in different formats
        if "does not match" in error and "pattern" in error:
            # Try to extract field name
            field_match = re.search(r"'([^']+)'.*does not match", error)
            if not field_match:
                field_match = re.search(r"Instance\['([^']+)'\]", error)
            
            if field_match:
                field = field_match.group(1)
                
                if field == "id" and entity_type == "research_priority":
                    # Fix research priority ID pattern
                    if not data.get("id", "").startswith("RT-"):
                        old_id = data.get("id", "")
                        # Convert to valid format
                        clean_id = re.sub(r'[^a-z0-9-]', '-', old_id.lower())
                        data["id"] = f"RT-001-{clean_id}"
                        logger.info(f"Fixed ID pattern: {old_id} -> {data['id']}")
        
        return data
    
    def _fix_type_error(self, data: Dict, error: str) -> Dict:
        """Fix type mismatches"""
        field_match = re.search(r"Instance\['([^']+)'\]", error)
        type_match = re.search(r"is not of type '([^']+)'", error)
        
        if field_match and type_match:
            field = field_match.group(1)
            expected_type = type_match.group(1)
            
            logger.info(f"Fixing type error for {field}: converting to {expected_type}")
            
            if expected_type == "integer":
                try:
                    data[field] = int(data[field])
                except (ValueError, TypeError):
                    data[field] = 5  # Default for priorities/importance
            
            elif expected_type == "string":
                data[field] = str(data[field])
            
            elif expected_type == "array":
                if not isinstance(data[field], list):
                    data[field] = [data[field]] if data[field] else []
        
        return data
    
    def _fix_min_length(self, data: Dict, error: str) -> Dict:
        """Fix minimum length violations"""
        # Look for the actual field name in the error path
        # Pattern: On instance['field_name']:
        field = None
        instance_match = re.search(r"On instance\['([^']+)'\]", error)
        if instance_match:
            field = instance_match.group(1)
        else:
            # Try alternative pattern
            field_match = re.search(r"'([^']+)'.*is too short", error)
            if field_match:
                # This might be the value, not the field name
                value = field_match.group(1)
                # Find which field has this value
                for k, v in data.items():
                    if str(v) == value:
                        field = k
                        break
        
        if field and field in data:
            current_value = str(data.get(field, ""))
            
            # Extract minimum length if specified
            min_length = 10  # default
            length_match = re.search(r"minLength.*?(\d+)", error)
            if length_match:
                min_length = int(length_match.group(1))
            
            if len(current_value) < min_length:
                if field == "title":
                    # Extend title to meet minimum
                    padding_needed = min_length - len(current_value)
                    data[field] = current_value + " [Extended for validation]" if padding_needed > 0 else current_value
                    logger.info(f"Extended {field} to meet minimum length of {min_length}")
                
                elif field == "description":
                    # Extend description
                    data[field] = current_value + " - Additional context and details to meet minimum requirements."
                    logger.info(f"Extended {field} to meet minimum length")
                
                else:
                    # Generic extension for other fields
                    padding = " [Extended to meet requirements]" 
                    data[field] = current_value + padding
                    logger.info(f"Extended {field} to meet minimum length")
        
        return data
    
    def _fix_enum_error(self, data: Dict, error: str) -> Dict:
        """Fix enum value errors"""
        # Look for the field name in the error path
        field = None
        valid_values = []
        
        # Pattern: On instance['field_name']:
        instance_match = re.search(r"On instance\['([^']+)'\]", error)
        if instance_match:
            field = instance_match.group(1)
        
        # Get valid enum values
        enum_match = re.search(r"is not one of \[([^\]]+)\]", error)
        
        if field and field in data and enum_match:
            valid_values = [v.strip().strip("'\"u") for v in enum_match.group(1).split(',')]
            
            if field == "status":
                data[field] = "pending"  # Safe default
            elif field == "verification_status":
                data[field] = "pending"  # Safe default
            elif valid_values:
                data[field] = valid_values[0]  # Use first valid option
            
            logger.info(f"Fixed enum error for {field}: set to {data[field]}")
        
        return data
    
    def _fix_research_priority(self, data: Dict) -> Dict:
        """Apply research priority specific fixes"""
        # Ensure ID format
        if "id" in data and not data["id"].startswith("RT-"):
            data["id"] = f"RT-{data['id']}"
        
        # Ensure valid priority range - handle string values
        if "priority" in data:
            try:
                # Try to convert to int
                priority_val = data.get("priority", 5)
                if isinstance(priority_val, str):
                    # Try to extract number from string
                    if priority_val.lower() in ['high', 'critical', 'urgent']:
                        priority_val = 9
                    elif priority_val.lower() in ['medium', 'normal']:
                        priority_val = 5
                    elif priority_val.lower() in ['low']:
                        priority_val = 2
                    else:
                        # Try to extract any number from string
                        import re
                        num_match = re.search(r'\d+', str(priority_val))
                        if num_match:
                            priority_val = int(num_match.group())
                        else:
                            priority_val = 5  # default
                data["priority"] = max(1, min(10, int(priority_val)))
            except (ValueError, TypeError):
                data["priority"] = 5  # Safe default
        
        # Handle estimated_importance similarly
        if "estimated_importance" in data:
            try:
                importance = int(data["estimated_importance"])
                data["estimated_importance"] = max(1, min(10, importance))
            except (ValueError, TypeError):
                data["estimated_importance"] = 5
        
        # Clean up dates
        for date_field in ["created_date", "updated_date", "completion_date"]:
            if date_field in data and data[date_field]:
                try:
                    # Parse and reformat date
                    if isinstance(data[date_field], str) and len(data[date_field]) > 10:
                        data[date_field] = data[date_field][:10]
                except:
                    data[date_field] = datetime.now().strftime('%Y-%m-%d')
        
        return data
    
    def _fix_timeline_event(self, data: Dict) -> Dict:
        """Apply timeline event specific fixes"""
        # Ensure date format
        if "date" in data:
            try:
                # Parse various date formats
                date_str = str(data["date"])
                if len(date_str) > 10:
                    date_str = date_str[:10]
                data["date"] = date_str
            except:
                data["date"] = datetime.now().strftime('%Y-%m-%d')
        
        # Ensure importance range
        if "importance" in data:
            data["importance"] = max(1, min(10, int(data.get("importance", 5))))
        
        # Ensure sources is array
        if "sources" in data and not isinstance(data["sources"], list):
            data["sources"] = [data["sources"]] if data["sources"] else []
        
        return data
    
    def sanitize_for_schema(self, data: Dict, entity_type: str) -> Dict:
        """
        Pre-emptively sanitize data to match schema requirements
        Called before initial validation attempt
        """
        sanitized = data.copy()
        
        # Remove None values
        sanitized = {k: v for k, v in sanitized.items() if v is not None}
        
        # Apply entity-specific sanitization
        if entity_type in self.known_fixes:
            sanitized = self.known_fixes[entity_type](sanitized)
        
        return sanitized


# Global validation handler instance
validation_handler = ValidationHandler()

def handle_validation_with_retry(data: Dict, entity_type: str, 
                                validator_func: callable) -> Tuple[bool, Dict, List[str]]:
    """
    Convenience function to validate and fix data with retries
    
    Returns:
        (success, fixed_data, remaining_errors)
    """
    # Pre-sanitize the data
    sanitized_data = validation_handler.sanitize_for_schema(data, entity_type)
    
    # Validate and fix with retries
    return validation_handler.validate_and_fix(sanitized_data, entity_type, validator_func)