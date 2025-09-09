#!/usr/bin/env python3
"""
Test Validation Handler with Intentional Errors
Verifies that the validation system can automatically fix common errors
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.validation_handler import ValidationHandler, handle_validation_with_retry
from utils.logging_system import validate_timeline_event, validate_research_priority

def test_missing_required_fields():
    """Test fixing missing required fields"""
    print("\n=== Testing Missing Required Fields ===")
    
    # Research priority missing required fields
    priority_data = {
        "title": "Test Priority",
        "description": "This is a test priority for validation"
        # Missing: id, priority, status
    }
    
    print(f"Input data: {json.dumps(priority_data, indent=2)}")
    
    is_valid, fixed_data, errors = handle_validation_with_retry(
        priority_data, "research_priority", validate_research_priority
    )
    
    print(f"Valid after fix: {is_valid}")
    print(f"Fixed data: {json.dumps(fixed_data, indent=2)}")
    print(f"Remaining errors: {errors}")
    
    assert "id" in fixed_data, "ID should be added"
    assert fixed_data["id"].startswith("RT-"), "ID should have correct prefix"
    assert "priority" in fixed_data, "Priority should be added"
    assert "status" in fixed_data, "Status should be added"
    print("✓ Missing fields were successfully added")

def test_pattern_mismatch():
    """Test fixing pattern mismatches"""
    print("\n=== Testing Pattern Mismatch ===")
    
    # Research priority with invalid ID pattern
    priority_data = {
        "id": "invalid-id-format",  # Should start with RT-
        "title": "Test Priority with Bad ID",
        "description": "Testing pattern mismatch correction",
        "priority": 7,
        "status": "pending"
    }
    
    print(f"Input data: {json.dumps(priority_data, indent=2)}")
    
    is_valid, fixed_data, errors = handle_validation_with_retry(
        priority_data, "research_priority", validate_research_priority
    )
    
    print(f"Valid after fix: {is_valid}")
    print(f"Fixed data: {json.dumps(fixed_data, indent=2)}")
    
    assert fixed_data["id"].startswith("RT-"), f"ID should be fixed to start with RT-, got: {fixed_data['id']}"
    print("✓ Pattern mismatch was successfully fixed")

def test_type_errors():
    """Test fixing type errors"""
    print("\n=== Testing Type Errors ===")
    
    # Timeline event with wrong types
    event_data = {
        "id": "2024-01-01--test-event",
        "date": "2024-01-01",
        "title": "Test Event with Type Errors",
        "description": "Testing type error correction mechanisms",
        "importance": "5",  # Should be integer
        "sources": "single source string"  # Should be array
    }
    
    print(f"Input data: {json.dumps(event_data, indent=2)}")
    
    is_valid, fixed_data, errors = handle_validation_with_retry(
        event_data, "timeline_event", validate_timeline_event
    )
    
    print(f"Valid after fix: {is_valid}")
    print(f"Fixed data: {json.dumps(fixed_data, indent=2)}")
    
    assert isinstance(fixed_data.get("importance"), int), "Importance should be converted to integer"
    assert isinstance(fixed_data.get("sources"), list), "Sources should be converted to array"
    print("✓ Type errors were successfully fixed")

def test_enum_errors():
    """Test fixing enum value errors"""
    print("\n=== Testing Enum Errors ===")
    
    # Research priority with invalid enum value
    priority_data = {
        "id": "RT-001-test-enum",
        "title": "Test Priority with Bad Status",
        "description": "Testing enum value correction",
        "priority": 5,
        "status": "invalid_status"  # Not in allowed enum
    }
    
    print(f"Input data: {json.dumps(priority_data, indent=2)}")
    
    is_valid, fixed_data, errors = handle_validation_with_retry(
        priority_data, "research_priority", validate_research_priority
    )
    
    print(f"Valid after fix: {is_valid}")
    print(f"Fixed data: {json.dumps(fixed_data, indent=2)}")
    
    valid_statuses = ["pending", "in_progress", "completed", "blocked", "abandoned"]
    assert fixed_data["status"] in valid_statuses, f"Status should be valid enum value, got: {fixed_data['status']}"
    print("✓ Enum error was successfully fixed")

def test_minimum_length():
    """Test fixing minimum length violations"""
    print("\n=== Testing Minimum Length ===")
    
    # Timeline event with too-short fields
    event_data = {
        "id": "2024-01-01--short",
        "date": "2024-01-01",
        "title": "Short",  # Too short (min 10 chars)
        "description": "Too short"  # Too short (min 20 chars)
    }
    
    print(f"Input data: {json.dumps(event_data, indent=2)}")
    
    is_valid, fixed_data, errors = handle_validation_with_retry(
        event_data, "timeline_event", validate_timeline_event
    )
    
    print(f"Valid after fix: {is_valid}")
    print(f"Fixed data: {json.dumps(fixed_data, indent=2)}")
    
    assert len(fixed_data["title"]) >= 10, f"Title should be extended to min length, got: {len(fixed_data['title'])} chars"
    assert len(fixed_data["description"]) >= 20, f"Description should be extended to min length, got: {len(fixed_data['description'])} chars"
    print("✓ Minimum length violations were successfully fixed")

def test_additional_properties():
    """Test handling additional properties"""
    print("\n=== Testing Additional Properties ===")
    
    # Priority with extra fields (should be allowed with our flexible schema)
    priority_data = {
        "id": "RT-001-extra-fields",
        "title": "Test Priority with Extra Fields",
        "description": "Testing additional properties handling",
        "priority": 5,
        "status": "pending",
        "custom_field": "custom value",
        "generation_method": "test_suite",
        "source_document": "test.pdf"
    }
    
    print(f"Input data: {json.dumps(priority_data, indent=2)}")
    
    is_valid, fixed_data, errors = handle_validation_with_retry(
        priority_data, "research_priority", validate_research_priority
    )
    
    print(f"Valid after fix: {is_valid}")
    print(f"Fixed data: {json.dumps(fixed_data, indent=2)}")
    print(f"Remaining errors: {errors}")
    
    # With flexible schema, additional properties should be allowed
    assert is_valid, "Should be valid with additional properties"
    assert "custom_field" in fixed_data, "Additional properties should be preserved"
    print("✓ Additional properties are correctly handled")

def test_complex_validation_errors():
    """Test fixing multiple validation errors in one document"""
    print("\n=== Testing Complex Validation Errors ===")
    
    # Document with multiple issues
    priority_data = {
        "title": "Test",  # Too short
        "description": "Short desc",  # Too short
        "priority": "high",  # Wrong type
        "status": "working"  # Invalid enum
        # Missing: id
    }
    
    print(f"Input data: {json.dumps(priority_data, indent=2)}")
    
    is_valid, fixed_data, errors = handle_validation_with_retry(
        priority_data, "research_priority", validate_research_priority
    )
    
    print(f"Valid after fix: {is_valid}")
    print(f"Fixed data: {json.dumps(fixed_data, indent=2)}")
    print(f"Remaining errors: {errors}")
    
    # Check all fixes were applied
    assert "id" in fixed_data and fixed_data["id"].startswith("RT-"), "ID should be added with correct prefix"
    assert len(fixed_data["title"]) >= 10, "Title should be extended"
    assert len(fixed_data["description"]) >= 20, "Description should be extended"
    assert isinstance(fixed_data["priority"], int), "Priority should be integer"
    assert fixed_data["status"] in ["pending", "in_progress", "completed", "blocked", "abandoned"], "Status should be valid"
    
    print("✓ Multiple validation errors were successfully fixed")

def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\n=== Testing Edge Cases ===")
    
    # Priority with out-of-range values
    priority_data = {
        "id": "RT-001-edge-case",
        "title": "Test Priority with Edge Cases",
        "description": "Testing boundary conditions and edge cases",
        "priority": 15,  # Above max (10)
        "status": "pending",
        "estimated_importance": -5  # Below min (1)
    }
    
    print(f"Input data: {json.dumps(priority_data, indent=2)}")
    
    is_valid, fixed_data, errors = handle_validation_with_retry(
        priority_data, "research_priority", validate_research_priority
    )
    
    print(f"Valid after fix: {is_valid}")
    print(f"Fixed data: {json.dumps(fixed_data, indent=2)}")
    
    assert 1 <= fixed_data["priority"] <= 10, f"Priority should be clamped to range, got: {fixed_data['priority']}"
    if "estimated_importance" in fixed_data:
        assert fixed_data["estimated_importance"] >= 1, "Importance should be at least 1"
    print("✓ Edge cases were successfully handled")

def run_all_tests():
    """Run all validation tests"""
    print("=" * 60)
    print("VALIDATION HANDLER TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_missing_required_fields,
        test_pattern_mismatch,
        test_type_errors,
        test_enum_errors,
        test_minimum_length,
        test_additional_properties,
        test_complex_validation_errors,
        test_edge_cases
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)